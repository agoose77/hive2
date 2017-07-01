import dragonfly
import hive

import hive_editor

from hive_editor.debugging.network import NetworkDebugContext
from panda_project.launch import Launch


def create_cube():
    entity = loader.loadModel("panda_project/cube.egg")
    from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode
    from panda3d.core import NodePath

    shape = BulletBoxShape((0.5, 0.5, 0.5))

    node = BulletRigidBodyNode('Box')
    node.setMass(1.0)
    node.addShape(shape)

    nodepath = NodePath(node)
    entity.wrt_reparent_to(nodepath)

    return nodepath


class MyHiveClass:

    def __init__(self, tick_rate=60):
        self._factories = {'cube': create_cube}

    def set_register_factory(self, register_factory):
        for name, factory in self._factories.items():
            register_factory(name, factory)


def build_my_hive(cls, i, ex, args):
    ex.get_register_template = hive.socket(cls.set_register_factory, "entity.register_factory")
    i.main_hive = Launch()


MyHive = dragonfly.panda3d.Mainloop.extend("MyHive", build_my_hive, builder_cls=MyHiveClass)

DO_DEBUG = False

if DO_DEBUG:
    debug_context = NetworkDebugContext()
    with debug_context:
        my_hive = MyHive()
        my_hive.run()
else:
    my_hive = MyHive()
    my_hive.run()