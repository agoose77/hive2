from .manager import ModeFactory, memoize
from .protocols import Output, Exportable, Bee


class HiveOutput(Exportable, Output):
    """Exportable proxy for Output bees"""

    def __init__(self, target):
        assert isinstance(target, Bee), target
        # TODO: IMP Here we want something that will, when resolved to an instance, expose the output protocl
        assert target.implements(Output), target
        self._target = target

        super().__init__()

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._target)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        target = self._target
        if isinstance(target, Exportable):
            target = target.export()
        return target


output = ModeFactory("hive.output", build=HiveOutput)
