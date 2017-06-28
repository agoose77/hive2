import os
from collections import namedtuple, defaultdict
from collections.abc import KeysView
from functools import lru_cache, partial
from itertools import product
from logging import getLogger
from struct import pack, unpack_from, calcsize
from threading import Event
from weakref import WeakKeyDictionary

from hive.debug import ReportedDebugContextBase
from hive.protocols import Nameable

from .utils import pack_pascal_string, unpack_pascal_string
from .network import Server, Client

from ...importer import get_hook
from ...models import model
from ...observer import Observable

HivemapConnection = namedtuple("Connection", "from_node from_name to_node to_name")


def id_generator(i=0):
    while True:
        yield i
        i += 1


class OpCodes:
    (register_root, pull_in, push_out, trigger,
     pretrigger, add_breakpoint, skip_breakpoint,
     remove_breakpoint, hit_breakpoint) = range(9)


ContainerCandidates = namedtuple("ContainerCandidates", "containers paths")
ContainerPairInfo = namedtuple("PairInfo", "source_container_name target_container_name hivemap_path")
ContainerBeeReference = namedtuple("ContainerBeeReference", "container_id bee_container_name")


class NetworkDebugContext(ReportedDebugContextBase):
    """Context manager to communicate debug information with remote debugger (server)"""

    def __init__(self, logger=None, host=None, port=None):
        self._container_hives = WeakKeyDictionary()
        self._container_hive_ref_to_id = {}

        self._id_generator = id_generator()

        self._client = Client(host, port)
        self._client.on_received.subscribe(self._on_received_response)
        self._client.on_disconnected.subscribe(self._on_disconnected)

        self._breakpoints = {}

        if logger is None:
            logger = getLogger(__name__)

        self._logger = logger

    def __enter__(self):
        super().__enter__()

        self._client.launch()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self._client.stop()

        except Exception:
            self._logger.exception()

        super().__exit__(exc_type, exc_val, exc_tb)

    def _clear_breakpoints(self):
        """Unset all breakpoints and clear them"""
        for breakpoint in self._breakpoints.values():
            self._unset_breakpoint(breakpoint)

        self._breakpoints.clear()

    def _on_disconnected(self):
        self._clear_breakpoints()

    def report_trigger(self, source_bee_ref, target_bee_ref):
        """Report a trigger operation

        :param source_bee_ref: weakref of source bee
        :param target_bee_ref: weakref of target bee
        """
        self._on_operation(OpCodes.trigger, source_bee_ref, target_bee_ref)

    def report_pretrigger(self, source_bee_ref, target_bee_ref):
        """Report a pre-trigger operation

        :param source_bee_ref: weakref of source bee
        :param target_bee_ref: weakref of target bee
        """
        self._on_operation(OpCodes.pretrigger, source_bee_ref, target_bee_ref)

    def report_push_out(self, source_bee_ref, target_ref, data):
        """Report a push-out operation

        :param source_bee_ref: weakref of source bee
        :param target_bee_ref: weakref of target bee
        :param data: data pushed from source bee
        """
        self._on_operation(OpCodes.push_out, source_bee_ref, target_ref, data)

    def report_pull_in(self, source_bee_ref, target_ref, data):
        """Report a pull-in operation

        :param source_bee_ref: weakref of source bee
        :param target_bee_ref: weakref of target bee
        :param data: data pulled from source bee
        """
        self._on_operation(OpCodes.pull_in, source_bee_ref, target_ref, data)

    def _on_received_response(self, response):
        """Server response callback

        :param response: byte string
        """
        opcode, = unpack_from('B', response)
        body = response[calcsize('B'):]

        if opcode == OpCodes.add_breakpoint:
            self._add_breakpoint(body)

        elif opcode == OpCodes.remove_breakpoint:
            self._remove_breakpoint(body)

        elif opcode == OpCodes.skip_breakpoint:
            self._skip_breakpoint(body)

        else:
            raise ValueError("Invalid OPCODE: '{}'".format(opcode))

    def _add_breakpoint(self, message):
        """Add breakpoint to breakpoints dict (internal)

        :param message: byte string
        """

        container_id, = unpack_from('B', message)
        bee_container_name, read_bytes = unpack_pascal_string(message, 1)

        print("DBG::Add breakpoint!", [bee_container_name])

        bee_container_ref = container_id, bee_container_name
        self._breakpoints[bee_container_ref] = Event()

    def _remove_breakpoint(self, message):
        """Remove breakpoint from breakpoints dict (internal)

        :param message: byte string
        """
        container_id, = unpack_from('B', message)
        bee_container_name, read_bytes = unpack_pascal_string(message, 1)
        print("DBG::Remove breakpoint!", [bee_container_name])

        bee_container_ref = container_id, bee_container_name
        breakpoint = self._breakpoints.pop(bee_container_ref)
        self._unset_breakpoint(breakpoint)

    def _skip_breakpoint(self, message):
        """Skip set breakpoint (internal)

        :param message: byte string
        """
        container_id, = unpack_from('B', message)
        bee_container_name, read_bytes = unpack_pascal_string(message, 1)

        bee_container_ref = container_id, bee_container_name
        breakpoint = self._breakpoints[bee_container_ref]

        print("DBG::Skip breakpoint!", bee_container_name)
        self._unset_breakpoint(breakpoint)

    def _unset_breakpoint(self, breakpoint):
        """Attempt to clear a triggered breakpoint

        :param breakpoint: breakpoint info (container id, container name)
        """
        try:
            breakpoint.set()
            breakpoint.clear()

        except RuntimeError:
            pass

    def _send_command(self, opcode, payload):
        """Send command to server

        :param opcode: opcode integer (byte)
        :param payload: payload (byte string)
        """
        serialised = pack('B', opcode) + payload
        self._client.send(serialised)

    def _send_operation(self, opcode, root_hive_id, source_container_name, target_container_name, data):
        """Send operation command to server

        :param opcode: opcode integer (byte)
        :param root_hive_id: ID of root hive (byte)
        :param source_container_name: source container name (str)
        :param target_container_name: target container name (str)

        :param data: payload (byte string)
        """
        serialised = pack('B', root_hive_id) + pack_pascal_string(source_container_name) + \
                     pack_pascal_string(target_container_name)

        if opcode != OpCodes.trigger:
            serialised += pack_pascal_string(repr(data))

        self._send_command(opcode, serialised)

    def _send_container_hive_id(self, root_hive_id, container_hive_path):
        """Send command to register hive ID on server. Sends file path of hive

        :param root_hive_id: ID of root hive (byte)
        :param container_hive_path: file_path of container hive
        """
        data = pack_pascal_string(container_hive_path) + pack('B', root_hive_id)
        self._send_command(OpCodes.register_root, data)

    def _send_hit_breakpoint(self, root_hive_id, container_name):
        """Send OpCodes.hive_breakpoint command to server

        :param root_hive_id: ID of root hive (byte)
        :param container_name: name of bee relative to root hive
        """
        data = pack('B', root_hive_id) + pack_pascal_string(container_name)
        self._send_command(OpCodes.hit_breakpoint, data)

    @staticmethod
    def _find_container_candidates(bee):
        """Find hives containing the hives to which a given bee belongs.
        e.g SomeHive.OtherHive.FooBee -> {ref(<HiveObject ...>) : (OtherHive, FooBee)}

        :param bee: bee instance
        """
        if not isinstance(bee, Nameable):
            raise TypeError("Bee is not Nameable")

        paths = defaultdict(set)
        # Iterate over parent infos, find path relative to parent's container (to find parent_node_name.bee_name)
        for info in bee._hive_runtime_aliases:
            parent_ref, bee_name = info
            parent = parent_ref()

            # For each parent runtime info, store path relative to top-level container
            for runtime_alias in parent._hive_runtime_aliases:
                container_ref, node_name = runtime_alias

                paths[container_ref].add((node_name, bee_name))

        return paths

    @lru_cache()
    def _get_hivemap_connections(self, file_path):
        """Parse all connections belonging to hivemap with given file path

        :param file_path: file path of hivemap
        """
        hivemap = model.Hivemap.fromfile(file_path)
        name_to_hive = {n.identifier: n for n in hivemap.nodes if n.family == "HIVE"}

        connections = set()

        for connection in hivemap.connections:
            from_identifier = connection.from_node
            to_identifier = connection.to_node

            if from_identifier not in name_to_hive:
                continue

            if to_identifier not in name_to_hive:
                continue

            connection = HivemapConnection(from_identifier, connection.output_name,
                                           to_identifier, connection.input_name)
            connections.add(connection)

        return connections

    @lru_cache()
    def _find_container_pair_info(self, source_bee_ref, target_bee_ref):
        """Find the source bee name, target bee name and container hivemap file_path from two bee references

        :return ContainerPairInfo(...)
        """
        source_bee = source_bee_ref()
        target_bee = target_bee_ref()

        source_candidates = self._find_container_candidates(source_bee)
        target_candidates = self._find_container_candidates(target_bee)

        # Find root hives which contain both
        containers = set(source_candidates).intersection(target_candidates)

        try:
            containing_hive_ref = containers.pop()

        except KeyError:
            self._logger.warn("Bee is not a container member")
            return None

        assert not containers, "Containers cannot have multiple intersections!"

        try:
            parent_bind_class = containing_hive_ref()._hive_object._hive_parent_class

        except AttributeError:
            self._logger.warn("Bee is not a container member")
            return None

        # Find hivemap file path
        importer = get_hook()
        find_loader_result = importer.find_loader_result_for_class

        # If this fails, not a hivemap hive
        try:
            loader_result = find_loader_result(parent_bind_class)

        except ValueError:
            return None

        hivemap_file_path = loader_result.module.__file__
        connections = self._get_hivemap_connections(hivemap_file_path)

        # Iterate over potential combinations of source names and target names.
        # If they are found in the hivemap connection set, these are the valid names
        for source_name, target_name in product(source_candidates[containing_hive_ref],
                                                target_candidates[containing_hive_ref]):
            candidate = HivemapConnection(*(source_name + target_name))
            if candidate not in connections:
                continue

            source_bee_name = "{}.{}".format(*source_name)
            target_bee_name = "{}.{}".format(*target_name)
            return ContainerPairInfo(source_bee_name, target_bee_name, hivemap_file_path)

    @lru_cache()
    def _get_container_hive_id(self, container_hive_path):
        """Generate a unique id for a given file-path

        :param container_hive_path: file path of hive
        """
        hive_id = next(self._id_generator)
        self._send_container_hive_id(hive_id, container_hive_path)
        return hive_id

    def _on_operation(self, opcode, source_bee_ref, target_bee_ref, data=None):
        """Send operation information to server

        :param opcode: opcode integer (byte)
        :param source_container_name: source container name (str)
        :param target_container_name: target container name (str)

        :param data: payload (byte string)
        """
        container_pair_info = self._find_container_pair_info(source_bee_ref, target_bee_ref)

        # We require a container_pair_info object to proceed
        if container_pair_info is None:
            return

        container_hive_id = self._get_container_hive_id(container_pair_info.hivemap_path)

        print("DBG::Report", container_pair_info, opcode)

        # Send operation ...
        self._send_operation(opcode, container_hive_id, container_pair_info.source_container_name,
                             container_pair_info.target_container_name, data)

        # Check if any breakpoints are set on involved bees
        self._check_for_breakpoint(container_pair_info.source_container_name, container_hive_id,
                                   container_pair_info.hivemap_path)
        self._check_for_breakpoint(container_pair_info.target_container_name, container_hive_id,
                                   container_pair_info.hivemap_path)

    def _check_for_breakpoint(self, bee_container_name, container_hive_id, hivemap_path):
        """Determine if breakpoint exists, and if so, wait for it

        :param bee_container_name: source container name (str)
        :param container_hive_id: ID of container hive
        :param hivemap_path: file_path of container hive
        """

        # Check for breakpoint on pin
        bee_container_ref = container_hive_id, bee_container_name

        try:
            breakpoint = self._breakpoints[bee_container_ref]

        except KeyError:
            return

        self._send_hit_breakpoint(container_hive_id, bee_container_name)
        file_name = os.path.basename(hivemap_path)

        print("Hit breakpoint @ {} - {}".format(file_name, bee_container_name))
        breakpoint.wait()


