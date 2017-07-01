from weakref import WeakSet

from builtins import property as py_property

from .contexts import get_mode
from .manager import memoize
from .protocols import Stateful, Exportable, Bindable, Parameter, Nameable
from .typing import is_valid_data_type


class Property(Bindable, Stateful, Nameable):
    """Interface to bind class attributes"""

    def __init__(self, cls, attr, data_type, start_value):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._bound = WeakSet()
        self._cls = cls
        self._attr = attr
        self._data_type = data_type

        self.start_value = start_value

        super().__init__()

    @py_property
    def data_type(self):
        return self._data_type

    def _hive_stateful_getter(self, run_hive):
        instance = run_hive._drone_class_to_instance[self._cls]

        return getattr(instance, self._attr)

    def _hive_stateful_setter(self, run_hive, value):
        instance = run_hive._drone_class_to_instance[self._cls]

        setattr(instance, self._attr, value)

    @memoize
    def bind(self, run_hive):
        self._bound.add(run_hive)

        instance = run_hive._drone_class_to_instance[self._cls]

        start_value = self.start_value
        if start_value is not None or not hasattr(instance, self._attr):
            if isinstance(start_value, Parameter):
                start_value = run_hive._hive_object._hive_args_frozen.resolve_parameter(start_value)

            setattr(instance, self._attr, start_value)

        return self

    def __repr__(self):
        return "Property({!r}, {!r}, {!r}, {!r})".format(self._cls, self._attr, self._data_type, self.start_value)


def property(cls, attr, data_type="", start_value=None):
    if get_mode() == "immediate":
        raise ValueError("hive.property cannot be used in immediate mode")

    from .classes import HiveClassProxy
    assert isinstance(cls, HiveClassProxy), "hive.property(cls) must be the cls argument in build(cls, i, ex, args)"

    return Property(cls._cls, attr, data_type, start_value)
