from functools import partial

from .annotations import get_return_type
from .classes import Pusher
from .exception import HiveConnectionError
from .manager import ModeFactory, memoize
from .protocols import (Antenna, Output, Stateful, Bindable, Callable, ConnectSource, TriggerSource, TriggerTarget,
                        Socket, Nameable, Bee)
from .typing import data_type_is_untyped, data_types_match, MatchFlags, is_valid_data_type


class PPOutBase(Bindable, Output, ConnectSource, TriggerSource, Nameable):
    def __init__(self, target, data_type='', run_hive=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        is_stateful = isinstance(target, Stateful)

        if not (is_stateful or callable(target) or target.implements(Callable)):
            raise TypeError("Target must implement Callable or Stateful protocol")

        if is_stateful:
            data_type = target.data_type
            self._get_value = partial(target._hive_stateful_getter, run_hive)

        else:
            if data_type_is_untyped(data_type):
                data_type = get_return_type(target)

            self._get_value = target

        self.target = target
        self.data_type = data_type

        self._run_hive = run_hive
        self._trigger = Pusher(self)
        self._pretrigger = Pusher(self)

        super().__init__()

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        target = self.target
        if isinstance(target, Bindable):
            target = target.bind(run_hive)

        return self.__class__(target, data_type=self.data_type, run_hive=run_hive)

    def _hive_trigger_source(self, func):
        self._trigger.add_target(func)

    def _hive_pretrigger_source(self, func):
        self._pretrigger.add_target(func)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type, self._run_hive)


class PullOut(PPOutBase):
    mode = "pull"

    def pull(self):
        # TODO: exception handling hooks
        self._pretrigger.push()
        value = self._get_value()
        self._trigger.push()

        return value

    def _hive_is_connectable_source(self, target):
        # TODO what if already connected
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != "pull":
            raise HiveConnectionError("Target {} is not configured for pull mode".format(target))

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def _hive_connect_source(self, target):
        pass


class PushOut(PPOutBase, Socket, TriggerTarget):
    mode = "push"

    def __init__(self, target, data_type='', run_hive=None):
        super(PushOut, self).__init__(target, data_type, run_hive)

        self._targets = []

    def push(self):
        # TODO: exception handling hooks
        self._pretrigger.push()

        value = self._get_value()

        for target in self._targets:
            target(value)

        self._trigger.push()

    def socket(self):
        return self.push

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Antenna):
            raise HiveConnectionError("Target {} does not implement Antenna".format(target))

        if target.mode != "push":
            raise HiveConnectionError("Target {} is not configured for push mode".format(target))

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def _hive_connect_source(self, target):
        self._targets.append(target.push)

    def _hive_trigger_target(self):
        return self.push

    __call__ = push


class PPOutBuilder(Bee, Output, ConnectSource, TriggerSource):
    mode = None

    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # TODO: IMP sane as ppinbee
        is_stateful = isinstance(target, Stateful)

        assert is_stateful or callable(target) or target.implements(Callable)  # TODO: nice error message

        if is_stateful:
            data_type = target.data_type

        elif data_type_is_untyped(data_type):
            data_type = get_return_type(target)

        self.data_type = data_type
        self.target = target

        super().__init__()

    @memoize
    def getinstance(self, hive_object):
        target = self.target

        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        if self.mode == "push":
            cls = PushOut
        else:
            cls = PullOut

        return cls(target, data_type=self.data_type)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushOutBuilder(PPOutBuilder, TriggerTarget):
    mode = "push"


class PullOutBuilder(PPOutBuilder):
    mode = "pull"


push_out = ModeFactory("hive.push_out", immediate=PushOut, build=PushOutBuilder)
pull_out = ModeFactory("hive.pull_out", immediate=PullOut, build=PullOutBuilder)
