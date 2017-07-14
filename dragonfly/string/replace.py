import hive


def do_replace(i, ex):
    i.result.value = i.string.value.replace(i.substring.value, i.replacement_string.value)


def build_replace(i, ex, args):
    """Replace occurances of substring in string with replacement"""
    i.string = hive.attribute('str')
    i.substring = hive.attribute('str')
    i.replacement = hive.attribute('str')

    ex.string = i.string.pull_in
    ex.substring = i.substring.pull_in
    ex.replacement = i.replacement.pull_in

    i.result = hive.attribute('str')
    ex.result = i.result.pull_out

    i.do_replace = hive.modifier(do_replace)
    i.result.pull_out.pre_pushed.connect(i.string.pull_in.trigger,
                                         i.substring.pull_in.trigger,
                                         i.replacement.pull_in.trigger,
                                         i.do_replace.trigger)


Replace = hive.hive("Replace", build_replace)