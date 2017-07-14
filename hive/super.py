"""Provide clean API to access RuntimeHive instance from Drone instance"""
from weakref import WeakValueDictionary

_drone_instance_to_run_hive = WeakValueDictionary()


def register_drone(drone, run_hive):
    _drone_instance_to_run_hive[drone] = run_hive


def args(drone_instance):
    """Convenience method to get current run hive args from drone instance

    :param drone_instance: drone class instance
    """
    return _drone_instance_to_run_hive[drone_instance]._hive_object._hive_args_frozen


def meta_args(drone_instance):
    """Convenience method to get current run hive meta-args from drone instance

    :param drone_instance: drone class instance
    """
    return _drone_instance_to_run_hive[drone_instance]._hive_object._hive_meta_args_frozen


def external(drone_instance):
    """Convenience method to get current run hive from drone instance

    :param drone_instance: drone class instance
    """
    return _drone_instance_to_run_hive[drone_instance]


def internal(drone_instance):
    """Convenience method to get current run hive private wrapper from drone instance

    :param drone_instance: drone class instance
    """
    return _drone_instance_to_run_hive[drone_instance]._hive_i
