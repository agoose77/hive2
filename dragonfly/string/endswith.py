import hive

# TODO future - perhaps this should instead provide an advanced mode,
# where substring can be pulled, otherwise use a normal argument to define the substring


def do_endswith(self):
    self._endswith = self._string.endswith(self._substring)


def build_endswith(i, ex, args):
    """Check if string ends with a substring"""
    i.string = hive.variable('str')
    i.substring = hive.variable('str')

    i.pull_string = hive.pull_in(i.string)
    i.pull_substring = hive.pull_in(i.substring)

    ex.string = hive.antenna(i.pull_string)
    ex.substring = hive.antenna(i.pull_substring)

    i.endswith = hive.variable('bool')
    i.pull_endswith = hive.pull_out(i.endswith)
    ex.endswith = hive.output(i.pull_endswith)

    i.do_find_substr = hive.modifier(do_endswith)

    hive.trigger(i.pull_endswith, i.pull_string, pretrigger=True)
    hive.trigger(i.pull_string, i.pull_substring)
    hive.trigger(i.pull_substring, i.do_find_substr)


EndsWith = hive.hive("EndsWith", build_endswith)