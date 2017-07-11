import hive


class VisibilityClass:

    def __init__(self):
        self._set_visibility = None
        self._get_visibility = None
        self._get_bound_entity = None

        self.entity_id = None

    def get_bound_entity(self):
        self.entity_id = self._get_bound_entity()

    def set_get_entity_id(self, get_entity_id):
        self._get_bound_entity = get_entity_id

    def set_set_visibility(self, set_visibility):
        self._set_visibility = set_visibility

    def set_get_visibility(self, get_visibility):
        self._get_visibility = get_visibility

    @hive.return_type('bool')
    def get_visibility(self):
        return self._get_visibility(self.entity_id)

    @hive.types(visible='bool')
    def set_visibility(self, visible):
        self._set_visibility(self.entity_id, visible)


def declare_visibility(meta_args):
    meta_args.mode = hive.parameter("str", "get", {'get', 'set'})
    meta_args.bound = hive.parameter("bool", True)


def build_visibility(cls, i, ex, args, meta_args):
    """Set/Get entity visibility"""

    if meta_args.bound:
        ex.get_bound_id = hive.socket(cls.set_get_entity_id, identifier="entity.get_bound")
        i.do_get_entity_id = hive.triggerable(cls.get_bound_entity)

    else:
        i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
        i.do_get_entity_id = hive.pull_in(i.entity_id)
        ex.entity_id = hive.antenna(i.do_get_entity_id)

    if meta_args.mode == 'get':
        ex.get_get_visibility = hive.socket(cls.set_get_visibility, identifier="entity.visibility.get")
        i.pull_visibility = hive.pull_out(cls.get_visibility)
        ex.visibility = hive.output(i.pull_visibility)
        hive.trigger(i.pull_visibility, i.do_get_entity_id, pretrigger=True)

    else:
        ex.get_set_visibility = hive.socket(cls.set_set_visibility, identifier="entity.visibility.set")
        i.push_in_visibility = hive.push_in(cls.set_visibility)
        ex.visibility = hive.antenna(i.push_in_visibility)
        hive.trigger(i.push_in_visibility, i.do_get_entity_id, pretrigger=True)


Visibility = hive.dyna_hive("Visibility", build_visibility, declare_visibility, drone_class=VisibilityClass)
