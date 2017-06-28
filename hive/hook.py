from .manager import ModeFactory
from .protocols import Bee, TriggerSource, Exportable


class Hook(Exportable):
    """Exportable proxy for TriggerSource bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        assert target.implements(TriggerSource), target

        self._target = target
        super().__init__()

    def export(self):
        # TODO: somehow log the redirection path
        target = self._target

        if isinstance(target, Exportable):
            target = target.export()

        return target

    def __repr__(self):
        return "Hook({!r})".format(self._target)


hook = ModeFactory("hive.hook", build=Hook)
