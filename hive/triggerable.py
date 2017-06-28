from .exception import HiveConnectionError
from .manager import ModeFactory, memoize
from .protocols import TriggerTarget, ConnectTarget, TriggerSource, Callable, Bee, Bindable, Nameable


class Triggerable(Bindable, TriggerTarget, ConnectTarget, Callable, Nameable):
    """Callable Python snippet"""

    def __init__(self, func, run_hive=None):
        assert callable(func), func
        self._func = func
        self._run_hive = run_hive

        super().__init__()

    def __call__(self):
        self.trigger()

    def trigger(self):
        # TODO: exception handling hooks
        self._func()

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        func = self._func

        if isinstance(func, Bindable):
            func = func.bind(run_hive)

        return self.__class__(func, run_hive=run_hive)

    def _hive_trigger_target(self):
        return self.trigger

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, TriggerSource):
            raise HiveConnectionError("Source does not implement TriggerSource: {}".format(source))

    def _hive_connect_target(self, source):
        pass

    def __repr__(self):
        return "Triggerable({!r}, {!r})".format(self._func, self._run_hive)


class TriggerableBuilder(Bee, TriggerTarget, ConnectTarget):
    """Callable Python snippet"""

    def __init__(self, func):
        self._func = func

        super().__init__()

    @memoize
    def getinstance(self, hive_object):
        func = self._func
        if isinstance(func, Bee):
            func = func.getinstance(hive_object)

        return Triggerable(func)

    def implements(self, cls):
        if cls is Callable:
            return True

        return super().implements(cls)

    def __repr__(self):
        return "TriggerableBuilder({!r})".format(self._func)


triggerable = ModeFactory("hive.triggerable", immediate=Triggerable, build=TriggerableBuilder)
