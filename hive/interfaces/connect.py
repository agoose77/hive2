"""
Hives that are ConnectSourceBases can be used as the source argument in the connect command
They exist in two flavors:
- ConnectSource must have a _hive_connectable_source method, accepting a target ConnectTarget.
    The method must raise an informative HiveConnectError if the target is not connectable, nothing otherwise
    It must also have a _hive_connect_source method, invoked upon connection to the target
- ConnectSourceDerived must contain a _hive_find_connect_sources attribute
    This attribute must be a dict with string keys and ConnectSource values

Hives that are ConnectTargetBases can be used as the target argument in the connect command
They exist in two flavors:
- ConnectTarget must have a _hive_connectable_target method, accepting a source ConnectSource.
    The method must raise an informative HiveConnectError if the target is not connectable, nothing otherwise
    It must also have a _hive_connect_target method, invoked upon connection to the source
- ConnectTargetDerived must contain a _hive_connect_targets class attribute
    This attribute must be a dict with string keys and ConnectTarget values
"""
from typing import NamedTuple, List


class ConnectCandidate(NamedTuple):
    bee_name: str
    data_type: str


class ConnectSourceBase:
    pass


class ConnectTargetBase:
    pass


class ConnectSource(ConnectSourceBase):
    data_type = None

    def _hive_is_connectable_source(self, target: 'ConnectTarget'):
        raise NotImplementedError

    def _hive_connect_source(self, target: 'ConnectTarget'):
        raise NotImplementedError


class ConnectSourceDerived(ConnectSourceBase):

    def _hive_find_connect_sources(self) -> List[ConnectCandidate]:
        raise NotImplementedError

    def _hive_get_connect_source(self, target: 'ConnectTarget'):
        raise NotImplementedError


class ConnectTarget(ConnectTargetBase):
    data_type = None

    def _hive_is_connectable_target(self, source: ConnectSource):
        raise NotImplementedError

    def _hive_connect_target(self, source: ConnectSource):
        raise NotImplementedError


class ConnectTargetDerived(ConnectTargetBase):

    def _hive_find_connect_targets(self) -> List[ConnectCandidate]:
        raise NotImplementedError

    def _hive_get_connect_target(self, source: ConnectSource):
        raise NotImplementedError
