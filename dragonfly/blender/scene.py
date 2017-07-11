import hive

from ..bind import Instantiator as _Instantiator
from ..event import bind_info as event_bind_info

bind_infos = (event_bind_info,)


def build_scene_instantiator(i, ex, args, meta_args):
    bind_bases = tuple((b_i.environment_hive for b_i in bind_infos if b_i.is_enabled(meta_args)))

    # Update bind environment to use new bases
    environment_class = i.bind_meta_class.start_value
    i.bind_meta_class.start_value = environment_class.extend("SceneBindEnvironment", bases=tuple(bind_bases))


Instantiator = _Instantiator.extend("Instantiator", build_scene_instantiator,
                                    bases=tuple(b_i.bind_hive for b_i in bind_infos))


class SceneClass:

    def __init__(self):
        self._entities = {}
        self.scene = None

    def get_entity_id(self, identifier):
        return self._entities[identifier]

    def get_position_absolute(self, entity):
        return tuple(entity.worldPosition)

    def get_orientation_absolute(self, entity):
        return tuple(entity.worldOrientation.to_quaternion())

    def get_position_relative(self, entity, other):
        return tuple(entity.worldPosition - other.worldPosition)

    def get_orientation_relative(self, entity, other):
        return tuple(entity.worldOrientation.to_quaternion().rotation_difference(other.worldPosition.to_quaternion()))

    def spawn_entity(self, class_name, identifier):
        entity = self.scene.addObject(class_name, 'Empty')
      #  entity.worldTransform = entity.worldTransform.inverted() * entity.worldTransform

        self._entities[identifier] = entity
        return entity

    def get_scene(self):
        return self.scene


def build_scene(cls, i, ex, args):
    i.bge_scene = hive.property(cls, "scene")

    ex.get_entity_id = hive.plugin(cls.get_entity_id, identifier="entity.get")
    ex.get_position_absolute = hive.plugin(cls.get_position_absolute, identifier="entity.position.absolute.get")
    ex.get_position_relative = hive.plugin(cls.get_position_relative, identifier="entity.position.relative.get")
    ex.get_orientation_absolute = hive.plugin(cls.get_orientation_absolute, identifier="entity.orientation.absolute.get")
    ex.get_orientation_relative = hive.plugin(cls.get_orientation_relative, identifier="entity.orientation.relative.get")
    ex.spawn_entity = hive.plugin(cls.spawn_entity, identifier="entity.spawn")
    ex.get_scene = hive.plugin(cls.get_scene, identifier="entity.get_current")

    import dragonfly
    ex.on_tick = dragonfly.event.Tick()

    def f(self):
        print("I")
        if not hasattr(self, 'a'):
            self.a = 1

            self.spawn_entity.plugin()("Cube", "c1")

    i.mod_tick = hive.modifier(f)
    hive.trigger(ex.on_tick, i.mod_tick)


Scene = hive.hive("Scene", build_scene, drone_class=SceneClass)
