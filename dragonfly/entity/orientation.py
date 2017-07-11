import hive


class OrientationClass:

    def __init__(self):
        self.orientation = None

        self.entity_id = None
        self.other_entity_id = None

        self._get_orientation = None
        self._get_entity_id = None

        self._set_orientation = None
        self._set_entity = None

    def do_get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def do_get_orientation(self):
        self.orientation = self._get_orientation(self.entity_id)

    def do_get_relative_orientation(self):
        self.orientation = self._get_orientation(self.entity_id, self.other_entity_id)

    def do_set_orientation(self):
        self._set_orientation(self.entity_id, self.orientation)

    def do_set_relative_orientation(self):
        self._set_orientation(self.entity_id, self.other_entity_id, self.orientation)

    def set_get_orientation(self, get_orientation):
        self._get_orientation = get_orientation

    def set_set_orientation(self, set_orientation):
        self._set_orientation = set_orientation

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def declare_orientation(meta_args):
    meta_args.bound = hive.parameter("bool", True)
    meta_args.coordinate_system = hive.parameter("str", 'absolute', options={'absolute', 'relative'})
    meta_args.mode = hive.parameter("str", "get", options={"get", "set"})


def build_orientation(cls, i, ex, args, meta_args):
    """Access to entity orientation API"""
    coordinate_system = meta_args.coordinate_system

    i.orientation = hive.property(cls, "orientation", "euler")

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
        i.pull_orientation = hive.pull_out(i.orientation)
        ex.orientation = hive.output(i.pull_orientation)

    else:
        i.push_orientation = hive.push_in(i.orientation)
        ex.orientation = hive.antenna(i.push_orientation)

    if meta_args.mode == "get":
        if coordinate_system == 'absolute':
            ex.get_get_orientation = hive.socket(cls.set_get_orientation, identifier="entity.orientation.get.absolute")

            i.do_get_orientation = hive.triggerable(cls.do_get_orientation)

        else:
            ex.get_get_orientation = hive.socket(cls.set_get_orientation, identifier="entity.orientation.get.relative")
            i.do_get_orientation = hive.triggerable(cls.do_get_relative_orientation)
            hive.trigger(i.pull_orientation, i.pull_other_entity_id, pretrigger=True)

        if meta_args.bound:
            hive.trigger(i.pull_orientation, i.do_get_entity_id, pretrigger=True)

        else:
            hive.trigger(i.pull_orientation, i.pull_entity_id, pretrigger=True)

        hive.trigger(i.pull_orientation, i.do_get_orientation, pretrigger=True)

    else:
        if coordinate_system == 'absolute':
            ex.get_set_orientation = hive.socket(cls.set_set_orientation, identifier="entity.orientation.set.absolute")
            i.do_set_orientation = hive.triggerable(cls.do_set_orientation)

        else:
            ex.get_set_orientation = hive.socket(cls.set_set_orientation, identifier="entity.orientation.set.relative")
            i.do_set_orientation = hive.triggerable(cls.do_set_relative_orientation)
            hive.trigger(i.push_orientation, i.pull_other_entity_id)

        if meta_args.bound:
            hive.trigger(i.push_orientation, i.do_get_entity_id)

        else:
            hive.trigger(i.push_orientation, i.pull_entity_id)

        hive.trigger(i.push_orientation, i.do_set_orientation)


Orientation = hive.dyna_hive("Orientation", build_orientation, declare_orientation, drone_class=OrientationClass)