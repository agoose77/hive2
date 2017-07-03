from .protocols import Stateful
from .ppin import PullInBuilder, PullIn, PushInBuilder, PushIn
from .ppout import PullOutBuilder, PushOutBuilder, PullOut, PushOut
from .property_descriptor import PropertyBee
from .manager import memo_property
from .trigg


class StatefulRuntime(Stateful):

    def __init__(self, run_hive, parent):
        self._run_hive = run_hive
        self._parent = parent

    @property
    def property(self):
        return self._hive_stateful_getter()

    @property.setter
    def property(self, value):
        self._hive_stateful_setter(value)

    @memo_property
    def pull_in(self):
        return self._parent.pull_in.bind(self)

    @memo_property
    def push_in(self):
        return self._parent.push_in.bind(self)

    @memo_property
    def push_out(self):
        return self._parent.push_out.bind(self)

    @memo_property
    def pull_out(self):
        return self._parent.pull_out.bind(self)



class StatefulBuilder:

    def property(self, read_only=False):
        return PropertyBee(self, read_only) # TODO

    @memo_property
    def pull_in(self):
        return PullInBuilder(self)

    @memo_property
    def push_in(self):
        return PushInBuilder(self)

    @memo_property
    def push_out(self):
        return PushOutBuilder(self)

    @memo_property
    def pull_out(self):
        return PullOutBuilder(self)

    @memo_property
    def updated(self):
        return