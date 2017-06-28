import hive


def declare_sorted(meta_args):
    meta_args.data_type = hive.parameter('str', 'list', {'list', 'dict', 'set', 'tuple'})


def build_sorted(i, ex, args, meta_args):
    """Sort an iterable and output list"""
    args.reverse = hive.parameter('bool', False)
    i.reverse = hive.variable('bool', args.reverse)

    i.result = hive.variable('list')
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.value = hive.variable(meta_args.data_type)
    i.pull_value = hive.pull_in(i.value)
    ex.value = hive.antenna(i.pull_value)

    def sort(self):
        self._result = sorted(self._value, reverse=self._reverse)

    i.sort = hive.modifier(sort)
    hive.trigger(i.pull_result, i.pull_value, pretrigger=True)
    hive.trigger(i.pull_value, i.sort)


Sorted = hive.dyna_hive("Sorted", build_sorted, declare_sorted)