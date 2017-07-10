from collections import namedtuple
from weakref import ref

from ..manager import memo_property

from abc import ABC, abstractmethod


class Descriptor(ABC):
    @abstractmethod
    def _hive_descriptor_get(self):
        pass

    @abstractmethod
    def _hive_descriptor_set(self, value):
        pass


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


class Callable(ABC):

    @abstractmethod
    def __call__(self):
        pass


class Plugin:
    pass


class Socket:
    pass


from .bees import Exportable, Bee
from .io import IO, Antenna, Output, IOModes
from .stateful import Stateful
from .trigger_source import TriggerSourceBase, TriggerSource, TriggerSourceDerived
from .trigger_target import TriggerTargetBase, TriggerTarget, TriggerTargetDerived
from .connect_source import ConnectSource ,ConnectSourceBase, ConnectSourceDerived
from .connect_target import ConnectTarget, ConnectTargetBase, ConnectTargetDerived