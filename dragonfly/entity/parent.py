import hive


class ParentClass:

    def __init__(self):
        self._set_parent_id = None
        self._get_parent_id = None
        self._get_entity_id = None

        self.entity_id = None
        self.parent_id = None

    def set_parent_id(self):
        self._set_parent_id(self.entity_id, self.parent_id)

    def get_parent_id(self):
        self.parent_id = self._get_parent_id(self.entity_id)

    def get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def set_set_parent(self, set_parent_id):
        self._set_parent_id = set_parent_id

    def set_get_parent(self, get_parent):
        self._get_parent_id = get_parent

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def declare_parent(meta_args):
    meta_args.mode = hive.parameter("str", "get", {'get', 'set'})
    meta_args.bound = hive.parameter("bool", True)


def build_parent(cls, i, ex, args, meta_args):
    """Set/Get entity parent"""
    ex.get_get_parent = hive.socket(cls.set_get_parent, identifier="entity.parent.get")
    ex.get_set_parent = hive.socket(cls.set_set_parent, identifier="entity.parent.set")

    i.parent_id = hive.property(cls, "parent_id", "int.entity_id")

    if meta_args.bound:
        ex.get_bound = hive.socket(cls.set_get_entity_id, identifier="entity.get_bound")
        i.do_get_bound_entity_id = hive.triggerable(cls.get_entity_id)

    else:
        i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
        i.pull_entity_id = hive.pull_in(i.entity_id)
        ex.entity_id = hive.antenna(i.pull_entity_id)
        i.do_get_bound_entity_id = hive.triggerable(i.pull_entity_id)

    if meta_args.mode == "get":
        i.pull_parent_id = hive.pull_out(i.parent_id)
        ex.parent_id = hive.output(i.pull_parent_id)

        i.get_parent_id = hive.triggerable(cls.get_parent_id)
        hive.trigger(i.pull_parent_id, i.do_get_bound_entity_id, pretrigger=True)
        hive.trigger(i.pull_parent_id, i.get_parent_id, pretrigger=True)

    else:
        i.push_parent_id = hive.push_in(i.parent_id_id)
        ex.parent_id = hive.antenna(i.push_parent_id)

        i.set_parent = hive.triggerable(cls.set_parent)
        hive.trigger(i.push_parent_id, i.do_get_bound_entity_id)
        hive.trigger(i.push_parent_id, i.set_parent)


Parent = hive.dyna_hive("Parent", build_parent, declare_parent, drone_class=ParentClass)
