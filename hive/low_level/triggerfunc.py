from hive.trigger import trigger
from ..functional.triggerfunc import TriggerFuncBuilder as FunctionalTriggerFuncBuilder


class TriggerFuncBuilder(FunctionalTriggerFuncBuilder):

    def trigger(self, other):
        return trigger(self, other)

    def pretrigger(self, other):
        return trigger(self, other, pretrigger=True)

    connect = trigger