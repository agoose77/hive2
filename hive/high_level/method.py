# from ..functional.modifier import Modifier
from functools import partial

from ..low_level.triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..functional.triggerable import TriggerableBuilder, TriggerableRuntime
from ..manager import ModeFactory, memoize, memo_property
from ..interfaces import Bee, TriggerSource, Callable


class MethodBound(Bee, Callable):

    def __init__(self, build_bee, run_hive, func):
        self._build_bee = build_bee
        self._run_hive = run_hive
        self._func = func

        super().__init__()

    def __call__(self):
        self.before_triggered()
        self._func()
        self.triggered()

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def before_triggered(self):
        return self._build_bee.before_triggered.bind(self._run_hive)

    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class MethodBuilder(Bee):

    def __init__(self, cls, name):
        self._drone_cls = getattr(cls, '_hive_wrapped_drone_class')
        self._name = name

        super().__init__()

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

    @memoize
    def bind(self, run_hive):
        instance = run_hive._drone_class_to_instance[self._drone_cls]
        method = getattr(instance, self._name)
        return MethodBound(self, run_hive, method)

    def implements(self, cls):
        if issubclass(MethodBound, cls):
            return True

        return super().implements(cls)


function = ModeFactory("Function", build=MethodBuilder)
