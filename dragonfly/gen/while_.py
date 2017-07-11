import hive


def do_while(i, ex):
    while True:
        i.condition.pull_in()

        if not i.condition.value:
            break

        i.do_trig()


def build_while(i, ex, args):
    """Trigger output while condition is True"""
    i.condition = hive.attribute()
    ex.condition_in = i.condition.pull_in

    i.do_trig = hive.modifier()
    ex.trig_out = i.do_trig.triggered

    i.trig_in = hive.modifier(do_while)
    ex.trig_in = i.trig_in.trigger


While = hive.hive("While", build_while)
