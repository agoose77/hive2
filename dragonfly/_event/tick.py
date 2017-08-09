import hive

from .event import EventHandler


class _TickCls:

    @hive.types(activate_on_start='bool')
    def __init__(self, activate_on_start=True):
        self._hive = hive.get_run_hive()

        self._add_handler = None
        self._remove_handler = None

        self._active = False
        self._activate_on_started = activate_on_start

    def set_add_handler(self, add_handler):
        self._add_handler = add_handler

        self._handler = EventHandler(self._hive._on_tick, ("tick",), mode="match")

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


def build_tick(cls, i, ex, args):
    """Tick event sensor, trigger on_tick every tick"""
    i.on_tick = hive.triggerfunc()
    ex.on_tick = hive.hook(i.on_tick)

    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler", policy=hive.SingleRequired)
    ex.get_remove_handler = hive.socket(cls.set_remove_handler, "event.remove_handler", policy=hive.SingleRequired)

    i.enable = hive.triggerable(cls.enable)
    ex.enable = hive.entry(i.enable)

    i.disable = hive.triggerable(cls.disable)
    ex.disable = hive.entry(i.disable)


OnTick = hive.hive("OnTick", build_tick, drone_class=_TickCls)
