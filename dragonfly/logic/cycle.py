import hive


def build_cycle(i, ex, args):
    """Emit trigger to trig_out when N triggers to trig_in are received, where N = period_in"""
    ex.period = hive.attribute("int", 0)
    ex.counter = hive.attribute("int", 0)

    i.period_in = hive.pull_in(ex.period)
    i.counter_out = hive.pull_out(ex.counter)

    ex.index = hive.output(i.counter_out)
    ex.period_in = hive.antenna(i.period_in)
    ex.trig_in = hive.entry(i.period_in)

    def cycle(self):
        self.counter += 1

        if self.counter >= self.period:
            self.counter -= self.period
            self._output()

    i.trigger = hive.modifier(cycle)
    hive.trigger(i.period_in, i.trigger)

    i.output = hive.triggerfunc()
    ex.trig_out = hive.hook(i.output)


Cycle = hive.hive("Cycle", build_cycle)
