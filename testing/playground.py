# import dragonfly
# import hive
#
# import hive_editor
#
# from hive_editor.debugging.network import NetworkDebugContext
# from example_calc import ExampleCalc
#
#
# class MyHiveClass:
#     pass
#
#
# def build_my_hive(cls, i, ex, args):
#     i.main_hive = ExampleCalc()
#
#
# MyHive = dragonfly.panda3d.Mainloop.extend("MyHive", build_my_hive, drone_class=MyHiveClass)
#
# DO_DEBUG = True
#
# if DO_DEBUG:
#     debug_context = NetworkDebugContext()
#     with debug_context:
#         my_hive = MyHive()
#         my_hive.run()
# else:
#     my_hive = MyHive()
#     my_hive.run()

from types import ModuleType

import os
import testing
import hive_editor
mod = ModuleType("testing")
mod.__package__ = mod.__name__
mod.__file__ = "SomeFile"

from hive_editor.connection import Connection
test_string = """
from .panda_project import launch
"""
exec(test_string, mod.__dict__)

import sys; sys.path.append("D:/users/angus/documents/pycharmprojects/hive2"); import hive