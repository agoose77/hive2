from __future__ import print_function

import sys
import os

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


def get_last(n, a):
    while True:
        if not hasattr(n, a):
            return n
        n = getattr(n, a)


class C:
    def __init__(self, name="<internal>"):
        self.name = name

    def print_name(self):
        print("NAME =", self.name)

    def get_plug(self, o):
        o()


def build_h(cls, i, ex, args):
    print("Build hive", args.i)

    is_root = args.root

    if is_root:
        ex.plug = hive.plugin(cls.print_name, identifier=("some_api", "func"), auto_connect=True)

    if args.i:
        ex.h = SomeHive(i=args.i-1, root=False, name="<internal>", import_namespace=True)

    else:
        ex.sock = hive.socket(cls.get_plug, identifier=("some_api", "func"), auto_connect=True)

    if is_root and 0:
        hive.connect(ex.plug, get_last(ex, "h").sock)


def declare_h(args):
    args.i = hive.parameter("int", 2)
    args.root = hive.parameter("bool", True)

SomeHive = hive.hive("H1", build_h, cls=C, declarator=declare_h)

# This works
h1 = SomeHive(name="OtherHive")

# This doesn't
h2 = SomeHive()

print(h2.h.h.sock is h1.h.h.sock)