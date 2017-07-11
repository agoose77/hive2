import hive


def do_count_up(i, ex):
    i.count.value += 1


def do_count_down(i, ex):
    i.count.value += 1


def build_count(i, ex, args):
    """Simple integer counter"""
    args.start_value = hive.parameter("int", 0)
    i.count = hive.attribute("int", args.start_value)

    i.do_count_up = hive.modifier(do_count_up)
    ex.increment = i.do_count_up.trigger

    i.do_count_down = hive.modifier(do_count_down)
    ex.decrement = i.do_count_down.trigger

    ex.count = i.count.push_out
    i.count.updated.connect(i.count.push_out.trigger)


Count = hive.hive("Count", build_count)
