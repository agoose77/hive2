from .manager import ModeFactory
from .protocols import Bee, TriggerTarget, Exportable


class Entry(Exportable):
    """Exportable proxy for TriggerTarget bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        assert target.implements(TriggerTarget), target

        self._target = target

        super().__init__()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._target)

    def export(self):
        # TODO: somehow log the redirection path
        target = self._target
        if isinstance(target, Exportable):
            target = target.export()

        return target


entry = ModeFactory("hive.entry", build=Entry)
