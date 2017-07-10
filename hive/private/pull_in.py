from .interfaces import ConnectableMixin
from .triggerable import TriggerableBuilder, TriggerableRuntime
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..exception import HiveConnectionError
from ..interfaces import Antenna, Output, Stateful, ConnectTarget, Callable, Exportable, Bee, IOModes
from ..manager import memoize, ModeFactory, memo_property
from ..typing import data_types_match, MatchFlags


class PullInBase(Bee, Antenna, ConnectTarget, ConnectableMixin, Callable):
    mode = IOModes.PULL

    def __init__(self, target):
        # Once bound, hive Method object is resolved to a function, not bee
        assert isinstance(target, Stateful)

        self._target = target
        self._pull_callback = None
        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    def pull(self):
        # TODO: exception handling hooks
        self.before_triggered()
        value = self._pull_callback()
        self._target._hive_stateful_setter(value)
        self.triggered()

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Output):
            raise HiveConnectionError("Source {} does not implement Output".format(source))

        if source.mode != IOModes.PULL:
            raise HiveConnectionError("Source {} is not configured for pull mode".format(source))

        if not data_types_match(source.data_type, self._target.data_type,
                                MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def _hive_connect_target(self, source):
        if self._pull_callback is not None:
            raise TypeError("pull_in cannot accept more than one connection: {}".format(source))

        self._pull_callback = source.pull

    __call__ = pull


class PullInImmediate(PullInBase):
    def __init__(self, target):
        self.before_triggered = TriggerFuncRuntime()
        self.triggered = TriggerFuncRuntime()
        self.trigger = TriggerableRuntime(self)

        super().__init__(target)

    def __repr__(self):
        return "PullInImmediate({!r})".format(self._target)


class PullInBound(PullInBase):
    def __init__(self, build_bee, run_hive, target):
        self._run_hive = run_hive
        self._build_bee = build_bee

        super().__init__(target)

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def before_triggered(self):
        return self._build_bee.before_triggered.bind(self._run_hive)

    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)

    def __repr__(self):
        return "PullInBound({!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._target)


class PullInBuilder(Antenna, Exportable, ConnectableMixin):
    mode = IOModes.PULL

    def __init__(self, target):
        assert target.implements(Stateful)

        self._target = target

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

        super().__init__()

    @memoize
    def bind(self, run_hive):
        return PullInBound(self, run_hive, self._target.bind(run_hive))

    def implements(self, cls):
        return issubclass(PullInBound, cls) or super().implements(cls)

    def __repr__(self):
        return "PullInBuilder({!r})".format(self.__class__.__name__, self._target)


pull_in = ModeFactory("hive.pull_in", immediate=PullInImmediate, build=PullInBuilder)
