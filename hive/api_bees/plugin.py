from ..exception import HiveConnectionError
from ..identifier import is_valid_identifier
from ..interfaces import Plugin, Socket, ConnectSource, Exportable, Callable, Bee
from ..manager import memoize, ModeFactory
from ..policies import MultipleOptional
from ..typing import is_valid_data_type
from ..internal_bees.interfaces import ConnectableMixin


class HivePluginRuntime(Plugin, ConnectSource, ConnectableMixin):
    def __init__(self, func, data_type=''):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        assert callable(func), func

        self._func = func
        self._data_type = data_type

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    def plugin(self):
        return self._func

    def _hive_is_connectable_source(self, target):
        if not isinstance(target, Socket):
            raise HiveConnectionError("Plugin target must be a subclass of Socket")

    def _hive_connect_source(self, target):
        pass

    def __repr__(self):
        return "HivePluginRuntime({!r}, {!r})".format(self._func, self.data_type)


class HivePluginBuilder(Exportable, Plugin, ConnectSource, ConnectableMixin):
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
    def bind(self, run_hive):
        func = self._target
        if isinstance(func, Bee):
            func = func.bind(run_hive)

        return HivePluginRuntime(func, self._data_type)

    def __repr__(self):
        return "HivePluginBuilder({!r}, {!r}, {!r}, {!r}, {!r})".format(self._target, self._identifier, self._data_type,
                                                                        self._policy, self.export_to_parent)


plugin = ModeFactory("hive.plugin", immediate=HivePluginRuntime, build=HivePluginBuilder)
