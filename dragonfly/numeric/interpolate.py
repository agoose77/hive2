import hive


def do_interpolation(self):
    self._result = self._min + (self._max - self._min) * min(1.0, max(self._factor, 0.0))


def build_interpolate(i, ex, args):
    """Interpolate between two values by a floating point factor"""
    i.min = hive.variable("float")
    i.max = hive.variable("float")
    i.factor = hive.variable("float")

    i.pull_min = hive.pull_in(i.min)
    i.pull_max = hive.pull_in(i.max)
    i.pull_factor = hive.pull_in(i.factor)

    ex.min = hive.antenna(i.pull_min)
    ex.max = hive.antenna(i.pull_max)
    ex.value = hive.antenna(i.pull_factor)

    i.result = hive.variable("float")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.do_interpolate = hive.modifier(do_interpolation)

    hive.trigger(i.pull_result, i.pull_min, pretrigger=True)
    hive.trigger(i.pull_result, i.pull_max, pretrigger=True)
    hive.trigger(i.pull_result, i.pull_factor, pretrigger=True)
    hive.trigger(i.pull_result, i.do_interpolate, pretrigger=True)


Interpolate = hive.hive("Interpolate", build_interpolate)
