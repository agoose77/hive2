from operator import add, sub, mul, truediv, mod, eq, or_, not_, and_, gt, lt, ge, le

import hive


operators = {'+': add, '-': sub, '*': mul, '/': truediv, '%': mod}
operator_names = set(operators)


def configure_operator(meta_args):
    meta_args.data_type = hive.parameter("str", "int")
    meta_args.operator = hive.parameter("str", "+", options=operator_names)


def build_operator(i, ex, args, meta_args):
    """HIVE interface to python mathematical operators"""
    assert meta_args.operator in operators
    op = operators[meta_args.operator]

    i.a = hive.attribute(meta_args.data_type)
    i.b = hive.attribute(meta_args.data_type)

    ex.a = i.a.pull_in
    ex.b = i.b.pull_in
    i.a.pull_in.pushed.connect(i.b.pull_in.trigger)

    i.result = hive.attribute(meta_args.data_type)
    ex.result = i.result.pull_out

    def run_operator(i, ex):
        i.result.value = op(i.a.value, i.b.value)

    i.run_operator = hive.modifier(run_operator)
    i.a.pull_in.pushed.connect(i.run_operator.trigger)
    i.a.pull_in.pushed.connect(i.run_operator.trigger)
    i.result.pull_out.before.connect(i.a.pull_in.trigger)


MathOperator = hive.dyna_hive("MathOperator", build_operator, configure_operator)
