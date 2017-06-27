from functools import partial

from .annotations import get_return_type
from .classes import Pusher
from .exception import HiveConnectionError
from .manager import get_mode, get_building_hive, memoize
from .mixins import (Antenna, Output, Stateful, Bee, Bindable, Callable, ConnectSource, TriggerSource, TriggerTarget,
                     Socket, Nameable)
from .typing import data_type_is_untyped, data_types_match, MatchFlags


class PPOutBase(Output, ConnectSource, TriggerSource, Bindable, Nameable):
    def __init__(self, target, data_type='', run_hive=None):
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

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.full_match):
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

        if not data_types_match(self.data_type, target.data_type, MatchFlags.permit_any | MatchFlags.full_match):
            raise HiveConnectionError("Data types do not match")

    def _hive_connect_source(self, target):
        self._targets.append(target.push)

    def _hive_trigger_target(self):
        return self.push

    __call__ = push


class PPOutBee(Output, ConnectSource, TriggerSource):
    mode = None

    def __init__(self, target, data_type=''):
        is_stateful = isinstance(target, Stateful)

        assert is_stateful or callable(target) or target.implements(Callable)  # TODO: nice error message

        if is_stateful:
            data_type = target.data_type

        else:
            if not data_type:
                data_type = get_return_type(target)

        self._hive_object_cls = get_building_hive()
        self.data_type = data_type
        self.target = target

    @memoize
    def getinstance(self, hive_object):
        target = self.target

        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        if self.mode == "push":
            instance = PushOut(target, data_type=self.data_type)

        else:
            instance = PullOut(target, data_type=self.data_type)

        return instance

    def implements(self, cls):
        if Bee.implements(self, cls):
            return True

        target = self.target
        if isinstance(target, Bee):
            return target.implements(cls)

        return False


class PushOutBee(PPOutBee, TriggerTarget):
    mode = "push"


class PullOutBee(PPOutBee):
    mode = "pull"


def push_out(target, data_type=''):
    if get_mode() == "immediate":
        return PushOut(target, data_type=data_type)

    else:
        return PushOutBee(target, data_type=data_type)


def pull_out(target, data_type=''):
    if get_mode() == "immediate":
        return PullOut(target, data_type=data_type)

    else:
        return PullOutBee(target, data_type=data_type)
