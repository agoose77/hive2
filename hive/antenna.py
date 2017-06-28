from .manager import ModeFactory
from .protocols import Bee, Antenna, Exportable


class HiveAntenna(Exportable, Antenna):
    """Exportable proxy for Antenna bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        # TODO: IMP want something that resolves to an antenna
        assert target.implements(Antenna), target

        self._target = target

        super().__init__()

    def export(self):
        # TODO: somehow log the redirection path
        target = self._target

        if isinstance(target, Exportable):
            target = target.export()

        return target

    def __repr__(self):
        return "HiveAntenna({!r})".format(self._target)


antenna = ModeFactory("hive.antenna", build=HiveAntenna)
