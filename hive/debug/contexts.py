from csv import writer as csv_writer
from weakref import ref

from ..compatability import cache
from ..ppin import PullIn
from ..ppout import PushOut
from ..mixins import Nameable

from .bees import DebugPushOutTarget, DebugPretriggerTarget, DebugPullInSource, DebugTriggerTarget


_debug_context = None


def get_debug_context():
    return _debug_context


def set_debug_context(context):
    global _debug_context
    if context is not None:
        assert _debug_context is None
    _debug_context = context


class DebugContextBase(object):

    def __enter__(self):
        set_debug_context(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_debug_context(None)

    def build_connection(self, source, target):
        raise NotImplementedError

    def build_trigger(self, source, target, pre):
        raise NotImplementedError


class ReportedDebugContextBase(DebugContextBase):
    """Base class for connection and trigger listener callbacks"""

    def report_trigger(self, source_ref, target_ref):
        raise NotImplementedError

    def report_pretrigger(self, source_ref, target_ref):
        raise NotImplementedError

    def report_push_out(self, source_ref, target_ref, data):
        raise NotImplementedError

    def report_pull_in(self, source_ref, target_ref, data):
        raise NotImplementedError

    def build_connection(self, source, target):
        if isinstance(source, PushOut):
            target = DebugPushOutTarget(self, ref(source), ref(target))

        elif isinstance(target, PullIn):
            source = DebugPullInSource(self, ref(source), ref(target))

        target._hive_connect_target(source)
        source._hive_connect_source(target)

    def build_trigger(self, source, target, pre):
        target_func = target._hive_trigger_target()

        if pre:
            callable_target = DebugPretriggerTarget(self, ref(source), ref(target))
            source._hive_pretrigger_source(callable_target)
            source._hive_pretrigger_source(target_func)

        else:
            callable_target = DebugTriggerTarget(self, ref(source), ref(target))
            source._hive_trigger_source(callable_target)
            source._hive_trigger_source(target_func)


class BeeNotNameableError(Exception):
    pass


class FileDebugContext(ReportedDebugContextBase):
    """Basic debug context to write to file.

    Uses first absolute name (for aliased bees, this may create some confusion).
    """

    class _NoData:
        """Placeholder for omitted arguments"""
        pass

    def __init__(self, file_):
        self._file = file_
        self._lines = []

    def report_trigger(self, source_ref, target_ref):
        self._write_reported_operation("trigger", source_ref, target_ref)

    def report_pretrigger(self, source_ref, target_ref):
        self._write_reported_operation("pre-trigger", source_ref, target_ref)

    def report_push_out(self, source_ref, target_ref, data):
        self._write_reported_operation("push-out", source_ref, target_ref, data)

    def report_pull_in(self, source_ref, target_ref, data):
        self._write_reported_operation("pull-in", source_ref, target_ref, data)

    @cache()
    def _get_absolute_name(self, bee_ref):
        bee = bee_ref()

        if not isinstance(bee, Nameable):
            raise BeeNotNameableError("Bee is not Nameable")

        path = []
        while True:
            try:
                parent_ref, bee_name = next(iter(bee._hive_runtime_aliases))

            except TypeError:
                break

            path.append(bee_name)

            bee = parent_ref()

        return ".".join(path)

    def _write_reported_operation(self, op_name, source_ref, target_ref, data=_NoData):
        try:
            source_name = self._get_absolute_name(source_ref)
            target_name = self._get_absolute_name(target_ref)

        except BeeNotNameableError:
            return

        if data is self._NoData:
            line = op_name, source_name, target_name

        else:
            line = op_name, source_name, target_name, data

        self._lines.append(line)

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(FileDebugContext, self).__exit__(exc_type, exc_val, exc_tb)

        debug_writer = csv_writer(self._file, dialect='excel')
        debug_writer.writerow("Operation", "Source", "Target", "Value(?)")
        debug_writer.writerows(self._lines)

        self._lines.clear()
