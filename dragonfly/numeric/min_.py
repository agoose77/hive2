import hive


def configure_min(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})


def do_min(i, ex):
    i.value.value = min(i.a.value, i.b.value)


def build_min(i, ex, args, meta_args):
    """Determine the minimum of two values"""
    i.a_value = hive.attribute(meta_args.data_type)
    i.b_value = hive.attribute(meta_args.data_type)
    i.value = hive.attribute(meta_args.data_type)

    ex.a = i.a.pull_in
    ex.b = i.b.pull_in
    ex.value = i.value.pull_out

    i.do_min = hive.modifier(do_min)

    i.value.pull_out.pre_triggered.connect(i.a.pull_in.trigger,
                                              i.b.pull_in.trigger,
                                              i.do_min.trigger)


Min = hive.dyna_hive("Min", build_min, configure_min)
