import hive


def configure_transistor(meta_args):
    meta_args.data_type = hive.parameter("str", "int")


def build_transistor(i, ex, args, meta_args):
    """Convert a pull output into a push output, using a trigger input"""
    i.value = hive.attribute(meta_args.data_type)
    ex.value = i.value.pull_in

    ex.result = i.value.push_out
    ex.trigger = i.value.push_out.trigger

    i.value.pull_in.triggered.connect(i.value.push_out.trigger)


Transistor = hive.dyna_hive("Transistor", build_transistor, configure_transistor)
