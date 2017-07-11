import hive


class DestroyClass:

    def __init__(self):
        self.entity_id = None

        self._destroy_entity = None
        self._get_entity_id = None

    def destroy(self):
        self._destroy_entity(self.entity_id)

    def do_get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id

    def set_destroy_entity(self, destroy_entity):
        self._destroy_entity = destroy_entity


def declare_destroy(meta_args):
    meta_args.bound = hive.parameter("bool", False)


def build_destroy(cls, i, ex, args, meta_args):
    """Destroy an entity"""
    i.trig_destroy = hive.triggerfunc(cls.destroy)
    i.do_destroy = hive.triggerable(i.trig_destroy)
    ex.destroy = hive.entry(i.do_destroy)

    if meta_args.bound:
        ex.get_bound = hive.socket(cls.set_get_entity_id, identifier="entity.get_bound")
        i.do_get_entity_id = hive.triggerable(cls.do_get_entity_id)

        hive.trigger(i.trig_destroy, i.do_get_entity_id, pretrigger=True)

    else:
        i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
        i.pull_entity_id = hive.pull_in(i.entity_id)
        ex.entity_id = hive.antenna(i.pull_entity_id)

        hive.trigger(i.trig_destroy, i.pull_entity_id, pretrigger=True)

    ex.get_destroy_entity = hive.socket(cls.set_destroy_entity, identifier="entity.destroy")


Destroy = hive.dyna_hive("Destroy", build_destroy, declare_destroy, drone_class=DestroyClass)
