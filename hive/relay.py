from .classes import Pusher
from .exception import HiveConnectionError
from .manager import ModeFactory, memoize
from .protocols import TriggerSource, TriggerTarget, ConnectSource, Callable, Bee, Bindable, Nameable


class Relay(Bee, TriggerSource, TriggerTarget, Callable, Nameable):
    """Callable interface to HIVE (pre)trigger"""

    def __init__(self):
        self._trigger = Pusher(self)
        self._pretrigger = Pusher(self)

        super().__init__()

    def __call__(self):
        self.trigger()

    def trigger(self):
        # TODO: exception handling hooks
        self._pretrigger.push()
        self._trigger.push()

    def _hive_trigger_target(self):
        return self.trigger

    def _hive_trigger_source(self, target_func):
        self._trigger.add_target(target_func)

    def _hive_pretrigger_source(self, target_func):
        self._pretrigger.add_target(target_func)


    def __repr__(self):
        return "Relay()"


class RelayBuilder(Bee, TriggerSource, ConnectSource, Callable):
    data_type = 'trigger'

    @memoize
    def getinstance(self, hive_object):
        return Relay()

    def implements(self, cls):
        if issubclass(Relay, cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "RelayBuilder()"


relay = ModeFactory("hive.relay", immediate=Relay, build=RelayBuilder)
