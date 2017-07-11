import hive


SET_SET_OPERATIONS = {'intersection': set.intersection, 'union': set.union, 'difference': set.difference,
                      'symmetric_difference': set.symmetric_difference}


def build_set(i, ex, args):
    """Perform set operation on two sets"""
    i.a = hive.attribute('set')
    i.pull_a = hive.pull_in(i.a)
    ex.a = hive.antenna(i.pull_a)

    i.b = hive.attribute('set')
    i.pull_b = hive.pull_in(i.b)
    ex.b = hive.antenna(i.pull_b)

    i.result = hive.attribute('set')
    for op_name, op in SET_SET_OPERATIONS.items():
        pull_op = hive.pull_out(i.result)
        setattr(i, "pull_{}".format(op_name), pull_op)
        setattr(ex, op_name, hive.output(pull_op))

        def do_operation(self):
            self._result = op(self._a, self._b)

        mod = hive.modifier(do_operation)
        setattr(i, "do_{}".format(op_name), mod)

        hive.trigger(pull_op, i.pull_a, pretrigger=True)
        hive.trigger(pull_op, mod, pretrigger=True)

    hive.trigger(i.pull_a, i.pull_b)


FrozenSet = hive.hive("FrozenSet", build_set)
