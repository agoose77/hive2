import hive


def dot_modifier(self):
    a = self._a
    b = self._b
    self._result = (a[0] * b[0]) + (a[1] * b[1]) + (a[2] * b[2])


def build_dot(i, ex, args):
    """Calculate the dot product between two vectors"""
    i.a = hive.attribute("vector")
    i.b = hive.attribute("vector")

    i.pull_a = hive.pull_in(i.a)
    i.pull_b = hive.pull_in(i.b)

    ex.a = hive.antenna(i.pull_a)
    ex.b = hive.antenna(i.pull_b)

    i.result = hive.attribute("float")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.calculate = hive.modifier(dot_modifier)

    hive.trigger(i.pull_result, i.pull_a, pretrigger=True)
    hive.trigger(i.pull_a, i.pull_b)
    hive.trigger(i.pull_b, i.calculate)


Dot = hive.hive("Dot", build_dot)
