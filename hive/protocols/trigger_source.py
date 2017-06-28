"""
Hives that are TriggerSources can be used as the source argument in the trigger and pretrigger commands
A TriggerSource must have _hive_trigger_source and _hive_pretrigger_source methods, invoked upon connection to the target
This method must return a callable or raise an informative HiveConnectError 
"""

from . import Connectable


class TriggerSourceBase(Connectable):
    pass


class TriggerSource(TriggerSourceBase):

    def _hive_trigger_source(self, target):
        raise NotImplementedError

    def _hive_pretrigger_source(self):
        raise NotImplementedError


class TriggerSourceDerived(TriggerSourceBase):

    def _hive_get_trigger_source(self):
        raise NotImplementedError