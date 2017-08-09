import hive


def configure_max(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})


def do_max(i, ex):
    i.value.value = max(i.a.value, i.b.value)


def build_max(i, ex, args, meta_args):
    """Determine the maximum of two values"""
    i.a_value = hive.attribute(meta_args.data_type)
    i.b_value = hive.attribute(meta_args.data_type)
    i.value = hive.attribute(meta_args.data_type)

    ex.a = i.a.pull_in
    ex.b = i.b.pull_in
    ex.value = i.value.pull_out

    i.do_max = hive.modifier(do_max)

    i.value.pull_out.before.connect(i.a.pull_in.trigger,
                                        i.b.pull_in.trigger,
                                        i.do_max.trigger)


Max = hive.dyna_hive("Max", build_max, configure_max)
