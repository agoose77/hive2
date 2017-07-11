import hive


class EntityTransformClass:

    def __init__(self):
        self._entities = {}

    def set_absolute_position(self, entity_id, position):
        entity = self._entities[entity_id]
        entity.set_pos(entity.get_top(), position)

    def set_relative_position(self, entity_id, other_entity_id, position):
        entity = self._entities[entity_id]
        other_entity = self._entities[other_entity_id]
        entity.set_pos(other_entity, position)

    def get_absolute_position(self, entity_id):
        entity = self._entities[entity_id]
        return entity.get_pos(entity.get_top())

    def get_relative_position(self, entity_id, other_entity_id):
        entity = self._entities[entity_id]
        other_entity = self._entities[other_entity_id]
        return entity.get_pos(other_entity)

    def set_absolute_orientation(self, entity_id, orientation):
        p, r, h = orientation
        entity = self._entities[entity_id]
        entity.set_hpr(entity.get_top(), h, p, r)

    def set_relative_orientation(self, entity_id, other_entity_id, orientation):
        p, r, h = orientation
        entity = self._entities[entity_id]
        other_entity = self._entities[other_entity_id]
        entity.set_pos(other_entity, h, p, r)

    def get_absolute_orientation(self, entity_id):
        entity = self._entities[entity_id]
        h, p, r = entity.get_hpr(entity.get_top())
        return p, r, h

    def get_relative_orientation(self, entity_id, other_entity_id):
        entity = self._entities[entity_id]
        other_entity = self._entities[other_entity_id]
        h, p, r = entity.get_hpr(other_entity)
        return p, r, h

    def set_parent(self, entity_id, parent):
        entity = self._entities[entity_id]
        entity.wrt_reparent_to(parent)

    def get_parent(self, entity_id):
        entity = self._entities[entity_id]
        return entity.getParent()

    def on_entity_created(self, entity_id, entity):
        self._entities[entity_id] = entity

    def on_entity_destroyed(self, entity_id, entity):
        del self._entities[entity_id]


def build_entity_transform(cls, i, ex, args):
    ex.set_abs_position = hive.plugin(cls.set_absolute_position, identifier="entity.position.set.absolute",
                                      export_to_parent=True)
    ex.get_abs_position = hive.plugin(cls.get_absolute_position, identifier="entity.position.get.absolute",
                                      export_to_parent=True)

    ex.set_rel_position = hive.plugin(cls.set_relative_position, identifier="entity.position.set.relative",
                                      export_to_parent=True)
    ex.get_rel_position = hive.plugin(cls.get_relative_position, identifier="entity.position.get.relative",
                                      export_to_parent=True)

    ex.set_abs_orientation = hive.plugin(cls.set_absolute_orientation, identifier="entity.orientation.set.absolute",
                                         export_to_parent=True)
    ex.get_abs_orientation = hive.plugin(cls.get_absolute_orientation, identifier="entity.orientation.get.absolute",
                                         export_to_parent=True)

    ex.set_rel_orientation = hive.plugin(cls.set_relative_orientation, identifier="entity.orientation.set.relative",
                                         export_to_parent=True)
    ex.get_rel_orientation = hive.plugin(cls.get_relative_orientation, identifier="entity.orientation.get.relative",
                                         export_to_parent=True)

    ex.set_parent = hive.plugin(cls.set_parent, identifier="entity.parent.set",
                                export_to_parent=True)
    ex.get_parent = hive.plugin(cls.get_parent, identifier="entity.parent.get",
                                export_to_parent=True)

    ex.on_entity_destroyed = hive.plugin(cls.on_entity_destroyed, "entity.on_destroyed", policy=hive.SingleRequired)
    ex.on_entity_created = hive.plugin(cls.on_entity_created, "entity.on_created", policy=hive.SingleRequired)


TransformManager = hive.hive("TransformManager", build_entity_transform, drone_class=EntityTransformClass)
