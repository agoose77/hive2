import hive

from json import loads


def build_loads(i, ex, args):
    """Interface to JSON loads function"""
    def do_loads(self):
        self._result = loads(self._object_)

    i.result = hive.attribute('str')
    i.object_ = hive.attribute()

    i.pull_result = hive.pull_out(i.result)
    ex.result = hive.output(i.pull_result)

    i.pull_object = hive.pull_in(i.object_)
    ex.object_ = hive.antenna(i.pull_object)

    i.do_loads = hive.modifier(do_loads)

    hive.trigger(i.pull_result, i.pull_object, pretrigger=True)
    hive.trigger(i.pull_object, i.do_loads)


Loads = hive.hive("Loads", build_loads)
