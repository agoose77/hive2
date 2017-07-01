from ..method import Method
from ..property import Property

from ..annotations import get_argument_options, get_return_type
from ..compatability import is_method


# Hack to find the type of a getset_descriptor
from struct import Struct as _Struct
getset_descriptor = type(_Struct.size)


class HiveClassProxy(object):
    """Intercept attribute lookups to return bee equivalents to instance methods and properties belonging to a bind
    class."""

    def __init__(self, cls):
        object.__setattr__(self, "_cls", cls)

    def __getattr__(self, attr):
        value = getattr(self._cls, attr)

        if is_method(value):
            return Method(self._cls, value)

        elif isinstance(value, property):
            return self._property_from_descriptor(attr, value)

        elif isinstance(value, getset_descriptor):
            return self._property_from_getset_descriptor(attr)

        else:
            return value

    def __setattr__(self, attr):
        raise AttributeError("HiveMethodWrapper of class '{}' is read-only".format(self._cls.__name__))

    def __repr__(self):
        self_cls = object.__getattribute__(self, "__class__")
        wrapped_cls = object.__getattribute__(self, "_cls")
        return "{}({})".format(self_cls.__name__, wrapped_cls)

    def _property_from_descriptor(self, attr, prop):
        """Create a hive.property object from property descriptor"""
        data_type = get_return_type(prop.fget)

        if prop.fset is not None:
            setter_data_type = next(iter(get_argument_options(prop.fset)), None)
            if setter_data_type != data_type:
                raise TypeError()

        return Property(self._cls, attr, data_type, None)

    def _property_from_getset_descriptor(self, attr):
        """Create a hive.property object from getset_descriptor"""
        return Property(self._cls, attr, None, None)