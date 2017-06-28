import hive


def declare_constrain(meta_args):
    meta_args.data_type = hive.parameter('str', 'float', options={'complex', 'int', 'float'})


def build_constrain(i, ex, args, meta_args):
    """Constrain a value between two bounding values"""
    args.min_value = hive.parameter(meta_args.data_type)
    args.max_value = hive.parameter(meta_args.data_type)

    i.min_value = hive.variable(meta_args.data_type, args.min_value)
    i.max_value = hive.variable(meta_args.data_type, args.max_value)

    i.value = hive.variable(meta_args.data_type)
    i.result = hive.variable(meta_args.data_type)

    i.pull_result = hive.pull_out(i.result)
    i.pull_value = hive.pull_in(i.value)

    ex.result = hive.output(i.pull_result)
    ex.value = hive.antenna(i.pull_value)

    def do_contrain(self):
        self._result = min(max(self._value, self._min_value), self._max_value)

    i.do_constrain = hive.modifier(do_contrain)
    hive.trigger(i.pull_result, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_value, i.do_constrain)


Constrain = hive.dyna_hive("Constrain", build_constrain, declare_constrain)
