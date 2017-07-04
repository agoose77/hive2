from ..functional.stateful_descriptor import stateful_descriptor, READ_WRITE
from ..interfaces import Stateful, Bee
from ..low_level.push_pull_in import PushInBuilder, PullInBuilder, PullInBound, PushInBound, PushInImmediate, PullInImmediate
from ..low_level.push_pull_out import PushOutBuilder, PullOutBuilder, PullOutBound, PushOutBound, PushOutImmediate, PullOutImmediate
from ..low_level.triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..manager import ModeFactory, memoize, memo_property


class AttributeImplementation(Bee, Stateful):
    before_updated = None
    updated = None

    def __init__(self, data_type='', start_value=None):
        self._value = start_value
        self._data_type = data_type
        self._start_value = start_value

        super().__init__()

    def _hive_stateful_getter(self):
        return self._value

    def _hive_stateful_setter(self, value):
        self.before_updated()
        self._value = value
        self.updated()

    value = property(_hive_stateful_getter, _hive_stateful_setter)


class AttributeImmediate(AttributeImplementation):
    def __init__(self, data_type='', start_value=None):
        super().__init__(data_type, start_value)

        self.pull_in = PullInImmediate(self, data_type)
        self.pull_out = PullOutImmediate(self, data_type)
        self.push_in = PushInImmediate(self, data_type)
        self.push_out = PushOutImmediate(self, data_type)
        self.before_updated = TriggerFuncRuntime()
        self.updated = TriggerFuncRuntime()

    def __repr__(self):
        return "AttributeImmediate({!r}, {!r})".format(self._data_type, self._start_value)


class AttributeBound(AttributeImplementation):
    def __init__(self, build_bee, run_hive, data_type='', start_value=None):
        self._build_bee = build_bee
        self._run_hive = run_hive

        super().__init__(data_type, start_value)

    @memo_property
    def pull_out(self):
        return self._build_bee.pull_out.bind(self._run_hive)

    @memo_property
    def pull_in(self):
        return self._build_bee.pull_in.bind(self._run_hive)

    @memo_property
    def push_out(self):
        return self._build_bee.push_out.bind(self._run_hive)

    @memo_property
    def push_in(self):
        return self._build_bee.push_in.bind(self._run_hive)

    @memo_property
    def updated(self):
        return self._build_bee.updated.bind(self._run_hive)

    @memo_property
    def before_updated(self):
        return self._build_bee.before_updated.bind(self._run_hive)

    def __repr__(self):
        return "AttributeBound({!r}, {!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._data_type,
                                                               self._start_value)


builtin_property = property


class AttributeBuilder(Bee):
    def __init__(self, data_type='', start_value=None):
        self._data_type = data_type
        self._start_value = start_value

        super().__init__()

        self.pull_in = PullInBuilder(self)
        self.pull_out = PullOutBuilder(self)
        self.push_in = PushInBuilder(self)
        self.push_out = PushOutBuilder(self)
        self.before_updated = TriggerFuncBuilder()
        self.updated = TriggerFuncBuilder()

    def property(self, flags=READ_WRITE):
        return stateful_descriptor(self, flags=flags)

    @builtin_property
    def data_type(self):
        return self._data_type

    @builtin_property
    def start_value(self):
        return self._start_value

    def implements(self, cls):
        if issubclass(AttributeBound, cls):
            return True

        return super().implements(cls)

    @memoize
    def bind(self, run_hive):
        return AttributeBound(self, run_hive, self._data_type, self._start_value)

    def __repr__(self):
        return "AttributeBuilder({!r}, {!r})".format(self._data_type, self._start_value)


attribute = ModeFactory("hive.attribute", build=AttributeBuilder, immediate=AttributeImmediate)