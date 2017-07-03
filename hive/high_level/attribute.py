from ..manager import ModeFactory, memoize, memo_property
from ..interfaces import Stateful

from ..functional.stateful_descriptor import stateful_descriptor
from ..functional.triggerfunc import TriggerFunc

from ..low_level.push_pull_in import PushInBuilder, PullInBuilder, PullIn, PushIn
# from ..low_level.push_pull_out import PushOutBuilder, PullOutBuilder, PullOut, PushOut


class AttributeImplementation(Stateful):

    updated = None

    def __init__(self, data_type='', start_value=None):
        self._value = start_value
        self._data_type = data_type

    def _hive_stateful_getter(self):
        return self._value

    def _hive_stateful_setter(self, value):
        self._value = value
        self.updated()  # TODO

    value = property(_hive_stateful_getter, _hive_stateful_setter)


class AttributeImmediate(AttributeImplementation):

    def __init__(self, data_type='', start_value=None):
        super().__init__(data_type, start_value)

        self.pull_in = PullIn(self)
        # self.pull_out = PullOut(self)
        self.push_in = PushIn(self)
        # self.push_out = PushOut(self)
        self.updated = TriggerFunc()


class AttributeBound(AttributeImplementation):

    def __init__(self, build_attribute, run_hive, data_type='', start_value=None):
        self._builder_attribute = build_attribute
        self._run_hive = run_hive

        self._value = start_value
        self._data_type = data_type

        super().__init__()

    @memo_property
    def pull_out(self):
        return self._builder_attribute.pull_out.bind(self._run_hive)

    @memo_property
    def pull_in(self):
        return self._builder_attribute.pull_in.bind(self._run_hive)

    @memo_property
    def push_out(self):
        return self._builder_attribute.push_out.bind(self._run_hive)

    @memo_property
    def push_in(self):
        return self._builder_attribute.push_in.bind(self._run_hive)

    @memo_property
    def updated(self):
        return self._builder_attribute.updated.bind(self._run_hive)


class AttributeBuilder:

    def __init__(self, data_type='', start_value=None):
        # self.pull_in = PullInBuilder(self)
        # self.pull_out = PullOutBuilder(self)
        self.push_in = PushInBuilder(self)
        # self.push_out = PushOutBuilder(self)
        self.updated = TriggerFunc()

        self.descriptor = stateful_descriptor(self, read_only=False)
        self.read_only_descriptor = stateful_descriptor(self, read_only=True)

        self._data_type = data_type
        self._start_value = start_value

    @memoize
    def bind(self, run_hive):
        return AttributeBound(self, run_hive, self._data_type, self._start_value)


attribute = ModeFactory("hive.attribute", build=AttributeBuilder, immediate=AttributeImmediate)