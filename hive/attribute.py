from weakref import WeakKeyDictionary

from .contexts import get_building_hive
from .manager import ModeFactory, memoize
from .mixins import Stateful, Exportable, Bindable, Parameter, Nameable, Bee
from .typing import is_valid_data_type


class Attribute(Bee, Stateful, Bindable, Exportable, Nameable):
    """Stateful data store object"""

    export_only = False

    def __init__(self, data_type='', start_value=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._hive_object_cls = get_building_hive()

        self.data_type = data_type
        self.start_value = start_value

        self._values = WeakKeyDictionary()

    def _hive_stateful_getter(self, run_hive):
        return self._values[run_hive]

    def _hive_stateful_setter(self, run_hive, value):
        assert run_hive in self._values, run_hive
        self._values[run_hive] = value

    @memoize
    def bind(self, run_hive):
        start_value = self.start_value

        if isinstance(start_value, Parameter):
            start_value = run_hive._hive_object._hive_args_frozen.get_parameter_value(start_value)

        self._values[run_hive] = start_value
        return self

    def export(self):
        return self


attribute = ModeFactory("hive.attribute", build=Attribute)