class EditorDebugController:
    """Bound editor debug controller.

    Unique to Hivemap type for active session.
    """

    on_push_out = Observable()
    on_pull_in = Observable()
    on_trigger = Observable()
    on_pre_trigger = Observable()
    on_breakpoint_hit = Observable()
    on_breakpoint_added = Observable()
    on_breakpoint_removed = Observable()
    on_io = Observable()

    def __init__(self, file_path):
        self._breakpoints = set()
        self._file_path = file_path

        self._request_close = None

    @property
    def breakpoints(self):
        return KeysView(self._breakpoints)

    @property
    def file_path(self):
        return self._file_path

    def close(self):
        self._request_close()

    def on_closed(self):
        for breakpoint in self._breakpoints:
            self.on_breakpoint_removed(breakpoint)

    def add_breakpoint(self, bee_name):
        assert bee_name not in self._breakpoints
        self._breakpoints.add(bee_name)

        data = pack_pascal_string(bee_name)
        self.send_operation(OpCodes.add_breakpoint, data)
        self.on_breakpoint_added(bee_name)

    def remove_breakpoint(self, bee_name):
        self._breakpoints.remove(bee_name)
        data = pack_pascal_string(bee_name)

        self.send_operation(OpCodes.remove_breakpoint, data)
        self.on_breakpoint_removed(bee_name)

    def skip_breakpoint(self, bee_name):
        if bee_name not in self._breakpoints:
            raise ValueError

        data = pack_pascal_string(bee_name)
        self.send_operation(OpCodes.skip_breakpoint, data)

    def send_operation(self, opcode, data):
        raise NotImplementedError

    def process_operation(self, opcode, data):
        source_container_name, read_bytes = unpack_pascal_string(data)
        offset = read_bytes

        if opcode == OpCodes.hit_breakpoint:
            self.on_breakpoint_hit(source_container_name)

        else:
            target_container_name, read_bytes = unpack_pascal_string(data, offset=offset)
            offset += read_bytes

            if opcode == OpCodes.push_out:
                value, read_bytes = unpack_pascal_string(data, offset=offset)
                self.on_push_out(source_container_name, target_container_name, value)

            elif opcode == OpCodes.pull_in:
                value, read_bytes = unpack_pascal_string(data, offset=offset)
                self.on_pull_in(source_container_name, target_container_name, value)

            elif opcode == OpCodes.trigger:
                self.on_trigger(source_container_name, target_container_name)

            elif opcode == OpCodes.pretrigger:
                self.on_pre_trigger(source_container_name, target_container_name)


