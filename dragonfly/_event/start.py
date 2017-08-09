import hive

from .event import EventHandler


class OnStartClass:

    def set_add_handler(self, add_handler):
        callback = hive.internal(self).on_started
        handler = EventHandler(callback, ("start",), mode='match')
        add_handler(handler)


def build_on_start(i, ex, args):
    """Listen for start event"""
    i.on_start_drone = hive.drone(OnStartClass)
    ex.get_add_handler = i.on_start_drone.set_add_handler.socket("event.add_handler")

    i.on_started = hive.modifier()
    ex.on_started = i.on_started.triggered


OnStart = hive.hive("OnStart", build_on_start)
