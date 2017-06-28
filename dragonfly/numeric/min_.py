import hive


def declare_min(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})


def build_min(i, ex, args, meta_args):
    """Determine the minimum of two values"""
    i.a_value = hive.variable(meta_args.data_type)
    i.b_value = hive.variable(meta_args.data_type)
    i.value = hive.variable(meta_args.data_type)

    i.pull_a = hive.pull_in(i.a_value)
    i.pull_b = hive.pull_in(i.b_value)
    i.pull_value = hive.pull_out(i.value)

    ex.value = hive.output(i.pull_value)
    ex.a = hive.antenna(i.pull_a)
    ex.b = hive.antenna(i.pull_b)

    def do_min(self):
        self._value = min(self._a, self._b)

    i.do_min = hive.modifier(do_min)

    hive.trigger(i.pull_value, i.pull_a, pretrigger=True)
    hive.trigger(i.pull_a, i.pull_b)
    hive.trigger(i.pull_b, i.do_min)


Min = hive.dyna_hive("Min", build_min, declare_min)