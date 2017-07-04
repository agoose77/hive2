from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


class DroneCls:
    def __init__(self, name="<internal>"):
        self.name = name

    def print_name(self):
        print("NAME =", self.name)


def build_drone(cls, i, ex, args):
    ex.plug = hive.plugin(cls.print_name, identifier="some_api.func", export_to_parent=True)


Drone = hive.hive("Drone", build_drone, drone_cls=DroneCls)


class HiveCls:

    def set_plugin(self, print_name_plugin):
        print_name_plugin()


def build_h(cls, i, ex, args):
    i.drone = Drone()
    ex.sock = hive.socket(cls.set_plugin, identifier="some_api.func")


Hive = hive.hive("Hive", build_h, drone_cls=HiveCls)

h = Hive()
