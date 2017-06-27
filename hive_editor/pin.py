from hive.typing import data_types_match, MatchFlags
from .data_views import ListView
from .protected_container import ProtectedContainer, RestrictedAttribute
from .sockets import get_colour, get_shape


class MimicFlags(object):
    NONE = 0
    COLOUR = 1
    SHAPE = 2


PIN_MODES = {'pull', 'push', 'any'}
IO_TYPES = {'input', 'output'}


class IOPin(ProtectedContainer):
    def __init__(self, node, name, io_type, data_type, mode="pull", max_connections=-1, restricted_types=None,
                 mimic_flags=MimicFlags.NONE, is_virtual=False, count_proxies=False):
        assert io_type in IO_TYPES, "Invalid io type for pin: '{}".format(io_type)
        assert mode in PIN_MODES, "Invalid mode for pin: '{}'".format(mode)

        # Non-permitted connection types
        if restricted_types is None:
            restricted_types = []

        # Pull rule
        if mode == "pull" and io_type == "input":
            max_connections = 1

        # Mimicking pins
        if mode == "any":
            if not -1 < max_connections <= 1:
                max_connections = 1

            mimic_flags |= MimicFlags.SHAPE

        # Read only
        with self.make_writable():
            self.is_folded = False

        self._name = name
        self._colour = get_colour(data_type)
        self._data_type = data_type
        self._mode = mode
        self._is_trigger = bool(data_types_match(data_type, "trigger", MatchFlags.match_shortest))
        self._io_type = io_type
        self._node = node
        self._restricted_data_types = restricted_types
        self._shape = get_shape(mode)
        self._mimic_flags = mimic_flags
        self._is_virtual = is_virtual

        self._connections = []
        self._connection_count = 0
        self._count_proxies = count_proxies
        self._max_connections = max_connections

    # Read only view
    is_folded = RestrictedAttribute()

    @property
    def name(self):
        return self._name

    @property
    def connections(self):
        return ListView(self._connections)

    @property
    def is_trigger(self):
        return self._is_trigger

    @property
    def data_type(self):
        return self._data_type

    @property
    def is_virtual(self):
        """Whether pin is actually a connectable pin"""
        return self._is_virtual

    @property
    def node(self):
        return self._node

    @property
    def mode(self):
        return self._mode

    @property
    def shape(self):
        return self._shape

    @property
    def colour(self):
        return self._colour

    @property
    def io_type(self):
        return self._io_type

    @property
    def data_type(self):
        return self._data_type

    @property
    def max_connections(self):
        return self._max_connections

    @property
    def mimic_flags(self):
        return self._mimic_flags

    @property
    def is_foldable(self):
        if self.is_folded:
            return False

        # Only hives support folding
        if self.is_virtual:
            return False

        if self.io_type != "input":
            return False

        if self.mode != "pull":
            return False

        if not self.connections:
            return True

        if len(self.connections) == 1:
            target_connection = next(iter(self.connections))
            target_pin = target_connection.output_pin

            # Only allow variables to be folded
            return target_pin.node.is_foldable

        return False

    def can_connect_to(self, other_pin):
        # If a restricted data type
        for data_type in self._restricted_data_types:
            if data_types_match(other_pin.data_type, data_type, MatchFlags.match_shortest):
                return False

        # Limit connections if provided
        if self._connection_count == self._max_connections:
            return False

        return True

    def mimic_other_pin(self, other_pin):
        """Mimic properties of other pin, such as colour or shape

        :param other_pin: IOPin object
        """
        # Update cosmetics for other
        flags = self._mimic_flags

        if flags & MimicFlags.SHAPE:
            self._shape = other_pin.shape

        if flags & MimicFlags.COLOUR:
            self._colour = other_pin.colour

    def unmimic_other_pin(self, other_pin):
        # TODO implement this if necessary
        pass

    def add_connection(self, connection):
        assert connection not in self._connections
        self._connections.append(connection)

        # Determine the "other pin" in this connection, relative to this pin
        if connection.output_pin is self:
            other_pin = connection.input_pin
        else:
            other_pin = connection.output_pin

        # Only increment connection count if the other pin is real, or we count virtual pins
        if self._count_proxies or not other_pin.is_virtual:
            self._connection_count += 1

        # Mimic aesthetics
        self.mimic_other_pin(other_pin)

    def remove_connection(self, connection):
        self._connections.remove(connection)

        # Post connection
        if connection.output_pin is self:
            other_pin = connection.input_pin
        else:
            other_pin = connection.output_pin

        if self._count_proxies or not other_pin.is_virtual:
            self._connection_count -= 1

        self.unmimic_other_pin(other_pin)

    def reorder_target(self, connection, index):
        current_index = self._connections.index(connection)
        del self._connections[current_index]
        self._connections.insert(index, connection)

    def __repr__(self):
        return "<{} pin {}.{}>".format(self._io_type, self._node.name, self.name)
