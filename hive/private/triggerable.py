from .plugin import HivePluginBuilder
from ..exception import HiveConnectionError
from ..interfaces import TriggerTarget, ConnectTarget, TriggerSource, Callable, BeeBase, Exportable, Bee
from ..manager import HiveModeFactory, memoize


class TriggerableRuntime(TriggerTarget, ConnectTarget, Callable, BeeBase):
    """Callable Python snippet which is passed the current run hive"""

    def __init__(self, func):
        assert callable(func), func

        self._func = func

        super().__init__()

    def _trigger(self):
        self._func()

    def _hive_trigger_target(self):
        return self._trigger

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, TriggerSource):
            raise HiveConnectionError("Connect target {} is not a TriggerSource".format(source))

    def _hive_connect_target(self, source):
        pass

    __call__ = _trigger

    def __repr__(self):
        return "TriggerableRuntime({!r})".format(self._func)


class TriggerableBuilder(BeeBase, TriggerTarget, ConnectTarget, Exportable):
    """Callable Python snippet which is passed the current run hive"""

    def __init__(self, target):
        assert callable(target) or target.implements(Callable)
        self._target = target

        super().__init__()

    @memoize
    def bind(self, run_hive):
        target = self._target
        if isinstance(target, Bee):
            target = target.bind(run_hive)
        return TriggerableRuntime(target)

    def implements(self, cls):
        if issubclass(TriggerableRuntime, cls):
            return True

        return super().implements(cls)

    def plugin(self, *args, **kwargs):
        return HivePluginBuilder(self, *args, **kwargs)

    def __repr__(self):
        return "TriggerableBuilder({!r})".format(self._target)


triggerable = HiveModeFactory("hive.triggerable", IMMEDIATE=TriggerableRuntime, BUILD=TriggerableBuilder)
