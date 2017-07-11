"""Provide clean API to access RuntimeHive instance from Drone instance"""
from weakref import WeakValueDictionary

_drone_instance_to_run_hive = WeakValueDictionary()


def register_drone(drone, run_hive):
    _drone_instance_to_run_hive[drone] = run_hive


def public(drone_instance):
    """Convenience method to get current run hive from drone instance

    :param drone_instance: Pythonic drone instance
    """
    return _drone_instance_to_run_hive[drone_instance]


def private(drone_instance):
    """Convenience method to get current run hive from drone instance

    :param drone_instance: Pythonic drone instance
    """
    return _drone_instance_to_run_hive[drone_instance]._hive_i
