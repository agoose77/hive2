import hive

from .event import EventHandler


class _ListenerCls:

    @hive.types(event="tuple.event", mode="str")
    def __init__(self, event=()):
        self.add_handler = None
        self.event = event

        self._hive = hive.get_run_hive()
        self._mode = self._hive._hive_object._hive_meta_args_frozen.mode

        self.following_leader = None

    def on_event_leader(self, tail):
        self.following_leader = tail

        self._hive._on_event()

    def on_event(self):
        self._hive._on_event()

    def set_add_handler(self, add_handler):
        mode = self._mode

        if mode == "leader":
            callback = self.on_event_leader

        else:
            callback = self.on_event

        handler = EventHandler(callback, self.event, mode=mode)
        add_handler(handler)


def declare_listener(meta_args):
    meta_args.mode = hive.parameter("str", 'leader', options={'leader', 'match', 'trigger'})


def build_listener(cls, i, ex, args, meta_args):
    """Tick event sensor, trigger on_tick every tick"""
    i.on_event = hive.triggerfunc()
    ex.on_event = hive.hook(i.on_event)

    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")

    if meta_args.mode == 'leader':
        i.after_leader = hive.property(cls, 'after_leader', 'tuple')
        i.pull_after_leader = hive.pull_out(i.after_leader)
        ex.after_leader = hive.output(i.pull_after_leader)


Listener = hive.dyna_hive("Listener", build_listener, drone_class=_ListenerCls, declarator=declare_listener)