class NetworkDebugSession:
    """Interface to editor debugging features"""
    debug_controller_class = EditorDebugController

    on_created_controller = Observable()
    on_destroyed_controller = Observable()

    def __init__(self):
        self._container_id_to_filepath = {}
        self._filepath_to_container_id = {}

        self._breakpoints = {}
        self._debug_controllers = {}

        self._request_close = None
        self._send_data = None

    def is_debugging_hivemap(self, file_path):
        sanitised = self._sanitise_path(file_path)
        return sanitised in self._filepath_to_container_id

    def _create_hive_debug_controller(self, container_id, file_path):
        # Create debug controller
        controller = self.__class__.debug_controller_class(file_path)
        controller.send_operation = partial(self._send_data_from, container_id)
        controller._request_close = self.close

        self.on_created_controller(controller)

        return controller

    def _on_received_register_container_id(self, container_id, file_path):
        sanitised_path = self._sanitise_path(file_path)

        self._container_id_to_filepath[container_id] = sanitised_path
        self._filepath_to_container_id[sanitised_path] = container_id

        self._debug_controllers[container_id] = self._create_hive_debug_controller(container_id, sanitised_path)

    def _send_data_from(self, container_id, opcode, data):
        full_data = pack('BB', opcode, container_id) + data
        self._send_data(full_data)

    @staticmethod
    def _sanitise_path(file_path):
        return os.path.normpath(file_path)

    def process_data(self, data):
        opcode, = unpack_from('B', data)
        offset = 1

        if opcode == OpCodes.register_root:
            file_path, read_bytes = unpack_pascal_string(data, offset=offset)
            offset += read_bytes

            container_id, = unpack_from('B', data, offset=offset)
            offset += 1

            self._on_received_register_container_id(container_id, file_path)

        else:
            container_id, = unpack_from('B', data, offset=offset)
            offset += 1

            debug_controller = self._debug_controllers[container_id]
            remaining_data = data[offset:]

            debug_controller.process_operation(opcode, remaining_data)

    def on_closed(self):
        for controller in self._debug_controllers.values():
            controller.on_closed()

            self.on_destroyed_controller(controller)

    def close(self):
        self._request_close()


