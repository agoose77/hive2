from .manager import ModeFactory, memoize
from .protocols import Bee, Stateful, Bindable, Parameter
from .stateful import StatefulBuilder, StatefulRuntime, RuntimeHelpers
from .typing import is_valid_data_type
from functools import partial


class RuntimeVariable(StatefulRuntime, Bee):
    def __init__(self, data_type, start_value=None, parent=None):
        self._data_type = data_type
        self._value = start_value
        self._start_value = start_value

        super().__init__(parent)

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
        self._

    def __repr__(self):
        return "RuntimeVariable({!r}, {!r}, ...)".format(self._data_type, self._start_value)


class BuilderVariable(StatefulBuilder, Bindable):
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
        start_value = self._start_value
        if isinstance(start_value, Parameter):
            start_value = run_hive._hive_object._hive_args_frozen.resolve_parameter(start_value)

        # Helpers to resolve the runtime reference to the instances of builder pull in
        # Without this, we could just return create new runtime pull in/out, but the execution order would be different
        # And triggering on pull_in would not work
        helpers = RuntimeHelpers(partial(self.pull_in.bind, run_hive), partial(self.pull_out.bind, run_hive),
                                 partial(self.push_in.bind, run_hive), partial(self.push_out.bind, run_hive))
        return RuntimeVariable(self._data_type, start_value, helpers)

    def implements(self, cls):
        if cls is Stateful:
            return True

        return super().implements(cls)

    def __repr__(self):
        return "BuilderVariable({!r}, {!r})".format(self._data_type, self._start_value)


variable = ModeFactory("hive.variable", build=BuilderVariable, immediate=RuntimeVariable)
