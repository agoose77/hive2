from .classes import HiveBee
from .manager import ModeFactory, memoize
from .mixins import TriggerTarget, ConnectTarget, TriggerSource, Callable, Bee, Bindable, Nameable
from .exception import HiveConnectionError


class Triggerable(TriggerTarget, ConnectTarget, Bindable, Callable, Nameable):
    """Callable Python snippet"""

    def __init__(self, func, run_hive=None):
        assert callable(func) or isinstance(func, Callable), func
        self._func = func
        self._run_hive = run_hive

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


class TriggerableBee(TriggerTarget, ConnectTarget, Callable, HiveBee):
    """Callable Python snippet"""

    def __init__(self, func):
        super(TriggerTarget, self).__init__()

        self._func = func

    @memoize
    def getinstance(self, hive_object):
        func = self._func
        if isinstance(func, Bee): 
            func = func.getinstance(hive_object)

        return Triggerable(func)


triggerable = ModeFactory("hive.triggerable", immediate=Triggerable, build=TriggerableBee)