# from __future__ import print_function
#
# import sys
# import os
#
# current_directory = os.path.split(os.path.abspath(__file__))[0]
# sys.path.append(current_directory + "/" + "..")
#
# import hive
# import debug
#
# # Enable debugging
# debug.enabled = True
#
#
# def build_hive2(i, ex, args):
#     i.variable = hive.attribute()
#     i.output = hive.pull_out(i.variable)
#     ex.output = hive.output(i.output)
#
# Hive2 = hive.hive("Hive2", build_hive2)
#
#
# def build_hive1(i, ex, args):
#     """Some hive"""
#     i.inp = hive.attribute()
#     i.pinp = hive.pull_in(i.inp)
#     ex.input = hive.antenna(i.pinp)
#
#     i.hive2 = Hive2()
#     hive.connect(i.hive2, i.pinp)
#
#
# Hive1 = hive.hive("Hive1", build_hive1)
# hive1 = Hive1()
#
# hive1._hive2._variable = 12
# hive1.input.pull()
#
# print(hive1._inp)
# print(debug.report.stack)
#
#
# import debug
# ostack = debug.report.stack.copy()
# debug.report.decode_and_fill_stack(debug.report.encode_and_clear_stack())
#
# print(debug.report.stack, ostack)

from dragonfly.event.event import EventHandler, EventManager


class MyHiveCls:

    def __init__(self):
        pass

    def get_handler(self, add_handler):
        leader = ("tick",)
        handler = EventHandler(self.on_tick, leader, 1, mode="trigger")
        add_handler(handler)

    def on_tick(self):
        print("On Tick")


import hive


def my_hive_builder(cls, i, ex, args):
    ex.some_socket = hive.socket(cls.get_handler)
    hive.connect(ex.add_handler, ex.some_socket)


MyHive = EventManager.extend("M", my_hive_builder, MyHiveCls)
my_hive = MyHive()


event = ("tick",)
my_hive.read_event.plugin()(event)

from dragonfly.app.mainloop import Mainloop
m = Mainloop(max_framerate=12.0)
