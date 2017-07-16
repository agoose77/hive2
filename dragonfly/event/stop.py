import hive

from .event import EventHandler


class OnStopClass:

    def set_add_handler(self, add_handler):
        callback = hive.internal(self).on_stop
        handler = EventHandler(callback, ("stop",), mode='match')
        add_handler(handler)


def build_on_stop(i, ex, args):
    """Listen for quit event"""
    i.on_stop_drone = hive.drone(OnStopClass)
    ex.get_add_handler = i.on_stop_drone.set_add_handler.socket("event.add_handler")

    i.on_stopped = hive.modifier()
    ex.on_stopped = i.on_stopped.triggered


OnStop = hive.hive("OnStop", build_on_stop)
