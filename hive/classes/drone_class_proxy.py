from ..high_level.property import PropertyBuilder
from ..high_level.method import MethodBuilder

from ..annotations import get_argument_options, get_return_type
from ..compatability import is_method

# Hack to find the type of a getset_descriptor
from struct import Struct as _Struct

getset_descriptor = type(_Struct.size)


class DroneClassProxy:
    """Intercept attribute lookups to return bee equivalents to instance methods and properties belonging to a bind
    class."""

    def __init__(self, cls):
        object.__setattr__(self, "_hive_wrapped_drone_class", cls)

    def __getattr__(self, attr):
        value = getattr(self._hive_wrapped_drone_class, attr)

        if is_method(value):
            return MethodBuilder(self, attr)

        elif isinstance(value, property):
            return self._property_from_descriptor(attr, value)

        elif isinstance(value, getset_descriptor):
            return self._property_from_getset_descriptor(attr)

        else:
            return value

    def __setattr__(self, name, value):
        raise AttributeError("DroneClassProxy({!r}) is read-only".format(self))

    def __repr__(self):
        wrapped_cls = self._hive_wrapped_drone_class
        return "DroneClassProxy({!r})".format(wrapped_cls)

    def _property_from_descriptor(self, attr, prop):
        """Create a hive.property object from property descriptor"""
        data_type = get_return_type(prop.fget)

        if prop.fset is not None:
            setter_data_type = next(iter(get_argument_options(prop.fset)), None)
            if setter_data_type != data_type:
                raise TypeError()

        return PropertyBuilder(self, attr, data_type, None)

    def _property_from_getset_descriptor(self, attr):
        """Create a hive.property object from getset_descriptor"""
        return PropertyBuilder(self, attr, None, None)
