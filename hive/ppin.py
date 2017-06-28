from functools import partial

from .annotations import get_argument_types
from .classes import Pusher
from .exception import HiveConnectionError
from .manager import memoize, ModeFactory
from .protocols import (Antenna, Output, Stateful, ConnectTarget, TriggerSource, TriggerTarget, Bindable, Callable,
                        Nameable, Bee)
from .typing import data_type_is_untyped, data_types_match, MatchFlags, is_valid_data_type


def get_callable_data_type(target):
    arg_types = get_argument_types(target)
    if len(arg_types) > 1:
        raise ValueError("Target must have only one argument")

    return next(iter(arg_types.values()), None)


class PPInBase(Bindable, Antenna, ConnectTarget, TriggerSource, Nameable):
    def __init__(self, target, data_type='', run_hive=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # Once bound, hive Method object is resolved to a function, not bee
        assert isinstance(target, Stateful) or isinstance(target, Callable) or callable(target), target

        if isinstance(target, Stateful):
            data_type = target.data_type
            # If not yet bound, set_value will have None for run hive!
            self._set_value = partial(target._hive_stateful_setter, run_hive)

        else:
            if data_type_is_untyped(data_type):
                data_type = get_callable_data_type(target)
            self._set_value = target

        self.target = target
        self.data_type = data_type

        self._run_hive = run_hive
        self._trigger = Pusher(self)
        self._pretrigger = Pusher(self)

        super().__init__()

    def _hive_trigger_source(self, func):
        self._trigger.add_target(func)

    def _hive_pretrigger_source(self, func):
        self._pretrigger.add_target(func)

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        target = self.target
        if isinstance(target, Bindable):
            target = target.bind(run_hive)

        return self.__class__(target, data_type=self.data_type, run_hive=run_hive)

    def __repr__(self):
        return "{}({!r}, {!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type, self._run_hive)


class PushIn(PPInBase):
    mode = "push"

    def push(self, value):
        # TODO: exception handling hooks
        self._pretrigger.push()

        self._set_value(value)

        self._trigger.push()

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Output):
            raise HiveConnectionError("Source {} does not implement Output".format(source))

        if source.mode != "push":
            raise HiveConnectionError("Source {} is not configured for push mode".format(source))

        if not data_types_match(source.data_type, self.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match: {}, {}".format(source.data_type, self.data_type))

    def _hive_connect_target(self, source):
        pass


class PullIn(PPInBase, TriggerTarget):
    mode = "pull"
    _pull_callback = None

    def pull(self):
        # TODO: exception handling hooks
        self._pretrigger.push()
        value = self._pull_callback()

        self._set_value(value)

        self._trigger.push()

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Output):
            raise HiveConnectionError("Source {} does not implement Output".format(source))

        if source.mode != "pull":
            raise HiveConnectionError("Source {} is not configured for pull mode".format(source))

        if not data_types_match(source.data_type, self.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match")

    def _hive_connect_target(self, source):
        if self._pull_callback is not None:
            raise TypeError("pull_in cannot accept more than one connection: {}".format(source))

        self._pull_callback = source.pull

    def _hive_trigger_target(self):
        return self.pull

    __call__ = pull


class PPInBuilder(Bee, Antenna, ConnectTarget, TriggerSource):
    mode = None

    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # TODO: IMP - here we want an actually stateful object, or a resolvebee to a stateful object
        # In other words, something that resolves to something implementing the stateful protocol
        is_stateful = isinstance(target, Stateful)
        if not (is_stateful or target.implements(Callable)):
            raise TypeError("Target must implement Callable or Stateful protocol")

        if is_stateful:
            data_type = target.data_type

        elif data_type_is_untyped(data_type):
            data_type = get_callable_data_type(target)

        self.target = target
        self.data_type = data_type

        super().__init__()

    @memoize
    def getinstance(self, hive_object):
        target = self.target

        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        if self.mode == "push":
            return PushIn(target, data_type=self.data_type)

        return PullIn(target, data_type=self.data_type)

    def implements(self, cls):
        if Bee.implements(self, cls):
            return True

        target = self.target
        if isinstance(target, Bee):
            return target.implements(cls)

        return False

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushInBuilder(PPInBuilder):
    mode = "push"


class PullInBuilder(PPInBuilder, TriggerTarget):
    mode = "pull"


push_in = ModeFactory("hive.push_in", immediate=PushIn, build=PushInBuilder)
pull_in = ModeFactory("hive.pull_in", immediate=PullIn, build=PullInBuilder)
