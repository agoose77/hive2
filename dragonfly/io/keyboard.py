import hive
import string

from ..event import EventHandler

_SPECIAL_KEYCODES = ['left_control', 'left_shift', 'right_alt', 'right_control', 'left_alt', 'space', 'escape', 'home',
                     'insert', 'backspace', 'shift', 'right_shift', 'page_up', 'page_down', 'tab', 'delete', 'end',
                     'enter', 'arrow_up', 'arrow_down', 'arrow_left', 'arrow_right']

ALL_KEYCODES = list(string.ascii_lowercase)
ALL_KEYCODES.extend(string.digits)
ALL_KEYCODES.extend(string.punctuation)
ALL_KEYCODES.extend(_SPECIAL_KEYCODES)


class Keyboard_:

    def __init__(self):
        self._hive = hive.get_run_hive()
        self.key = None

        self._pressed_listener = None
        self._released_listener = None

        self.key_pressed = None
        self.key_released = None

        self.is_pressed = False

    def _on_single_key_pressed(self):
        self.is_pressed = True
        self._hive._on_pressed()

    def _on_single_key_released(self):
        self.is_pressed = False
        self._hive._on_released()

    def _get_pattern(self, state):
        return "keyboard", state, self.key

    def add_single_listener(self, add_handler):
        self._pressed_listener = EventHandler(self._on_single_key_pressed, self._get_pattern("pressed"), mode='match')
        add_handler(self._pressed_listener)

        self._released_listener = EventHandler(self._on_single_key_released, self._get_pattern("released"), mode='match')
        add_handler(self._released_listener)

    def add_any_listener(self, add_handler):
        self._pressed_listener = EventHandler(self._on_key_pressed, ("keyboard", "pressed"))
        add_handler(self._pressed_listener)

        self._released_listener = EventHandler(self._on_key_released, ("keyboard", "released"))
        add_handler(self._released_listener)

    def _on_key_pressed(self, trailing):
        self.key_pressed = trailing[0]
        self._hive.key_pressed.push()

    def _on_key_released(self, trailing):
        self.key_released = trailing[0]
        self._hive.key_released.push()

    def change_listener_keys(self):
        self._pressed_listener.pattern = self._get_pattern("pressed")
        self._released_listener.pattern = self._get_pattern("released")


def configure_keyboard(meta_args):
    meta_args.mode = hive.parameter("str", 'single key', options={'single key', 'any key'})


def build_keyboard(cls, i, ex, args, meta_args):
    """Listen for keyboard event"""
    if meta_args.mode == 'single key':
        ex.on_event = hive.socket(cls.add_single_listener, identifier="event.add_handler")

        args.key = hive.parameter("str.keycode", "w")
        i.key = hive.property(cls, "key", "str.keycode", args.key)

        i.push_key = hive.push_in(i.key)
        ex.key = hive.antenna(i.push_key)

        i.on_key_changed = hive.triggerable(cls.change_listener_keys)
        hive.trigger(i.push_key, i.on_key_changed)

        i.on_pressed = hive.triggerfunc()
        ex.on_pressed = hive.hook(i.on_pressed)

        i.on_released = hive.triggerfunc()
        ex.on_released = hive.hook(i.on_released)

        i.is_pressed = hive.property(cls, "is_pressed", "bool")
        i.pull_is_pressed = hive.pull_out(i.is_pressed)
        ex.is_pressed = hive.output(i.pull_is_pressed)

    else:
        ex.on_event = hive.socket(cls.add_any_listener, identifier="event.add_handler")

        i.key_pressed = hive.property(cls, 'key_pressed', data_type='str.keycode')
        i.pull_key_pressed = hive.push_out(i.key_pressed)
        ex.key_pressed = hive.output(i.pull_key_pressed)

        i.key_released = hive.property(cls, 'key_released', data_type='str.keycode')
        i.pull_key_released = hive.push_out(i.key_released)
        ex.key_released = hive.output(i.pull_key_released)


Keyboard = hive.dyna_hive("Keyboard", build_keyboard, configurer=configure_keyboard, drone_class=Keyboard_)
