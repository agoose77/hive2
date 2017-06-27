from collections import OrderedDict

from .data_views import ListView, DictView
from .protected_container import ProtectedContainer, RestrictedAttribute, RestrictedProperty
from .pin import MimicFlags, IOPin


FOLD_NODE_REFERENCE_PATH = "dragonfly.std.Variable"


class NodeTypes(object):
    HIVE, BEE, HELPER = range(3)


class Node(ProtectedContainer):

    def __init__(self, name, node_type, reference_path, params, params_info):
        """
        Container for GUI configuration of HiveObject instance

        :param name: unique node name
        :param reference_path: path to find object representing node (may not exist for certain node types)
        :param params: parameter dictionary containing data about node
        :param params_info: parameter dictionary containing data about params dict
        :return:
        """
        super(Node, self).__init__()

        with self.make_writable():
            self.name = name
            self.tooltip = ""
            self.position = (0.0, 0.0)

        # Read only
        self._node_type = node_type
        self._reference_path = reference_path

        self._params = params
        self._params_info = params_info

        # Pin IO
        self._pin_order = []
        self._inputs = OrderedDict()
        self._outputs = OrderedDict()

    def add_input(self, name, data_type="", mode="pull", max_connections=-1, restricted_types=None,
                  mimic_flags=MimicFlags.NONE, is_virtual=False, count_proxies=False):
        pin = IOPin(self, name, "input", data_type, mode, max_connections, restricted_types, mimic_flags,
                    is_virtual, count_proxies)
        self._inputs[name] = pin
        self._pin_order.append(name)
        return pin

    def add_output(self, name, data_type="", mode="pull", max_connections=-1, restricted_types=None,
                   mimic_flags=MimicFlags.NONE, is_virtual=False, count_proxies=False):
        pin = IOPin(self, name, "output", data_type, mode, max_connections, restricted_types, mimic_flags,
                    is_virtual, count_proxies)
        self._outputs[name] = pin
        self._pin_order.append(name)
        return pin

    @property
    def reference_path(self):
        return self._reference_path

    @property
    def node_type(self):
        return self._node_type

    @property
    def inputs(self):
        return DictView(self._inputs)

    @property
    def outputs(self):
        return DictView(self._outputs)

    @property
    def pin_order(self):
        return ListView(self._pin_order)

    @RestrictedProperty
    def params(self):
        return DictView({k: DictView(v) for k, v in self._params.items()})

    @params.restricted_getter
    def params(self):
        return self._params

    @property
    def params_info(self):
        return DictView({k: DictView(v) for k, v in self._params_info.items()})

    @property
    def is_folded(self):
        for output_pin in self._outputs.values():
            for connection in output_pin.connections:
                if connection.input_pin.is_folded:
                    return True
        return False

    @property
    def is_foldable(self):
        if self.is_folded:
            return False

        all_connections = sum(len(p.connections) for p in self._outputs.values())
        all_connections += sum(len(p.connections) for p in self._inputs.values())

        # If other pin is in use else where
        return all_connections <= 1

    position = RestrictedAttribute()
    name = RestrictedAttribute()
    tooltip = RestrictedAttribute()

    def __repr__(self):
        return "<HiveNode ({})>".format(self.name)
