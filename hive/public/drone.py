from inspect import isfunction
from itertools import chain
from logging import getLogger

from typing import Any, Type

from ..annotations import get_argument_options, get_return_type
from ..interfaces import BeeBase
from ..manager import HiveModeFactory, memoize
from ..parameter import Parameter
from ..private import PropertyBuilder, MethodBuilder, NO_START_VALUE

logger = getLogger(__name__)


def is_internal_descriptor(value) -> bool:
    from struct import Struct
    getset_descriptor = type(Struct.size)
    return isinstance(value, getset_descriptor)


def is_property(value) -> bool:
    return isinstance(value, property)


def resolve_arg(arg, run_hive: 'RuntimeHive'):
    if isinstance(arg, Parameter):
        return run_hive._hive_args_frozen.resolve_parameter(arg)
    return arg


class DroneBuilder(BeeBase):
    def __init__(self, cls: Type, *args, **kwargs):
        self._class = cls
        self._args = args
        self._kwargs = kwargs

        # Check no shadowed attributes
        for name in chain.from_iterable((dir(c) for c in cls.__mro__[:-1])):
            if hasattr(self.__class__, name) and not hasattr(object, name):
                logger.warning(
                    "Drone class {!r} has attribute that is shadowed in hive.drone bee, and cannot be accessed"
                        .format(cls)
                )

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

    @memoize
    def bind(self, run_hive: 'RuntimeHive'):
        args = [resolve_arg(a, run_hive) for a in self._args]
        kwargs = {k: resolve_arg(v, run_hive) for k, v in self._kwargs.items()}
        return self._class(*args, **kwargs)

    def property(self, name: str, data_type: str = '', start_value: Any = NO_START_VALUE) -> PropertyBuilder:
        return PropertyBuilder(self, name, data_type, start_value)

    def method(self, name: str) -> MethodBuilder:
        return MethodBuilder(self, name)

    def _build_property(self, name: str) -> PropertyBuilder:
        prop = getattr(self._class, name)
        data_type = get_return_type(prop.fget)

        if prop.fset is not None:
            setter_data_type = next(iter(get_argument_options(prop.fset)), None)
            if setter_data_type != data_type:
                raise TypeError("Property setter and getter types do not match")

        return self.property(name, data_type)


drone = HiveModeFactory("hive.drone", BUILD=DroneBuilder)
