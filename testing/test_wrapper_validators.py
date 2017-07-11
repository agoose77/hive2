from __future__ import print_function

import os
import sys

current_directory = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(current_directory + "/" + "..")

import hive


def build_h(i, ex, args):
    # The following should raise AttributeErrors
    ex.export = hive.attribute()
    i.hive_object = hive.attribute()


Hive = hive.hive("Hive", build_h)

h = Hive()
