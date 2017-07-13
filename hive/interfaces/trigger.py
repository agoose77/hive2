"""
Hives that are TriggerSources can be used as the source argument in the trigger and pretrigger commands
A TriggerSource must have _hive_trigger_source and _hive_pretrigger_source methods, invoked upon connection to the target
This method must return a callable or raise an informative HiveConnectError 

Hives that are TriggerTargets can be used as the target argument in the trigger and pretrigger commands
A TriggerTarget must have a _hive_trigger_target method
This method must return a callable or raise an informative HiveConnectError
"""


class TriggerSourceBase:
    pass


class TriggerTargetBase:
    pass


class TriggerSource(TriggerSourceBase):

    def _hive_trigger_source(self, target):
        raise NotImplementedError


class TriggerSourceDerived(TriggerSourceBase):

    def _hive_get_trigger_source(self):
        raise NotImplementedError


class TriggerTarget(TriggerTargetBase):

    def _hive_trigger_target(self):
        raise NotImplementedError


class TriggerTargetDerived(TriggerTargetBase):

    def _hive_get_trigger_target(self):
        raise NotImplementedError