import hive


def build_range(i, ex, args):
    """A range iterator hive"""
    i.min_value = hive.attribute("int")
    i.max_value = hive.attribute("int")
    i.step = hive.attribute("int")

    i.pull_min_value = hive.pull_in(i.min_value)
    i.pull_max_value = hive.pull_in(i.max_value)
    i.pull_step = hive.pull_in(i.step)

    ex.min_value = hive.antenna(i.pull_min_value)
    ex.max_value = hive.antenna(i.pull_max_value)
    ex.step = hive.antenna(i.pull_step)

    i.iterator = hive.attribute("int")

    def get_range(self):
        self._iterator = range(self._min_value, self._max_value, self._step)

    i.get_range = hive.modifier(get_range)

    i.pull_iterator = hive.pull_out(i.iterator, "iterator")
    ex.iterator = hive.output(i.pull_iterator)

    hive.trigger(i.pull_iterator, i.pull_min_value, pretrigger=True)
    hive.trigger(i.pull_iterator, i.pull_max_value, pretrigger=True)
    hive.trigger(i.pull_iterator, i.pull_step, pretrigger=True)
    hive.trigger(i.pull_iterator, i.get_range, pretrigger=True)


Range = hive.hive("Range", build_range)
