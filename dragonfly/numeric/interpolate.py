import hive


def do_interpolation(self):
    self._result = self._min + (self._max - self._min) * min(1.0, max(self._factor, 0.0))


def build_interpolate(i, ex, args):
    """Interpolate between two values by a floating point factor"""
    i.min = hive.attribute("float")
    i.max = hive.attribute("float")
    i.factor = hive.attribute("float")

    i.pull_min = hive.pull_in(i.min)
    i.pull_max = hive.pull_in(i.max)
    i.pull_factor = hive.pull_in(i.factor)

    ex.min = hive.antenna(i.pull_min)
    ex.max = hive.antenna(i.pull_max)
    ex.value = hive.antenna(i.pull_factor)

    i.result = hive.attribute("float")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.do_interpolate = hive.modifier(do_interpolation)

    i.pull_result.before_triggered.connect(i.pull_min.pull_in.trigger)
    i.pull_result.before_triggered.connect(i.pull_max.pull_in.trigger)
    i.pull_result.before_triggered.connect(i.pull_factor.pull_in.trigger)
    i.pull_result.before_triggered.connect(i.do_interpolate.trigger)


Interpolate = hive.hive("Interpolate", build_interpolate)
