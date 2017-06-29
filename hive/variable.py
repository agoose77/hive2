from weakref import WeakKeyDictionary

from .manager import ModeFactory, memoize
from .protocols import Stateful, Exportable, Bindable, Parameter, Nameable
from .typing import is_valid_data_type


class Variable(Bindable, Stateful, Nameable):
    """Stateful data store object"""

    def __init__(self, data_type='', start_value=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._values = WeakKeyDictionary()
        self._data_type = data_type

        self.start_value = start_value

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    def _hive_stateful_getter(self, run_hive):
        return self._values[run_hive]

    def _hive_stateful_setter(self, run_hive, value):
        self._values[run_hive] = value

    @memoize
    def bind(self, run_hive):
        start_value = self.start_value

        if isinstance(start_value, Parameter):
            start_value = run_hive._hive_object._hive_args_frozen.get_parameter_value(start_value)

        self._values[run_hive] = start_value
        return self

    def __repr__(self):
        return "Variable({!r}, {!r})".format(self._data_type, self.start_value)


variable = ModeFactory("hive.variable", build=Variable)
