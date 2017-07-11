import hive

# TODO future - it might be that this should be given a declarator for "advanced mode", and by default
# Just use a normal argument to define the substring


def do_startswith(self):
    self._startswith = self._string.startswith(self._substring)


def build_startswith(i, ex, args):
    """Check if string starts with a substring"""
    i.string = hive.attribute('str')
    i.substring = hive.attribute('str')

    i.pull_string = hive.pull_in(i.string)
    i.pull_substring = hive.pull_in(i.substring)

    ex.string = hive.antenna(i.pull_string)
    ex.substring = hive.antenna(i.pull_substring)

    i.startswith = hive.attribute('bool')
    i.pull_startswith = hive.pull_out(i.startswith)
    ex.startswith = hive.output(i.pull_startswith)

    i.do_find_substr = hive.modifier(do_startswith)

    hive.trigger(i.pull_startswith, i.pull_string, pretrigger=True)
    hive.trigger(i.pull_string, i.pull_substring)
    hive.trigger(i.pull_substring, i.do_find_substr)


StartsWith = hive.hive("StartsWith", build_startswith)