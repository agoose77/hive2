from .function import FunctionBound, FunctionBuilder
from ..manager import ModeFactory, memoize


class MethodBuilder(FunctionBuilder):
    def __init__(self, cls, name):
        self._drone_cls = getattr(cls, '_hive_wrapped_drone_class')
        self._name = name

        super().__init__()

    @memoize
    def bind(self, run_hive):
        instance = run_hive._drone_class_to_instance[self._drone_cls]
        method = getattr(instance, self._name)
        return FunctionBound(self, run_hive, method)


method = ModeFactory("hive.method", build=MethodBuilder)
