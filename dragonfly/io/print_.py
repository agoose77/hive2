import hive


def build_print(i, ex, args):
    """Output object to Python stdout"""
    ex.value = hive.variable()
    i.value_in = hive.push_in(ex.value)
    ex.value_in = hive.antenna(i.value_in)

    i.func = hive.modifier(lambda self: print(self.value))

    hive.trigger(i.value_in, i.func)


Print = hive.hive("Print", build_print)
