import hive

from .event import EventHandler


class TickClass:

    @hive.types(activate_on_start='bool')
    def __init__(self, activate_on_start=True):
        self._add_handler = None
        self._remove_handler = None

        self._active = False
        self._activate_on_started = activate_on_start

    def set_add_handler(self, add_handler):
        self._add_handler = add_handler

        self._handler = EventHandler(hive.internal(self).on_tick, ("tick",), mode="match")

        if self._activate_on_started:
            self.enable()

    def set_remove_handler(self, remove_handler):
        self._remove_handler = remove_handler

    def enable(self):
        if not self._active:
            self._add_handler(self._handler)
            self._active = True

    def disable(self):
        if self._active:
            self._remove_handler(self._handler)
            self._active = False


def build_tick(i, ex, args):
    """Tick event sensor, trigger on_tick every tick"""
    i.tick_drone = hive.drone(TickClass)
    i.on_tick = hive.modifier()
    ex.on_tick = i.on_tick.triggered

    ex.get_add_handler = i.tick_drone.set_add_handler.socket("event.add_handler", policy=hive.SingleRequired)
    ex.get_remove_handler = i.tick_drone.set_remove_handler.socket("event.remove_handler", policy=hive.SingleRequired)

    ex.enable = i.tick_drone.enable.trigger
    ex.disable = i.tick_drone.disable.trigger


OnTick = hive.hive("OnTick", build_tick)
