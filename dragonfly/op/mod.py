from operator import add, sub, mul, truediv, mod, eq, or_, not_, and_, gt, lt, ge, le

import hive


def declare_mod(meta_args):
    meta_args.data_type = hive.parameter("str", "int", options={'int', 'float'})


def build_mod(i, ex, args, meta_args):
    """Perform modulo operation of two inputs"""
    i.a = hive.attribute(meta_args.data_type)
    i.b = hive.attribute(meta_args.data_type)

    i.pull_a = hive.pull_in(i.a)
    ex.a = hive.antenna(i.pull_a)

    i.pull_b = hive.pull_in(i.b)
    ex.b = hive.antenna(i.pull_b)
    hive.trigger(i.pull_a, i.pull_b)

    i.result = hive.attribute('float')
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    def calc(self):
        self._result = self._a % self._b

    i.run_operator = hive.modifier(calc)

    hive.trigger(i.pull_a, i.run_operator)
    hive.trigger(i.pull_result, i.pull_a, pretrigger=True)


Mod = hive.dyna_hive("Mod", build_mod, declare_mod)
