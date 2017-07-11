import hive


class AngularClass:

    def __init__(self):
        self.angular = None

        self.entity_id = None
        self.other_entity_id = None

        self._get_angular = None
        self._get_entity_id = None

        self._set_angular = None
        self._set_entity = None

    def do_get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def do_get_angular(self):
        self.angular = self._get_angular(self.entity_id)

    def do_get_relative_angular(self):
        self.angular = self._get_angular(self.entity_id, self.other_entity_id)

    def do_set_angular(self):
        self._set_angular(self.entity_id, self.angular)

    def do_set_relative_angular(self):
        self._set_angular(self.entity_id, self.other_entity_id, self.angular)

    def set_get_angular(self, get_angular):
        self._get_angular = get_angular

    def set_set_angular(self, set_angular):
        self._set_angular = set_angular

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def declare_angular(meta_args):
    meta_args.bound = hive.parameter("bool", True)
    meta_args.coordinate_system = hive.parameter("str", 'absolute', options={'absolute'}) #TODO add relative support
    meta_args.mode = hive.parameter("str", "get", options={"get", "set"})


def build_angular(cls, i, ex, args, meta_args):
    """Access to entity angular API"""
    coordinate_system = meta_args.coordinate_system
    i.angular = hive.property(cls, "angular", "vector")

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
        i.pull_angular = hive.pull_out(i.angular)
        ex.angular = hive.output(i.pull_angular)

    else:
        i.push_angular = hive.push_in(i.angular)
        ex.angular = hive.antenna(i.push_angular)

    if meta_args.mode == "get":
        if coordinate_system == 'absolute':
            ex.get_get_angular = hive.socket(cls.set_get_angular, identifier="entity.angular_velocity.get")
            i.do_get_angular = hive.triggerable(cls.do_get_angular)

        else:
            ex.get_get_angular = hive.socket(cls.set_get_angular, identifier="entity.angular_velocity.get")
            i.do_get_angular = hive.triggerable(cls.do_get_relative_angular)
            hive.trigger(i.pull_angular, i.pull_other_entity_id, pretrigger=True)

        if meta_args.bound:
            hive.trigger(i.pull_angular, i.do_get_entity_id, pretrigger=True)

        else:
            hive.trigger(i.pull_angular, i.pull_entity_id, pretrigger=True)

        hive.trigger(i.pull_angular, i.do_get_angular, pretrigger=True)

    else:
        if coordinate_system == 'absolute':
            ex.get_set_angular = hive.socket(cls.set_set_angular, identifier="entity.angular_velocity.set")
            i.do_set_angular = hive.triggerable(cls.do_set_angular)

        else:
            ex.get_set_angular = hive.socket(cls.set_set_angular, identifier="entity.angular_velocity.set")
            i.do_set_angular = hive.triggerable(cls.do_set_relative_angular)
            hive.trigger(i.push_angular, i.pull_other_entity_id)

        if meta_args.bound:
            hive.trigger(i.push_angular, i.do_get_entity_id)

        else:
            hive.trigger(i.push_angular, i.pull_entity_id)

        hive.trigger(i.push_angular, i.do_set_angular)


Angular = hive.dyna_hive("Angular", build_angular, declare_angular, drone_class=AngularClass)
