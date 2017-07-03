from .manager import ModeFactory, memoize
from .protocols import Stateful, Descriptor, Exportable, Bee


class BoundStatefulDescriptor(Bee, Descriptor):
    def __init__(self, target, read_only, run_hive):
        self._target = target
        self._read_only = read_only
        self._run_hive = run_hive

        self._hive_descriptor_get = target._hive_stateful_getter
        self._hive_descriptor_set = target._hive_stateful_setter

        super().__init__()

    _hive_descriptor_get = None
    _hive_descriptor_set = None


class BuilderStatefulDescriptor(Exportable):

    def __init__(self, target, read_only=False):
        assert target.implements(Stateful)
        self._target = target
        self._read_only = read_only

        super().__init__()

    @memoize
    def bind(self, run_hive):
        target = self._target.bind(run_hive)
        return BoundStatefulDescriptor(target, self._read_only, run_hive)


    def implements(self, cls):
        if cls is Descriptor:
            return True

        return super().implements(cls)

    def __repr__(self):
        return "BuilderStatefulDescriptor({!r}, {!r})".format(self._target, self._read_only)


stateful_descriptor = ModeFactory("stateful_descriptor", build=BuilderStatefulDescriptor)
