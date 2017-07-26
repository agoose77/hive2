from hive.manager import memoize
from hive.private.function import FunctionBound, FunctionBuilder


class MethodBuilder(FunctionBuilder):
    def __init__(self, drone, name):
        self._drone = drone
        self._name = name

        super().__init__()

    @memoize
    def bind(self, run_hive) -> FunctionBound:
        instance = self._drone.bind(run_hive)
        method = getattr(instance, self._name)
        return FunctionBound(self, run_hive, method)
