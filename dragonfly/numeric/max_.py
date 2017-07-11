import hive


def declare_max(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})


def build_max(i, ex, args, meta_args):
    """Determine the maximum of two values"""
    i.a_value = hive.attribute(meta_args.data_type)
    i.b_value = hive.attribute(meta_args.data_type)
    i.value = hive.attribute(meta_args.data_type)

    i.pull_a = hive.pull_in(i.a_value)
    i.pull_b = hive.pull_in(i.b_value)
    i.pull_value = hive.pull_out(i.value)

    ex.value = hive.output(i.pull_value)
    ex.a = hive.antenna(i.pull_a)
    ex.b = hive.antenna(i.pull_b)

    def do_max(self):
        self._value = max(self._a, self._b)

    i.do_max = hive.modifier(do_max)

    hive.trigger(i.pull_value, i.pull_a, pretrigger=True)
    hive.trigger(i.pull_a, i.pull_b)
    hive.trigger(i.pull_b, i.do_max)


Max = hive.dyna_hive("Max", build_max, declare_max)