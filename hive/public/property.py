from functools import partial

from ..interfaces import Stateful, BeeBase
from ..manager import HiveModeFactory, memoize, memo_property
from ..parameter import Parameter
from ..private import (PushInBuilder, PullInBuilder, PushOutBuilder, PullOutBuilder, StatefulDescriptorBuilder,
                       READ_WRITE, TriggerFuncBuilder)

builtin_property = property


class PropertyBound(BeeBase, Stateful):
    def __init__(self, build_bee, run_hive, drone_class, name, data_type='', start_value=None):
        self._drone_class = drone_class
        self._name = name
        self._instance = run_hive._drone_class_to_instance[drone_class]

        self._getter = partial(getattr, self._instance, name)
        self._setter = partial(setattr, self._instance, name)

        self._data_type = data_type
        self._start_value = start_value

        self._build_bee = build_bee
        self._run_hive = run_hive

        self._setter(start_value)

        super().__init__()

    def __repr__(self):
        return "PropertyBound({!r}, {!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._data_type,
                                                              self._start_value)

    def _hive_stateful_getter(self):
        return self._getter()

    def _hive_stateful_setter(self, value):
        self.pre_updated()
        self._setter(value)
        self.updated()

    value = builtin_property(_hive_stateful_getter, _hive_stateful_setter)

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


class PropertyBuilder(BeeBase):
    def __init__(self, cls, name: str, data_type: str = '', start_value=None):
        self._drone_cls = getattr(cls, '_hive_wrapped_drone_class')
        self._name = name
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
        return "PropertyBuilder({!r}, {!r})".format(self._data_type, self._start_value)

    @builtin_property
    def data_type(self):
        return self._data_type

    @builtin_property
    def start_value(self):
        return self._start_value

    def implements(self, cls):
        if issubclass(PropertyBound, cls):
            return True

        return super().implements(cls)

    def property(self, flags=READ_WRITE):
        return StatefulDescriptorBuilder(self, flags=flags)

    @memoize
    def bind(self, run_hive):
        start_value = self._start_value

        if isinstance(start_value, Parameter):
            start_value = run_hive._hive_object._hive_args_frozen.resolve_parameter(start_value)

        return PropertyBound(self, run_hive, self._drone_cls, self._name, self._data_type, start_value)


property = HiveModeFactory("hive.property", BUILD=PropertyBuilder)
