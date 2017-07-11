import hive


def declare_constrain(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})

def do_contrain(i, ex):
    i.result.property = min(max(i.value.property, i.min_value.property), i.max_value.property)


def build_constrain(i, ex, args, meta_args):
    """Constrain a value between two bounding values"""
    args.min_value = hive.parameter(meta_args.data_type)
    args.max_value = hive.parameter(meta_args.data_type)

    i.min_value = hive.attribute(meta_args.data_type, args.min_value)
    i.max_value = hive.attribute(meta_args.data_type, args.max_value)

    i.value = hive.attribute(meta_args.data_type)
    i.result = hive.attribute(meta_args.data_type)

    i.pull_result.before_triggered.connect(i.pull_value.trigger)

    i.do_constrain = hive.modifier(do_contrain)
    i.pull_value.triggered.connect(i.do_constrain.trigger)

    ex.result = i.result.pull_out
    ex.value = i.value.pull_in


Constrain = hive.dyna_hive("Constrain", build_constrain, declare_constrain)
