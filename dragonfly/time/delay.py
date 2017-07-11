import hive

from dragonfly.event import EventHandler


class _DelayCls:

    def __init__(self):
        self.add_handler = None
        self.remove_handler = None
        self.delay = 0.0
        self.running = False

        self._hive = hive.get_run_hive()

        self._listener = EventHandler(self.on_tick, ("tick",), mode="match")

        self._delay_ticks = 0
        self._elapsed_ticks = 0

        self._tick_rate = 0

    @hive.typed_property("float")
    def elapsed(self):
        return self._tick_rate * self._elapsed_ticks

    def set_add_handler(self, add_handler):
        self.add_handler = add_handler

    def set_remove_handler(self, remove_handler):
        self.remove_handler = remove_handler

    def set_get_tick_rate(self, get_tick_rate):
        self._tick_rate = get_tick_rate()

    def on_triggered(self):
        assert self.delay > 0, "Delay must be greater than zero"

        if not self.running:
            self.add_handler(self._listener)

        self._delay_ticks = round(self.delay * self._tick_rate)
        self._elapsed_ticks = 0

    def on_elapsed(self):
        self.remove_handler(self._listener)

        self.running = False
        self._hive._on_elapsed()

    def on_tick(self):
        self._elapsed_ticks += 1

        if self._elapsed_ticks == self._delay_ticks:
            self.on_elapsed()


def build_delay(cls, i, ex, args):
    """Delay input trigger by X ticks, where X is the value of delay_in (greater than zero)"""
    i.on_elapsed = hive.triggerfunc()
    ex.on_elapsed = hive.hook(i.on_elapsed)

    i.trigger = hive.triggerfunc(cls.on_triggered)
    i.do_trig = hive.triggerable(i.trigger)
    ex.trig_in = hive.entry(i.do_trig)

    ex.delay = hive.property(cls, "delay", "float")
    i.delay_in = hive.pull_in(ex.delay)
    ex.delay_in = hive.antenna(i.delay_in)

    i.elapsed = hive.pull_out(cls.elapsed)
    ex.elapsed = hive.output(i.elapsed)

    hive.trigger(i.trigger, i.delay_in, pretrigger=True)

    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")
    ex.get_remove_handler = hive.socket(cls.set_remove_handler, "event.remove_handler")

    ex.get_get_tick_rate = hive.socket(cls.set_get_tick_rate, "app.get_tick_rate")


Delay = hive.hive("Delay", build_delay, drone_class=_DelayCls)