from .manager import ModeFactory
from .protocols import Parameter
from .typing import is_valid_data_type


class HiveParameter(Parameter):
    def __init__(self, data_type='', start_value=Parameter.no_value, options=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self.data_type = data_type
        self.start_value = start_value
        self.options = options

        # Validate start value
        if not (start_value is Parameter.no_value or options is None):
            assert start_value in options

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.start_value)


parameter = ModeFactory("hive.parameter", declare=HiveParameter, build=HiveParameter)
