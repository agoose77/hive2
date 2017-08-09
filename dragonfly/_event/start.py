import hive

from .event import EventHandler


class _OnStart:

    def __init__(self):
        self._hive = hive.get_run_hive()

    def set_add_handler(self, add_handler):
        callback = self._hive._on_started
        handler = EventHandler(callback, ("start",), mode='match')
        add_handler(handler)


def build_on_start(cls, i, ex, args):
    """Listen for start event"""
    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")

    i.on_started = hive.triggerfunc()
    ex.on_started = hive.hook(i.on_started)


OnStart = hive.hive("OnStart", build_on_start, drone_class=_OnStart)
