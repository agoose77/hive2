import hive


def build_debug(i, ex, args):
    def on_call(h):
        print(h.message)

    ex.message = hive.attribute(("str",), "Triggered!")
    i.trig_in = hive.modifier(on_call)
    ex.trig_in = hive.entry(i.trig_in)


Debug = hive.hive("Debug", build_debug)