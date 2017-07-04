from ..contexts import get_mode, register_bee
from ..interfaces import TriggerSourceBase, TriggerTargetBase, Bee
# from hive.debug import get_debug_context
from ..manager import memoize


def build_trigger(source, target):
    # TODO: register connection, or insert a listener function in between
    debug_context = None  # get_debug_context()
    if debug_context is not None:
        debug_context.build_trigger(source, target)

    else:
        target_func = target._hive_trigger_target()
        source._hive_trigger_source(target_func)


class TriggerBuilder(Bee):
    def __init__(self, source, target):
        self._source = source
        self._target = target
        super().__init__()

    @memoize
    def bind(self, run_hive):
        source = self._source.bind(run_hive)
        target = self._target.bind(run_hive)

        return build_trigger(source, target)

    def __repr__(self):
        return "TriggerBuilder({!r}, {!r})".format(self._source, self._target)


def trigger(source, target):
    if isinstance(source, Bee):
        assert source.implements(TriggerSourceBase), source
        assert target.implements(TriggerTargetBase), target

    else:
        assert isinstance(source, TriggerSourceBase), source
        assert isinstance(target, TriggerTargetBase), target

    if get_mode() == "immediate":
        build_trigger(source, target)

    else:
        trigger_bee = TriggerBuilder(source, target)
        register_bee(trigger_bee)
        return trigger_bee
