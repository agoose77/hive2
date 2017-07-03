"""
Stateful mixin
Hives that are Stateful behave differently when added to the i wrapper
Instead of adding the whole hive instance, a *Python attribute* is added to the wrapper
The getter/setter of this attribute are hiveinstance._hive_stateful.getter and hiveinstance._hive_stateful.setter, 
 respectively
 
A Stateful object's getter/setter always accept a run_hive object, which will be None in immediate mode
"""

from abc import ABC, abstractproperty



class Stateful(ABC):

    data_type = None

    def _hive_stateful_getter(self):
        raise NotImplementedError

    def _hive_stateful_setter(self, value):
        raise NotImplementedError


