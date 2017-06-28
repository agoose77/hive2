import hive

from json import dumps


def build_dumps(i, ex, args):
    """Interface to JSON dumps function"""
    def do_dumps(self):
        self._result = dumps(self._object_)

    i.result = hive.variable('str')
    i.object_ = hive.variable()

    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.pull_object = hive.pull_in(i.object_)
    ex.object_ = hive.antenna(i.pull_object)

    i.do_dumps = hive.modifier(do_dumps)

    hive.trigger(i.pull_result, i.pull_object, pretrigger=True)
    hive.trigger(i.pull_object, i.do_dumps)


Dumps = hive.hive("Dumps", build_dumps)
