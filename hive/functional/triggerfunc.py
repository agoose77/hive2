from ..exception import HiveConnectionError
from ..interfaces import TriggerSource, TriggerTarget, ConnectSource, Callable, Bee
from ..manager import ModeFactory, memoize


class TriggerFunc(TriggerSource, ConnectSource, Callable):
    """Callable interface to HIVE (pre)trigger"""

    data_type = 'trigger'

    def __init__(self):
        self._targets = []

        super().__init__()

    def _hive_trigger_source(self, target_func):
        self._targets.append(target_func)

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, TriggerTarget):
            raise HiveConnectionError("Target {} does not implement TriggerTarget".format(target))

    def _hive_connect_source(self, target):
        target_func = target._hive_trigger_target()
        self._targets.append(target_func)

    def __call__(self):
        for target in self._targets:
            target()

    def __repr__(self):
        return "TriggerFunc()".format()


class TriggerFuncBuilder(Bee, TriggerSource, ConnectSource):
    data_type = 'trigger'
    runtime_cls = TriggerFunc

    @memoize
    def bind(self, run_hive):
        return self.runtime_cls()

    def implements(self, cls):
        if issubclass(self.runtime_cls, cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "TriggerFuncBuilder()".format()


triggerfunc = ModeFactory("hive.triggerfunc", immediate=TriggerFunc, build=TriggerFuncBuilder)
