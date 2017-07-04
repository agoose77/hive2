import logging
from keyword import iskeyword

from .code_generator import parameter_group_array_to_dict, parameter_group_dict_to_array
from .connection import Connection, ConnectionType
from .factory import BeeNodeFactory, HiveNodeFactory
from .history import CommandLogManager
from .inspector import HiveNodeInspector, BeeNodeInspector
from .models import model
from .node import FOLD_NODE_REFERENCE_PATH, NodeTypes
from .observer import Observable
from .utils import start_value_from_type, is_identifier, camelcase_to_underscores

from hive import validate_external_name


def _sanitise_node_name(variable_name):
    variable_name = variable_name.lstrip('_')

    if ' ' in variable_name:
        raise ValueError("Invalid name '{}': contains spaces".format(variable_name))

    if variable_name[0].isdigit():
        raise ValueError("Invalid name '{}': starts with digit".format(variable_name))

    while iskeyword(variable_name):
        variable_name += "_"

    assert is_identifier(variable_name), "Invalid variable name, expected python identifier"
    return variable_name


def _validate_node_name(name):
    if name.startswith('_'):
        raise ValueError("Name must not start with '_'")

    if not is_identifier(name):
        raise ValueError("Name must be valid python identifier: {}".format(name))

    if iskeyword(name):
        raise ValueError("Name cannot be python keyword: {}".format(name))

    # Check that the wrapper *can* be assigned this name
    validate_external_name(name)


def _get_unique_name(existing_names, base_name):
    """Find unique value of base name which may have a number appended to the end

    :param existing_names: names currently in use
    :param base_name: base of name to use
    """
    # Return name without number if possible
    if base_name not in existing_names:
        return base_name

    i = 0
    while True:
        name = "{}_{}".format(base_name, i)
        if name not in existing_names:
            return name

        i += 1


class NodeConnectionError(Exception):
    pass


