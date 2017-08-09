import hive

from .event import EventHandler


class OnStopClass:

    def __init__(self):
        self._hive = hive.get_run_hive()

    def set_add_handler(self, add_handler):
        callback = self._hive._on_stop
        handler = EventHandler(callback, ("stop",), mode='match')
        add_handler(handler)


def build_on_stop(cls, i, ex, args):
    """Listen for quit event"""
    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")

    i.on_stop = hive.triggerfunc()
    ex.on_stop = hive.hook(i.on_stop)


OnStop = hive.hive("OnStop", build_on_stop, drone_class=OnStopClass)
