from .contexts import get_building_hive
from .manager import ModeFactory
from .mixins import Bee, TriggerTarget, Exportable


class Entry(Exportable, Bee):
    """Exportable proxy for TriggerTarget bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        assert target.implements(TriggerTarget), target

        self._hive_object_cls = get_building_hive()
        self._target = target

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._target)

    def export(self):
        # TODO: somehow log the redirection path
        target = self._target
        if isinstance(target, Exportable):
            target = target.export()

        return target


entry = ModeFactory("hive.entry", build=Entry)
