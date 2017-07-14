import hive


def evaluate_switch(i, ex):
    if i.switch.value:
        i.on_true()

    else:
        i.on_false()


def build_switch(i, ex, args):
    """Redirect input trigger to true / false outputs according to boolean evaluation of switch value"""
    i.switch = hive.attribute()
    ex.input = i.switch.push_in

    i.on_true = hive.modifier()
    ex.true = i.true.pushed

    i.on_false = hive.modifier()
    ex.false = i.false.pushed

    i.evaluate_input = hive.modifier(evaluate_switch)
    ex.input.push_in.trigger(i.evaluate_input.trigger)


Switch = hive.hive("Switch", build_switch)
