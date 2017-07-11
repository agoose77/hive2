import hive


def declare_set(meta_args):
    meta_args.data_type = hive.parameter('str', 'int')


def build_set(i, ex, args, meta_args):
    """Perform set operation on single sets"""

    i.set_ = hive.attribute('set', set())
    i.pull_set_ = hive.pull_out(i.set_)
    ex.set_out = hive.output(i.pull_set_)

    i.push_set_ = hive.push_in(i.set_)
    ex.set_ = hive.antenna(i.push_set_)

    # Pop item
    i.popped_item = hive.attribute(meta_args.data_type)
    i.pull_pop = hive.pull_out(i.popped_item)
    ex.pop = hive.output(i.pull_pop)

    def do_pop(self):
        self._popped_item = self._set_.pop()

    i.do_pop = hive.modifier(do_pop)
    hive.trigger(i.pull_pop, i.do_pop, pretrigger=True)

    # Add item
    i.to_add = hive.attribute(meta_args.data_type)
    i.push_to_add = hive.push_in(i.to_add)
    ex.add = hive.antenna(i.push_to_add)

    def to_add(self):
        self._set_.add(self._to_add)

    i.do_add = hive.modifier(to_add)
    hive.trigger(i.push_to_add, i.do_add)

    # Remove item
    i.to_remove = hive.attribute(meta_args.data_type)
    i.push_to_remove = hive.push_in(i.to_remove)
    ex.remove = hive.antenna(i.push_to_remove)

    def do_remove(self):
        self._set_.remove(self._to_remove)

    i.do_remove = hive.modifier(do_remove)
    hive.trigger(i.push_to_remove, i.do_remove)

    def do_clear(self):
        self._set_.clear()

    i.do_clear = hive.modifier(do_clear)
    ex.clear = hive.entry(i.do_clear)


Set = hive.dyna_hive("Set", build_set, declare_set)
