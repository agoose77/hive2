from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


class Dog(object):

    def __init__(self):
        self.name = None


def declare_dog(meta_args):
    print("Invoked Declarator")
    meta_args.puppies = hive.parameter(("int",), 1)


def build_dog(cls, i, ex, args, meta_args):

    print(meta_args)
    print("Invoked Builder")
    args.name = hive.parameter("str")
    ex.name = hive.property(cls, "name", "str", args.name)

    for ix in range(meta_args.puppies):
        mod = hive.modifier(lambda h: print("Puppy {} barked".format(h.name)))
        setattr(i, "mod_{}".format(ix), mod)
        setattr(ex, "bark_{}".format(ix), hive.entry(mod))


DogHive = hive.dyna_hive("Dog", build_dog, declare_dog, Dog)


d = DogHive(2, "Jack")
d.bark_0()
d.bark_1()

print()

d = DogHive(1, "Jill")
d.bark_0()