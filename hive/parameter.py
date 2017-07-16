from .manager import HiveModeFactory
from .typing import is_valid_data_type

from collections.abc import Collection

PARAM_NO_VALUE = object()


class Parameter:

    def __init__(self, data_type='', start_value=PARAM_NO_VALUE, options=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # Ensure options aren't easily mutated by accident
        if options is not None:
            if not isinstance(options, Collection):
                raise ValueError("Expected None or a collection for options")
            options = frozenset(options)

            if start_value is not PARAM_NO_VALUE and start_value not in options:
                raise ValueError("Invalid start value: {!r} not in {!r}".format(start_value, options))

        self._data_type = data_type
        self._start_value = start_value
        self._options = options

        # Validate start value
        if start_value is not PARAM_NO_VALUE and options is not None:
            assert start_value in options

    @property
    def data_type(self) -> str:
        return self._data_type

    @property
    def start_value(self):
        return self._start_value

    @property
    def options(self):
        return self._options

    def __repr__(self):
        return "HiveParameter({!r}, {!r}, {!r})".format(self._data_type, self._start_value, self._options)


parameter = HiveModeFactory("hive.parameter", DECLARE=Parameter, BUILD=Parameter)
