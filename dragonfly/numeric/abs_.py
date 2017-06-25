import hive


def declare_abs(meta_args):
    meta_args.data_type = hive.parameter('str', 'int', options={'int', 'complex', 'float'})


def build_abs(i, ex, args, meta_args):
    """Calculate the absolute abs() of a value"""
    i.value = hive.attribute(meta_args.data_type)
    i.pull_value = hive.pull_in(i.value)

    i.result = hive.attribute(meta_args.data_type)
    i.pull_result = hive.pull_out(i.result)

    ex.value = hive.antenna(i.pull_value)
    ex.result = hive.output(i.pull_result)

    def do_abs(self):
        self._result = abs(self._value)

    i.do_abs = hive.modifier(do_abs)

    hive.trigger(i.pull_result, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_value, i.do_abs)


Abs = hive.dyna_hive("Abs", build_abs, declarator=declare_abs)
