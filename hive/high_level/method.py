from ..functional import Modifier
from ..manager import ModeFactory, memoize


class MethodImmediate:

    def __init__(self, func):
        assert callable(func)
        self._func = func

        self.triggered = ...
        self.trigger = ...

    def __call__(self):
        pass


class MethodBuilder:

    def __init__(self, cls, name: str):
        self._cls = getattr(cls, '_hive_wrapped_drone_class')
        self._name = name

    triggered = None
    trigger = None

    @memoize
    def bind(self, run_hive):
        instance = run_hive._drone_class_to_instance[self._cls]
        return getattr(instance, self._name)


method = ModeFactory("hive.method", build=MethodBuilder, immediate=MethodImmediate)
