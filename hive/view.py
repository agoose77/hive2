from .manager import ModeFactory, memoize
from .protocols import Bee, Stateful, Exportable


class View(Exportable):
    """Exportable proxy for Antenna bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        # TODO: IMP want something that resolves to an antenna
        assert target.implements(Stateful), target

        self._target = target

        super().__init__()

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        target = self._target

        if isinstance(target, Exportable):
            target = target.export()

        return target

    def implements(self, cls):
        if isinstance(self._target, Bee) and self._target.implements(cls):
            return True

        return super().implements(cls)

    def __repr__(self):
        return "View({!r})".format(self._target)


view = ModeFactory("hive.view", build=View)
