from .mixins import ConnectableMixin
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..exception import HiveConnectionError
from ..interfaces import Antenna, Output, Stateful, ConnectTarget, Callable, Exportable, BeeBase, IOModes
from ..manager import memoize, HiveModeFactory, memo_property
from ..typing import data_types_match, MatchFlags


class PushInBase(BeeBase, Antenna, ConnectableMixin, Callable):
    mode = IOModes.PUSH

    def __init__(self, target):
        # Once bound, hive Method object is resolved to a function, not bee
        assert isinstance(target, Stateful)

        self._target = target
        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    def push(self, value):
        # TODO: exception handling hooks
        self.before()
        self._target._hive_stateful_setter(value)
        self.after()

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Output):
            raise HiveConnectionError("Source {} does not implement Output".format(source))

        if source.mode != IOModes.PUSH:
            raise HiveConnectionError("Source {} is not configured for push mode".format(source))

        if not data_types_match(source.data_type, self.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match: {}, {}".format(source.data_type, self.data_type))

    def _hive_connect_target(self, source):
        pass

    __call__ = push


class PushInImmediate(PushInBase):
    def __init__(self, target):
        super().__init__(target)

        self.before = TriggerFuncRuntime()
        self.after = TriggerFuncRuntime()

    def __repr__(self):
        return "PushInImmediate({!r})".format(self._target)


class PushInBound(PushInBase):
    def __init__(self, build_bee, run_hive, target):
        self._run_hive = run_hive
        self._build_bee = build_bee

        super().__init__(target)

    @memo_property
    def after(self):
        return self._build_bee.after.bind(self._run_hive)

    def __repr__(self):
        return "PushInBound({!r}, {!r}, {!r})".format(self._build_bee, self._run_hive, self._target)

    @memo_property
    def before(self):
        return self._build_bee.after.bind(self._run_hive)


class PushInBuilder(BeeBase, Antenna, Exportable, ConnectableMixin):
    mode = IOModes.PUSH

    def __init__(self, target):
        assert target.implements(Stateful)

        self._target = target

        self.after = TriggerFuncBuilder()
        self.before = TriggerFuncBuilder()

        super().__init__()

    @property
    def data_type(self):
        return self._target.data_type

    @memoize
    def bind(self, run_hive):
        return PushInBound(self, run_hive, self._target.bind(run_hive))

    def implements(self, cls):
        return issubclass(PushInBound, cls) or super().implements(cls)

    def __repr__(self):
        return "PushInBuilder({!r})".format(self._target)


push_in = HiveModeFactory("hive.push_in", IMMEDIATE=PushInImmediate, BUILD=PushInBuilder)
