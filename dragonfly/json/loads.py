import hive

from json import loads


def do_loads(i, ex):
    i.result.value = loads(i.object.value)


def build_loads(i, ex, args):
    """Interface to JSON loads function"""

    i.result = hive.attribute('str')
    i.object = hive.attribute()

    ex.result = i.result.pull_out
    ex.object = i.object.pull_in

    i.do_loads = hive.modifier(do_loads)
    i.result.pull_out.before.connect(i.pull_object.trigger)
    i.object.pull_in.pushed.connect(i.do_loads.trigger)


Loads = hive.hive("Loads", build_loads)
