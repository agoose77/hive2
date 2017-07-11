import hive

from .input_handler import InputHandler
from .entity_manager import EntityManager
from .physics_manager import PhysicsManager
from .transform_manager import TransformManager

from ..app import Mainloop as _Mainloop
from ..event import EventManager, EventHandler


class MainloopClass:

    def __init__(self, tick_rate):
        from direct.showbase.ShowBase import ShowBase

        self._base = ShowBase()
        self._hive = hive.get_run_hive()

        self._read_event = None
        self._add_handler = None

    def on_tick(self):
        base.taskMgr.step()

        self._read_event(("tick",))

    def set_event_dispatcher(self, func):
        # Dispatch events from input handler to event manager
        self._read_event = func

    def set_add_handler(self, add_handler):
        # Add input handler
        self._add_handler = add_handler

    def on_started(self):
        handler = EventHandler(self._hive.stop, ("keyboard", "pressed", "escape"), mode='match')
        self._add_handler(handler)


def build_mainloop(cls, i, ex, args):
    i.event_manager = EventManager(export_namespace=True)
    i.input_manager = InputHandler(export_namespace=True)
    i.entity_manager = EntityManager(export_namespace=True)
    i.transform_manager = TransformManager(export_namespace=True)
    i.physics_manager = PhysicsManager(export_namespace=True)

    # Connect input manager
    hive.connect(i.tick, i.input_manager.update)
    hive.connect(i.input_manager.event, i.event_manager.event_in)

    # Connect physics
    hive.connect(i.tick, i.physics_manager.tick)
    hive.connect(i.pull_tick_rate, i.physics_manager.tick_rate)

    # Send tick event and step Panda
    i.on_tick = hive.triggerable(cls.on_tick)
    hive.trigger(i.tick, i.on_tick)

    # Get read event
    ex.get_dispatcher = hive.socket(cls.set_event_dispatcher, "event.process")
    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")

    # Add startup and stop callbacks
    ex.main_on_started = hive.plugin(cls.on_started, identifier="on_started")


Mainloop = _Mainloop.extend("Mainloop", build_mainloop, drone_class=MainloopClass)