import hive


class DispatchClass:

    def __init__(self):
        self._read_event = None

        self.event = None

    def set_read_event(self, read_event):
        self._read_event = read_event

    def dispatch(self):
        hive.internal(self).event.pull_in()
        self._read_event(self.event)


def build_dispatch(i, ex, args):
    i.dispatch_drone = hive.drone(DispatchClass)
    i.event = i.dispatch_drone.property("event", "tuple.event")
    ex.event = i.event.pull_in

    ex.get_read_event = i.dispatch_drone.set_read_event.socket(identifier="event.process")
    ex.trig = i.dispatch_drone.dispatch.trigger


Dispatch = hive.hive("Dispatch", build_dispatch)
