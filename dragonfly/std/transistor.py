import hive


def declare_transistor(meta_args):
    meta_args.data_type = hive.parameter("str", "int")


def build_transistor(i, ex, args, meta_args):
    """Convert a pull output into a push output, using a trigger input"""
    i.value = hive.variable(meta_args.data_type)
    i.pull_value = hive.pull_in(i.value)
    ex.value = hive.antenna(i.pull_value)

    i.push_value = hive.push_out(i.value)
    ex.result = hive.output(i.push_value)

    ex.trigger = hive.entry(i.pull_value)

    hive.trigger(i.pull_value, i.push_value)


Transistor = hive.dyna_hive("Transistor", build_transistor, declare_transistor)
