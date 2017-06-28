from weakref import WeakSet

from .contexts import get_mode
from .manager import memoize
from .protocols import Stateful, Exportable, Bindable, Parameter, Nameable
from .typing import is_valid_data_type


class Property(Bindable, Stateful, Nameable):
    """Interface to bind class attributes"""

    def __init__(self, cls, attr, data_type, start_value):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._cls = cls
        self._attr = attr
        self._bound = WeakSet()

        self.data_type = data_type
        self.start_value = start_value

        super().__init__()

    def _hive_stateful_getter(self, run_hive):
        cls = self._cls

        assert cls in run_hive._hive_build_class_to_instance, cls
        instance = run_hive._hive_build_class_to_instance[cls]

        return getattr(instance, self._attr)

    def _hive_stateful_setter(self, run_hive, value):
        cls = self._cls

        assert cls in run_hive._hive_build_class_to_instance, cls
        instance = run_hive._hive_build_class_to_instance[cls]

        setattr(instance, self._attr, value)

    def export(self):
        return self

    @memoize
    def bind(self, run_hive):
        self._bound.add(run_hive)

        cls = self._cls
        assert cls in run_hive._hive_build_class_to_instance, cls  # TODO, DEBUG can remove?
        instance = run_hive._hive_build_class_to_instance[cls]

        start_value = self.start_value
        if start_value is not None or not hasattr(instance, self._attr):
            if isinstance(start_value, Parameter):
                start_value = run_hive._hive_object._hive_args_frozen.get_parameter_value(start_value)

            setattr(instance, self._attr, start_value)

        return self

    def __repr__(self):
        return "Property({!r}, {!r}, {!r}, {!r})".format(self._cls, self._attr, self.data_type, self.start_value)


def property(cls, attr, data_type="", start_value=None):
    if get_mode() == "immediate":
        raise ValueError("hive.property cannot be used in immediate mode")

    from .classes import HiveClassProxy
    assert isinstance(cls, HiveClassProxy), "hive.property(cls) must be the cls argument in build(cls, i, ex, args)"

    return Property(cls._cls, attr, data_type, start_value)
