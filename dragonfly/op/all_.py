import hive
import string


def declare_all(meta_args):
    meta_args.count = hive.parameter("int", 1, options=set(range(26)))
    meta_args.data_type = hive.parameter("str", "bool")


def build_all_func(count):
    argument_names = ["self._{}".format(char) for _, char in zip(range(count), string.ascii_lowercase)]
    argument_string = ', '.join(argument_names)

    func_body = """
def func(self):
    self._result = all({})
    """.format(argument_string)

    exec(func_body, locals(), globals())
    return func


def build_all(i, ex, args, meta_args):
    """Trigger output if all inputs evaluate to True"""
    # On pull
    func = build_all_func(meta_args.count)
    i.trigger = hive.modifier(func)

    i.result = hive.attribute(meta_args.data_type, False)
    pull_out = hive.pull_out(i.result)
    ex.output = hive.output(pull_out)

    hive.trigger(pull_out, i.trigger, pretrigger=True)

    for index, char in zip(range(meta_args.count), string.ascii_lowercase):
        variable = hive.attribute(meta_args.data_type, False)
        setattr(i, char, variable)

        pull_in = hive.pull_in(variable)

        antenna = hive.antenna(pull_in)
        setattr(ex, char, antenna)


All = hive.dyna_hive("All", build_all, declare_all)