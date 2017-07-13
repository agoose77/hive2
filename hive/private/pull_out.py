from .mixins import ConnectableMixin
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..exception import HiveConnectionError
from ..interfaces import Antenna, Output, Stateful, Callable, ConnectSource, IOModes, Exportable, BeeBase
from ..manager import HiveModeFactory, memoize, memo_property
from ..typing import data_types_match, MatchFlags


class PullOutBase(BeeBase, Output, ConnectableMixin, Callable):
    mode = IOModes.PULL

    def __init__(self, target):
        assert target.implements(Stateful)

        self._target = target

        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != IOModes.PULL:
            raise HiveConnectionError("Target {} is not configured for pull mode".format(target))

        if not data_types_match(self._target.data_type, target.data_type,
                                MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def pull(self):
        # TODO: exception handling hooks
        self.pre_triggered()
        value = self._target._hive_stateful_getter()
        self.triggered()

        return value

    def _hive_connect_source(self, target):
        pass

    __call__ = pull


class PullOutImmediate(PullOutBase):
    def __init__(self, target):
        super().__init__(target)

        self.pre_triggered = TriggerFuncRuntime()
        self.triggered = TriggerFuncRuntime()

    def __repr__(self):
        return "PullOutImmediate({!r})".format(self._target)


class PullOutBound(PullOutBase):
    def __init__(self, build_bee, run_hive, target):
        self._run_hive = run_hive
        self._build_bee = build_bee

        super().__init__(target)

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def pre_triggered(self):
        return self._build_bee.pre_triggered.bind(self._run_hive)

    def __repr__(self):
        return "PullOutBound({!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._target)


class PullOutBuilder(BeeBase, Output, Exportable, ConnectableMixin):
    mode = IOModes.PULL

    def __init__(self, target):
        assert target.implements(Stateful)

        self._target = target
        self.triggered = TriggerFuncBuilder()
        self.pre_triggered = TriggerFuncBuilder()

        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    @memoize
    def bind(self, run_hive):
        return PullOutBound(self, run_hive, self._target.bind(run_hive))

    def implements(self, cls):
        return issubclass(PullOutBound, cls) or super().implements(cls)

    def __repr__(self):
        return "PullOutBuilder({!r})".format(self._target)


pull_out = HiveModeFactory("hive.pull_out", IMMEDIATE=PullOutImmediate, BUILD=PullOutBuilder)
