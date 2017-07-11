import hive

from hive.compatability import next


def next_modifier(self):
    iterator = self._iterator

    if iterator is None:
        self._pull_iterator()
        if iterator is self._iterator:
            raise StopIteration("Could not pull a new generator")

        iterator = self._iterator

    try:
        self._result = next(iterator)

    except StopIteration:
        self._iterator = None
        next_modifier(self)


def declare_next(meta_args):
    meta_args.data_type = hive.parameter("str", "int")


def build_next(i, ex, args, meta_args):
    """Iterate over generator object, output new value when pulled"""
    i.iterator = hive.attribute("iterator")
    i.iterator_in = hive.pull_in(i.iterator)
    ex.iterator = hive.antenna(i.iterator_in)

    i.pull_iterator = hive.triggerfunc()
    hive.trigger(i.pull_iterator, i.iterator_in)

    i.result = hive.attribute(meta_args.data_type)
    i.pull_value = hive.pull_out(i.result)
    ex.value = hive.output(i.pull_value)

    i.do_next = hive.modifier(next_modifier)

    hive.trigger(i.pull_value, i.do_next, pretrigger=True)


Next = hive.dyna_hive("Next", build_next, declarator=declare_next)
