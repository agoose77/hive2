import hive


class DispatchClass:

    def __init__(self):
        self._read_event = None

        self.event = None
        self._hive = hive.get_run_hive()

    def set_read_event(self, read_event):
        self._read_event = read_event

    def dispatch(self):
        self._hive.event()
        self._read_event(self.event)


def build_dispatch(cls, i, ex, args):
    i.event = hive.property(cls, "event", "tuple.event")
    i.pull_event = hive.pull_in(i.event)
    ex.event = hive.antenna(i.pull_event)

    ex.get_read_event = hive.socket(cls.set_read_event, identifier="event.process")

    i.dispatch = hive.triggerable(cls.dispatch)
    ex.trig = hive.entry(i.dispatch)


Dispatch = hive.hive("Dispatch", build_dispatch, drone_class=DispatchClass)
