import hive


def cycle(i, ex):
    i.counter.value += 1

    if i.counter.value >= i.period.value:
        i.counter.value -= i.period.value
        i.output()


def build_cycle(i, ex, args):
    """Emit trigger to trig_out when N triggers to trig_in are received, where N = period_in"""
    i.period = hive.attribute("int", 0)
    i.counter = hive.attribute("int", 0)

    i.cycle = hive.modifier(cycle)
    i.period.pull_in.triggered.connect(i.cycle.trigger)

    i.output = hive.modifier()

    ex.index = i.counter.pull_out
    ex.period_in = i.period.pull_in
    ex.trig_in = i.period.pull_in.trigger
    ex.trig_out = i.output.triggered


Cycle = hive.hive("Cycle", build_cycle)
