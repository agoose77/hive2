from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


class Dog(object):

    def __init__(self, name):
        self._hive = hive.get_run_hive()
        self.name = name
        self.woof_count = 0

    def call(self):
        print("Dog.call ({})".format(self.name))

    def woof(self):
        self.woof_count += 1
        print("Dog.woof ({}) [{}]".format(self.name, self.woof_count))
        self._hive.woofed()


class House(object):

    def dog_appeared(self):
        print("A wild dog appeared!")

    def mail_arrived(self):
        print("Mail arrives")


def build_dog(cls, i, ex, args):
    i.call = hive.triggerfunc(cls.call)
    i.woof = hive.triggerable(cls.woof)
    hive.trigger(i.call, i.woof)

    i.bark = hive.triggerfunc()
    hive.trigger(i.bark, i.woof)

    i.woof_only = hive.triggerable(cls.woof)
    i.woofed = hive.triggerfunc()

    ex.woofs = hive.property(cls, "woofs")
    ex.woof = hive.entry(i.woof)
    ex.woof_only = hive.entry(i.woof_only)
    ex.woofed = hive.hook(i.woofed)
    ex.bark = hive.hook(i.bark)
    ex.call = hive.hook(i.call)


def build_house(cls, i, ex, args):
    i.brutus_ = DogHive("Brutus")
    i.fifi = DogHive("Fifi")

    i.dog_appeared = hive.triggerable(cls.dog_appeared)
    hive.trigger(i.brutus_.call, i.dog_appeared)

    i.mail_arrived = hive.triggerfunc(cls.mail_arrived)
    hive.trigger(i.mail_arrived, i.fifi.woof)

    ex.brutus = i.brutus_
    ex.fifi = i.fifi
    ex.mail_arrived = hive.hook(i.mail_arrived)
    ex.dog_appeared = hive.entry(i.dog_appeared)


DogHive = hive.hive("Dog", build_dog, Dog)
HouseHive = hive.hive("House", build_house, House)

house = HouseHive()
house.mail_arrived()
house.brutus.call()
house.fifi.bark()
house.dog_appeared()
