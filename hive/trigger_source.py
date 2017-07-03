from .protocols import ConnectSource, TriggerSource, Bee
from .classes import Pusher
from .trigger import trigger
from .manager import memoize, ModeFactory


class TriggerSourceRuntime(Bee, ConnectSource, TriggerSource):

    def __init__(self):
        self._pusher = Pusher(self)

        super().__init__()

    def __call__(self):
        self._pusher.push()

    def triggers(self, other):
        return trigger(self, other)

    def _hive_trigger_source(self, func):
        self._pusher.add_target(func)

    def _hive_pretrigger_source(self, func):
        self._pretrigger.add_target(func)


class TriggerSourceBuilder(Bee, ConnectSource, TriggerSource):

    def triggers(self, other):
        return trigger(self, other)

    def pretriggers(self, other):
        return trigger(self, other, pretrigger=True)

    @memoize
    def bind(self, run_hive):
        return TriggerSourceRuntime()


trigger_source = ModeFactory("hive.trigger_source", build=TriggerSourceBuilder, immediate=TriggerSourceRuntime)