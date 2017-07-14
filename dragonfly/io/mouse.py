import hive

from ..event import EventHandler


class Mouse_:

    def __init__(self):
        self.button = None

        self._pressed_listener = None
        self._released_listener = None

        self.pos_x = 0.0
        self.pos_y = 0.0

        self.dx = 0.0
        self.dy = 0.0

        self.is_pressed = False

    def _on_button_down(self):
        self.is_pressed = True
        hive.internal(self).on_pressed()

    def _on_button_up(self):
        self.is_pressed = False
        hive.internal(self).on_released()

    def on_moved(self, leader):
        old_x = self.pos_x
        old_y = self.pos_y
        pos_x, pos_y = leader[0]

        self.pos_x = pos_x
        self.pos_y = pos_y

        self.dx = pos_x - old_x
        self.dy = pos_y - old_y

        hive.internal(self).on_moved()

    def get_pattern(self, state):
        return "mouse", state, self.button.lower()

    def set_add_handler(self, add_handler):
        moved_listener = EventHandler(self.on_moved, ("mouse", "move"))
        add_handler(moved_listener)

        self._pressed_listener = EventHandler(self._on_button_down, self.get_pattern("pressed"), mode='match')
        add_handler(self._pressed_listener)

        self._released_listener = EventHandler(self._on_button_up, self.get_pattern("released"), mode='match')
        add_handler(self._released_listener)

    def change_listener_buttons(self):
        self._pressed_listener.pattern = self.get_pattern("pressed")
        self._released_listener.pattern = self.get_pattern("released")


def build_mouse(cls, i, ex, args):
    ex.on_event = cls.set_add_handler.socket(identifier="event.add_handler")
    i.on_tick = hive.modifier()

    args.button = hive.parameter("str", "left", options={"left", "middle", "right"})

    i.button = hive.property(cls, "button", "str", args.button)
    ex.button = i.button.push_in

    i.on_button_changed = cls.change_listener_buttons
    i.push_button.pushed.connect(i.on_button_changed.trigger)

    i.on_pressed = hive.modifier()
    ex.on_pressed = i.on_pressed.trigger

    i.on_moved = hive.modifier()
    ex.on_moved = i.on_moved.trigger

    i.pos_x = hive.property(cls, "pos_x", "float")
    ex.x = i.pos_x.pull_out

    i.pos_y = hive.property(cls, "pos_y", "float")
    ex.y = i.pos_y.pull_out

    i.dx = hive.property(cls, "dx", "float")
    ex.dx = i.dx.pull_out

    i.dy = hive.property(cls, "dy", "float")
    ex.dy = i.dy.pull_out

    i.is_pressed = hive.property(cls, "is_pressed", "bool")
    ex.is_pressed = i.is_pressed.pull_out


Mouse = hive.hive("Mouse", build_mouse, drone_class=Mouse_)
