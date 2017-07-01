from __future__ import print_function
#
# import sys
# import os
#
# current_directory = os.path.split(os.path.abspath(__file__))[0]
# sys.path.append(current_directory + "/" + "..")
#
# import hive
#
#
# class SomeClass(object):
#
#     def __init__(self):
#         self.a = 0
#         self.b = 0
#
#
# def build_myhive(cls, i, ex, args):
#     ex.a_ = hive.property(cls, "a", "int")
#     ex.b_ = hive.property(cls, "b", "int")
#
#     i.a_in = hive.push_in(ex.a_)
#     i.b_in = hive.push_in(ex.b_)
#
#     ex.a = hive.antenna(i.a_in)
#     ex.b = hive.antenna(i.b_in)
#
#     ex.c_ = hive.attribute()
#     i.c_out = hive.push_out(ex.c_)
#     ex.c = hive.output(i.c_out)
#
#     # On triggered
#     def on_triggered(this):
#         this.c_ = this.a_ + this.b_
#         this.c.push()
#
#     i.on_triggered = hive.modifier(lambda this: setattr(this, 'c_', (this.a_ + this.b_)))
#     ex.trigger = hive.entry(i.on_triggered)
#
#
# MyHive = hive.hive("MyHive", build_myhive, SomeClass)
#
#
# # Create runtime hive instances
# my_hive = MyHive()
#
# my_hive.a.push(1)
# my_hive.b.push(1)
# my_hive.trigger()
#

from unittest import TestCase, main

import hive
import logging
logging.getLogger().setLevel(logging.INFO)

class SomeClass(object):

    def __init__(self):
        self.a = 0
        self.b = 0


def build_myhive(cls, i, ex, args):
    ex.a_ = hive.property(cls, "a", "int")
    ex.b_ = hive.property(cls, "b", "int")

    i.a_in = hive.push_in(ex.a_)
    i.b_in = hive.push_in(ex.b_)

    ex.a = hive.antenna(i.a_in)
    ex.b = hive.antenna(i.b_in)

    ex.c_ = hive.variable()
    i.c_out = hive.push_out(ex.c_)
    ex.c = hive.output(i.c_out)

    # On triggered
    def on_triggered(this):
        this.c_ = this.a_ + this.b_
        this.c.push()

    i.on_triggered = hive.modifier(on_triggered)
    ex.trigger = hive.entry(i.on_triggered)


class TestIO(TestCase):

    def test(self):
        MyHive = hive.hive("MyHive", build_myhive, SomeClass)


        # Create runtime hive instances
        my_hive = MyHive()

        my_hive.a.push(1)
        my_hive.b.push(1)
        my_hive.trigger()
        self.assertEqual(my_hive.c_, 2)


if __name__ == "__main__":
    main()