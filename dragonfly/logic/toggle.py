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
    i.toggle = hive.attribute("bool", args.start_value)

    i.modifier = hive.modifier(evaluate_toggle)
    ex.trig_in = i.modifier.trigger

    i.trig_a = hive.triggerfunc()
    i.trig_b = hive.triggerfunc()

    ex.trig_a = i.trig_a.trigger
    ex.trig_b = i.trig_b.trigger


Toggle = hive.hive("Toggle", build_toggle)
