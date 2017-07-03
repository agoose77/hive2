from .exception import HiveConnectionError
from .manager import ModeFactory, memoize
from .protocols import TriggerTarget, ConnectTarget, TriggerSource, Callable, Bee, Bindable, Nameable


class Modifier(TriggerTarget, ConnectTarget, Bindable, Callable, Nameable):
    """Callable Python snippet which is passed the current run hive"""

    def __init__(self, func, run_hive=None):
        assert callable(func), func

        self._func = func
        self._run_hive = run_hive

    def __call__(self):
        self.trigger()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._func)

    def trigger(self):
        # TODO: exception handling hooks
        self._func(self._run_hive)

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        return self.__class__(self._func, run_hive=run_hive)

    def _hive_trigger_target(self):
        return self.trigger

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, TriggerSource):
            raise HiveConnectionError("Connect target {} is not a TriggerSource".format(source))

    def _hive_connect_target(self, source):
        pass


class ModifierBuilder(Bee, TriggerTarget, ConnectTarget):
    """Callable Python snippet which is passed the current run hive"""

    def __init__(self, target):
        #assert callable(target), target # TODO what if is a bee...
        self._target = target

        super().__init__()

    @memoize
    def bind(self, run_hive):
        func = self._target

        if isinstance(func, Bee):
            bound_func = func.bind(run_hive)
            if func is not bound_func:
                return Modifier(bound_func)

        return self

    def implements(self, cls):
        from derp.ast.formatting import Colours
        print("IMPL MOD",Colours.green(cls.__name__),issubclass(Modifier, cls),self)
        if issubclass(Modifier, cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "Modifier({!r})".format(self._target)


modifier = ModeFactory("hive.modifier", immediate=Modifier, build=ModifierBuilder)
