from math import sqrt

import hive


def normalise_modifier(self):
    x, y, z = self._vector
    length = sqrt(x ** 2 + y ** 2 + z ** 2)

    self._result = (x / length, y / length, z / length)


def build_normalise(i, ex, args):
    """Find the unit vector for a given vector"""
    i.vector = hive.attribute("vector")
    i.pull_vector = hive.pull_in(i.vector)
    ex.vector = hive.antenna(i.pull_vector)

    i.result = hive.attribute("vector")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.calculate = hive.modifier(normalise_modifier)
    hive.trigger(i.pull_result, i.calculate, pretrigger=True)


Normalise = hive.hive("Normalise", build_normalise)
