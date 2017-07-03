from inspect import signature

from ..classes import Pusher
from ..exception import HiveConnectionError
from ..interfaces import TriggerSource, TriggerTarget, ConnectSource, Callable, Bee
from ..manager import ModeFactory, memoize


class TriggerFunc(TriggerSource, ConnectSource, Callable):
    """Callable interface to HIVE (pre)trigger"""

    data_type = 'trigger'

    def __init__(self, func=None):
        if func:
            assert callable(func) or func is None or isinstance(func, Callable), func
            if signature(func).parameters:
                raise ValueError("Cannot be accept function with any args")

        self._func = func

        self._trigger = Pusher(self)
        self._pretrigger = Pusher(self)

        super().__init__()

    def __call__(self, *args, **kwargs):
        # TODO: exception handling hooks
        self._pretrigger.push()

        if self._func is not None:
            self._func(*args, **kwargs)

        self._trigger.push()

    def _hive_trigger_source(self, target_func):
        self._trigger.add_target(target_func)

    def _hive_pretrigger_source(self, target_func):
        self._pretrigger.add_target(target_func)

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, TriggerTarget):
            raise HiveConnectionError("Target {} does not implement TriggerTarget".format(target))

    def _hive_connect_source(self, target):
        target_func = target._hive_trigger_target()
        self._trigger.add_target(target_func)

    def __repr__(self):
        return "TriggerFunc({!r})".format(self._func)


class TriggerFuncBuilder(Bee, TriggerSource, ConnectSource, Callable):
    data_type = 'trigger'

    def __init__(self, func=None):
        self._func = func

        if signature(func).parameters:
            raise ValueError("Cannot be accept function with any args")

        super().__init__()

    @memoize
    def bind(self, run_hive):
        func = self._func
        if isinstance(func, Bindable):
            func = func.bind(run_hive)

        return TriggerFunc(func)

    def implements(self, cls):
        if isinstance(self._func, Bee) and self._func.implements(cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "TriggerFuncBuilder({!r})".format(self._func)


triggerfunc = ModeFactory("hive.triggerfunc", immediate=TriggerFunc, build=TriggerFuncBuilder)
