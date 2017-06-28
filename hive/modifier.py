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


class ModifierBee(Bee, TriggerTarget, ConnectTarget, Callable):
    """Callable Python snippet which is passed the current run hive"""

    def __init__(self, func):
        assert callable(func), func
        self._func = func
        super().__init__()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._func)

    @memoize
    def getinstance(self, hive_object):
        func = self._func
        if isinstance(func, Bee):
            func = func.getinstance(hive_object)

        return Modifier(func)

    def implements(self, cls):
        if super().implements(cls):
            return True

            # func = self._func
            # if isinstance(func, Bee):
            #     return func.implements(cls)
            #
            # return False


modifier = ModeFactory("hive.modifier", immediate=Modifier, build=ModifierBee)
