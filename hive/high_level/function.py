from ..functional.modifier import Modifier
from ..functional.triggerfunc import TriggerFunc
from ..low_level.triggerfunc import TriggerFuncBuilder
from ..manager import ModeFactory
from ..interfaces import TriggerTarget, ConnectTarget, Bee, TriggerSource


class FunctionImmediate(Bee):

    def __init__(self, func):
        assert callable(func)
        self._func = func

        self.triggered = TriggerFunc(self._on_triggered)
        self.trigger = ...

    def __call__(self):
        self.trigger()

    def _on_triggered(self):
        self._func()
        self.triggered()

    def _hive_trigger_target(self):
        return self._on_triggered

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, TriggerSource):
            raise HiveConnectionError("Connect target {} is not a TriggerSource".format(source))

    def _hive_connect_target(self, source):
        pass


class FunctionBound(Bee):

    def __init__(self, func, run_hive):
        self._func = func
        self._run_hive = run_hive
        super().__init__()


class FunctionBuilder(Bee):

    def __init__(self, func):
        self._func = Modifier(func)
        super().__init__()

        self.triggered = TriggerFuncBuilder()

    def bind(self, run_hive):
        return self._func.bind(run_hive)

    def implements(self, cls):
        if cls is TriggerTarget or cls is ConnectTarget:
            return True

        return super().implements(cls)


function = ModeFactory("Function", build=FunctionBuilder, immediate=FunctionImmediate)
