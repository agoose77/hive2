from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

from unittest import TestCase, main
import hive
from io import StringIO
from contextlib import contextmanager, redirect_stdout

bark_template = "Woof ... {}'s puppy ({})"


@contextmanager
def redirect_string():
    io = StringIO(newline='')
    with redirect_stdout(io):
        yield io
    io.seek(0)


def configure_dog(meta_args):
    meta_args.puppies = hive.parameter("int", 1)


def build_dog(i, ex, args, meta_args):
    args.name = hive.parameter("str")
    i.name = hive.attribute("str", args.name)
    ex.name = i.name.proxy(hive.READ)

    for n in range(meta_args.puppies):
        def bark(i, ex, n=n):
            print(bark_template.format(ex.name, n))

        mod = hive.modifier(bark)
        setattr(i, "mod_{}".format(n), mod)
        setattr(ex, "bark_{}".format(n), mod.trigger)


DogHive = hive.dyna_hive("Dog", build_dog, configure_dog)


class TestDeclarator(TestCase):
    def test_configurer(self):
        d = DogHive(2, "Jack")

        with redirect_string() as io:
            d.bark_0()
        self.assertEqual(io.read(), bark_template.format("Jack", 0) + "\n")

        with redirect_string() as io:
            d.bark_1()
        self.assertEqual(io.read(), bark_template.format("Jack", 1) + "\n")

        d = DogHive(1, "Jill")
        with redirect_string() as io:
            d.bark_0()
        self.assertEqual(io.read(), bark_template.format("Jill", 0) + "\n")


if __name__ == "__main__":
    main()
