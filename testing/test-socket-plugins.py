from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


class Dog(object):

    def __init__(self, name=""):
        self.name = name
        print("MAKE DOGGY", name)

    def print_house(self):
        print("Found House for", self.name, self.get_house())

    def set_get_house(self, get_house_func):
        self.get_house = get_house_func
        print("SET FUNC", get_house_func, self.name, self)


def build_dog(cls, i, ex, args):
    i.print_house = hive.triggerable(cls.print_house)
    ex.print_house = hive.entry(i.print_house)
    ex.some_socket = hive.socket(cls.set_get_house, identifier="get.house", data_type="float")


DogHive = hive.hive("DogHive", build_dog, Dog)


def declare_filler(meta_args):
    meta_args.i = hive.parameter("int", 2)


def build_filler(i, ex, args, meta_args):
    print("NEW FILLER", meta_args.i)
    if meta_args.i:
        i.inner = FillerHive(meta_args.i - 1, import_namespace=True)
        ex.inner = hive.hook(i.inner)

    else:
        i.inner = DogHive(import_namespace=True, name="DOGGY")
        ex.inner = hive.hook(i.inner)


FillerHive = hive.dyna_hive("FillerHive", build_filler, declarator=declare_filler)


class House(object):

    def get_current_hive(self):
        return self


def build_house(cls, i, ex, args):
    ex.some_plugin = hive.plugin(cls.get_current_hive, identifier="get.house", data_type="float")

    # Auto connect
    i.filler = FillerHive()
    ex.filler = hive.hook(i.filler)

    # Manual connect
    i.fido = DogHive(name="Main", import_namespace=False)
    ex.fido = hive.hook(i.fido)

    hive.connect(ex.some_plugin, i.fido.some_socket)


HouseHive = hive.hive("HouseHive", build_house, House)


house = HouseHive()
print()
print("NEW")
print()
house2 = HouseHive()

s1 = house.filler.inner#.inner.inner.some_socket
s2 = house2.filler.inner#.inner.inner.some_socket
print(s1,s2)

# import time
# s = time.monotonic()
# for i in range(1000):
#     h = HouseHive()
#
# print(time.monotonic() - s)

# house.filler.inner.inner.inner.print_house()
# house.fido.print_house()