from hive.internal_bees.triggerable import TriggerableBuilder, TriggerableRuntime
from .interfaces import ConnectableMixin
from .triggerfunc import TriggerFuncBuilder, TriggerFuncRuntime
from ..annotations import get_argument_types
from ..exception import HiveConnectionError
from ..interfaces import Antenna, Output, Stateful, ConnectTarget, Callable, Exportable, Bee
from ..manager import memoize, ModeFactory, memo_property
from ..typing import data_type_is_untyped, data_types_match, MatchFlags, is_valid_data_type


def get_callable_data_type(target):
    arg_types = get_argument_types(target)
    if len(arg_types) > 1:
        raise ValueError("Target must have only one argument")

    return next(iter(arg_types.values()), None)


class PushPullInBase(Bee, Antenna, ConnectTarget, ConnectableMixin, Callable):
    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        # Once bound, hive Method object is resolved to a function, not bee
        assert isinstance(target, Stateful) or isinstance(target, Callable) or callable(target), target

        if isinstance(target, Stateful):
            data_type = target.data_type
            # If not yet bound, set_value will have None for run hive!
            self._set_value = target._hive_stateful_setter

        else:
            if data_type_is_untyped(data_type):
                data_type = get_callable_data_type(target)
            self._set_value = target

        self.target = target
        self.data_type = data_type
        super(PushPullInBase, self).__init__()

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushInBase:
    mode = "push"

    def push(self, value):
        # TODO: exception handling hooks
        self.before_triggered()
        self._set_value(value)
        self.triggered()

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Output):
            raise HiveConnectionError("Source {} does not implement Output".format(source))

        if source.mode != "push":
            raise HiveConnectionError("Source {} is not configured for push mode".format(source))

        if not data_types_match(source.data_type, self.data_type, MatchFlags.permit_any | MatchFlags.match_shortest):
            raise HiveConnectionError("Data types do not match: {}, {}".format(source.data_type, self.data_type))

    def _hive_connect_target(self, source):
        pass

    __call__ = push


class PullInBase(Callable):
    mode = "pull"
    _pull_callback = None

    def pull(self):
        # TODO: exception handling hooks
        self.before_triggered()
        value = self._pull_callback()
        self._set_value(value)
        self.triggered()

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

    __call__ = pull


class PushPullInImmediate(PushPullInBase):
    def __init__(self, target, data_type=''):
        self.before_triggered = TriggerFuncRuntime()
        self.triggered = TriggerFuncRuntime()
        super(PushPullInImmediate, self).__init__(target, data_type)


class PushInImmediate(PushInBase, PushPullInImmediate):
    pass


class PullInImmediate(PullInBase, PushPullInImmediate):
    def __init__(self, target, data_type=''):
        super(PullInImmediate, self).__init__(target, data_type)

        self.trigger = TriggerableRuntime(self)


class PushPullInBound(PushPullInBase):
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


class PullInBound(PullInBase, PushPullInBound):
    @memo_property
    def trigger(self):
        return self._build_bee.trigger.bind(self._run_hive)


class PushInBound(PushInBase, PushPullInBound):
    pass


class PPInBuilder(Antenna, Exportable, ConnectableMixin):
    mode = None
    runtime_cls = None

    def __init__(self, target, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        is_stateful = target.implements(Stateful)
        if not (is_stateful or target.implements(Callable)):
            raise TypeError("Target must implement Callable or Stateful protocol")

        if is_stateful:
            data_type = target.data_type

        elif data_type_is_untyped(data_type):
            data_type = get_callable_data_type(target)

        self.target = target
        self.data_type = data_type

        self.triggered = TriggerFuncBuilder()
        self.before_triggered = TriggerFuncBuilder()

        super().__init__()

    @memoize
    def bind(self, run_hive):
        return self.runtime_cls(self, run_hive, self.target.bind(run_hive), data_type=self.data_type)

    def implements(self, cls):
        if issubclass(PushPullInBound, cls):
            return True
        return super().implements(cls)

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.target, self.data_type)


class PushInBuilder(PPInBuilder):
    mode = "push"
    runtime_cls = PushInBound


class PullInBuilder(PPInBuilder):
    mode = "pull"
    runtime_cls = PullInBound

    def __init__(self, target, data_type=''):
        super().__init__(target, data_type)
        self.trigger = TriggerableBuilder(self)


push_in = ModeFactory("hive.push_in", immediate=PushInImmediate, build=PushInBuilder)
pull_in = ModeFactory("hive.pull_in", immediate=PushInImmediate, build=PullInBuilder)
