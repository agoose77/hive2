import hive

from dragonfly.event import EventHandler


class Keyboard_:

    def __init__(self):
        self._hive = hive.get_run_hive()
        self.key = None

    def on_key(self, event_tail):
        key, *_ = event_tail

        if key == self.key:
            self._hive.is_positive = True
            self._hive.trig_out()

    def add_listener(self, func):
        listener = EventHandler(self.on_key, ("event", "keyboard", "pressed"))
        func(listener)


def build_keyboard(cls, i, ex, args):
    ex.on_event = hive.socket(cls.add_single_listener, identifier="event.add_handler")
    i.on_tick = hive.triggerfunc()

    ex.name = hive.attribute(("str",), "<Sensor>")
    ex.key = hive.property(cls, "key", "str")
    ex.is_positive = hive.attribute(("bool",), False)

    i.positive = hive.pull_out(ex.is_positive)
    ex.positive = hive.output(i.positive)

    i.trig_out = hive.triggerfunc()
    ex.trig_out = hive.hook(i.trig_out)


Keyboard = hive.hive("Keyboard", build_keyboard, drone_class=Keyboard_)