import hive


class _PhysicsManagerClass:

    def __init__(self):
        from panda3d.bullet import BulletWorld
        self._world = BulletWorld()
        self._world.set_gravity(0, 0, -9.807)

        self.tick_rate = None
        self.time = 0.0

        self._rigid_bodies = {}

    def update(self):
        self._world.do_physics(1./self.tick_rate)
        self.time += 1./self.tick_rate

    def get_linear_velocity(self, entity_id):
        node = self._rigid_bodies[entity_id]
        return tuple(node.get_linear_velocity())

    def set_linear_velocity(self, entity_id, velocity):
        node = self._rigid_bodies[entity_id]
        return node.set_linear_velocity(*velocity)

    def get_angular_velocity(self, entity_id):
        node = self._rigid_bodies[entity_id]
        return tuple(node.get_angular_velocity())

    def set_angular_velocity(self, entity_id, velocity):
        node = self._rigid_bodies[entity_id]
        return node.set_angular_velocity(*velocity)

    def on_entity_created(self, entity_id, entity):
        parent = entity.get_parent()
        nodepath = parent.find("+BulletRigidBodyNode")
        self._world.attach_rigid_body(nodepath.node())

    def on_entity_destroyed(self, entity):
        parent = entity.get_parent()
        nodepath = parent.find("+BulletRigidBodyNode")
        self._world.remove_rigid_body(nodepath.node())


def build_physics_manager(cls, i, ex, args):
    i.tick_rate = hive.property(cls, "tick_rate", 'int')
    i.pull_tick_rate = hive.pull_in(i.tick_rate)
    ex.tick_rate = hive.antenna(i.pull_tick_rate)

    i.do_update = hive.triggerfunc(cls.update)
    hive.trigger(i.do_update, i.pull_tick_rate, pretrigger=True)

    i.on_tick = hive.triggerable(i.do_update)
    ex.tick = hive.entry(i.on_tick)

    ex.on_entity_destroyed = hive.plugin(cls.on_entity_destroyed, "entity.on_destroyed", policy=hive.SingleRequired)
    ex.on_entity_created = hive.plugin(cls.on_entity_created, "entity.on_created", policy=hive.SingleRequired)

    ex.get_angular_velocity = hive.plugin(cls.get_angular_velocity, "entity.angular_velocity.get",
                                          export_to_parent=True)
    ex.set_angular_velocity = hive.plugin(cls.set_angular_velocity, "entity.angular_velocity.set",
                                          export_to_parent=True)

    ex.get_linear_velocity = hive.plugin(cls.get_linear_velocity, "entity.angular_velocity.get", export_to_parent=True)
    ex.set_linear_velocity = hive.plugin(cls.set_linear_velocity, "entity.angular_velocity.set", export_to_parent=True)


PhysicsManager = hive.hive("PhysicsManager", build_physics_manager, drone_class=_PhysicsManagerClass)
