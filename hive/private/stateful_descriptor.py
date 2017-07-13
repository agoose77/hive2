from ..manager import HiveModeFactory, memoize
from ..interfaces import Stateful, Descriptor, Exportable, BeeBase

from enum import auto, IntFlag


class _ReadWriteFlags(IntFlag):
    READ = auto()
    WRITE = auto()
    READ_WRITE = READ | WRITE

READ = _ReadWriteFlags.READ
WRITE = _ReadWriteFlags.WRITE
READ_WRITE = _ReadWriteFlags.READ_WRITE


class StatefulDescriptorBound(BeeBase, Descriptor):

    def __init__(self, target, flags):
        self._target = target
        self._flags = flags

        if not (flags & READ_WRITE):
            raise ValueError("Attribute must be readable or writable")

        if flags & READ:
            self._hive_descriptor_get = target._hive_stateful_getter

        if flags & WRITE:
            self._hive_descriptor_set = target._hive_stateful_setter

        super().__init__()

    def _hive_descriptor_get(self):
        raise RuntimeError("Attribute cannot be read")

    def _hive_descriptor_set(self, value):
        raise RuntimeError("Attribute cannot be written")

    def __repr__(self):
        return "StatefulDescriptorBound({!r}, {!r})".format(self._target, self._flags)


class StatefulDescriptorBuilder(BeeBase, Exportable):

    def __init__(self, target, flags=READ_WRITE):
        assert target.implements(Stateful)

        if not (flags & READ_WRITE):
            raise ValueError("Attribute must be readable or writable")

        self._target = target
        self._flags = flags

        super().__init__()

    @memoize
    def bind(self, run_hive):
        target = self._target.bind(run_hive)
        return StatefulDescriptorBound(target, self._flags)

    def implements(self, cls):
        return issubclass(StatefulDescriptorBound, cls) or super().implements(cls)

    def __repr__(self):
        return "BuilderStatefulDescriptor({!r}, {!r})".format(self._target, self._flags)


stateful_descriptor = HiveModeFactory("stateful_descriptor", BUILD=StatefulDescriptorBuilder)
