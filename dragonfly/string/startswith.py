import hive


def do_startswith(i, ex):
    i.result.value = i.string.value.startswith(i.substring.value)


def build_startswith(i, ex, args):
    """Check if a string starts with a substring"""
    i.string = hive.attribute('str')
    i.substring = hive.attribute('str')

    ex.string = i.string.pull_in
    ex.substring = i.substring.pull_in

    i.result = hive.attribute('str')
    ex.result = i.result.pull_out

    i.do_startswith = hive.modifier(do_startswith)
    i.result.pull_out.pre_triggered.connect(i.string.pull_in.trigger,
                                               i.substring.pull_in.trigger,
                                               i.do_startswith.trigger)


StartsWith = hive.hive("StartsWith", build_startswith)