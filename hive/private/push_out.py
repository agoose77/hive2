from .mixins import ConnectableMixin
from .triggerable import TriggerableBuilder, TriggerableRuntime
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..exception import HiveConnectionError
from ..interfaces import Antenna, Output, Stateful, Callable, ConnectSource, Exportable, Bee, IOModes
from ..manager import ModeFactory, memoize, memo_property
from ..typing import data_types_match, MatchFlags


class PushOutBase(Bee, Output, ConnectSource, ConnectableMixin, Callable):
    mode = IOModes.PUSH

    def __init__(self, target):
        assert target.implements(Stateful)

        self._target = target
        self._targets = []

        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != IOModes.PUSH:
            raise HiveConnectionError("Target {} is not configured for push mode".format(target))

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def push(self):
        # TODO: exception handling hooks
        self.before_triggered()

        value = self._target._hive_stateful_getter()
        for target in self._targets:
            target(value)

        self.triggered()

    def socket(self):
        return self.push

    def _hive_connect_source(self, target):
        self._targets.append(target.push)

    __call__ = push


class PushOutImmediate(PushOutBase):
    def __init__(self, target):
        super().__init__(target)

        self.before_triggered = TriggerFuncRuntime()
        self.triggered = TriggerFuncRuntime()
        self.trigger = TriggerableRuntime(self)

    def __repr__(self):
        return "PushOutImmediate({!r})".format(self._target)


class PushOutBound(PushOutBase):
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
        return "PushOutBound({!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._target)


class PushOutBuilder(Output, Exportable, ConnectableMixin):
    mode = IOModes.PUSH

    def __init__(self, target):
        assert target.implements(Stateful)

        self.target = target

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

        super().__init__()

    @memoize
    def bind(self, run_hive):
        return PushOutBound(self, run_hive, self.target.bind(run_hive))

    def implements(self, cls):
        return issubclass(PushOutBound, cls) or super().implements(cls)

    def __repr__(self):
        return "PushOutBuilder({!r})".format(self.target)


push_out = ModeFactory("hive.push_out", immediate=PushOutImmediate, build=PushOutBuilder)
