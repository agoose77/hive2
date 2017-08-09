import hive

from .event import EventHandler


class ListenerClass:

    def __init__(self, event, mode):
        self.add_handler = None
        self.event = event
        self.mode = mode

        self.following_leader = None

    def on_event_leader(self, tail):
        self.following_leader = tail

        hive.internal(self).on_event()

    def on_event(self):
        hive.internal(self).on_event()

    def set_add_handler(self, add_handler):
        mode = self.mode

        if mode == "leader":
            callback = self.on_event_leader

        else:
            callback = self.on_event

        handler = EventHandler(callback, self.event, mode=mode)
        add_handler(handler)


def configure_listener(meta_args):
    meta_args.mode = hive.parameter("str", 'leader', options={'leader', 'match', 'trigger'})


def build_listener(i, ex, args, meta_args):
    """Tick event sensor, trigger on_tick every tick"""
    args.event = hive.parameter("str.event")
    i.listener_drone = hive.drone(ListenerClass, event=args.event, mode=meta_args.mode)

    i.on_event = hive.modifier()
    ex.on_event = i.on_event.triggered

    ex.get_add_handler = i.listener_drone.set_add_handler.socket("event.add_handler")

    if meta_args.mode == 'leader':
        i.after_leader = i.listener_drone.property('after_leader', 'tuple')
        ex.after_leader = i.after_leader.pull_out


Listener = hive.dyna_hive("Listener", build_listener, configurer=configure_listener)
