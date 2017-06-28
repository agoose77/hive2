"""
Hives that are ConnectTargetBases can be used as the target argument in the connect command
They exist in two flavors:
- ConnectTarget must have a _hive_connectable_target method, accepting a source ConnectSource.
    The method must raise an informative HiveConnectError if the target is not connectable, nothing otherwise
    It must also have a _hive_connect_target method, invoked upon connection to the source
- ConnectTargetDerived must contain a _hive_connect_targets class attribute
    This attribute must be a dict with string keys and ConnectTarget values
"""

from . import Connectable


class ConnectTargetBase(Connectable):
    pass


class ConnectTarget(ConnectTargetBase):
    data_type = None

    def _hive_is_connectable_target(self, source):
        raise NotImplementedError

    def _hive_connect_target(self, source):
        raise NotImplementedError


class ConnectTargetDerived(ConnectTargetBase):    

    def _hive_find_connect_targets(self):
        raise NotImplementedError

    def _hive_get_connect_target(self, source):
        raise NotImplementedError    
