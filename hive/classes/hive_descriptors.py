from abc import ABC, abstractmethod


class HiveDescriptor(ABC):
    _hive_redirect_self_descriptor = True


    @abstractmethod
    def __get__(self, instance, owner):
        pass


class HiveProperty(property, HiveDescriptor):
    pass