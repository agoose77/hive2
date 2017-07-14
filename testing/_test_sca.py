from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

from dragonfly.event import EventManager
from sca.sensors import Keyboard
from sca.controllers import AND
from sca.actuators import Debug

import hive


def build_some_hive(i, ex, args):
    ex.keyboard = Keyboard(import_namespace=True)
    ex.and_ = AND()
    ex.debug = Debug()

    hive.connect(ex.keyboard.positive, ex.and_.a)
    hive.connect(ex.keyboard.positive, ex.and_.b)
    hive.connect(ex.keyboard.trig_out, ex.and_.trig_in)
    hive.connect(ex.and_.trig_out, ex.debug.trig_in)


MyHive = EventManager.extend("EMyHive", build_some_hive)

h = MyHive()
h.keyboard.key = "w"

re = (h.read_event.plugin())

e = ("event", "keyboard", "pressed", "w")
re(e)