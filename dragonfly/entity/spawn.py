import hive

from .instantiate import Instantiator


class SpawnClass:

    def __init__(self):
        self._spawn_entity = None
        self._register_destructor = None

        self.entity_class_id = None
        self.entity_last_created_id = None

        self._hive = hive.get_run_hive()

    def set_spawn_entity(self, spawn_entity):
        self._spawn_entity = spawn_entity

    def do_spawn_entity(self):
        self.entity_last_created_id = self._spawn_entity(self.entity_class_id)

    def on_entity_process_created(self, process_id, entity_hive):
        destructor = lambda: self._hive._instantiator.stop_process.push(process_id)
        self._register_destructor(self.entity_last_created_id, destructor)

    def set_register_destructor(self, register_destructor):
        self._register_destructor = register_destructor


def declare_spawn(meta_args):
    meta_args.spawn_hive = hive.parameter("bool", True)


def build_spawn(cls, i, ex, args, meta_args):
    """Spawn an entity into the scene"""
    ex.get_spawn_entity = hive.socket(cls.set_spawn_entity, "entity.spawn")

    # Associate entity with this hive so it is safely destroyed
    ex.get_register_destructor = hive.socket(cls.set_register_destructor, "entity.register_destructor")
    ex.on_entity_process_instantiated = hive.plugin(cls.on_entity_process_created, "bind.on_created")

    i.entity_class_id = hive.property(cls, "entity_class_id", "str.entity_class_id")
    i.pull_class_id = hive.pull_in(i.entity_class_id)
    ex.entity_class_id = hive.antenna(i.pull_class_id)

    i.entity_last_created_id = hive.property(cls, "entity_last_created_id", "int.entity_id")

    if meta_args.spawn_hive:
        i.pull_entity_id = hive.pull_out(i.entity_last_created_id)
        ex.entity_last_created_id = hive.output(i.pull_entity_id)

    else:
        i.push_entity_id = hive.push_out(i.entity_last_created_id)
        ex.created_entity_id = hive.output(i.push_entity_id)

    i.do_spawn = hive.triggerable(cls.do_spawn_entity)
    i.trigger = hive.triggerfunc(i.do_spawn)
    i.on_triggered = hive.triggerable(i.trigger)

    hive.trigger(i.trigger, i.pull_class_id, pretrigger=True)

    # Process instantiator
    if meta_args.spawn_hive:
        i.instantiator = Instantiator(forward_events='all', bind_process='child')

        # Pull entity to instantiator
        hive.connect(i.pull_entity_id, i.instantiator.entity_id)

        # Get last created
        ex.hive_class = hive.antenna(i.instantiator.hive_class)
        ex.last_process_id = hive.output(i.instantiator.last_process_id)
        ex.stop_process = hive.antenna(i.instantiator.stop_process)
        ex.pause_events = hive.antenna(i.instantiator.pause_events)
        ex.resume_events = hive.antenna(i.instantiator.resume_events)

        # Instantiate
        hive.trigger(i.trigger, i.instantiator.create)

    else:
        # Finally push out entity
        hive.trigger(i.trigger, i.push_entity_id)

    ex.spawn = hive.entry(i.on_triggered)


Spawn = hive.dyna_hive("Spawn", build_spawn, declarator=declare_spawn, drone_class=SpawnClass)
