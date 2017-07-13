import hive


def configure_abs(meta_args):
    meta_args.data_type = hive.parameter('str', 'int', options={'int', 'complex', 'float'})


def do_abs(i, ex):
    i.result.value = abs(i.value.value)


def build_abs(i, ex, args, meta_args):
    """Calculate the absolute abs() of a value"""
    i.value = hive.attribute(meta_args.data_type)
    i.result = hive.attribute(meta_args.data_type)

    ex.value = i.value.pull_in
    ex.result = i.value.pull_out

    i.do_abs = hive.modifier(do_abs)
    i.result.pull_out.pre_triggered.connect(i.value.pull_in.trigger,
                                               i.do_abs.trigger)


Abs = hive.dyna_hive("Abs", build_abs, configurer=configure_abs)
