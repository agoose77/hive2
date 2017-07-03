from .manager import ModeFactory, memoize
from .protocols import Bee, Stateful, Bindable, Parameter
from .stateful import StatefulBuilder, StatefulRuntime
from .typing import is_valid_data_type


class RuntimeVariable(StatefulRuntime, Bee):
    def __init__(self, run_hive, data_type, start_value, parent):
        self._data_type = data_type
        self._start_value = start_value

        if isinstance(start_value, Parameter):
            start_value = run_hive._hive_object._hive_args_frozen.get_parameter_value(start_value)

        self._value = start_value

        super().__init__(run_hive, parent)

    @property
    def data_type(self):
        return self._data_type

    @property
    def start_value(self):
        return self._start_value

    def _hive_stateful_getter(self):
        return self._value

    def _hive_stateful_setter(self, value):
        self._value = value

    def __repr__(self):
        return "BuilderVariable({!r}, {!r})".format(self._data_type, self._start_value)


class BuilderVariable(Bindable, StatefulBuilder):
    """Stateful data store object"""

    def __init__(self, data_type='', start_value=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._data_type = data_type
        self._start_value = start_value

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    @property
    def start_value(self):
        return self._start_value

    @memoize
    def bind(self, run_hive):
        return RuntimeVariable(run_hive, self._data_type, self._start_value, self)

    def implements(self, cls):
        if cls is Stateful:
            return True

        return super().implements(cls)

    def __repr__(self):
        return "BuilderVariable({!r}, {!r})".format(self._data_type, self._start_value)


variable = ModeFactory("hive.variable", build=BuilderVariable, immediate=RuntimeVariable)
