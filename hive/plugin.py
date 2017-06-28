from .manager import get_building_hive, memoize, ModeFactory
from .mixins import Plugin, Socket, ConnectSource, Exportable, Callable, Bee, Bindable, Nameable
from .policies import MultipleOptional
from .exception import HiveConnectionError
from .typing import is_valid_data_type


class HivePlugin(Plugin, ConnectSource, Bindable, Exportable, Nameable):
    def __init__(self, func, data_type='', run_hive=None):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        assert callable(func) or isinstance(func, Callable), func

        self._run_hive = run_hive
        self._func = func

        self.data_type = data_type

    def __repr__(self):
        return "<Plugin: {}>".format(self._func)

    def plugin(self):
        return self._func

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Socket):
            raise HiveConnectionError("Plugin target must be a subclass of Socket")

    def _hive_connect_source(self, target):
        pass

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


class HivePluginBee(Plugin, ConnectSource, Exportable):
    def __init__(self, target, identifier=None, data_type='', policy=None, export_to_parent=False):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        self._hive_object_cls = get_building_hive()
        self._target = target

        self.identifier = identifier
        self.data_type = data_type
        self.export_to_parent = export_to_parent

        if policy is None:
            policy = MultipleOptional

        self.policy = policy

    def __repr__(self):
        return "<Plugin: {}>".format(self._target)

    @memoize
    def getinstance(self, hive_object):
        target = self._target
        if isinstance(target, Bee):
            target = target.getinstance(hive_object)

        return HivePlugin(target, self.data_type)

    @memoize
    def export(self):
        # TODO: somehow log the redirection path
        target = self._target

        if isinstance(target, Exportable):
            exported = target.export()
            return self.__class__(exported, self.identifier, self.data_type, self.policy, self.export_to_parent)

        else:
            return self


plugin = ModeFactory("hive.plugin", immediate=HivePlugin, build=HivePluginBee)
