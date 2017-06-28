from .exception import HiveConnectionError
from .manager import memoize, ModeFactory
from .policies import SingleRequired
from .protocols import ConnectTarget, Plugin, Socket, Callable, Exportable, Bee, Bindable, Nameable
from .typing import is_valid_data_type


class HiveSocket(Exportable, Bindable, Socket, ConnectTarget, Nameable):
    def __init__(self, func, data_type="", run_hive=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        assert callable(func) or isinstance(func, Callable), func
        self._run_hive = run_hive
        self._func = func

        self.data_type = data_type

        super().__init__()

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        if isinstance(self._func, Bindable):
            func = self._func.bind(run_hive)

        else:
            func = self._func

        return self.__class__(func, self.data_type, run_hive)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        func = self._func

        if isinstance(func, Exportable):
            exported = func.export()
            return self.__class__(exported, self.data_type, self._run_hive)

        else:
            return self

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Plugin):
            raise HiveConnectionError("Socket source must be a subclass of Plugin")

    def _hive_connect_target(self, source):
        plugin = source.plugin()
        self._func(plugin)

    def __repr__(self):
        return "HiveSocket({!r}, {!r}, {!r})".format(self._func, self.data_type, self._run_hive)


class HiveSocketBuilder(Exportable, Socket, ConnectTarget):
    def __init__(self, target, identifier=None, data_type="", policy=None, export_to_parent=False):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._target = target

        self.identifier = identifier
        self.data_type = data_type
        self.export_to_parent = export_to_parent

        if policy is None:
            policy = SingleRequired

        self.policy = policy

        super().__init__()

    def __repr__(self):
        return "<Socket: {}>".format(self._target)

    @memoize
    def getinstance(self, hive_object):
        target = self._target
        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        return HiveSocket(target, self.data_type)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        target = self._target
        if isinstance(target, Exportable):
            exported = target.export()

            return self.__class__(exported, self.identifier, self.data_type, self.policy, self.export_to_parent)

        else:
            return self

    def __repr__(self):
        return "HiveSocketBuilder({!r}, {!r}, {!r}, {!r}, {!r})".format(self._target, self.identifier, self.data_type,
                                                                        self.policy, self.export_to_parent)


socket = ModeFactory("hive.socket", immediate=HiveSocket, build=HiveSocketBuilder)
