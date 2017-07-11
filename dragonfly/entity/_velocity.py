import hive


class VelocityClass:

    def __init__(self):
        self.velocity = None

        self.entity_id = None
        self.other_entity_id = None

        self._get_entity_id = None
        self._get_velocity = None
        self._set_velocity = None

    def do_get_entity_id(self):
        self.entity_id = self._get_entity_id()

    def do_get_velocity(self):
        self.velocity = self._get_velocity(self.entity_id)

    def do_get_relative_velocity(self):
        self.velocity = self._get_velocity(self.entity_id, self.other_entity_id)

    def do_set_velocity(self):
        self._set_velocity(self.entity_id, self.velocity)

    def do_set_relative_velocity(self):
        self._set_velocity(self.entity_id, self.other_entity_id, self.velocity)

    def set_get_velocity(self, get_velocity):
        self._get_velocity = get_velocity

    def set_set_velocity(self, set_velocity):
        self._set_velocity = set_velocity

    def set_get_entity_id(self, get_entity_id):
        self._get_entity_id = get_entity_id


def declare_velocity(meta_args):
    meta_args.bound = hive.parameter("bool", True)
    meta_args.coordinate_system = hive.parameter("str", 'absolute', options={'absolute'}) # TODO support relative
    meta_args.mode = hive.parameter("str", "get", options={"get", "set"})


def build_velocity(cls, i, ex, args, meta_args):
    """Access to entity velocity API"""
    coordinate_system = meta_args.coordinate_system

    i.velocity = hive.property(cls, "velocity", "vector")

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
        i.pull_velocity = hive.pull_out(i.velocity)
        ex.velocity = hive.output(i.pull_velocity)

    else:
        i.push_velocity = hive.push_in(i.velocity)
        ex.velocity = hive.antenna(i.push_velocity)

    if meta_args.mode == "get":
        if coordinate_system == 'absolute':
            ex.get_get_velocity = hive.socket(cls.set_get_velocity, identifier="entity.linear_velocity.get")
            i.do_get_velocity = hive.triggerable(cls.do_get_velocity)

        else:
            ex.get_get_velocity = hive.socket(cls.set_get_velocity, identifier="entity.linear_velocity.get")
            i.do_get_velocity = hive.triggerable(cls.do_get_relative_velocity)
            hive.trigger(i.pull_velocity, i.pull_other_entity_id, pretrigger=True)

        if meta_args.bound:
            hive.trigger(i.pull_velocity, i.do_get_entity_id, pretrigger=True)

        else:
            hive.trigger(i.pull_velocity, i.pull_entity_id, pretrigger=True)

        hive.trigger(i.pull_velocity, i.do_get_velocity, pretrigger=True)

    else:
        if coordinate_system == 'absolute':
            ex.get_set_velocity = hive.socket(cls.set_set_velocity, identifier="entity.linear_velocity.set")
            i.do_set_velocity = hive.triggerable(cls.do_set_velocity)

        else:
            ex.get_set_velocity = hive.socket(cls.set_set_velocity, identifier="entity.linear_velocity.set")
            i.do_set_velocity = hive.triggerable(cls.do_set_relative_velocity)
            hive.trigger(i.push_velocity, i.pull_other_entity_id)

        if meta_args.bound:
            hive.trigger(i.push_velocity, i.do_get_entity_id)

        else:
            hive.trigger(i.push_velocity, i.pull_entity_id)

        hive.trigger(i.push_velocity, i.do_set_velocity)


Velocity = hive.dyna_hive("Velocity", build_velocity, declare_velocity, drone_class=VelocityClass)
