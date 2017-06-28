import hive


def do_count_up(self):
    self.count += 1
    self.count_out.push()


def do_count_down(self):
    self.count -= 1
    self.count_out.push()


def build_count(i, ex, args):
    """Simple integer counter"""
    args.start_value = hive.parameter("int", 0)
    ex.count = hive.variable("int", args.start_value)

    i.do_count_up = hive.modifier(do_count_up)
    ex.increment = hive.entry(i.do_count_up)

    i.do_count_down = hive.modifier(do_count_down)
    ex.decrement = hive.entry(i.do_count_down)

    i.count_out = hive.push_out(ex.count)
    ex.count_out = hive.output(i.count_out)


Count = hive.hive("Count", build_count)
