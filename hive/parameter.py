from .manager import ContextFactory
from .mixins import Parameter
from .typing import is_valid_data_type


class HiveParameter(Parameter):
    def __init__(self, data_type='', start_value=Parameter.NoValue, options=None):
        self.data_type = data_type
        self.start_value = start_value
        self.options = options

        # Validate start value
        if not (start_value is Parameter.NoValue or options is None):
            assert start_value in options

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.start_value)


parameter = ContextFactory("hive.parameter", declare_mode_cls=HiveParameter, build_mode_cls=HiveParameter)
