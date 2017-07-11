# from gui.models.model import Hivemap
#
# import hive
# from gui.code_generator import class_from_hivemap
#
#
# class BoundHiveContainer:
#
#     def __init__(self, entity):
#         self.entity = entity
#
#
# class _StartupBinderCls:
#
#     def __init__(self):
#         self.bge = __import__("bge")
#         self.scene = self.bge.logic.getCurrentScene()
#
#         self.path_to_hive_cls = {}
#
#     def set_add_startup_callback(self, func):
#         func(self.on_startup)
#
#     def on_startup(self):
#         for obj in self.scene.objects:
#             try:
#                 hivemap_path = obj['hivemap_path']
#
#             except KeyError:
#                 continue
#
#             try:
#                 hive_cls = self.path_to_hive_cls[hivemap_path]
#
#             except KeyError:
#                 with open(obj['hivemap']) as f:
#                     data = f.read()
#
#                 hivemap = Hivemap(data)
#                 hive_cls = class_from_hivemap("<hivemap>", hivemap)
#                 self.path_to_hive_cls[hivemap_path] = hive_cls
#
#
# def build_startup_binder(cls, i, ex, args):
#     ex.get_add_startup_callback = hive.socket(cls.set_add_startup_callback, "callback.startup")
#
#
# StartupBinder = hive.hive("StartupBinder", builder=build_startup_binder, drone_class=_StartupBinderCls)
