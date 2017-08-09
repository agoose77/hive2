import hive

from dragonfly.event import EventHandler


class DelayCls:

    def __init__(self):
        self.add_handler = None
        self.remove_handler = None
        self.delay = 0.0
        self.running = False

        self._listener = EventHandler(self.on_tick, ("tick",), mode="match")

        self._delay_ticks = 0
        self._elapsed_ticks = 0
        self._awaiting_triggers = []

        self._tick_rate = 0

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

        delta_ticks = round(self.delay * self._tick_rate)
        target_tick = delta_ticks + self._elapsed_ticks
        self._awaiting_triggers.append(target_tick)

    def on_elapsed(self):
        self.remove_handler(self._listener)

        self.running = False
        hive.internal(self).on_elapsed()

    def on_tick(self):
        self._elapsed_ticks += 1
        elapsed_ticks = self._elapsed_ticks

        while self._awaiting_triggers:
            if self._awaiting_triggers[0] <= elapsed_ticks:
                del self._awaiting_triggers[0]
                self.on_elapsed()


def build_delay(i, ex, args):
    """Delay input trigger by X ticks, where X is the value of delay_in (greater than zero)"""
    i.delay_drone = hive.drone(DelayCls)
    i.on_elapsed = hive.modifier()
    ex.on_elapsed = i.on_elapsed.pushed

    ex.trig_in = i.delay_drone.on_triggered.trigger

    i.delay = i.delay_drone.property("delay", "float")
    ex.delay_in = i.delay.push_in

    ex.get_add_handler = i.delay_drone.set_add_handler.socket("event.add_handler")
    ex.get_remove_handler = i.delay_drone.set_remove_handler.socket("event.remove_handler")
    ex.get_get_tick_rate = i.delay_drone.set_get_tick_rate.socket("app.get_tick_rate")


Delay = hive.hive("Delay", build_delay)
