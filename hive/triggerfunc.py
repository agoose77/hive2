from .classes import Pusher
from .exception import HiveConnectionError
from .manager import ModeFactory, memoize
from .protocols import TriggerSource, TriggerTarget, ConnectSource, Callable, Bee, Bindable, Nameable


class TriggerFunc(Bindable, TriggerSource, ConnectSource, Callable, Nameable):
    """Callable interface to HIVE (pre)trigger"""

    data_type = 'trigger'

    def __init__(self, func=None, run_hive=None):
        assert callable(func) or func is None or isinstance(func, Callable), func
        self._run_hive = run_hive
        self._func = func
        self._trigger = Pusher(self)
        self._pretrigger = Pusher(self)
        # TODO
        self._name_counter = 0

        super().__init__()

    def __call__(self, *args, **kwargs):
        # TODO: exception handling hooks
        self._pretrigger.push()
        if self._func is not None:
            self._func(*args, **kwargs)

        self._trigger.push()

    def _hive_trigger_source(self, target_func):
        self._name_counter += 1
        self._trigger.add_target(target_func, self._name_counter)

    def _hive_pretrigger_source(self, target_func):
        self._name_counter += 1
        self._pretrigger.add_target(target_func, self._name_counter)

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, TriggerTarget):
            raise HiveConnectionError("Target {} does not implement TriggerTarget".format(target))

    def _hive_connect_source(self, target):
        target_func = target._hive_trigger_target()
        self._trigger.add_target(target_func)

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        func = self._func
        if isinstance(func, Bindable):
            func = func.bind(run_hive)

        return self.__class__(func, run_hive=run_hive)

    def __repr__(self):
        return "TriggerFunc({!r}, {!r})".format(self._func, self._run_hive)


class TriggerFuncBuilder(Bee, TriggerSource, ConnectSource, Callable):
    data_type = 'trigger'

    def __init__(self, func=None):
        self._func = func

        super().__init__()

    @memoize
    def getinstance(self, hive_object):
        func = self._func
        if isinstance(func, Bee):
            func = func.getinstance(hive_object)

        return TriggerFunc(func)

    def implements(self, cls):
        if isinstance(self._func, Bee) and self._func.implements(cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "TriggerFuncBuilder({!r})".format(self._func)


triggerfunc = ModeFactory("hive.triggerfunc", immediate=TriggerFunc, build=TriggerFuncBuilder)
