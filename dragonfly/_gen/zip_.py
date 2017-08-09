import hive


def do_zip(i, ex):
    i.zippped.value = zip(i.first.value,
                             i.second.value)


def build_zip(i, ex, args):
    """Merge two iterables into a single iterable"""
    i.first = hive.attribute()
    i.second = hive.attribute()

    ex.a = i.first.pull_in
    ex.b = i.second.pull_in

    i.zipped = hive.attribute("iterator")
    ex.zipped = i.zipped.pull_out

    i.do_zip = hive.modifier(do_zip)
    ex.zipped.pretriggered.connect(i.first.pull_in.trigger,
                                   i.second.pull_in.trigger,
                                   i.do_zip.trigger)


Zip = hive.hive("Zip", build_zip)
