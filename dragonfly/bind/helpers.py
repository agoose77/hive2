from contextlib import contextmanager
from collections import namedtuple
from functools import wraps
import operator
from string import punctuation

import hive
from hive.parameter import HiveParameter


punctuation_no_underscore = punctuation.replace("_", "")

ForwardedIO = namedtuple("ForwardedIO", "identifier plugin_policy socket_policy")
BindParameterPair = namedtuple("BindParameterPair", "condition parameter")
PluginEntry = namedtuple("PluginEntry", "identifier plugin_policy socket_policy declare_for_environment condition_stack")


class BindClassDefinition:
    """Declares plugins and parameters of bind class and bind environments for binding Hives"""

    def __init__(self):
        self._condition_stack = []
        self._plugin_entries = []
        self._parameters = {}

    def forward_plugin(self, identifier, plugin_policy=hive.MultipleOptional, socket_policy=hive.SingleRequired,
                       declare_for_environment=True):
        condition_stack = self._condition_stack.copy()
        plugin_entry = PluginEntry(identifier, plugin_policy, socket_policy, declare_for_environment, condition_stack)
        self._plugin_entries.append(plugin_entry)

    def parameter(self, name, data_type=None, start_value=HiveParameter.no_value, options=None):
        self._parameters[name] = HiveParameter(data_type, start_value, options)
        return Variable(name)

    @contextmanager
    def condition(self, condition):
        self._condition_stack.append(condition)
        yield self
        self._condition_stack.pop()

    def build(self, name):
        return BindClassFactory(name, self._parameters.copy(), self._plugin_entries.copy())


def build_operator(operator_):

    def wrapper(self, right):
        if not isinstance(right, Operand):
            right = Value(right)

        return Operation(operator_, self, right)

    return wrapper


class Operand:
    """Base class for operands, which can form either side of an operation"""

    __and__ = build_operator(operator.and_)
    __or__ = build_operator(operator.or_)
    __ne__ = build_operator(operator.ne)
    __contains__ = build_operator(operator.contains)
    __add__ = build_operator(operator.add)
    __sub__ = build_operator(operator.sub)
    __lt__ = build_operator(operator.lt)
    __gt__ = build_operator(operator.gt)
    __eq__ = build_operator(operator.eq)
    __mul__ = build_operator(operator.mul)
    __truediv__ = build_operator(operator.truediv)


class Value(Operand):
    """A static value operand"""

    def __init__(self, value):
        super().__init__()

        self._value = value

    def __call__(self, context):
        return self._value


class Variable(Operand):
    """A dynamic named operand"""

    def __init__(self, name):
        super().__init__()

        self._name = name

    def __call__(self, context):
        return context[self._name]


class Operation(Operand):

    def __init__(self, operator_, left, right):
        super().__init__()

        self._operator = operator_
        self._left = left
        self._right = right

    def get_value(self, context):
        raise NotImplemented

    def __call__(self, context):
        left_value = self._left(context)
        right_value = self._right(context)
        return self._operator(left_value, right_value)


