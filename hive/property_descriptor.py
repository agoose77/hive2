from weakref import WeakValueDictionary

from .classes import HiveProperty, HiveDescriptor
from .protocols import Stateful, Descriptor, Exportable


class HivePropertyDescriptor(HiveDescriptor):

    def __get__(self, instance, owner):
        if instance is None:
            return instance

        return


class PropertyBee(Exportable, Descriptor):

    def __init__(self, target, read_only=False):
        assert target.implements(Stateful)
        self._target = target
        self._read_only = read_only

        self._internal_to_run_hive = WeakValueDictionary()

        super().__init__()

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return self._target.bind(instance)._hive_stateful_getter()

    def __set__(self, instance, value):
        return self._target.bind(instance)._hive_stateful_setter(value)


def property_descriptor(target):
    return PropertyBee(target)