from collections import namedtuple

from .manager import memo_property
from .ppin import PullInBuilder, PullIn, PushInBuilder, PushIn
from .ppout import PullOutBuilder, PushOutBuilder, PullOut, PushOut
from .protocols import Bee, Stateful
from .stateful_descriptor import BuilderStatefulDescriptor
from .trigger_source import TriggerSourceBuilder, TriggerSourceRuntime

RuntimeHelpers = namedtuple("RuntimeHelpers", "create_pull_in create_pull_out create_push_in create_push_out create_updated")


class StatefulRuntime(Stateful):
    def __init__(self, runtime_helpers=None):
        self._runtime_helpers = runtime_helpers

    @memo_property
    def pull_in(self):
        if self._runtime_helpers:
            return self._runtime_helpers.create_pull_in()
        return PullIn(self, self.data_type)

    @memo_property
    def push_in(self):
        if self._runtime_helpers:
            return self._runtime_helpers.create_push_in()
        return PushIn(self, self.data_type)

    @memo_property
    def pull_out(self):
        if self._runtime_helpers:
            return self._runtime_helpers.create_pull_out()
        return PullOut(self, self.data_type)

    @memo_property
    def push_out(self):
        if self._runtime_helpers:
            return self._runtime_helpers.create_push_out()
        return PushOut(self, self.data_type)

    @memo_property
    def updated(self):
        if self._runtime_helpers:
            return self._runtime_helpers.create_updated()
        return TriggerSourceRuntime()

    @property
    def value(self):
        return self._hive_stateful_getter()

    @value.setter
    def value(self, value):
        self._hive_stateful_setter(value)


class StatefulBuilder(Bee):
    _runtime_cls = None

    def __init__(self):
        self.pull_in = PullInBuilder(self)
        self.push_in = PushInBuilder(self)
        self.pull_out = PullOutBuilder(self)
        self.push_out = PushOutBuilder(self)
        self.property = BuilderStatefulDescriptor(self, read_only=False)
        self.read_only_property = BuilderStatefulDescriptor(self, read_only=True)
        self.updated = TriggerSourceBuilder()

        super().__init__()

    def implements(self, cls):
        if cls is Stateful:
            return True

        return super().implements(cls)
