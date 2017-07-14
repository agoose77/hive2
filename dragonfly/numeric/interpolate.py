import hive


def do_interpolation(self):
    self._result = self._min + (self._max - self._min) * min(1.0, max(self._factor, 0.0))


def build_interpolate(i, ex, args):
    """Interpolate between two values by a floating point factor"""
    i.min = hive.attribute("float")
    i.max = hive.attribute("float")
    i.factor = hive.attribute("float")

    ex.min = i.min.pull_in
    ex.max = i.max.pull_in
    ex.value = i.value.pull_in

    i.result = hive.attribute("float")
    ex.result = i.result.pull_out

    i.do_interpolate = hive.modifier(do_interpolation)

    i.pull_result.pre_pushed.connect(i.pull_min.pull_in.trigger,
                                     i.pull_max.pull_in.trigger,
                                     i.pull_factor.pull_in.trigger,
                                     i.do_interpolate.trigger)


Interpolate = hive.hive("Interpolate", build_interpolate)
