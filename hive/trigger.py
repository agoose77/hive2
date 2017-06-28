from .contexts import get_mode, register_bee
from .debug import get_debug_context
from .manager import memoize
from .protocols import TriggerSourceBase, TriggerTargetBase, Bee, Bindable, TriggerTargetDerived, TriggerSourceDerived


def build_trigger(source, target, pre):
    # TODO: register connection, or insert a listener function in between
    debug_context = get_debug_context()
    if debug_context is not None:
        debug_context.build_trigger(source, target, pre)

    else:
        target_func = target._hive_trigger_target()

        if pre:
            source._hive_pretrigger_source(target_func)

        else:
            source._hive_trigger_source(target_func)


class Trigger(Bindable):
    def __init__(self, source, target, pretrigger):
        self.source = source
        self.target = target
        self.pretrigger = pretrigger

        super().__init__()

    @memoize
    def bind(self, run_hive):
        source = self.source
        if isinstance(source, Bindable):
            source = source.bind(run_hive)

        target = self.target
        if isinstance(target, Bindable):
            target = target.bind(run_hive)

        return build_trigger(source, target, self.pretrigger)


class TriggerBee(Bee):
    def __init__(self, source, target, pretrigger):
        self.source = source
        self.target = target
        self.pretrigger = pretrigger

        super().__init__()

    @memoize
    def getinstance(self, hive_object):
        source = self.source
        target = self.target
        pretrigger = self.pretrigger

        if isinstance(source, TriggerSourceDerived):
            source = source._hive_get_trigger_source()

        if isinstance(source, Bee):
            source = source.getinstance(hive_object)

        if isinstance(target, TriggerTargetDerived):
            target = target._hive_get_trigger_target()

        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        if get_mode() == "immediate":
            return build_trigger(source, target, pretrigger)

        else:
            return Trigger(source, target, pretrigger)


def trigger(source, target, pretrigger=False):
    if isinstance(source, Bee):
        assert source.implements(TriggerSourceBase), source
        assert target.implements(TriggerTargetBase), target

    else:
        assert isinstance(source, TriggerSourceBase), source
        assert isinstance(target, TriggerTargetBase), target

    if get_mode() == "immediate":
        build_trigger(source, target, pretrigger)

    else:
        trigger_bee = TriggerBee(source, target, pretrigger)
        register_bee(trigger_bee)
        return trigger_bee
