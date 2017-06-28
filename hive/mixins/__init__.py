from abc import ABC, abstractmethod
from collections import namedtuple
from weakref import ref

from ..contexts import get_building_hive
from ..manager import memo_property

BoundRuntimeInfo = namedtuple("BoundRuntimeInfo", "parent_ref name")


class Bee:
    _hive_object_cls = None
    _hive_wrapper_name = None

    def __init__(self):
        self._hive_object_cls = get_building_hive()
        assert get_building_hive() is not None

    def implements(self, cls):
        return isinstance(self, cls)

    def instance_implements(self, cls):
        return isinstance(self, cls)

    def getinstance(self, hive_object):
        return self


class Parameter:
    _hive_parameter_name = None

    start_value = None
    data_type = None
    options = None

    no_value = object()


# Connectables don't need to be Bees!
class Connectable:
    pass


class Bindable(ABC):
    # Bindables don't need to be Bees!

    @abstractmethod
    def bind(self, run_hive):
        raise NotImplementedError


class Nameable:

    @memo_property
    def _hive_runtime_aliases(self):
        return set()

    def register_alias(self, parent, name):
        """Register alias to this bee as a child of a given parent hive, under attribute name
        
        :param parent: runtime hive instance
        :param name: attribute name under which this bee is referred
        """
        info = BoundRuntimeInfo(ref(parent), name)
        self._hive_runtime_aliases.add(info)


class Callable:
    pass


class Exportable(ABC):
    export_only = True

    @abstractmethod
    def export(self):
        raise NotImplementedError


class Plugin:
    pass


class Socket:
    pass


from .connect_source import ConnectSourceBase, ConnectSource, ConnectSourceDerived
from .connect_target import ConnectTargetBase, ConnectTarget, ConnectTargetDerived
from .io import IO, Antenna, Output
from .stateful import Stateful
from .trigger_source import TriggerSourceBase, TriggerSource, TriggerSourceDerived
from .trigger_target import TriggerTargetBase, TriggerTarget, TriggerTargetDerived

