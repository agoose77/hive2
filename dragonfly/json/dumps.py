import hive

from json import dumps


def do_dumps(i, ex):
    i.result.property = dumps(i.object.property)



def build_dumps(i, ex, args):
    """Interface to JSON dumps function"""
    i.result = hive.attribute('str')
    i.object = hive.attribute()

    ex.result = i.result.pull_out
    ex.object = i.object.pull_in

    i.do_dumps = hive.modifier(do_dumps)

    i.pull_result.before_triggered.connect(i.object.pull_in.trigger)
    i.pull_object.triggered.connect(i.do_dumps.trigger)


Dumps = hive.hive("Dumps", build_dumps)
