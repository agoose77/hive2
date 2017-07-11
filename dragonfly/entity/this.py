import hive


class ThisClass:

    def __init__(self):
        self._get_entity_id = None
        self.entity_id = None

    def get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def build_this(cls, i, ex, args):
    """Access to current bound entity"""
    ex.get_bound_entity = hive.socket(cls.set_get_entity_id, identifier="entity.get_bound")

    i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
    i.pull_entity_id = hive.pull_out(i.entity_id)
    ex.entity_id = hive.output(i.pull_entity_id)

    i.do_get_entity_id = hive.triggerable(cls.get_entity_id)
    hive.trigger(i.pull_entity_id, i.do_get_entity_id, pretrigger=True)


This = hive.hive("This", build_this, drone_class=ThisClass)
