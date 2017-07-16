from inspect import isfunction
from typing import Any, Type

from ..annotations import get_argument_options, get_return_type
from ..interfaces import BeeBase
from ..manager import HiveModeFactory
from ..private import PropertyBuilder, MethodBuilder

def is_internal_descriptor(value):
    from struct import Struct
    getset_descriptor = type(Struct.size)
    return isinstance(value, getset_descriptor)


def is_property(value):
    return isinstance(value, property)


class DroneBuilder(BeeBase):
    def __init__(self, cls: Type, *args, **kwargs):
        self._class = cls
        self._args = args
        self._kwargs = kwargs

        super().__init__()

    def __getattr__(self, name):
        try:
            value = getattr(self._class, name)
        except AttributeError:
            raise

        if isfunction(value):
            return self.method(name)

        elif is_internal_descriptor(value):
            return self.property(name)

        elif is_property(value):
            return self._build_property(name)

        return value

    def property(self, name: str, data_type: str = '', start_value: Any = None):
        raise PropertyBuilder(self._class, name, )

    def method(self, name: str):
        raise NotImplementedError

    def _build_property(self, name: str):
        prop = getattr(self._class, name)
        data_type = get_return_type(prop.fget)

        if prop.fset is not None:
            setter_data_type = next(iter(get_argument_options(prop.fset)), None)
            if setter_data_type != data_type:
                raise TypeError("Property setter and getter types do not match")

        return self.property(name, data_type)


drone = HiveModeFactory("hive.drone", BUILD=DroneBuilder)
