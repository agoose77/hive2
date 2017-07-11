import hive
import string

function_definition = """
def func(i, ex):
    for attribute in ({},):
        attribute.pull_in()
        if attribute.property:
            i.result.value = True
            return
            
    i.result.value = False
"""


def declare_any(meta_args):
    meta_args.count = hive.parameter("int", 1, options=set(range(1, 27)))
    meta_args.data_type = hive.parameter("str", "bool")


def build_all_func(count):
    argument_names = ("i.{}".format(char) for _, char in zip(range(count), string.ascii_lowercase))
    argument_string = ', '.join(argument_names)

    function_body = function_definition.format(argument_string)
    exec(function_body, locals(), globals())
    return func


def build_any(i, ex, args, meta_args):
    """Trigger output if any inputs evaluate to True"""
    # On pull
    do_test_all = build_all_func(meta_args.count)
    i.do_test_all = hive.modifier(do_test_all)

    i.result = hive.attribute(meta_args.data_type, False)

    for index, char in zip(range(meta_args.count), string.ascii_lowercase):
        variable = hive.attribute(meta_args.data_type, False)
        setattr(i, char, variable)
        setattr(ex, char, variable.pull_in)

    i.result.pull_out.pre_triggered.connect(i.do_test_all.trigger)
    ex.output = i.result.pull_out


Any = hive.dyna_hive("Any", build_any, declare_any)
