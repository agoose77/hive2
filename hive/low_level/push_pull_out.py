from .interfaces import ConnectableMixin
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..annotations import get_return_type
from ..exception import HiveConnectionError
from ..functional.triggerable import TriggerableBuilder, TriggerableRuntime
from ..interfaces import (Antenna, Output, Stateful, Callable, ConnectSource, Socket, Exportable, Bee)
from ..manager import ModeFactory, memoize, memo_property
from ..typing import data_type_is_untyped, data_types_match, MatchFlags, is_valid_data_type


class PullOutBase:
    mode = "pull"

    def pull(self):
        # TODO: exception handling hooks
        self.before_triggered()
        value = self._get_value()
        self.triggered()

        return value

    def _hive_connect_source(self, target):
        pass

    __call__ = pull


class PushOutBase(Socket):
    mode = "push"

    def __init__(self, target, data_type=''):
        self._targets = []

        super().__init__(target, data_type)

    def push(self):
        # TODO: exception handling hooks
        self.before_triggered()

        value = self._get_value()
        for target in self._targets:
            target(value)

        self.triggered()

    def socket(self):
        return self.push

    def _hive_connect_source(self, target):
        self._targets.append(target.push)

    __call__ = push


class PushPullOutBase(Bee, Output, ConnectSource, ConnectableMixin, Callable):
    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        is_stateful = target.implements(Stateful)

        if not (is_stateful or callable(target) or target.implements(Callable)):
            raise TypeError("Target must implement Callable or Stateful protocol")

        if is_stateful:
            data_type = target.data_type
            if isinstance(target, Stateful):
                self._get_value = target._hive_stateful_getter

        else:
            if data_type_is_untyped(data_type):
                data_type = get_return_type(target)

            self._get_value = target

        self.target = target
        self.data_type = data_type

        super().__init__()

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != self.mode:
            raise HiveConnectionError("Target {} is not configured for push mode".format(target))

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushPullInImmediate(PushPullOutBase):
    def __init__(self, target, data_type=''):
        super().__init__(target, data_type)

        self.before_triggered = TriggerFuncRuntime()
        self.triggered = TriggerFuncRuntime()


class PullOutImmediate(PullOutBase, PushPullInImmediate):
    pass


class PushOutImmediate(PushOutBase, PushPullInImmediate):
    def __init__(self, target, data_type=''):
        super().__init__(target, data_type)

        self.trigger = TriggerableRuntime(self)


class PushPullOutBound(PushPullOutBase):
    def __init__(self, build_bee, run_hive, target, data_type=''):
        self._run_hive = run_hive
        self._build_bee = build_bee

        super().__init__(target, data_type)

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def before_triggered(self):
        return self._build_bee.before_triggered.bind(self._run_hive)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r}, {!r})".format(self.__class__.__name__, self._build_bee, self._run_hive,
                                                   self.target, self.data_type)


class PullOutBound(PullOutBase, PushPullOutBound):
    pass


class PushOutBound(PushOutBase, PushPullOutBound):
    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class PPOutBuilder(Output, Exportable, ConnectableMixin):
    mode = None
    runtime_cls = None

    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # TODO: IMP sane as ppinbee
        is_stateful = target.implements(Stateful)

        assert is_stateful or callable(target) or target.implements(Callable)  # TODO: nice error message

        if is_stateful:
            data_type = target.data_type

        elif data_type_is_untyped(data_type):
            data_type = get_return_type(target)

        self.data_type = data_type
        self.target = target

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()
        self.trigger = TriggerableBuilder(self)

        super().__init__()

    @memoize
    def bind(self, run_hive):
        return self.runtime_cls(self, run_hive, self.target.bind(run_hive), data_type=self.data_type)

    def implements(self, cls):
        if issubclass(PushPullOutBase, cls):
            return True
        return super().implements(cls)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushOutBuilder(PPOutBuilder):
    mode = "push"
    runtime_cls = PushOutBound


class PullOutBuilder(PPOutBuilder):
    mode = "pull"
    runtime_cls = PullOutBound


push_out = ModeFactory("hive.push_out", immediate=PushOutImmediate, build=PushOutBuilder)
pull_out = ModeFactory("hive.pull_out", immediate=PullOutImmediate, build=PullOutBuilder)
