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


class C:
    def __init__(self, name="<internal>"):
        self.name = name

    def print_name(self):
        print("NAME =", self.name)

    def get_plug(self, o):
        o()


def build_h(cls, i, ex, args, meta_args):
    print("Build hive", meta_args.i)

    is_root = meta_args.root

    if is_root:
        print("IS ROOT")
        ex.plug = hive.plugin(cls.print_name, identifier="some_api.func")

    if meta_args.i:
        setattr(ex, "h_{}".format(meta_args.i-1), SomeHive(i=meta_args.i-1, root=False, name="<internal>"))

    else:
        ex.sock = hive.socket(cls.get_plug, identifier="some_api.func")


def declare_h(meta_args):
    meta_args.i = hive.parameter("int", 2)
    meta_args.root = hive.parameter("bool", True)

SomeHive = hive.dyna_hive("H1", build_h, builder_cls=C, declarator=declare_h)

# This works
h_2 = SomeHive(name="OtherHive")
h_3 = SomeHive(name="OtherHive4")
