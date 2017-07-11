import string

import hive


def declare_any(meta_args):
    meta_args.count = hive.parameter("int", 1, options=set(range(26)))
    meta_args.data_type = hive.parameter("str", "bool")


def build_any_func(count):
    argument_names = ["self._{}".format(char) for _, char in zip(range(count), string.ascii_lowercase)]
    argument_string = ', '.join(argument_names)

    func_body = """
def func(self):
    self._result = any({})
    """.format(argument_string)

    exec(func_body, locals(), globals())
    return func


def build_any(i, ex, args, meta_args):
    """Trigger output if any inputs evaluate to True"""
    # On pull
    func = build_any_func(meta_args.count)
    i.run_any = hive.modifier(func)

    i.result = hive.attribute(meta_args.data_type, False)
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    hive.trigger(i.pull_result, i.run_any, pretrigger=True)

    for index, char in zip(range(meta_args.count), string.ascii_lowercase):
        variable = hive.attribute(meta_args.data_type, False)
        setattr(i, char, variable)

        pull_in = hive.pull_in(variable)
        setattr(i, "pull_{}".format(char), pull_in)

        antenna = hive.antenna(pull_in)
        setattr(ex, char, antenna)


Any = hive.dyna_hive("Any", build_any, declare_any)
