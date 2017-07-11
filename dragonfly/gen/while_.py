import hive


def do_while(self):
    while True:
        self.condition_in()
        if not self.condition:
            break

        self.trig_out()


def build_while(i, ex, args):
    """Trigger output while condition is True"""
    ex.condition = hive.attribute()
    i.condition_in = hive.pull_in(ex.condition)
    ex.condition_in = hive.antenna(i.condition_in)

    i.trig = hive.triggerfunc()
    ex.trig_out = hive.hook(i.trig)

    i.trig_in = hive.modifier(do_while)
    ex.trig_in = hive.entry(i.trig_in)


While = hive.hive("While", build_while)
