import hive


def match_leader(event, leader):
    event_leader = event[:len(leader)]

    if event_leader != leader:
        return None

    return event[len(leader):]


class EventHandler:

    def __init__(self, callback, pattern=None, priority=0, mode='leader'):
        self.callback = callback
        self.pattern = pattern
        self.priority = priority
        self.mode = mode

    def __lt__(self, other):
        return self.priority < other.priority

    def __call__(self, event):
        pattern = self.pattern

        if not pattern:
            self.callback(event)

        else:
            mode = self.mode
            if mode == "leader":
                tail = match_leader(event, pattern)

                if tail is not None:
                    self.callback(tail)

            elif mode == "match":
                if event == pattern:
                    self.callback()

            elif mode == "trigger":
                if match_leader(event, pattern) is not None:
                    self.callback()


class EventDispatcher:

    def __init__(self):
        self._handlers = []

    @property
    def has_handlers(self):
        return bool(self._handlers)

    def add_handler(self, handler):
        self._handlers.append(handler)
        self._handlers.sort()

    def remove_handler(self, handler):
        self._handlers.remove(handler)
        self._handlers.sort()

    def clear_handlers(self):
        self._handlers.clear()

    def handle_event(self, event):
        for handler in self._handlers:
            handler(event)


class EventHiveClass(EventDispatcher):

    def __init__(self):
        super(EventHiveClass, self).__init__()

        self.pushed_event = None

    def on_started(self):
        self.handle_event(("start",))

    def on_stopped(self):
        self.handle_event(("stop",))

    def on_event_in(self):
        self.handle_event(self.pushed_event)


def event_builder(cls, i, ex, args):
    ex.add_handler = hive.plugin(cls.add_handler, identifier="event.add_handler", export_to_parent=True)
    ex.remove_handler = hive.plugin(cls.remove_handler, identifier="event.remove_handler", export_to_parent=True)
    ex.read_event = hive.plugin(cls.handle_event, identifier="event.process", export_to_parent=True)

    # Send startup and stop events
    ex.on_stopped = hive.plugin(cls.on_stopped, identifier="on_stopped")
    ex.on_started = hive.plugin(cls.on_started, identifier="on_started")

    # Allow events to be pushed in
    i.event_in = hive.property(cls, 'pushed_event', 'tuple')
    i.push_event = hive.push_in(i.event_in)
    ex.event_in = hive.antenna(i.push_event)

    i.on_event_in = hive.triggerable(cls.on_event_in)
    hive.trigger(i.push_event, i.on_event_in)


EventManager = hive.hive("EventManager", event_builder, EventHiveClass)


