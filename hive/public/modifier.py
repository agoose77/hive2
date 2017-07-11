from functools import partial

from .function import FunctionBuilder, FunctionBound
from ..manager import ModeFactory, memoize


class ModifierBuilder(FunctionBuilder):
    def __init__(self, func=None):
        self._func = func

        super().__init__()

    @memoize
    def bind(self, run_hive):
        func = self._func
        if func is not None:
            func = partial(func, run_hive._hive_i, run_hive)
        return FunctionBound(self, run_hive, func)


modifier = ModeFactory("hive.modifier", build=ModifierBuilder)