class BindClassFactory:
    """Generates bind class and bind environments for binding Hives"""

    def __init__(self, name, parameters, plugin_entries):
        assert name.isidentifier()

        self._plugins = {self.sanitise_identifier(e.identifier): e for e in plugin_entries}
        self._parameters = parameters

        self._name = name

    @property
    def name(self):
        return self._name


    @staticmethod
    def sanitise_identifier(identifier):
        """Convert string identifier to underscore delimited string"""
        return identifier.replace(".", "_").replace(punctuation_no_underscore, "").replace(" ", "_")

    def create_external_class(self):
        """Create the External Hive class"""
        class_name = "ExternalBindClass"

        class BinderClassBase:

            def __init__(self_binder):
                self_binder._plugins = {}

            def get_plugins(self_binder):
                return self_binder._plugins

            def get_config(self_binder):
                return {}

        cls_dict = {}

        # For each plugin, create a capture function to be used by a capture-socket
        for attr_name, plugin_entry in self._plugins.items():
            def capture_plugin(self_binder, plugin, forwarded_io=plugin_entry):
                self_binder._plugins[forwarded_io.identifier] = plugin

            capture_plugin.__qualname__ = "{}.{}".format(class_name, attr_name)
            cls_dict[attr_name] = capture_plugin

        return type(class_name, (BinderClassBase,), cls_dict)

    def create_environment_class(self):
        """Create the Environment Hive class"""
        class_name = "EnvironmentBindClass"

        class BinderClassBase:

            def __init__(self_binder, context):
                self_binder._plugins = context.plugins
                self_binder._config = context.config

        cls_dict = {}

        # TODO if bottleneck, set plugins on class instance at runtime (instead of looking up from self_environment dict)

        # For each plugin, create a getter function to be used by a getter plugin
        for attr_name, plugin_entry in self._plugins.items():
            def get_captured_plugin(self_environment, *args, forwarded_io=plugin_entry, **kwargs):
                plugin = self_environment._plugins[forwarded_io.identifier]
                return plugin(*args, **kwargs)

            get_captured_plugin.__qualname__ = "{}.{}".format(class_name, attr_name)
            cls_dict[attr_name] = get_captured_plugin

        return type(class_name, (BinderClassBase,), cls_dict)

    def build_external_hive(self):
        external_class = self.create_external_class()
        return hive.dyna_hive("{}External".format(self._name), self.external_builder,
                              declarator=self.external_declarator, builder_cls=external_class)

    def build_environment_hive(self):
        environment_class = self.create_environment_class()
        return hive.meta_hive("{}Environment".format(self._name), self.environment_builder,
                              declarator=self.environment_declarator, builder_cls=environment_class)

    def external_declarator(self, meta_args):
        """Adds bind parameters to meta args wrapper"""
        for name, parameter in self._parameters.items():
            setattr(meta_args, name, parameter)

    def external_builder(self, cls, i, ex, args, meta_args):
        """Adds bind-plugin sockets to ex wrapper if conditions allow."""
        meta_args_dict = meta_args.to_ordered_dict()

        for attr_name, plugin_entry in self._plugins.items():
            for condition in plugin_entry.condition_stack:
                if not condition(meta_args_dict):
                    break

            else:
                method = getattr(cls, attr_name)
                socket = hive.socket(method, plugin_entry.identifier, plugin_entry.socket_policy)
                setattr(ex, attr_name, socket)

        get_plugins_plugin = hive.plugin(cls.get_plugins, identifier="bind.get_plugins")
        get_config_plugin = hive.plugin(cls.get_config, identifier="bind.get_config")

        setattr(ex, '{}_get_plugins'.format(self._name), get_plugins_plugin)
        setattr(ex, '{}_get_config'.format(self._name), get_config_plugin)

    def environment_declarator(self, meta_args):
        """Inactive function to provide consistent API"""

    def environment_builder(self, cls, i, ex, args, meta_args):
        """Adds bind-plugin plugins to ex wrapper if conditions allow."""
        meta_args_dict = meta_args.bind_meta_args.to_ordered_dict()

        for attr_name, plugin_entry in self._plugins.items():
            if not plugin_entry.declare_for_environment:
                continue

            for condition in plugin_entry.condition_stack:
                if not condition(meta_args_dict):
                    break

            else:
                method = getattr(cls, attr_name)
                plugin = hive.plugin(method, plugin_entry.identifier, plugin_entry.plugin_policy)
                setattr(ex, attr_name, plugin)

    def builds_external(self, func):
        """External builder decorator.

        Adds configured bind-plugin sockets to bind External class

        :param func: subsequent builder
        """
        @wraps(func)
        def builder(cls, i, ex, args, meta_args):
            self.external_builder(cls, i, ex, args, meta_args)
            func(cls, i, ex, args, meta_args)

        return builder

    def builds_environment(self, func):
        """Environment builder decorator.

        Adds configured bind-plugin plugins to bind environment class

        :param func: subsequent builder
        """
        @wraps(func)
        def builder(cls, i, ex, args, meta_args):
            self.environment_builder(cls, i, ex, args, meta_args)
            func(cls, i, ex, args, meta_args)

        return builder

    def declares_external(self, func):
        """External declarator decorator.

        Adds bind parameters to external meta args wrapper

        :param func: subsequent declarator
        """

        @wraps(func)
        def declarator(meta_args):
            self.external_declarator(meta_args)
            func(meta_args)

        return declarator

    def declares_environment(self, func):
        """Environment declarator decorator.

        Adds bind parameters to environment meta args wrapper

        :param func: subsequent declarator
        """

        @wraps(func)
        def declarator(meta_args):
            self.environment_declarator(meta_args)
            func(meta_args)

        return declarator


# Example usage
"""
# Create some bind hive
definition = BindClassDefinition()

flag = definition.parameter("bind_some_plugin", "str", options={'yes', 'no'})
flag2 = definition.parameter("bind_some_other_plugin", "str", options={'yes', 'no'})

with definition.condition(flag == "yes") as then:
    then.forward_plugin("some_plugin")

    with definition.condition(flag2 != "no"): # Omit the variable, still fine
        definition.forward_plugin("some_other_plugin")


factory = definition.build("TestBinder")

bind_hive = hive.dyna_hive("BindHive", factory.external_builder, declarator=factory.external_declarator,
                             builder_cls=factory.external_class)
bind_environment = hive.meta_hive("BindEnvironment", factory.environment_builder,
                            declarator=factory.environment_declarator, builder_cls=factory.environment_class)

# Optionally inspect meta args to disable binding (optimisation)
def get_environment(meta_args):
    return bind_environment

bind_info = BindInfo(factory.name, bind_hive, get_environment)
"""

# The above generates a builder like this
"""
def declare_bind_hive(meta_args):
    meta_args.bind_some_plugin = hive.parameter("str", options={"yes", "no"})
    meta_args.bind_some_other_plugin = hive.parameter("str", options={"yes", "no"})

    
def build_bind_hive(cls, i, ex, args, meta_args):
    if meta_args.bind_some_plugin == "yes":
        ex.some_plugin = ...

        if meta_args.bind_some_other_plugin != "no":
            ex.some_other_plugin = ...
"""