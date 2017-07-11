import hive


def id_generator():
    i = 0
    while True:
        yield i
        i += 1


class EntityManagerClass:

    def __init__(self):
        self._entities = {}
        self._factories = {}
        self._entity_hive_destructors = {}
        self._id_generator = id_generator()

        self._on_destroyed_callbacks = []
        self._on_created_callbacks = []

        self._hive = hive.get_run_hive()

    def spawn_entity(self, class_name):
        factory = self._factories[class_name]

        entity = factory()
        entity.reparent_to(base.render)

        entity_id = next(self._id_generator)
        self._entities[entity_id] = entity

        for callback in self._on_created_callbacks:
            callback(entity_id, entity)

        return entity_id

    def destroy_entity(self, entity_id):
        if entity_id in self._entity_hive_destructors:
            destructors = self._entity_hive_destructors.pop(entity_id)

            for callback in destructors:
                callback(entity_id)

        entity = self._entities.pop(entity_id)

        for callback in self._on_destroyed_callbacks:
            callback(entity_id, entity)

        entity.detach_node()

    def set_tag(self, entity_id, name, value):
        entity = self._entities[entity_id]
        entity.set_python_tag(name, value)

    def get_tag(self, entity_id, name):
        entity = self._entities[entity_id]
        return entity.get_python_tag(name)

    def set_visibility(self, entity_id, visible):
        entity = self._entities[entity_id]

        if visible:
            entity.show()

        else:
            entity.hide()

    def get_visibility(self, entity_id):
        entity = self._entities[entity_id]
        return entity.is_hidden()

    def register_hive_destructor(self, entity, destructor):
        self._entity_hive_destructors.setdefault(entity, []).append(destructor)

    def register_entity_factory(self, template_name, factory):
        self._factories[template_name] = factory

    def on_entity_destroyed(self, on_destroyed):
        self._on_destroyed_callbacks.append(on_destroyed)

    def on_entity_created(self, on_created):
        self._on_created_callbacks.append(on_created)


def build_entity(cls, i, ex, args):
    ex.set_tag = hive.plugin(cls.set_tag, identifier="entity.tag.set", export_to_parent=True)
    ex.get_tag = hive.plugin(cls.get_tag, identifier="entity.tag.get", export_to_parent=True)
    ex.set_visibility = hive.plugin(cls.set_visibility, identifier="entity.visibility.set", export_to_parent=True)
    ex.get_visibility = hive.plugin(cls.get_visibility, identifier="entity.visibility.get", export_to_parent=True)
    ex.spawn_entity = hive.plugin(cls.spawn_entity, identifier="entity.spawn", export_to_parent=True)
    ex.destroy_entity = hive.plugin(cls.destroy_entity, identifier="entity.destroy", export_to_parent=True)
    ex.register_entity_factory = hive.plugin(cls.register_entity_factory, "entity.register_factory",
                                             export_to_parent=True)
    ex.register_hive_destructor = hive.plugin(cls.register_hive_destructor, "entity.register_destructor",
                                              export_to_parent=True)

    # Push out entity destroyed
    ex.on_entity_destroyed = hive.socket(cls.on_entity_destroyed, "entity.on_destroyed", policy=hive.MultipleOptional,
                                         export_to_parent=True)
    ex.on_entity_created = hive.socket(cls.on_entity_created, "entity.on_created", policy=hive.MultipleOptional,
                                       export_to_parent=True)


EntityManager = hive.hive("EntitySystem", build_entity, drone_class=EntityManagerClass)
