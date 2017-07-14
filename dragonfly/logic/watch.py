import hive

from dragonfly.event import EventHandler


class WatchClass:
    def __init__(self):
        self.current_value = None
        self._last_value = None

    def _on_tick(self):
        hive.internal(self).value()
        self.compare_values()

    def compare_values(self):
        current_value = self.current_value
        last_value, self._last_value = self._last_value, current_value

        if current_value != last_value:
            hive.internal(self).on_changed()

    def set_add_handler(self, add_handler):
        handler = EventHandler(self._on_tick, ("tick",), mode='match')
        add_handler(handler)


def configure_watch(meta_args):
    meta_args.data_type = hive.parameter("str", "int")
    meta_args.mode = hive.parameter("str", "pull", {"push", "pull"})


def build_watch(cls, i, ex, args, meta_args):
    """Watch value and indicate when it is changed.

    Uses a tick callback.
    """
    args.start_value = hive.parameter(meta_args.data_type, None)
    i.value = hive.property(cls, "current_value", meta_args.data_type, args.start_value)

    if meta_args.mode == 'pull':
        i.value_in = i.value.pull_in

    else:
        i.value_in = i.value.push_in

    i.on_changed = hive.modifier()

    ex.value = i.value_in
    ex.on_changed = i.on_changed.trigger

    if meta_args.mode == 'pull':
        ex.get_add_handler = cls.set_add_handler.socket(identifier="event.add_handler")

    else:
        i.value_in.pushed.connect(cls.compare_values.trigger)


Watch = hive.dyna_hive("Watch", build_watch, configure_watch, drone_class=WatchClass)
