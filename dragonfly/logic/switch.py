import hive


def evaluate_switch(self, i):
    if i.switch.value:
        i.on_true()

    else:
        i.on_false()


def build_switch(i, ex, args, meta_args):
    """Redirect input trigger to true / false outputs according to boolean evaluation of switch value"""
    i.switch = hive.attribute()
    ex.input = i.switch.push_in

    i.on_true = hive.triggerfunc()
    ex.true = i.true.triggered

    i.on_false = hive.triggerfunc()
    ex.false = i.false.triggered

    i.evaluate_input = hive.modifier(evaluate_switch)
    ex.input.push_in.trigger(i.evaluate_input)


Switch = hive.hive("Switch", build_switch)
