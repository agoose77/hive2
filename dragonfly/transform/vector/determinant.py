from math import sqrt

import hive


def length_modifier(self):
    vector = self._vector
    self._result = sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)


def build_determinant(i, ex, args):
    """Calculate the determinant (length) of a vector"""
    i.vector = hive.attribute("vector")
    i.pull_vector = hive.pull_in(i.vector)
    ex.vector = hive.antenna(i.pull_vector)

    i.result = hive.attribute("float")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.calculate = hive.modifier(length_modifier)
    hive.trigger(i.pull_result, i.calculate, pretrigger=True)


Determinant = hive.hive("Determinant", build_determinant)
