import hive


def do_iter(self):
    self._iterator = iter(self._iterable)


def build_iter(i, ex, args, meta_args):
    """Create iterator for object"""
    i.iterable = hive.attribute()
    i.pull_iterable = hive.pull_in(i.iterable)
    ex.iterable = hive.antenna(i.pull_iterable)

    i.iterator = hive.attribute("iterator")
    i.pull_iterator = hive.pull_out(i.iterator)
    ex.iterator = hive.output(i.pull_iterator)

    i.do_iter = hive.modifier(do_iter)

    hive.trigger(i.pull_iterator, i.pull_iterable, pretrigger=True)
    hive.trigger(i.pull_iterable, i.do_iter)


Iterator = hive.hive("Iterator", build_iter)
