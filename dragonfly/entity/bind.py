import hive

from ..bind import BindInfo, BindClassDefinition


definition = BindClassDefinition()
bind_mode_param = definition.parameter("bind_entity", "str", 'bound', {'none', 'bound', 'unbound'})


with definition.condition(bind_mode_param != "none"):
    definition.forward_plugin("entity.position.get.absolute")
    definition.forward_plugin("entity.position.get.relative")
    definition.forward_plugin("entity.position.set.absolute")
    definition.forward_plugin("entity.position.set.relative")

    definition.forward_plugin("entity.orientation.get.relative")
    definition.forward_plugin("entity.orientation.get.absolute")
    definition.forward_plugin("entity.orientation.set.absolute")
    definition.forward_plugin("entity.orientation.set.absolute")

    definition.forward_plugin("entity.parent.get")
    definition.forward_plugin("entity.parent.set")

    definition.forward_plugin("entity.tag.get")
    definition.forward_plugin("entity.tag.set")

    definition.forward_plugin("entity.visibility.get")
    definition.forward_plugin("entity.visibility.set")

    definition.forward_plugin("entity.destroy")
    definition.forward_plugin("entity.spawn")

    definition.forward_plugin("entity.register_destructor")


factory = definition.build("BindEntity")


class EntityEnvironmentClass(factory.create_environment_class()):

    def __init__(self, context):
        super().__init__(context)

        self._hive = hive.get_run_hive()

        # Add reference to this hive for this entity
        if "entity_id" in context.config:
            self._entity_id = context.config["entity_id"]

    def get_bound_entity(self):
        return self._entity_id

    def get_bound_pos_abs(self):
        return self._plugins["entity.bound.position.get.absolute"](self._entity_id)

    def get_bound_pos_rel(self, other_id):
        return self._plugins["entity.bound.position.get.relative"](self._entity_id, other_id)

    def get_bound_ori_abs(self):
        return self._plugins["entity.bound.orientation.get.absolute"](self._entity_id)

    def get_bound_ori_rel(self, other_id):
        return self._plugins["entity.bound.orientation.get.relative"](self._entity_id, other_id)

    def set_bound_pos_abs(self, position):
        self._plugins["entity.bound.position.set.absolute"](self._entity_id, position)

    def set_bound_pos_rel(self, other_id, position):
        self._plugins["entity.bound.position.set.relative"](self._entity_id, other_id, position)

    def set_bound_ori_abs(self, orientation):
        self._plugins["entity.bound.orientation.set.absolute"](self._entity_id, orientation)

    def set_bound_ori_rel(self, other_id, orientation):
        self._plugins["entity.bound.orientation.set.relative"](self._entity_id, other_id, orientation)

    def get_bound_tag(self, name):
        return self._plugins['entity.tag.get'](self._entity_id, name)

    def set_bound_tag(self, name, value):
        self._plugins['entity.tag.set'](self._entity_id, name, value)

    def get_bound_parent(self, name):
        return self._plugins['entity.parent.get'](self._entity_id, name)

    def set_bound_parent(self, name, value):
        self._plugins['entity.parent.set'](self._entity_id, name, value)

    def get_bound_visibility(self, name):
        return self._plugins['entity.visibility.get'](self._entity_id, name)

    def set_bound_visibility(self, name, value):
        self._plugins['entity.visibility.set'](self._entity_id, name, value)

    def bound_destroy(self):
        self._plugins['entity.bound.destroy']()


@factory.builds_environment
def build_entity_environment(cls, i, ex, args, meta_args):
    """Runtime event environment for instantiated hive.

    Provides appropriate sockets and plugins for event interface
    """
    if meta_args.bind_meta_args.bind_entity != "bound":
        return

    ex.get_bound_entity = hive.plugin(cls.get_bound_entity, "entity.get_bound")

    ex.get_bound_position_absolute = hive.plugin(cls.get_bound_pos_abs, "entity.bound.position.get.absolute")
    ex.set_bound_position_absolute = hive.plugin(cls.set_bound_pos_abs, "entity.bound.position.set.absolute")
    ex.get_bound_position_relative = hive.plugin(cls.get_bound_pos_rel, "entity.bound.position.get.relative")
    ex.set_bound_position_relative = hive.plugin(cls.set_bound_pos_rel, "entity.bound.position.set.relative")

    ex.get_bound_orientation_absolute = hive.plugin(cls.get_bound_ori_abs, "entity.bound.orientation.get.absolute")
    ex.set_bound_orientation_absolute = hive.plugin(cls.set_bound_ori_abs, "entity.bound.orientation.set.absolute")
    ex.get_bound_orientation_relative = hive.plugin(cls.get_bound_ori_rel, "entity.bound.orientation.get.relative")
    ex.set_bound_orientation_relative = hive.plugin(cls.set_bound_ori_rel, "entity.bound.orientation.set.relative")

    ex.get_bound_parent = hive.plugin(cls.get_bound_parent, "entity.bound.parent.get")
    ex.set_bound_parent = hive.plugin(cls.set_bound_parent, "entity.bound.parent.set")

    ex.get_bound_tag = hive.plugin(cls.get_bound_tag, "entity.bound.tag.get")
    ex.set_bound_tag = hive.plugin(cls.set_bound_tag, "entity.bound.tag.set")

    ex.get_bound_visibility = hive.plugin(cls.get_bound_visibility, "entity.bound.visibility.get")
    ex.set_bound_visibility = hive.plugin(cls.set_bound_visibility, "entity.bound.visibility.set")

    ex.bound_destroy = hive.plugin(cls.bound_destroy, "entity.bound.destroy")


_EntityEnvironment = hive.meta_hive("EntityEnvironment", build_entity_environment, factory.environment_declarator,
                                   drone_class=EntityEnvironmentClass)


class EntityCls(factory.create_external_class()):

    def __init__(self):
        super().__init__()

        self._hive = hive.get_run_hive()
        self.entity_id = None

    def get_config(self):
        if hasattr(self._hive, 'entity_id'):
            self._hive.entity_id()
            return dict(entity_id=self.entity_id)

        return {}


@factory.builds_external
def build_bind(cls, i, ex, args, meta_args):
    bind_mode = meta_args.bind_entity

    if bind_mode == 'bound':
        i.entity_id = hive.property(cls, "entity_id", "int.entity_id")
        i.pull_entity_id = hive.pull_in(i.entity_id)
        ex.entity_id = hive.antenna(i.pull_entity_id)


_BindEntity = hive.dyna_hive("BindEntity", build_bind, declarator=factory.external_declarator, drone_class=EntityCls)


def get_environment(meta_args):
    if meta_args.bind_entity != 'none':
        return _EntityEnvironment

    return None


bind_info = BindInfo("entity", _BindEntity, get_environment)
