import hive


def build_always(i, ex, args):
    ex.name = hive.attribute(("str",), "<Sensor>")
    ex.is_positive = hive.attribute(("bool",), True)

    i.positive = hive.pull_out(ex.is_positive)
    ex.positive = hive.output(i.positive)

    def trigger(h):
        h.trig_out()

    i.trig_in = hive.modifier(trigger)
    ex.trig_in = hive.entry(i.trig_in)

    i.trig_out = hive.triggerfunc()
    ex.trig_out = hive.hook(i.trig_out)


Always = hive.hive("Always", build_always)