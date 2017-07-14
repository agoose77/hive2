from ..interfaces import Stateful, BeeBase
from ..manager import HiveModeFactory, memoize, memo_property
from ..parameter import Parameter
from ..private import (PushInBuilder, PushInImmediate, PullInBuilder, PullInImmediate, PushOutBuilder, PullOutBuilder,
                       PullOutImmediate, PushOutImmediate, StatefulDescriptorBuilder, READ_WRITE, TriggerFuncBuilder,
                       TriggerFuncRuntime)

class AttributeBase(BeeBase, Stateful):
    pre_updated = None
    updated = None

    def __init__(self, data_type='', start_value=None):
        self._value = start_value
        self._data_type = data_type
        self._start_value = start_value

        super().__init__()

    def _hive_stateful_getter(self):
        return self._value

    def _hive_stateful_setter(self, value):
        self.pre_updated()
        self._value = value
        self.updated()

    value = property(_hive_stateful_getter, _hive_stateful_setter)


class AttributeImmediate(AttributeBase):
    def __init__(self, data_type='', start_value=None):
        super().__init__(data_type, start_value)

        self.pull_in = PullInImmediate(self)
        self.pull_out = PullOutImmediate(self)
        self.push_in = PushInImmediate(self)
        self.push_out = PushOutImmediate(self)
        self.pre_updated = TriggerFuncRuntime()
        self.updated = TriggerFuncRuntime()

    def __repr__(self):
        return "AttributeImmediate({!r}, {!r})".format(self._data_type, self._start_value)


class AttributeBound(AttributeBase):
    def __init__(self, build_bee, run_hive, data_type='', start_value=None):
        self._build_bee = build_bee
        self._run_hive = run_hive

        super().__init__(data_type, start_value)

    def __repr__(self):
        return "AttributeBound({!r}, {!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._data_type,
                                                               self._start_value)

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
    def pre_updated(self):
        return self._build_bee.pre_updated.bind(self._run_hive)


builtin_property = property


class AttributeBuilder(BeeBase):
    def __init__(self, data_type='', start_value=None):
        self._data_type = data_type
        self._start_value = start_value

        super().__init__()

        self.pull_in = PullInBuilder(self)
        self.pull_out = PullOutBuilder(self)
        self.push_in = PushInBuilder(self)
        self.push_out = PushOutBuilder(self)
        self.pre_updated = TriggerFuncBuilder()
        self.updated = TriggerFuncBuilder()

    def __repr__(self):
        return "AttributeBuilder({!r}, {!r})".format(self._data_type, self._start_value)

    @builtin_property
    def data_type(self):
        return self._data_type

    @builtin_property
    def start_value(self):
        return self._start_value

    @memoize
    def bind(self, run_hive):
        start_value = self._start_value

        if isinstance(start_value, Parameter):
            hive_args_resolved = run_hive._hive_object._hive_args_frozen
            start_value = hive_args_resolved.resolve_parameter(start_value)

        return AttributeBound(self, run_hive, self._data_type, start_value)

    def implements(self, cls):
        return issubclass(AttributeBound, cls) or super().implements(cls)

    def property(self, flags=READ_WRITE):
        return StatefulDescriptorBuilder(self, flags=flags)


attribute = HiveModeFactory("hive.attribute", BUILD=AttributeBuilder, IMMEDIATE=AttributeImmediate)
