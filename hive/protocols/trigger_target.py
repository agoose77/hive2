"""
Hives that are TriggerTargets can be used as the target argument in the trigger and pretrigger commands
A TriggerTarget must have a _hive_trigger_target method
This method must return a callable or raise an informative HiveConnectError 
"""

from . import Connectable


class TriggerTargetBase(Connectable):
    pass


class TriggerTarget(TriggerTargetBase):

    def _hive_trigger_target(self):
        raise NotImplementedError


class TriggerTargetDerived(TriggerTargetBase):

    def _hive_get_trigger_target(self):
        raise NotImplementedError