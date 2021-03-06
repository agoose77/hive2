from .exception import HiveConnectionError
from .identifier import is_valid_identifier
from .manager import memoize, ModeFactory
from .policies import MultipleOptional
from .protocols import Plugin, Socket, ConnectSource, Exportable, Callable, Bee, Bindable, Nameable
from .typing import is_valid_data_type


class HivePlugin(Exportable, Bindable, Plugin, ConnectSource, Nameable):
    def __init__(self, func, data_type='', run_hive=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        assert callable(func) or isinstance(func, Callable), func

        self._run_hive = run_hive
        self._func = func
        self._data_type = data_type

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    def plugin(self):
        return self._func

    @memoize
    def bind(self, run_hive):
        if self._run_hive:
            return self

        if isinstance(self._func, Bindable):
            func = self._func.bind(run_hive)

        else:
            func = self._func

        return self.__class__(func, self._data_type, run_hive)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        func = self._func
        if isinstance(func, Exportable):
            exported = func.export()
            return self.__class__(exported, self.data_type, self._run_hive)

        else:
            return self

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Socket):
            raise HiveConnectionError("Plugin target must be a subclass of Socket")

    def _hive_connect_source(self, target):
        pass

    def __repr__(self):
        return "HivePlugin({!r}, {!r}, {!r})".format(self._func, self.data_type, self._run_hive)


class HivePluginBuilder(Exportable, Plugin, ConnectSource):
    def __init__(self, target, identifier=None, data_type='', policy=None, export_to_parent=False):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        if not is_valid_identifier(identifier):
            raise ValueError(identifier)

        self._target = target
        self._identifier = identifier
        self._data_type = data_type
        self._export_to_parent = export_to_parent

        if policy is None:
            policy = MultipleOptional

        self._policy = policy

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    @property
    def policy(self):
        return self._policy

    @property
    def export_to_parent(self):
        return self._export_to_parent

    @property
    def identifier(self):
        return self._identifier

    @memoize
    def getinstance(self, hive_object):
        target = self._target
        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        return HivePlugin(target, self._data_type)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        target = self._target

        if isinstance(target, Exportable):
            exported = target.export()
            return self.__class__(exported, self._identifier, self._data_type, self._policy, self._export_to_parent)

        return self

    def __repr__(self):
        return "HivePluginBuilder({!r}, {!r}, {!r}, {!r}, {!r})".format(self._target, self._identifier, self._data_type,
                                                                        self._policy, self.export_to_parent)


plugin = ModeFactory("hive.plugin", immediate=HivePlugin, build=HivePluginBuilder)
