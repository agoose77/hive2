# from ..functional.modifier import Modifier
from functools import partial

from hive.internal_bees.triggerable import TriggerableBuilder, TriggerableRuntime
from ..interfaces import Bee, Callable
from ..internal_bees.triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..manager import ModeFactory, memoize, memo_property


class FunctionBase(Bee, Callable):
    before_triggered = None
    _func = None
    triggered = None

    def __call__(self):
        self.before_triggered()
        self._func()
        self.triggered()


class FunctionImmediate(FunctionBase):

    def __init__(self, func):
        assert callable(func)
        self._func = func

        self.triggered = TriggerFuncRuntime()
        self.before_triggered = TriggerFuncRuntime()
        self.trigger = TriggerableRuntime(self)

        super().__init__()


class FunctionBound(FunctionBase):

    def __init__(self, build_bee, run_hive, func):
        self._build_bee = build_bee
        self._run_hive = run_hive
        self._func = partial(func, run_hive._hive_i, run_hive)

        super().__init__()

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def before_triggered(self):
        return self._build_bee.before_triggered.bind(self._run_hive)

    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class FunctionBuilder(Bee):

    def __init__(self, func):
        self._func = func

        super().__init__()

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

    @memoize
    def bind(self, run_hive):
        return FunctionBound(self, run_hive, self._func)

    def implements(self, cls):
        if issubclass(FunctionBound, cls):
            return True

        return super().implements(cls)


function = ModeFactory("hive.function", build=FunctionBuilder, immediate=FunctionImmediate)
