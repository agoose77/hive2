import hive

from ..event import EventHandler


class _CollisionClass:

    def __init__(self):
        self._hive = hive.get_run_hive()
        self._entity = None

        self.hit_entity = None
        self.hit_position = None
        self.hit_impulse = None
        self.hit_normal = None

    def _on_collision(self, tail):
        collision_info = tail[0]

        self.hit_entity = collision_info.hit_entity
        self.hit_position = collision_info.hit_normal
        self.hit_impulse = collision_info.hit_impulse
        self.hit_normal = collision_info.hit_normal

        self._hive.on_collided()

    def set_get_entity_id(self, get_entity_id):
        self._entity = get_entity_id()

    def set_add_handler(self, add_handler):
        handler = EventHandler(self._on_collision, ('collision', self._entity), mode="leader")
        add_handler(handler)


def build_collision(cls, i, ex, args):
    """Interface to collision events for bound hive"""
    i.hit_entity = hive.property(cls, "hit_entity_id", "int.entity_id")
    i.hit_position = hive.property(cls, "hit_position", "vector")
    i.hit_normal = hive.property(cls, "hit_normal", "vector")
    i.hit_impulse = hive.property(cls, "hit_impulse", "vector")

    i.pull_hit_entity = hive.pull_out(i.hit_entity)
    i.pull_hit_position = hive.pull_out(i.hit_position)
    i.pull_hit_normal = hive.pull_out(i.hit_normal)
    i.pull_hit_impulse = hive.pull_out(i.hit_impulse)

    ex.hit_entity = hive.output(i.pull_hit_entity)
    ex.hit_position = hive.output(i.pull_hit_position)
    ex.hit_normal = hive.output(i.pull_hit_normal)
    ex.hit_impulse = hive.output(i.pull_hit_impulse)

    i.on_collided = hive.triggerfunc()
    ex.on_collided = hive.hook(i.on_collided)

    ex.get_get_entity_id = hive.socket(cls.set_get_entity_id, "entity.get_bound")
    ex.get_add_handler = hive.socket(cls.set_add_handler, "event.add_handler")


Collision = hive.hive("Collision", build_collision, drone_class=_CollisionClass)
