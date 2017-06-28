from collections import namedtuple
from weakref import ref

from ..manager import memo_property


class Parameter:
    _hive_parameter_name = None

    start_value = None
    data_type = None
    options = None

    no_value = object()


class Connectable:
    pass


RuntimeAlias = namedtuple("RuntimeAlias", "parent_ref name")


class Nameable:
    # TOOD move this to bee
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


from .bees import Bindable, Exportable, Bee
from .connect_source import ConnectSourceBase, ConnectSource, ConnectSourceDerived
from .connect_target import ConnectTargetBase, ConnectTarget, ConnectTargetDerived
from .io import IO, Antenna, Output
from .stateful import Stateful
from .trigger_source import TriggerSourceBase, TriggerSource, TriggerSourceDerived
from .trigger_target import TriggerTargetBase, TriggerTarget, TriggerTargetDerived
