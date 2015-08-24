import hive

from ..event import EventListener


class Mouse_:

    def __init__(self):
        self._hive = hive.get_run_hive()
        self.button = None

        self.pos_x = 0.0
        self.pos_y = 0.0

    def on_button(self, event_tail):
        button, *_ = event_tail

        if button == self.button:
            self._hive.on_pressed()

    def on_moved(self, coordinates):
        self.pos_x, self.pos_y = coordinates
        self._hive._on_moved()

    def add_listener(self, func):
        button_listener = EventListener(self.on_button, ("event", "mouse", "pressed"))
        moved_listener = EventListener(self.on_button, ("event", "mouse", "move"))

        func(button_listener)
        func(moved_listener)


def build_mouse(cls, i, ex, args):
    ex.on_event = hive.socket(cls.add_listener, identifier=("event", "add_handler"), auto_connect=True)
    i.on_tick = hive.triggerfunc()

    ex.name = hive.attribute(("str",), "<Sensor>")
    ex.button = hive.property(cls, "button", "str")

    i.button_in = hive.pull_in(ex.button)
    ex.button_in = hive.antenna(i.button_in)

    i.on_pressed = hive.triggerfunc()
    ex.on_pressed = hive.hook(i.on_pressed)

    i.on_moved = hive.triggerfunc()
    ex.on_moved = hive.hook(i.on_moved)

    ex.pos_x = hive.property(cls, "pos_x")
    ex.pos_y = hive.property(cls, "pos_y")

    x_out = hive.pull_out(ex.pos_x)
    ex.x_out = hive.output(x_out)

    y_out = hive.pull_out(ex.pos_y)
    ex.y_out = hive.output(y_out)


Mouse = hive.hive("Mouse", build_mouse, cls=Mouse_)