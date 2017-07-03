# from ..functional.modifier import Modifier
from functools import partial

from ..low_level.triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..functional.triggerable import TriggerableBuilder, TriggerableRuntime
from ..manager import ModeFactory, memoize, memo_property
from ..interfaces import TriggerTarget, ConnectTarget, Bee, TriggerSource, Callable


class FunctionBase(Bee, ConnectTarget, TriggerTarget, Callable):
    before_triggered = None
    _func = None
    triggered = None

    def __call__(self):
        self.before_triggered()
        self._func()
        self.triggered()

    def _hive_trigger_target(self):
        return self

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, TriggerSource):
            raise Exception("Connect target {} is not a TriggerSource".format(source))

    def _hive_connect_target(self, source):
        pass


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


function = ModeFactory("Function", build=FunctionBuilder, immediate=FunctionImmediate)
