import hive


def declare_foreach(meta_args):
    meta_args.data_type = hive.parameter("str", "int")


def do_iter(self):
    self._break_ = False

    for index, item in enumerate(self._iterable):
        if self._break_:
            break

        self._item = item
        self._index = index

        self.item.push()

    self.finished()


def do_break(self):
    self._break_ = True


def build_foreach(i, ex, args, meta_args):
    """Iterate over iterable object"""
    # Set iterable
    i.iterable = hive.attribute("$iterable[int]")
    i.pull_iterable = hive.pull_in(i.iterable)
    ex.iterable = hive.antenna(i.pull_iterable)

    i.do_trig = hive.triggerfunc()
    i.trig_in = hive.triggerable(i.do_trig)
    ex.start = hive.entry(i.trig_in)

    i.break_ = hive.attribute('bool', False)

    i.item = hive.attribute(meta_args.data_type)
    i.push_item = hive.push_out(i.item)
    ex.item = hive.output(i.push_item)

    i.index = hive.attribute('int', 0)
    i.pull_index = hive.pull_out(i.index)
    ex.index = hive.output(i.pull_index)

    i.finished = hive.triggerfunc()

    i.do_break = hive.modifier(do_break)
    ex.break_ = hive.entry(i.do_break)
    ex.finished = hive.hook(i.finished)

    i.iter = hive.modifier(do_iter)
    hive.trigger(i.do_trig, i.pull_iterable)
    hive.trigger(i.do_trig, i.iter)


ForEach = hive.dyna_hive("ForEach", build_foreach, declare_foreach)
