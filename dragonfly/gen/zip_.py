import hive


def build_zip(i, ex, args):
    """Merge two iterables into a single iterable"""
    i.iterable_a = hive.attribute()
    i.iterable_b = hive.attribute()

    i.pull_a = hive.pull_in(i.iterable_a)
    i.pull_b = hive.pull_in(i.iterable_b)

    ex.a = hive.antenna(i.pull_a)
    ex.b = hive.antenna(i.pull_b)

    i.result = hive.attribute("iterator")
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    def do_zip(self):
        self._result = zip(self._iterable_a, self._iterable_b)

    i.do_zip = hive.modifier(do_zip)
    hive.trigger(i.pull_result, i.pull_a, pretrigger=True)
    hive.trigger(i.pull_a, i.pull_b)
    hive.trigger(i.pull_b, i.do_zip)


Zip = hive.hive("Zip", build_zip)