class NetworkDebugManager:
    """Manages sessions for Hivemap debugging"""

    session_class = NetworkDebugSession

    on_created_session = Observable()
    on_closed_session = Observable()

    def __init__(self, host=None, port=None):
        self._server = Server(host, port)
        self._server.on_received.subscribe(self._on_received)
        self._server.on_connected.subscribe(self._on_connected)
        self._server.on_disconnected.subscribe(self._on_disconnected)

        self._session = None
        self._server.launch()

    @property
    def session(self):
        return self._session

    def _create_session(self):
        session = self.__class__.session_class()
        session._send_data = partial(self._send_data, session)
        session._request_close = partial(self._session_request_close, session)

        self.on_created_session(session)

        return session

    def _session_request_close(self, session):
        self._close_session(session)
        self._server.disconnect()

    def _close_session(self, session):
        if session is not self._session:
            raise RuntimeError("Session not active session")

        session.on_closed()

        self.on_closed_session(session)

        session._request_close = None
        session._send_data = None

        self._session = None

    def _send_data(self, session, data):
        if session is not self._session:
            raise RuntimeError("No active session")

        self._server.send(data)

    def _on_received(self, data):
        if self._session is None:
            raise RuntimeError("No active session")

        self._session.process_data(data)

    def _on_connected(self):
        if self._session is not None:
            raise RuntimeError("Expected no active session")

        self._session = self._create_session()

    def _on_disconnected(self):
        if self._session is None:
            return

        self._close_session(self._session)
