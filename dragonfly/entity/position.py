import hive


class PositionClass:

    def __init__(self):
        self.position = None

        self.entity_id = None
        self.other_entity_id = None

        self._get_position = None
        self._get_entity_id = None

        self._set_position = None
        self._set_entity = None

    def do_get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def do_get_position(self):
        self.position = self._get_position(self.entity_id)

    def do_get_relative_position(self):
        self.position = self._get_position(self.entity_id, self.other_entity_id)

    def do_set_position(self):
        self._set_position(self.entity_id, self.position)

    def do_set_relative_position(self):
        self._set_position(self.entity_id, self.other_entity_id, self.position)

    def set_get_position(self, get_position):
        self._get_position = get_position

    def set_set_position(self, set_position):
        self._set_position = set_position

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def declare_position(meta_args):
    meta_args.bound = hive.parameter("bool", True)
    meta_args.coordinate_system = hive.parameter("str", 'absolute', options={'absolute', 'relative'})
    meta_args.mode = hive.parameter("str", "get", options={"get", "set"})


def build_position(cls, i, ex, args, meta_args):
    """Access to entity position API"""
    coordinate_system = meta_args.coordinate_system

    i.position = hive.property(cls, "position", "vector")

    if meta_args.bound:
        ex.get_bound = hive.socket(cls.set_get_entity_id, identifier="entity.get_bound")
        i.do_get_entity_id = hive.triggerable(cls.do_get_entity_id)

    else:
        i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
        i.pull_entity_id = hive.pull_in(i.entity_id)
        ex.entity_id = hive.antenna(i.pull_entity_id)

    if coordinate_system == 'relative':
        i.other_entity_id = hive.property(cls, "other_entity_id", "int.entity_id")
        i.pull_other_entity_id = hive.pull_in(i.other_entity_id)
        ex.other_entity_id = hive.antenna(i.pull_other_entity_id)

    if meta_args.mode == "get":
        i.pull_position = hive.pull_out(i.position)
        ex.position = hive.output(i.pull_position)

    else:
        i.push_position = hive.push_in(i.position)
        ex.position = hive.antenna(i.push_position)

    if meta_args.mode == "get":
        if coordinate_system == 'absolute':
            ex.get_get_position = hive.socket(cls.set_get_position, identifier="entity.position.get.absolute")
            i.do_get_position = hive.triggerable(cls.do_get_position)

        else:
            ex.get_get_position = hive.socket(cls.set_get_position, identifier="entity.position.get.relative")
            i.do_get_position = hive.triggerable(cls.do_get_relative_position)
            hive.trigger(i.pull_position, i.pull_other_entity_id, pretrigger=True)

        if meta_args.bound:
            hive.trigger(i.pull_position, i.do_get_entity_id, pretrigger=True)

        else:
            hive.trigger(i.pull_position, i.pull_entity_id, pretrigger=True)

        hive.trigger(i.pull_position, i.do_get_position, pretrigger=True)

    else:
        if coordinate_system == 'absolute':
            ex.get_set_position = hive.socket(cls.set_set_position, identifier="entity.position.set.absolute")
            i.do_set_position = hive.triggerable(cls.do_set_position)

        else:
            ex.get_set_position = hive.socket(cls.set_set_position, identifier="entity.position.set.relative")
            i.do_set_position = hive.triggerable(cls.do_set_relative_position)
            hive.trigger(i.push_position, i.pull_other_entity_id)

        if meta_args.bound:
            hive.trigger(i.push_position, i.do_get_entity_id)

        else:
            hive.trigger(i.push_position, i.pull_entity_id)

        hive.trigger(i.push_position, i.do_set_position)


Position = hive.dyna_hive("Position", build_position, declare_position, drone_class=PositionClass)