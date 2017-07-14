from abc import ABC, abstractmethod

from hive.private.socket import HiveSocketBuilder
from ..interfaces import BeeBase, Callable
from ..manager import memo_property
from ..private import TriggerableBuilder, TriggerableRuntime, TriggerFuncBuilder, TriggerFuncRuntime, HivePluginBuilder


class FunctionBase(BeeBase, Callable):

    def __call__(self, *args, **kwargs):
        self.pre_triggered()
        if self._func is not None:
            self._func(*args, **kwargs)
        self.triggered()


class FunctionImmediate(FunctionBase):
    def __init__(self, func):
        assert callable(func)
        self._func = func

        self.triggered = TriggerFuncRuntime()
        self.pre_triggered = TriggerFuncRuntime()
        self.trigger = TriggerableRuntime(self)

        super().__init__()


class FunctionBound(FunctionBase):
    def __init__(self, build_bee, run_hive, func):
        self._build_bee = build_bee
        self._run_hive = run_hive
        self._func = func

        super().__init__()

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def pre_triggered(self):
        return self._build_bee.pre_triggered.bind(self._run_hive)

    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class FunctionBuilder(BeeBase, ABC):
    def __init__(self):
        super().__init__()

        self.triggered = TriggerFuncBuilder()
        self.pre_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

    def socket(self, *args, **kwargs):
        return HiveSocketBuilder(self, *args, **kwargs)

    def plugin(self, *args, **kwargs):
        return HivePluginBuilder(self, *args, **kwargs)

    @abstractmethod
    def bind(self, run_hive):
        pass

    def implements(self, cls):
        if issubclass(FunctionBound, cls):
            return True

        return super().implements(cls)
