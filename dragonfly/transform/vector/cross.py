import hive


def cross_modifier(self):
    a = self._a
    b = self._b

    x = ((a[2] * b[3]) - (a[3] * b[2]))
    y = ((a[3] * b[1]) - (a[1] * b[3]))
    z = ((a[1] * b[2]) - (a[2] * b[1]))

    self._result = (x, y, z)


def build_cross(i, ex, args):
    """Calculate the cross product between two vectors"""
    i.a = hive.attribute("vector")
    i.b = hive.attribute("vector")

    pull_a = hive.pull_in(i.a)
    pull_b = hive.pull_in(i.b)

    ex.a = hive.antenna(pull_a)
    ex.b = hive.antenna(pull_b)

    i.result = hive.attribute("vector")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    calculate = hive.modifier(cross_modifier)
    hive.trigger(i.pull_result, calculate, pretrigger=True)


Cross = hive.hive("Cross", build_cross)
