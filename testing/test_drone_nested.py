from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


def get_last(n, a):
    while True:
        if not hasattr(n, a):
            return n
        n = getattr(n, a)


class DroneCls:
    
    def __init__(self, name="<internal>"):
        self.name = name

    def print_name(self):
        print("NAME =", self.name)


def build_drone(cls, i, ex, args):
    ex.plug = hive.plugin(cls.print_name, identifier="some_api.func", export_to_parent=True)


Drone = hive.hive("Drone", build_drone, builder_cls=DroneCls)


class InnerHiveCls:

    def get_plugin(self, plugin):
        plugin()


def build_inner(cls, i, ex, args):
    ex.sock = hive.socket(cls.get_plugin, identifier="some_api.func")


InnerHive = hive.hive("Hive", build_inner, builder_cls=InnerHiveCls)


def build_container(i, ex, args):
    ex.drone = Drone(import_namespace=True)
    ex.hive = InnerHive(import_namespace=True)

ContainerHive = hive.hive("Hive", build_container)

h = ContainerHive()
