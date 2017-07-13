from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

from unittest import TestCase, main
import hive
from io import StringIO
from contextlib import contextmanager, redirect_stdout

@contextmanager
def redirect_string():
    io = StringIO(newline='')
    with redirect_stdout(io):
        yield io
    io.seek(0)


class Dog(object):
    def __init__(self):
        self.name = None


def configure_dog(meta_args):
    meta_args.puppies = hive.parameter("int", 1)


def build_dog(cls, i, ex, args, meta_args):
    args.name = hive.parameter("str")
    i.name = hive.property(cls, "name", "str", args.name)
    ex.name = i.name.property(hive.READ)

    for ix in range(meta_args.puppies):
        mod = hive.modifier(lambda i, ex,ix=ix: print("{}'s puppy ({}) barked".format(ex.name, ix)))
        setattr(i, "mod_{}".format(ix), mod)
        setattr(ex, "bark_{}".format(ix), mod.trigger)


DogHive = hive.dyna_hive("Dog", build_dog, configure_dog, Dog)

class TestDeclarator(TestCase):

    def test_configurer(self):
        d = DogHive(2, "Jack")

        with redirect_string() as io:
            d.bark_0()
        self.assertEqual(io.read(), "Jack's puppy (0) barked\n")

        with redirect_string() as io:
            d.bark_1()
        self.assertEqual(io.read(), "Jack's puppy (1) barked\n")


        d = DogHive(1, "Jill")

        with redirect_string() as io:
            d.bark_0()
        self.assertEqual(io.read(), "Jill's puppy (0) barked\n")


if __name__ == "__main__":
    main()