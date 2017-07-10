from .mixins import TriggerableMixin
from ..exception import HiveConnectionError
from ..interfaces import TriggerSource, TriggerTarget, ConnectSource, Callable, Bee, Exportable
from ..manager import ModeFactory, memoize


class TriggerFuncRuntime(Bee, TriggerSource, ConnectSource, Callable, TriggerableMixin):
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


class TriggerFuncBuilder(TriggerSource, ConnectSource, Exportable, TriggerableMixin):
    data_type = 'trigger'

    @memoize
    def bind(self, run_hive):
        return TriggerFuncRuntime()

    def implements(self, cls):
        if issubclass(TriggerFuncRuntime, cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "TriggerFuncBuilder()".format()


triggerfunc = ModeFactory("hive.triggerfunc", immediate=TriggerFuncRuntime, build=TriggerFuncBuilder)
