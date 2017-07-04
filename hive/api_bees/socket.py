from ..exception import HiveConnectionError
from ..identifier import is_valid_identifier
from ..interfaces import ConnectTarget, Plugin, Socket, Exportable, Bee
from ..manager import memoize, ModeFactory
from ..policies import SingleRequired
from ..typing import is_valid_data_type


class HiveSocketRuntime(Socket, ConnectTarget):
    def __init__(self, func, data_type=""):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        assert callable(func), func

        self._func = func
        self._data_type = data_type

        super().__init__()

    @property
    def data_type(self):
        return self._data_type

    def _hive_is_connectable_target(self, source):
        if not isinstance(source, Plugin):
            raise HiveConnectionError("Socket source must be a subclass of Plugin")

    def _hive_connect_target(self, source):
        plugin = source.plugin()
        self._func(plugin)

    def __repr__(self):
        return "HiveSocketRuntime({!r}, {!r})".format(self._func, self._data_type)


class HiveSocketBuilder(Exportable, Socket, ConnectTarget):
    def __init__(self, target, identifier=None, data_type="", policy=None, export_to_parent=False):
        if not is_valid_data_type(data_type):
            raise ValueError(data_type)

        if not is_valid_identifier(identifier):
            raise ValueError(identifier)

        self._target = target
        self._identifier = identifier
        self._data_type = data_type
        self._export_to_parent = export_to_parent

        if policy is None:
            policy = SingleRequired

        self._policy = policy

        super().__init__()

    @memoize
    def bind(self, run_hive):
        target = self._target
        if isinstance(target, Bee):
            target = target.bind(run_hive)

        return HiveSocketRuntime(target, self._data_type)

    @property
    def data_type(self):
        return self._data_type

    @property
    def export_to_parent(self):
        return self._export_to_parent

    @property
    def identifier(self):
        return self._identifier

    @property
    def policy(self):
        return self._policy

    def __repr__(self):
        return "HiveSocketBuilder({!r}, {!r}, {!r}, {!r}, {!r})".format(self._target, self._identifier, self._data_type,
                                                                        self._policy, self._export_to_parent)


socket = ModeFactory("hive.socket", immediate=HiveSocketRuntime, build=HiveSocketBuilder)
