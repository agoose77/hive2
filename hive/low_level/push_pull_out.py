from hive.annotations import get_return_type
from hive.exception import HiveConnectionError
from hive.interfaces import (Antenna, Output, Stateful, Callable, ConnectSource, TriggerTarget,
                             Socket, Exportable)
from hive.manager import ModeFactory, memoize, memo_property
from hive.typing import data_type_is_untyped, data_types_match, MatchFlags, is_valid_data_type
from .interfaces import ConnectableMixin
from ..functional.triggerable import TriggerableBuilder
from ..low_level.triggerfunc import TriggerFuncBuilder


class PPOutBase(Output, ConnectSource, ConnectableMixin, Callable):
    def __init__(self, build_bee, run_hive, target, data_type=''):
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

        self._run_hive = run_hive
        self._build_bee = build_bee

        super().__init__()

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != self.mode:
            raise HiveConnectionError("Target {} is not configured for push mode".format(target))

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type, self._run_hive)

    @memo_property
    def triggered(self):
        return self._build_bee.triggered.bind(self._run_hive)

    @memo_property
    def before_triggered(self):
        return self._build_bee.before_triggered.bind(self._run_hive)

    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class PullOut(PPOutBase):
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


class PushOut(PPOutBase, Socket):
    mode = "push"

    def __init__(self, build_bee, run_hive, target, data_type=''):
        super().__init__(build_bee, run_hive, target, data_type)

        self._targets = []

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


class PPOutBuilder(Output, Exportable, ConnectableMixin):
    mode = None

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
        if self.mode == "push":
            cls = PushOut
        else:
            cls = PullOut

        return cls(self, run_hive, self.target.bind(run_hive), data_type=self.data_type)

    def implements(self, cls):
        if issubclass(PPOutBase, cls):
            return True
        return super().implements(cls)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushOutBuilder(PPOutBuilder, TriggerTarget):
    mode = "push"


class PullOutBuilder(PPOutBuilder):
    mode = "pull"


push_out = ModeFactory("hive.push_out", immediate=PushOut, build=PushOutBuilder)
pull_out = ModeFactory("hive.pull_out", immediate=PullOut, build=PullOutBuilder)
