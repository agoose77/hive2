import hive


def declare_pack_tuple(meta_args):
    meta_args.types = hive.parameter('tuple')


def build_pack_tuple(i, ex, args, meta_args):
    """Pack a tuple from individual inputs"""
    i.tuple_ = hive.attribute('tuple')
    i.pull_tuple = hive.pull_out(i.tuple_)
    ex.tuple_ = hive.output(i.pull_tuple)

    for index, data_type in enumerate(meta_args.types):
        attr = hive.attribute(data_type)
        setattr(i, "attr_{}".format(index), attr)

        pull_in = hive.pull_in(attr)
        setattr(i, "pull_in_{}".format(index), pull_in)

        setattr(ex, "item_{}".format(index), hive.antenna(pull_in))

        hive.trigger(i.pull_tuple, pull_in, pretrigger=True)

    def do_pack_tuple(self):
        self._tuple_ = tuple(getattr(self, "_attr_{}".format(index)) for index in range(len(meta_args.types)))

    i.do_pack_tuple = hive.modifier(do_pack_tuple)
    hive.trigger(i.pull_tuple, i.do_pack_tuple, pretrigger=True)


PackTuple = hive.dyna_hive("PackTuple", build_pack_tuple, declare_pack_tuple)