from .mixins import TriggerSource, TriggerTarget, Bee, Bindable
from .classes import HiveBee
from . import get_mode
from . import manager
from .hive import HiveObject

def build_trigger(source, target, pre):
    # TODO: register connection, or insert a listener function in between
    targetfunc = target._hive_trigger_target()
    if pre:
        source._hive_pretrigger_source(targetfunc)
    else:
        source._hive_trigger_source(targetfunc)


class Trigger(Bindable):

    def __init__(self, source, target, pretrigger):
        self.source = source
        self.target = target
        self.pretrigger = pretrigger

    @manager.bind
    def bind(self, runhive):
        source = self.source
        if isinstance(source, Bindable):
            source = source.bind(runhive)

        target = self.target
        if isinstance(target, Bindable):
            target = target.bind(runhive)

        return build_trigger(source, target, self.pretrigger)    


class TriggerBee(HiveBee):

    def __init__(self, source, target, pretrigger):
        HiveBee.__init__(self, None, source, target, pretrigger)

    @manager.getinstance
    def getinstance(self, hive_object):
        source, target, pre_trigger = self.args

        if isinstance(source, HiveObject):
            source = source.get_trigger_source()

        if isinstance(source, Bee):
            source = source.getinstance(hive_object)

        if isinstance(target, HiveObject):
            target = target.get_trigger_target()

        if isinstance(target, Bee):    
            target = target.getinstance(hive_object)

        if get_mode() == "immediate":            
            return build_trigger(source, target, pre_trigger)

        else:
            return Trigger(source, target, pre_trigger)


def _trigger(source, target, pre_trigger):
    if isinstance(source, Bee):
        assert source.implements(TriggerSource), source
        assert target.implements(TriggerTarget), target

    else:
        assert isinstance(source, TriggerSource), source
        assert isinstance(target, TriggerTarget), target

    if get_mode() == "immediate":
        build_trigger(source, target,pre_trigger)

    else:
        trigger_bee = TriggerBee(source, target, pre_trigger)
        manager.register_bee(trigger_bee)
        return trigger_bee


def trigger(source, target, pre_trigger=False):
    return _trigger(source, target, pre_trigger)
