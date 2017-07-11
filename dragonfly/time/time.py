import hive
from dragonfly.event import EventHandler


class TimeClass:

    def __init__(self):
        self._add_handler = None
        self._get_tick_rate = None
        self._tick_rate = None

        self.start_time = None
        self.elapsed = 0.0
        self.current_tick = 0

    def on_tick(self):
        self.current_tick += 1
        self.elapsed = self.current_tick / self._tick_rate

    def on_started(self):
        handler = EventHandler(self.on_tick, ("tick",), mode="match")

        self._add_handler(handler)

        # Assume tick rate does not change
        self._tick_rate = self._get_tick_rate()

    def set_add_handler(self, add_handler):
        self._add_handler = add_handler

    def set_get_tick_rate(self, get_tick_rate):
        self._get_tick_rate = get_tick_rate


def time_builder(cls, i, ex, args):
    """Access to Python time module"""
    i.elapsed = hive.property(cls, 'elapsed', 'float')
    i.elapsed_out = hive.pull_out(i.elapsed)
    ex.elapsed_out = hive.output(i.elapsed_out)

    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")
    ex.on_started = hive.plugin(cls.on_started, "on_started", policy=hive.SingleRequired)
    ex.get_get_tick_rate = hive.socket(cls.set_get_tick_rate, "app.get_tick_rate")


Time = hive.hive("Time", builder=time_builder, drone_class=TimeClass)