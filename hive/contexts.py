from contextlib import contextmanager
from enum import auto, Enum

from typing import List, Type


class HiveMode(Enum):
    IMMEDIATE = auto()
    BUILD = auto()
    DECLARE = auto()


_mode = HiveMode.IMMEDIATE
_building_hive = None
_run_hive = None
_bees = []
_validation_enabled = True


def get_matchmaker_validation_enabled() -> bool:
    return _validation_enabled


def set_matchmaker_validation_enabled(validate: bool):
    global _validation_enabled
    _validation_enabled = validate


@contextmanager
def matchmaker_validation_enabled_as(validate: bool):
    previous_validation_state = get_matchmaker_validation_enabled()
    try:
        set_matchmaker_validation_enabled(validate)
        yield

    finally:
        set_matchmaker_validation_enabled(previous_validation_state)


def get_mode() -> HiveMode:
    return _mode


def set_mode(mode: HiveMode):
    global _mode
    assert mode in HiveMode, mode
    _mode = mode


@contextmanager
def hive_mode_as(mode: HiveMode):
    previous_mode = get_mode()
    try:
        set_mode(mode)
        yield

    finally:
        set_mode(previous_mode)


def get_building_hive() -> Type['HiveObject']:
    """Return the current hive being built"""
    return _building_hive


def set_building_hive(building_hive: Type['HiveObject']):
    global _building_hive
    _building_hive = building_hive


@contextmanager
def building_hive_as(building_hive: Type['HiveObject']):
    previous_building_hive = get_building_hive()
    set_building_hive(building_hive)
    yield
    set_building_hive(previous_building_hive)


def get_run_hive() -> 'RuntimeHive':
    return _run_hive


def set_run_hive(run_hive: 'RuntimeHive'):
    global _run_hive
    _run_hive = run_hive


@contextmanager
def run_hive_as(run_hive: 'RuntimeHive'):
    previous_run_hive = get_run_hive()
    set_run_hive(run_hive)
    yield
    set_run_hive(previous_run_hive)


def register_bee(bee: 'Bee'):
    assert _bees, "No valid state exists registering public, call register_bee_push()"
    _bees[-1].append(bee)


def register_bee_pop() -> List['Bee']:
    assert _bees, "No valid state exists registering public"
    return _bees.pop()


def register_bee_push():
    _bees.append([])


@contextmanager
def bee_register_context():
    register_bee_push()
    yield _bees[-1]
    register_bee_pop()
