import hive


def do_replace(self):
    self._result = self._string.replace(self._substring, self._replacement_string)


def build_replace(i, ex, args):
    """Replace occurances of substring in string with replacement"""
    i.string = hive.attribute('str')
    i.substring = hive.attribute('str')
    i.replacement = hive.attribute('str')

    i.pull_string = hive.pull_in(i.string)
    i.pull_substring = hive.pull_in(i.substring)
    i.pull_replacement = hive.pull_in(i.replacement)

    ex.string = hive.antenna(i.pull_string)
    ex.substring = hive.antenna(i.pull_substring)
    ex.replacement = hive.antenna(i.pull_replacement)

    i.result = hive.attribute('str')
    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.do_replace = hive.modifier(do_replace)

    hive.trigger(i.pull_result, i.pull_string, pretrigger=True)
    hive.trigger(i.pull_string, i.pull_substring)
    hive.trigger(i.pull_substring, i.pull_replacement)
    hive.trigger(i.pull_replacement, i.do_replace)


Replace = hive.hive("Replace", build_replace)