class NodeManager(object):

    on_node_created = Observable()
    on_node_destroyed = Observable()
    on_node_moved = Observable()
    on_node_renamed = Observable()

    on_connection_created = Observable()
    on_connection_destroyed = Observable()
    on_connection_reordered = Observable()

    on_pin_folded = Observable()
    on_pin_unfolded = Observable()

    def __init__(self, history, logger=None):
        if history is None:
            history = CommandLogManager()

        self.history = history

        self._bee_node_factory = BeeNodeFactory()
        self._hive_node_factory = HiveNodeFactory()

        self._hive_node_inspector = HiveNodeInspector()
        self._bee_node_inspector = BeeNodeInspector(find_by_reference_path=self.find_by_reference_path)

        self.docstring = ""
        self.nodes = {}

        if logger is None:
            logger = logging.getLogger(repr(self))
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        self._logger = logger

    def _unique_name_from_reference_path(self, reference_path):
        obj_name = reference_path.split(".")[-1]
        identifier = camelcase_to_underscores(obj_name)
        identifier = _sanitise_node_name(identifier)
        return _get_unique_name(self.nodes, identifier)

    def find_by_reference_path(self, reference_path):
        """Return dict of nodes with the given reference path

        :param reference_path: reference path of node
        """
        return {name: node for name, node in self.nodes.items() if node.reference_path == reference_path}

    def _add_connection(self, connection):
        """Connect connection and push to history.

        :param connection: connection to connect
        """
        connection.connect()

        # Ask GUI to perform connection
        self.on_connection_created(connection)

        output_pin = connection.output_pin
        input_pin = connection.input_pin

        self._logger.info("Created connection between {}.{} and {}.{}"
                          .format(output_pin.node, output_pin.name, input_pin.node, input_pin.name))
        self.history.record_command(lambda: self._add_connection(connection),
                                    lambda: self.delete_connection(connection))

    def create_connection(self, output_pin, input_pin):
        """Create connection between two pins.

        :param output_pin: output pin from which the connection originates
        :param input_pin: input pin at which the connection is completed
        """
        # Check pin isn't folded
        if input_pin.is_folded:
            raise NodeConnectionError("Cannot connect to a folded pin")

        # Check connection is permitted
        result = Connection.get_connection_type(output_pin, input_pin)

        if result == ConnectionType.INVALID:
            raise NodeConnectionError("Can't connect {} to {}".format(output_pin, input_pin))

        connection = Connection(output_pin, input_pin, is_trigger=(result == ConnectionType.TRIGGER))

        # Must call connection.connect()
        self._add_connection(connection)

    def delete_connection(self, connection):
        """Delete connection and write to history.

        :param connection: connection object
        """
        # Ask GUI to perform connection
        self.on_connection_destroyed(connection)

        connection.delete()

        self._logger.info("Deleted Connection: {}".format(connection))

        self.history.record_command(lambda: self.delete_connection(connection),
                                    lambda: self._add_connection(connection))

    def delete_connections(self, connections):
        """Remove multiple connections from the model (as a composite operation)

        :param connections: Connection objects
        """
        with self.history.command_context("delete-connection-multiple"):
            for connection in connections:
                self.delete_connection(connection)

    def reorder_connection(self, connection, index):
        """Change connection order relative to other connections for the output pin.

        :param connection: connection object
        :param index: new connection index
        """
        output_pin = connection.output_pin
        old_index = output_pin.connections.index(connection)

        output_pin.reorder_target(connection, index)

        # Ask GUI to reorder connection
        self.on_connection_reordered(connection, index)

        self.history.record_command(lambda: self.reorder_connection(connection, index),
                                    lambda: self.reorder_connection(connection, old_index))

    def get_inspector_for(self, node_type):
        if node_type == NodeTypes.HIVE:
            return self._hive_node_inspector

        elif node_type == NodeTypes.BEE:
            return self._bee_node_inspector

        raise ValueError(node_type)

    def _add_node(self, node):
        """Add node to node dict and write to history.

        :param node: node to add
        """
        self.nodes[node.name] = node

        self.on_node_created(node)

        for pin in node.inputs.values():
            assert not pin.is_folded, (pin.name, pin.node)

        # Ensure node restored to original place
        self.on_node_moved(node, node.position)

        self.history.record_command(lambda: self._add_node(node), lambda: self.delete_node(node))

    def create_node(self, node_type, reference_path, params=None):
        print("CREATE", reference_path)
        if node_type == NodeTypes.HIVE:
            return self._create_hive(reference_path, params)

        elif node_type == NodeTypes.BEE:
            return self._create_bee(reference_path, params)

        raise ValueError(node_type)

    def _create_bee(self, reference_path, params=None):
        """Create a bee node with the given reference path"""
        if params is None:
            params = {}

        name = self._unique_name_from_reference_path(reference_path)
        param_info = self._bee_node_inspector.inspect_configured(reference_path, params)
        node = self._bee_node_factory.new(name, reference_path, params, param_info)

        self._add_node(node)
        return node

    def _create_hive(self, reference_path, params=None):
        """Create a hive node with the given path"""
        print("CREATE", reference_path)
        if params is None:
            params = {}

        name = self._unique_name_from_reference_path(reference_path)

        try:
            param_info = self._hive_node_inspector.inspect_configured(reference_path, params)

        except Exception:
            self._logger.error("Failed to inspect '{}'".format(reference_path))
            raise

        try:
            node = self._hive_node_factory.new(name, reference_path, params, param_info)

        except Exception:
            self._logger.error("Failed to instantiate '{}'".format(reference_path))
            raise

        self._add_node(node)
        return node

    def delete_node(self, node):
        """Remove node and its connections from the model

        :param node: Node object
        """
        if node not in self.nodes.values():
            raise ValueError("Invalid node being deleted")

        if node.is_folded:
            raise RuntimeError("Can't delete folded nodes")

        # Remove connections
        for input_pin in node.inputs.values():
            is_folded = input_pin.is_folded

            # Handle folded nodes
            if is_folded:
                self.unfold_pin(input_pin)
                output_pin = next(iter(input_pin.connections)).output_pin

            for connection in list(input_pin.connections):
                self.delete_connection(connection)

            # Delete folded nodes (only should be one folded node!)
            if is_folded:
                self.delete_node(output_pin.node)

        for output_pin in node.outputs.values():
            self.delete_connections(list(output_pin.connections))

        self.nodes.pop(node.name)

        self.on_node_destroyed(node)

        self.history.record_command(lambda: self.delete_node(node), lambda: self._add_node(node))

    def delete_nodes(self, nodes):
        """Remove multiple nodes and their connections from the model (as a composite operation)

        :param nodes: Node objects
        """
        with self.history.command_context("delete-node-multiple"):
            for node in nodes:
                try:
                    self.delete_node(node)

                except KeyError:
                    continue

    def delete_all_nodes(self):
        nodes_to_delete = set(self.nodes.values())

        # Ignore folded nodes (handled)
        for node in self.nodes.values():
            for pin in node.inputs.values():
                if pin.is_folded:
                    target_connection = next(iter(pin.connections))
                    target_pin = target_connection.output_pin
                    folded_node = target_pin.node

                    nodes_to_delete.remove(folded_node)

        self.delete_nodes(nodes_to_delete)

    def morph_node(self, node, params):
        with self.history.command_context("morph-node"):
            # Record the connected target pins for each IO pin by name
            input_name_to_pins = {n: [c.output_pin for c in p.connections] for n, p in node.inputs.items()}
            output_name_to_pins = {n: [c.input_pin for c in p.connections] for n, p in node.outputs.items()}

            # Unfold and recorded folded pins
            folded_input_names = []
            for pin_name, pin in node.inputs.items():
                if pin.is_folded:
                    folded_input_names.append(pin_name)
                    self.unfold_pin(pin)

            # If this node is folded by another, unfold first and record pin
            folding_parent_pin = None
            if node.is_folded:
                folding_parent_pin = next(c.input_pin for p in node.outputs.values()
                                          for c in p.connections if c.input_pin.is_folded)
                self.unfold_pin(folding_parent_pin)

            node_reference_path = node.reference_path
            node_name = node.name
            node_position = node.position
            node_type = node.node_type

            # Destroy original node
            self.delete_node(node)

            # Create new node
            new_node = self.create_node(node_type, node_reference_path, params)

            # Move and rename
            self.reposition_node(new_node, node_position)
            self.rename_node(new_node, node_name)

            # Find existing connection counterpart candidates
            new_connections = []
            new_folded_pins = []
            for name, pins in input_name_to_pins.items():
                try:
                    input_pin = new_node.inputs[name]

                except KeyError:
                    continue

                for output_pin in pins:
                    new_connections.append((output_pin, input_pin))

                # Make note to try and fold this pin
                if name in folded_input_names:
                    new_folded_pins.append(input_pin)

            for name, pins in output_name_to_pins.items():
                try:
                    output_pin = new_node.outputs[name]

                except KeyError:
                    continue

                for input_pin in pins:
                    new_connections.append((output_pin, input_pin))

            # Create old connections
            for output_pin, input_pin in new_connections:
                try:
                    self.create_connection(output_pin, input_pin)

                except NodeConnectionError:
                    continue

            # Fold all foldable pins
            for pin in new_folded_pins:
                self.fold_pin(pin)

            # If we were folded, refold
            if folding_parent_pin is not None:
                self.fold_pin(folding_parent_pin)

    def set_param_value(self, node, param_type, name, value):
        assert param_type in {'cls_args', 'args', 'meta_args'}, "Invalid param type given"
        if param_type == 'meta_args':
            raise ValueError("Meta args wrapper cannot be edited, node must be recreated")

        with node.make_writable():
            params_dict = node.params[param_type]

        original_value = params_dict[name]
        params_dict[name] = value

        self.history.record_command(lambda: self.set_param_value(node, param_type, name, value),
                                    lambda: self.set_param_value(node, param_type, name, original_value))

    def rename_node(self, node, name, attempt_till_success=False):
        """Rename node with a new identifier

        :param node: Node object
        :param name: new name of node
        :param attempt_till_success: if name is not available, find a valid name based upon it
        """
        if self.nodes.get(name, node) is not node:
            # Try till we succeed
            if attempt_till_success:
                name = _get_unique_name(self.nodes, name)

            else:
                raise ValueError("Can't rename {} to {}".format(node, name))

        _validate_node_name(name)

        # Change key
        old_name = node.name

        self.nodes.pop(old_name)
        self.nodes[name] = node

        # Update name
        with node.make_writable():
            node.name = name

        self.on_node_renamed(node, name)

        self.history.record_command(lambda: self.rename_node(node, name),
                                    lambda: self.rename_node(node, old_name))

    def reposition_node(self, node, position):
        """Re-position node in the model

        :param node: Node object
        :param position: new x, y position
        """
        old_position = node.position

        with node.make_writable():
            node.position = position

        # Move folded nodes too
        dx = position[0] - old_position[0]
        dy = position[1] - old_position[1]

        for pin in node.inputs.values():
            if pin.is_folded:
                target_connection = next(iter(pin.connections))
                target_pin = target_connection.output_pin
                other_node = target_pin.node

                new_position = other_node.position[0] + dx, other_node.position[1] + dy
                self.reposition_node(other_node, new_position)

        self.on_node_moved(node, position)

        self.history.record_command(lambda: self.reposition_node(node, position),
                                    lambda: self.reposition_node(node, old_position))

    def reposition_nodes(self, node_to_position):
        """Re-position multiple nodes in the model (as a composite operation)

        :param node_to_position: dictionary of node, position item pairs
        """
        with self.history.command_context("reposition-multiple"):
            for node, position in node_to_position.items():
                self.reposition_node(node, position)

    def fold_pin(self, pin):
        """Hide pin from node UI, as well as possible connected variable. If no variable, create, connect and hide.
        
        :param pin: IOPin object
        """
        assert pin.is_foldable

        # Create variable
        if not pin.connections:
            # TODO take start value from pin bee?
            params = dict(meta_args=dict(data_type=pin.data_type),
                          args=dict(start_value=start_value_from_type(pin.data_type)))

            # Create variable node, attempt to call it same as pin
            target_node = self._create_hive(FOLD_NODE_REFERENCE_PATH, params)
            target_pin = next(iter(target_node.outputs.values()))

            self.rename_node(target_node, pin.name, attempt_till_success=True)
            self.create_connection(target_pin, pin)

        # Set local pin as folded
        with pin.make_writable():
            pin.is_folded = True

        self.on_pin_folded(pin)

        self.history.record_command(lambda: self.fold_pin(pin), lambda: self.unfold_pin(pin))

    def unfold_pin(self, pin):
        """Expose pin to node UI, as well as possible connected variable. If no variable, create, connect and show.

        :param pin: IOPin object
        """
        assert pin.is_folded
        assert pin.connections

        # Set input pin as folded
        with pin.make_writable():
            pin.is_folded = False

        self.on_pin_unfolded(pin)

        self.history.record_command(lambda: self.unfold_pin(pin), lambda: self.fold_pin(pin))

    def to_string(self):
        hivemap = self.to_hivemap()
        return str(hivemap)

    def load_string(self, data):
        # Validate type
        if not isinstance(data, str):
            raise TypeError("Loaded data should be a string type, not {}".format(type(data)))

        # Read hivemap
        hivemap = model.Hivemap(data)
        self.load_hivemap(hivemap)

    def to_hivemap(self):
        return self._export_to_hivemap(docstring=self.docstring)

    def load_hivemap(self, hivemap):
        with self.history.command_context("load"):
            # Clear nodes first
            self.delete_all_nodes()
            data = self._import_from_hivemap(hivemap)
            self.docstring = data['docstring']

    def cut(self, nodes):
        """Cut nodes to clipboard

        :param nodes: nodes to cut
        """
        with self.history.command_context("cut"):
            clipboard = self.copy(nodes)

            # Delete nodes
            self.delete_nodes(nodes)

        return clipboard

    def copy(self, nodes):
        """Copy nodes to clipboard

        :param nodes: nodes to copy
        """
        with_folded_nodes = set(nodes)

        # Find nodes that are internally folded
        for node in nodes:
            for pin in node.inputs.values():
                if pin.is_folded:
                    target_connection = next(iter(pin.connections))
                    target_pin = target_connection.output_pin
                    target_node = target_pin.node
                    with_folded_nodes.add(target_node)

        return self._export_to_hivemap(with_folded_nodes)

    def paste(self, clipboard, position):
        """Paste nodes from clipboard

        :param position: position of target center of mass of nodes
        """
        with self.history.command_context("paste"):
            data = self._import_from_hivemap(clipboard)
            node_map = data['nodes']

            if not node_map:
                return

            names, nodes = zip(*node_map.items())

            # Find midpoint
            average_x = 0.0
            average_y = 0.0

            for node in nodes:
                average_x += node.position[0]
                average_y += node.position[1]

            average_x /= len(nodes)
            average_y /= len(nodes)

            # Displacement to the center
            offset_x = position[0] - average_x
            offset_y = position[1] - average_y

            # Move nodes to mouse position
            for node in nodes:
                position = node.position[0] + offset_x, node.position[1] + offset_y
                self.reposition_node(node, position)

    def _export_to_hivemap(self, nodes=None, docstring=""):
        if nodes is None:
            nodes = self.nodes.values()

        hivemap = model.Hivemap()
        hivemap.docstring = docstring

        for node in nodes:
            # Create parameter groups
            parameter_groups = parameter_group_dict_to_array(node.params)
            folded_pins = [pin_name for pin_name, pin in node.inputs.items() if pin.is_folded]

            # Serialise HiveNode instance
            if node.node_type == NodeTypes.HIVE:
                family = "HIVE"

            else:
                assert node.node_type == NodeTypes.BEE
                family = "BEE"

            spyder_node = model.Node(identifier=node.name, family=family, reference_path=node.reference_path,
                                     position=node.position, parameter_groups=parameter_groups,
                                     folded_pins=folded_pins)

            hivemap.nodes.append(spyder_node)

        for node in nodes:
            node_name = node.name

            for pin_name, pin in node.outputs.items():
                for connection in pin.connections:
                    target_pin = connection.input_pin
                    target_node = target_pin.node

                    # Omit connections that aren't in the copied nodes
                    if target_node not in nodes:
                        continue

                    is_trigger = connection.is_trigger
                    spyder_connection = model.Connection(node_name, pin_name, target_node.name, target_pin.name,
                                                         is_trigger)
                    hivemap.connections.append(spyder_connection)

        return hivemap

    def _import_from_hivemap(self, hivemap):
        # Create nodes
        # Mapping from original ID to new ID
        id_to_node_name = {}
        node_to_spyder_hive_node = {}
        node_to_spyder_node = {}

        created_nodes = {}

        # Load IO public
        for spyder_node in hivemap.nodes:
            reference_path = spyder_node.reference_path
            params = parameter_group_array_to_dict(spyder_node.parameter_groups)

            if spyder_node.family == "BEE":
                try:
                    node = self._create_bee(reference_path, params)

                except Exception as err:
                    self._logger.exception("Unable to create bee node {}".format(spyder_node.identifier))
                    continue

            else:
                try:
                    node = self._create_hive(reference_path, params)

                except Exception as err:
                    self._logger.exception("Unable to create hive node {}".format(spyder_node.identifier))
                    continue

                # Specific mapping for HIVE nodes only.
                node_to_spyder_hive_node[node] = spyder_node

            node_to_spyder_node[node] = spyder_node

        # Attempt to set common data between IO public and Hives
        for node, spyder_node in node_to_spyder_node.items():
            # Try to use original name, otherwise make unique
            self.rename_node(node, spyder_node.identifier, attempt_till_success=True)

            # Set original position
            self.reposition_node(node, (spyder_node.position.x, spyder_node.position.y))

            # Map original copied ID to new allocated ID
            node_name = node.name
            id_to_node_name[spyder_node.identifier] = node_name
            created_nodes[node_name] = node

        # Recreate connections
        for connection in hivemap.connections:
            try:
                from_id = id_to_node_name[connection.from_node]
                to_id = id_to_node_name[connection.to_node]

            except KeyError:
                self._logger.error("Unable to find all nodes in connection: {}, {}".format(connection.from_node,
                                                                                           connection.to_node))
                continue

            from_node = created_nodes[from_id]
            to_node = created_nodes[to_id]

            try:
                from_pin = from_node.outputs[connection.output_name]
                to_pin = to_node.inputs[connection.input_name]

            except KeyError:
                self._logger.error("Unable to find all node pins in connection: {}.{}, {}.{}"
                                   .format(connection.from_node, connection.output_name, connection.to_node,
                                           connection.input_name))
                continue

            try:
                self.create_connection(from_pin, to_pin)

            except Exception:
                self._logger.exception("Unable to create connection between {}.{}, {}.{}"
                                       .format(connection.from_node, connection.output_name, connection.to_node,
                                               connection.input_name))

        # Fold folded pins
        for node, spyder_node in node_to_spyder_node.items():

            for pin_name in spyder_node.folded_pins:
                try:
                    pin = node.inputs[pin_name]

                except KeyError:
                    self._logger.error("Couldn't find pin {}.{} to fold".format(node.name, pin_name))
                    continue

                self.fold_pin(pin)

        return dict(nodes=created_nodes, docstring=hivemap.docstring)
