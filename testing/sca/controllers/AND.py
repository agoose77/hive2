from __future__ import print_function

import hive


def build_and(i, ex, args):
    ex.a_value = hive.attribute(("bool",), False)
    ex.b_value = hive.attribute(("bool",), False)

    i.a = hive.pull_in(ex.a_value)
    i.b = hive.pull_in(ex.b_value)

    ex.a = hive.antenna(i.a)
    ex.b = hive.antenna(i.b)

    def on_and(h):
        h._pull_inputs()

        if h.a_value and h.b_value:
            h.trig_out()

    i.trig_out = hive.triggerfunc()
    i.trig_in = hive.modifier(on_and)

    # Update attributes before calling modifier
    i.pull_inputs = hive.triggerfunc()
    hive.trigger(i.pull_inputs, i.a, pretrigger=True)
    hive.trigger(i.pull_inputs, i.b, pretrigger=True)

    ex.trig_out = hive.hook(i.trig_out)
    ex.trig_in = hive.entry(i.trig_in)


AND = hive.hive("AND", build_and)