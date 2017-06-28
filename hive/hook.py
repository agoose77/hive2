from .mixins import Bee, TriggerSource, Exportable
from .manager import get_building_hive, ModeFactory


class Hook(Exportable, Bee):
    """Exportable proxy for TriggerSource bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        assert target.implements(TriggerSource), target

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


hook = ModeFactory("hive.hook", build=Hook)
