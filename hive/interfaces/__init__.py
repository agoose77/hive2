from collections import namedtuple
from weakref import ref

from ..manager import memo_property

from abc import ABC, abstractmethod


class Descriptor(ABC):
    _hive_descriptor_get = None
    _hive_descriptor_set = None


class Parameter:
    start_value = None
    data_type = None
    options = None

    no_value = object()


class Connectable:
    pass


RuntimeAlias = namedtuple("RuntimeAlias", "parent_ref name")


class Nameable:
    @memo_property
    def _hive_runtime_aliases(self):
        return set()

    def register_alias(self, parent, name):
        """Register alias to this bee as a child of a given parent hive, under attribute name
        
        :param parent: runtime hive instance
        :param name: attribute name under which this bee is referred
        """
        alias = RuntimeAlias(ref(parent), name)
        self._hive_runtime_aliases.add(alias)


class Callable:
    pass


class Plugin:
    pass


class Socket:
    pass


from .bees import Exportable, Bee
from .io import IO, Antenna, Output
from .stateful import Stateful
from .trigger_source import TriggerSourceBase, TriggerSource, TriggerSourceDerived
