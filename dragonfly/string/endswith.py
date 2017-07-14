import hive


# TODO future - perhaps this should instead provide an advanced mode,
# where substring can be pulled, otherwise use a normal argument to define the substring


def do_endswith(i, ex):
    i.endswith.value = i.string.value.endswith(i.substring.value)


def build_endswith(i, ex, args):
    """Check if string ends with a substring"""
    i.string = hive.attribute('str')
    i.substring = hive.attribute('str')

    ex.string = i.string.pull_in
    ex.substring = i.substring.pull_out

    i.endswith = hive.attribute('bool')
    ex.endswith = i.endswith.pull_out

    i.do_find_substr = hive.modifier(do_endswith)
    i.endswith.pull_out.pre_pushed.connect(i.string.pull_in.trigger,
                                           i.substring.pull_in.trigger,
                                           i.do_find_substr.trigger)


EndsWith = hive.hive("EndsWith", build_endswith)
