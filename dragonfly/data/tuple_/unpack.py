import hive


def declare_unpack_tuple(meta_args):
    meta_args.types = hive.parameter('tuple')


def build_unpack_tuple(i, ex, args, meta_args):
    """Unpack a tuple from individual inputs"""
    i.tuple_ = hive.attribute('tuple')
    i.push_tuple = hive.push_in(i.tuple_)
    ex.tuple_ = hive.antenna(i.push_tuple)

    for index, data_type in enumerate(meta_args.types):
        attr = hive.attribute(data_type)
        setattr(i, "attr_{}".format(index), attr)

        pull_out = hive.pull_out(attr)
        setattr(i, "pull_out_{}".format(index), pull_out)

        setattr(ex, "item_{}".format(index), hive.output(pull_out))

    def do_unpack_tuple(self):
        tuple_ = self._tuple_
        data_types = meta_args.types

        assert len(tuple_) == len(data_types)

        for index, item in enumerate(tuple_):
            setattr(self, "_attr_{}".format(index), item)

    i.do_unpack_tuple = hive.modifier(do_unpack_tuple)
    hive.trigger(i.push_tuple, i.do_unpack_tuple)


UnpackTuple = hive.dyna_hive("UnpackTuple", build_unpack_tuple, declare_unpack_tuple)
