import hive


def do_print(i, ex):
    print(i.value.value)


def build_print(i, ex, args):
    """Output object to Python stdout"""
    i.value = hive.attribute()
    ex.value = i.value.push_in

    i.func = hive.modifier(do_print)
    i.value.push_in.pushed.connect(i.func.trigger)


Print = hive.hive("Print", build_print)
