import hive


def declare_switch(meta_args):
    meta_args.data_type = hive.parameter("str", "bool")


def evaluate_switch(self):
    if self.switch:
        self._true()

    else:
        self._false()


def build_switch(i, ex, args, meta_args):
    """Redirect input trigger to true / false outputs according to boolean evaluation of switch value"""
    ex.switch = hive.variable(meta_args.data_type)

    i.input = hive.pull_in(ex.switch)
    ex.input = hive.antenna(i.input)

    i.true = hive.triggerfunc()
    ex.true = hive.hook(i.true)

    i.false = hive.triggerfunc()
    ex.false = hive.hook(i.false)

    i.do_evaluate = hive.modifier(evaluate_switch)
    i.do_trigger = hive.triggerfunc(i.do_evaluate)
    hive.trigger(i.do_trigger, i.input, pretrigger=True)

    i.on_trigger = hive.triggerable(i.do_trigger)
    ex.trigger = hive.entry(i.on_trigger)


Branch = hive.dyna_hive("Switch", build_switch, declare_switch)
