# import hive
#
# from .input_handler import InputHandler
# from .scene import Scene, Instantiator
#
# from ..mainloop import Mainloop as _Mainloop
# from ...event import EventHive, EventHandler
# from ...std import BuilderVariable
#
#
# class MainloopClass:
#
#     def __init__(self, max_framerate=60):
#         self.bge = __import__("bge")
#         self.input_handler = InputHandler()
#
#         self._hive = hive.get_run_hive()
#         self._read_event = None
#
#         self._scenes = {}
#         self.bind_id = None
#
#     def on_start(self):
#         self._read_event(("start",))
#
#         current_scene = self.bge.logic.getSceneList()[0]
#
#         # Instantiate and bind scene
#         self.bind_id = current_scene.name
#         self._hive._scene_instantiator.create()
#         self._scenes[self.bind_id] = added_hive = self._hive._scene_instantiator.last_created_hive
#         added_hive.hive._bge_scene = current_scene
#
#     def on_stop(self):
#         self._read_event(("stop",))
#
#     def on_tick(self):
#         self._read_event(("pre_tick",))
#
#         self.bge.logic.NextFrame()
#         self.input_handler.update_events()
#
#         self._read_event(("tick",))
#
#     def set_event_dispatcher(self, func):
#         # Dispatch events from input handler to event manager
#         self.input_handler.add_listener(func)
#         self._read_event = func
#
#     def add_handler(self, func):
#         # Add input handler
#         handler = EventHandler(self.stop, ("keyboard", "pressed", "ESCAPE"), mode='match')
#         func(handler)
#
#     def stop(self):
#         self._hive.stop()
#         self._read_event(("quit",))
#
#
# def build_mainloop(cls, i, ex, args):
#     i.event_manager = EventHive()
#
#     # Scene instantiator
#     i.scene_instantiator = Instantiator(forward_events='all')
#     i.scene_hive_class = BuilderVariable("class", Scene)
#     hive.connect(i.scene_hive_class, i.scene_instantiator.hive_class)
#
#     i.bind_id = hive.property(cls, "bind_id", ("str", "id"))
#     i.pull_bind_id = hive.pull_out(i.bind_id)
#     hive.connect(i.pull_bind_id, i.scene_instantiator.bind_id)
#
#     # Get read event
#     ex.get_dispatcher = hive.socket(cls.set_event_dispatcher, "event.process")
#     ex.get_add_handler = hive.socket(cls.add_handler, "event.add_handler")
#     ex.do_quit = hive.plugin(cls.stop, "quit")
#     ex.add_on_startup = hive.plugin(cls.on_start, identifier="on_started")
#     ex.add_on_stopped = hive.plugin(cls.on_stop, identifier="on_stopped")
#
#   #  i.startup_binder = StartupBinder()
#
#     i.on_tick = hive.triggerable(cls.on_tick)
#     hive.trigger(i.tick, i.on_tick)
#
#
# Mainloop = _Mainloop.extend("Mainloop", build_mainloop, builder_ builder_cls=MainloopClass)
