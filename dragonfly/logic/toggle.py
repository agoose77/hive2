import hive


def evaluate_toggle(self):
    self._toggle = not self._toggle

    if self._toggle:
        self._trig_a()

    else:
        self._trig_b()


def build_toggle(i, ex, args):
    """Toggle between two triggers"""
    args.start_value = hive.parameter('bool', False)
    i.toggle = hive.variable("bool", args.start_value)

    i.modifier = hive.modifier(evaluate_toggle)
    ex.trig_in = hive.entry(i.modifier)

    i.trig_a = hive.triggerfunc()
    i.trig_b = hive.triggerfunc()

    ex.trig_a = hive.hook(i.trig_a)
    ex.trig_b = hive.hook(i.trig_b)


Toggle = hive.hive("Toggle", build_toggle)
