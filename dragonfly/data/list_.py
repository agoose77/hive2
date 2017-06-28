import hive


def declare_list(meta_args):
    meta_args.data_type = hive.parameter('str', 'int')


def build_list(i, ex, args, meta_args):
    """Interface to list container"""
    data_type = "list[{}]".format(meta_args.data_type or '?')
    i.list_ = hive.variable(data_type, list())
    i.pull_list_ = hive.pull_out(i.list_)
    ex.list_out = hive.output(i.pull_list_)

    i.push_list_ = hive.push_in(i.list_)
    ex.list_ = hive.antenna(i.push_list_)

    i.item = hive.variable(meta_args.data_type)

    # Pop item
    i.popped_item = hive.variable(meta_args.data_type)
    i.pull_pop = hive.pull_out(i.popped_item)
    ex.pop = hive.output(i.pull_pop)

    def do_pop(self):
        self._popped_item = self._list_.pop()

    i.do_pop = hive.modifier(do_pop)
    hive.trigger(i.pull_pop, i.do_pop, pretrigger=True)

    # Add item
    i.push_to_append = hive.push_in(i.item)
    ex.append = hive.antenna(i.push_to_append)

    def to_append(self):
        self._list_.append(self._item)

    i.do_append = hive.modifier(to_append)
    hive.trigger(i.push_to_append, i.do_append)

    # Remove item
    i.push_to_remove = hive.push_in(i.item)
    ex.remove = hive.antenna(i.push_to_remove)

    def do_remove(self):
        self._list_.remove(self._item)

    i.do_remove = hive.modifier(do_remove)
    hive.trigger(i.push_to_remove, i.do_remove)

    def do_clear(self):
        self._list_.clear()

    i.do_clear = hive.modifier(do_clear)
    ex.clear = hive.entry(i.do_clear)

    # Index
    i.index = hive.variable('int')

    # Getitem
    i.pull_getitem_index = hive.pull_in(i.index)
    ex.get_index = hive.antenna(i.pull_getitem_index)

    i.pull_getitem = hive.pull_out(i.item)
    ex.getitem = hive.output(i.pull_getitem)

    def do_getitem(self):
        self._item = self._list[self._index]

    i.do_getitem = hive.modifier(do_getitem)

    hive.trigger(i.pull_getitem, i.pull_getitem_index, pretrigger=True)
    hive.trigger(i.pull_getitem_index, i.do_getitem)

    # Setitem
    i.pull_setitem_index = hive.pull_in(i.item)
    ex.set_index = hive.antenna(i.pull_setitem_index)

    i.push_setitem = hive.push_in(i.item)
    ex.setitem = hive.antenna(i.push_setitem)

    def do_setitem(self):
        self._list[self._index] = self._item

    i.do_setitem = hive.modifier(do_setitem)

    hive.trigger(i.push_setitem, i.pull_setitem_index)
    hive.trigger(i.pull_setitem_index, i.do_setitem)


List = hive.dyna_hive("List", build_list, declare_list)
