from abc import ABC, abstractproperty
from collections import defaultdict
from itertools import count

from .classes import HiveInternalWrapper, HiveExportableWrapper, HiveArgsWrapper, HiveMetaArgsWrapper, HiveClassProxy
from .compatability import next, validate_signature
from .connect import connect, ConnectionCandidate
from .contexts import (bee_register_context, get_mode, hive_mode_as, building_hive_as, run_hive_as,
                       get_validation_enabled, get_building_hive)
from .manager import memoize
from .policies import MatchmakingPolicyError
from .protocols import *
from .resolve_bee import ResolveBee
from .typing import MatchFlags, data_types_match


def generate_anonymous_names(fmt_string='anonymous_bee_{}'):
    """Sequential generator of "bee names"""
    for i in count():
        yield fmt_string.format(i)


class RuntimeHiveInstantiator(Bindable):
    """Instantiator Bee to instantiate runtime hives.

     Create a new RuntimeHive for a HiveObject instance when bound to parent hive.
     """

    def __init__(self, hive_object):
        # TODO, maybe setattr for bee.getinstance(hive_object) in hive ex/i wrappers
        self._hive_object = hive_object

    @memoize
    def bind(self, run_hive):
        return self._hive_object.instantiate()


class RuntimeHive(Bee, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget, Nameable):
    """Unique Hive instance that is created at runtime for a Hive object.

    Lightweight instantiation is supported through caching performed by the HiveObject instance.
    """

    _hive_bee_name = ()
    _hive_object = None
    _hive_build_class_to_instance = None
    _hive_bee_instances = None
    _bee_names = None
    _drones = None

    def __init__(self, hive_object, builders):
        super().__init__()

        self._hive_bee_name = hive_object._hive_bee_name
        self._hive_object = hive_object
        self._hive_build_class_to_instance = {}
        self._hive_bee_instances = {}
        self._bee_names = ["_drones"]
        self._drones = []

        with run_hive_as(self):
            # Build args
            args = hive_object._hive_builder_args
            kwargs = hive_object._hive_builder_kwargs

            for builder, builder_cls in builders:

                if builder_cls is not None:
                    assert builder_cls not in self._hive_build_class_to_instance, builder_cls

                    # Do not initialise instance yet
                    build_class_instance = builder_cls.__new__(builder_cls)

                    self._hive_build_class_to_instance[builder_cls] = build_class_instance
                    self._drones.append(build_class_instance)

                    build_class_instance.__init__(*args, **kwargs)

            with building_hive_as(hive_object.__class__), hive_mode_as("build"):
                # Add external bees to runtime hive
                exposed_bees = []

                external_bees = hive_object._hive_ex
                for bee_name, bee in external_bees._items:
                    exported_bee = bee.export()

                    # TODO: nice exception reporting
                    instance = exported_bee.getinstance(self._hive_object)

                    if isinstance(instance, Bindable):
                        instance = instance.bind(self)
                        if instance is None:
                            continue

                    # Store runtime information on exported bee
                    if isinstance(instance, Nameable):
                        instance.register_alias(self, bee_name)

                    exposed_bees.append((bee_name, instance))

                # Add internal bees (that are hives, Callable or Stateful) to runtime hive
                internal_bees = hive_object._hive_i
                for bee_name, bee in internal_bees._items:
                    private_name = "_" + bee_name

                    # Some runtime hive attributes are protected, but in the case of Stateful bees,
                    # The RuntimeHive already has corresponding property descriptors
                    # Bee.implements indicates that the final bee (following bee.getinstance(...)) will be Stateful
                    if not bee.implements(Stateful):
                        assert not hasattr(self, private_name), private_name

                    # TODO: nice exception reporting
                    instance = bee.getinstance(self._hive_object)
                    if isinstance(instance, Bindable):
                        instance = instance.bind(self)
                        if instance is None:
                            continue

                    # Store runtime information on bee
                    if isinstance(instance, Nameable):
                        instance.register_alias(self, bee_name)

                    if bee.implements(HiveObject) or bee.implements(Callable):
                        exposed_bees.append((private_name, instance))

                for bee_name, instance in exposed_bees:
                    if isinstance(instance, Stateful):
                        continue

                    # Risk that multiple references to same bee exist
                    self._hive_bee_instances[bee_name] = instance
                    self._bee_names.append(bee_name)

                    setattr(self, bee_name, instance)

    @staticmethod
    def _hive_can_connect_hive(other):
        return isinstance(other, RuntimeHive)

    def _hive_find_connect_sources(self):
        return self._hive_object._hive_find_connect_sources()

    def _hive_find_connect_targets(self):
        return self._hive_object._hive_find_connect_targets()

    def _hive_trigger_source(self, target_func):
        source_name = self._hive_object._hive_find_trigger_source()
        instance = self._hive_bee_instances[source_name]
        return instance._hive_trigger_source(target_func)

    def _hive_trigger_target(self):
        target_name = self._hive_object._hive_find_trigger_target()
        instance = self._hive_bee_instances[target_name]
        return instance._hive_trigger_target()

    def _hive_get_connect_source(self, target):
        source_name = self._hive_object._hive_find_connect_source(target)
        return getattr(self, source_name)

    def _hive_get_connect_target(self, source):
        target_name = self._hive_object._hive_find_connect_target(source)
        return getattr(self, target_name)

    def implements(self, cls):
        return isinstance(self, cls)

    def __iter__(self):
        return iter(self._bee_names)

    def __dir__(self):
        return self._bee_names


class HiveObject(Exportable, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget):
    """Built Hive base-class responsible for creating new Hive instances.

    All bees defined with the builder functions are memoized and cached for faster instantiation
    """

    _hive_parent_class = None
    _hive_runtime_class = None
    _hive_bee_name = ()

    _hive_i = None
    _hive_ex = None
    _hive_exportable_to_parent = None

    _hive_args = None
    _hive_meta_args_frozen = None

    export_only = False

    def __init__(self, *args, **kwargs):
        super().__init__()

        # Automatically import parent sockets and plugins
        self._hive_allow_import_namespace = kwargs.pop("import_namespace", True)
        self._hive_allow_export_namespace = kwargs.pop("export_namespace", True)

        # Take out args parameters
        remaining_args, remaining_kwargs, arg_wrapper_values = self._hive_args.extract_from_args(args, kwargs)
        self._hive_args_frozen = self._hive_args.freeze(arg_wrapper_values)

        # Args to instantiate builder-class instances
        self._hive_builder_args = remaining_args
        self._hive_builder_kwargs = remaining_kwargs

        # Check build functions are valid
        for builder, builder_cls in self._hive_parent_class._builders:
            if builder_cls is not None:

                try:
                    validate_signature(builder_cls, *self._hive_builder_args, **self._hive_builder_kwargs)

                except TypeError as err:
                    raise TypeError("{}.{}".format(builder_cls.__name__, err.args[0]))

        # Create ResolveBee wrappers for external interface
        with  hive_mode_as("build"):
            external_bees = self.__class__._hive_ex
            for bee_name, bee in external_bees._items:
                target = bee.export()
                resolve_bee = ResolveBee(target, self)

                setattr(self, bee_name, resolve_bee)

    @memoize
    def getinstance(self, parent_hive_object):
        """Return a RuntimeHiveInstantiator for this parent hive_object"""
        return RuntimeHiveInstantiator(self)

    def instantiate(self):
        """Return an instance of the runtime Hive for this Hive object."""
        return self._hive_runtime_class(self, self._hive_parent_class._builders)

    @staticmethod
    def _hive_can_connect_hive(other):
        return isinstance(other, HiveObject)

    @classmethod
    def _hive_find_trigger_target(cls):
        """Find name of single external bee that supported TriggerTarget interface.

        Raise TypeError if such a condition cannot be met
        """
        external_bees = cls._hive_ex
        trigger_targets = []

        for bee_name, bee in external_bees._items:
            exported_bee = bee.export()

            if isinstance(exported_bee, TriggerTarget):
                assert bee.implements(TriggerTarget)
                trigger_targets.append(bee_name)

        if not trigger_targets:
            raise TypeError("No trigger targets in %s" % cls)

        elif len(trigger_targets) > 1:
            raise TypeError("Multiple trigger targets in {}: {}".format(cls, trigger_targets))

        return trigger_targets[0]

    @classmethod
    def _hive_find_trigger_source(cls):
        """Find and return name of single external bee that supported TriggerSource interface.

        Raise TypeError if such a condition cannot be met
        """
        external_bees = cls._hive_ex
        trigger_sources = []

        for bee_name, bee in external_bees._items:
            exported_bee = bee.export()

            if isinstance(exported_bee, TriggerSource):
                trigger_sources.append(bee_name)

        if not trigger_sources:
            raise TypeError("No TriggerSources in %s" % cls)

        elif len(trigger_sources) > 1:
            raise TypeError("Multiple TriggerSources in %s: %s" % (cls, trigger_sources))

        return trigger_sources[0]

    @classmethod
    def _hive_find_connect_sources(cls):
        externals = cls._hive_ex

        # Find source hive ConnectSources
        connect_sources = []
        for bee_name, bee in externals._items:
            exported_bee = bee.export()

            if not exported_bee.implements(ConnectSource):
                continue

            candidate = ConnectionCandidate(bee_name, exported_bee.data_type)
            connect_sources.append(candidate)

        return connect_sources

    @classmethod
    def _hive_find_connect_targets(cls):
        externals = cls._hive_ex

        # Find target hive ConnectTargets
        connect_targets = []
        for bee_name, bee in externals._items:
            exported_bee = bee.export()

            if not exported_bee.implements(ConnectTarget):
                continue

            candidate = ConnectionCandidate(bee_name, exported_bee.data_type)
            connect_targets.append(candidate)

        return connect_targets

    @classmethod
    def _hive_find_connect_source(cls, target):
        """Find and return the name of a suitable connect source within this hive

        :param target: target to connect to
        """
        assert target.implements(ConnectTarget)

        connect_sources = [c for c in cls._hive_find_connect_sources()
                           if data_types_match(c.data_type, target.data_type, MatchFlags.match_shortest)]
        if not connect_sources:
            connect_sources = [c for c in cls._hive_find_connect_sources()
                               if data_types_match(c.data_type, target.data_type,
                                                   MatchFlags.match_shortest | MatchFlags.permit_any_target)]

        if not connect_sources:
            raise TypeError("No matching connection sources found for {}".format(target))

        elif len(connect_sources) > 1:
            raise TypeError("Multiple connection sources found for {}: {}".format(target, connect_sources))

        return connect_sources[0].bee_name

    @classmethod
    def _hive_find_connect_target(cls, source):
        """Find and return the name of a suitable connect target within this hive
F
        :param source: source to connect to
        """
        assert source.implements(ConnectSource)

        connect_targets = [c for c in cls._hive_find_connect_targets()
                           if data_types_match(source.data_type, c.data_type, MatchFlags.match_shortest)]
        if not connect_targets:
            connect_targets = [c for c in cls._hive_find_connect_targets()
                               if data_types_match(source.data_type, c.data_type,
                                                   MatchFlags.match_shortest | MatchFlags.permit_any_target)]

        if not connect_targets:
            raise TypeError("No matching connections found for {}".format(source))

        elif len(connect_targets) > 1:
            raise TypeError("Multiple connection targets found for {}: {}".format(source, connect_targets))

        return connect_targets[0].bee_name

    def _hive_get_trigger_target(self):
        """Return single external bee that supported TriggerTarget interface"""
        trigger_name = self._hive_find_trigger_target()
        return getattr(self, trigger_name)

    def _hive_get_trigger_source(self):
        """Return single external bee that supported TriggerSource interface"""
        trigger_name = self._hive_find_trigger_source()
        return getattr(self, trigger_name)

    def _hive_get_connect_target(self, source):
        """Return single external bee that supported ConnectTarget interface"""
        target_name = self._hive_find_connect_target(source)
        return getattr(self, target_name)

    def _hive_get_connect_source(self, target):
        """Return single external bee that supported ConnectSource interface"""
        source_name = self._hive_find_connect_source(target)
        return getattr(self, source_name)

    def export(self):
        return self


def validate_external_name(attr_name):
    """Raise AttributeError if attribute name belongs to HiveObject or RuntimeHive"""
    if hasattr(HiveObject, attr_name):
        raise AttributeError('Cannot overwrite special attribute HiveObject.{}'.format(attr_name))

    if hasattr(RuntimeHive, attr_name):
        raise AttributeError('Cannot overwrite special attribute RuntimeHive.{}'.format(attr_name))


def validate_internal_name(attr_name):
    """Raise AttributeError if attribute name prefixed with underscore belongs to HiveObject or RuntimeHive"""
    internal_name = "_{}".format(attr_name)
    if hasattr(HiveObject, internal_name):
        raise AttributeError('Cannot overwrite special attribute HiveObject.{}'.format(attr_name))

    if hasattr(RuntimeHive, internal_name):
        raise AttributeError('Cannot overwrite special attribute RuntimeHive.{}'.format(attr_name))


class MetaHivePrimitive(ABC):
    """Primitive container to instantiate Hive with particular meta arguments"""

    _hive_object_class = abstractproperty()

    def __new__(cls, *args, **kwargs):
        hive_object = cls._hive_object_class(*args, **kwargs)

        if get_mode() == "immediate":
            return hive_object.instantiate()

        else:
            return hive_object


class HiveBuilder(object):
    """Deferred Builder for constructing Hive classes.

    Perform building once for multiple instances of the same Hive.
    """

    _builders = ()
    _declarators = ()
    _is_dyna_hive = False

    _hive_meta_args = None

    def __new__(cls, *args, **kwargs):
        print("INIT BUILDER", cls)
        # If MetaHive and not DynaHive
        if cls._declarators and not cls._is_dyna_hive:
            return cls._hive_get_meta_primitive(*args, **kwargs)

        args, kwargs, hive_object_class = cls._hive_get_hive_object_class(args, kwargs)
        hive_object = hive_object_class(*args, **kwargs)

        if get_mode() == "immediate":
            return hive_object.instantiate()

        else:
            return hive_object

    @classmethod
    def _hive_get_meta_primitive(cls, *args, **kwargs):
        """Return the MetaHivePrimitive subclass associated with the HiveObject class produced for these meta args"""
        args, kwargs, hive_object_class = cls._hive_get_hive_object_class(args, kwargs)
        assert not args or kwargs, "Meta primitive cannot be passed any runtime-arguments"

        return cls._hive_create_meta_primitive(hive_object_class)

    @classmethod
    @memoize
    def _hive_create_meta_primitive(cls, hive_object_class):
        """Return the MetaHivePrimitive subclass associated with this HiveObject class """
        return type("MetaHivePrimitive::{}".format(cls.__name__), (MetaHivePrimitive,),
                    {'_hive_object_class': hive_object_class})

    @classmethod
    @memoize
    def _hive_build(cls, meta_arg_values):
        """Build a HiveObject for this Hive, with appropriate Args instance

        :param kwargs: Parameter keyword arguments
        """
        hive_object_dict = {'__doc__': cls.__doc__, "_hive_parent_class": cls}
        hive_object_class_name = "HiveObject<{}>".format(cls.__name__)
        hive_object_class = type(hive_object_class_name, (HiveObject,), hive_object_dict)

        hive_object_class._hive_i = internals = HiveInternalWrapper(hive_object_class,
                                                                    validator=lambda n, v: validate_internal_name(n))
        hive_object_class._hive_ex = externals = HiveExportableWrapper(hive_object_class,
                                                                       validator=lambda n, v: validate_external_name(n))
        hive_object_class._hive_args = args = HiveArgsWrapper(hive_object_class)

        # Get frozen meta args
        frozen_meta_args = cls._hive_meta_args.freeze(meta_arg_values)
        hive_object_class._hive_meta_args_frozen = frozen_meta_args

        is_root = get_building_hive() is None
        is_meta_hive = bool(cls._declarators)

        with hive_mode_as("build"), building_hive_as(hive_object_class), bee_register_context() as registered_bees:
            # Invoke builder functions to build wrappers
            for builder, builder_cls in cls._builders:
                # Call builder with appropriate arguments depending upon Hive type
                if builder_cls is not None:
                    wrapper = HiveClassProxy(builder_cls)
                    builder_args = wrapper, internals, externals, args

                else:
                    builder_args = internals, externals, args

                if is_meta_hive:
                    builder_args = builder_args + (frozen_meta_args,)

                try:
                    builder(*builder_args)

                except Exception:
                    print("Unable to invoke builder '{}'".format(builder))
                    raise

            cls._hive_build_namespace(hive_object_class)

            # Root hives build
            if is_root:
                cls._hive_build_connectivity(hive_object_class)

        # Find anonymous bees
        anonymous_bees = set(registered_bees)

        # Find any anonymous bees which are held on object
        for bee_name, bee in internals._items:
            if bee in anonymous_bees:
                anonymous_bees.remove(bee)

        # Save anonymous bees to internal wrapper, with unique names

        sequential_bee_names = generate_anonymous_names()
        for bee in registered_bees:
            if bee not in anonymous_bees:
                continue

            # Find unique name for bee
            while True:
                bee_name = next(sequential_bee_names)
                if not hasattr(internals, bee_name):
                    break

            setattr(internals, bee_name, bee)

        # TODO: auto-remove connections/triggers for which the source/target has been deleted

        # Build runtime hive class
        run_hive_class_dict = {"__doc__": cls.__doc__}

        # For internal bees
        for bee_name, bee in internals._items:
            private_bee_name = "_{}".format(bee_name)

            # If the bee requires a property interface, build a property
            if isinstance(bee, Stateful):
                run_hive_class_dict[private_bee_name] = property(bee._hive_stateful_getter, bee._hive_stateful_setter)

        # For external bees
        for bee_name, bee in externals._items:
            # If the bee requires a property interface, build a property
            if isinstance(bee, Stateful):
                run_hive_class_dict[bee_name] = property(bee._hive_stateful_getter, bee._hive_stateful_setter)

        run_hive_cls_name = "{}::run_hive".format(hive_object_class.__name__)
        hive_object_class._hive_runtime_class = type(run_hive_cls_name, (RuntimeHive,), run_hive_class_dict)
        return hive_object_class

    @classmethod
    def _hive_build_connectivity(cls, resolved_hive_object, tracked_policies=None, plugin_map=None, socket_map=None):
        """Connect plugins and sockets together by identifier.

        If children allow importing of namespace, pass namespace to children.
        """
        externals = resolved_hive_object._hive_ex
        internals = resolved_hive_object._hive_i

        # For children of the root hive, we must connect relative to top-most hive
        # This is for the top level (building) hive
        is_root = tracked_policies is None

        if is_root:
            exported_to_parent = set()

            plugin_map = defaultdict(list)
            socket_map = defaultdict(list)

            bee_source = externals
            tracked_policies = []

        # This method call applies to a HiveObject instance (bee_source)
        else:
            # If this hive exported to parent
            if resolved_hive_object._hive_allow_export_namespace:
                exported_to_parent = resolved_hive_object._hive_exportable_to_parent

            # Nothing was exported
            else:
                exported_to_parent = set()

            plugin_map = plugin_map.copy()
            socket_map = socket_map.copy()

            # Get the external bees' resolvebee instead of raw bee
            bee_source = resolved_hive_object

        child_hives = set()

        # Find external hives
        for bee in externals._values:
            if not bee.implements(HiveObject):
                continue

            if not bee._hive_allow_import_namespace:
                continue

            child_hives.add(bee)

        # Find internal hives
        for bee in internals._values:
            if not bee.implements(HiveObject):
                continue

            if not bee._hive_allow_import_namespace:
                continue

            child_hives.add(bee)

        # Find sockets and plugins that are exportable
        for bee_name in externals._names:
            # This will have already been handled by parent (as this method is called top-down)
            if bee_name in exported_to_parent:
                continue

            bee = getattr(bee_source, bee_name)

            # Find and connect identified plugins with existing sockets
            if bee.implements(Plugin) and bee.identifier is not None:
                identifier = bee.identifier

                plugin_policy = bee.policy()

                node_info = bee, plugin_policy
                plugin_map[identifier].append(node_info)
                # Keep track of instantiated policies
                tracked_policies.append(node_info)

                # Can we connect to a socket?
                if identifier in socket_map:
                    socket_bees = socket_map[identifier]

                    for socket_bee, socket_policy in socket_bees:
                        try:
                            plugin_policy.pre_connected()
                            socket_policy.pre_connected()

                            connect(bee, socket_bee)

                            plugin_policy.on_connected()
                            socket_policy.on_connected()

                        except MatchmakingPolicyError:
                            print("An error occurred during matchmaking for socket {}, {}".format(bee_name, identifier))
                            print(socket_bee)
                            raise

            # Find and connect identified sockets with existing plugins
            if bee.implements(Socket) and bee.identifier is not None:
                identifier = bee.identifier

                socket_policy = bee.policy()
                node_info = bee, socket_policy
                socket_map[identifier].append(node_info)
                # Keep track of instantiated policies
                tracked_policies.append(node_info)

                # Can we connect to a plugin?
                if identifier in plugin_map:
                    plugin_bees = plugin_map[identifier]

                    for plugin_bee, plugin_policy in plugin_bees:
                        try:

                            plugin_policy.pre_connected()
                            socket_policy.pre_connected()

                            connect(plugin_bee, bee)

                            plugin_policy.on_connected()
                            socket_policy.on_connected()

                        except MatchmakingPolicyError:
                            print("An error occurred during matchmaking for socket {}, {}".format(bee_name, identifier))
                            print(plugin_bee)
                            raise

        # Get resolve bees instead of raw HiveObject instances (ResolveBees relative to parent)
        if not is_root:
            child_hives = {ResolveBee(bee.export(), resolved_hive_object) for bee in child_hives}

        # Now export to child hives
        for child in child_hives:
            cls._hive_build_connectivity(child, tracked_policies, plugin_map, socket_map)

        # Validate policies
        if get_validation_enabled():
            for bee, policy in tracked_policies:
                try:
                    policy.validate()

                except MatchmakingPolicyError:
                    print("Error in validating policy of {}".format(bee))
                    raise

    @classmethod
    def _hive_build_namespace(cls, hive_object_cls):
        externals = hive_object_cls._hive_ex
        internals = hive_object_cls._hive_i

        # Importing
        child_hives = set()

        # Find external hives
        for bee in externals._values:
            if isinstance(bee, HiveObject):
                child_hives.add(bee)

        # Find internal hives
        for bee in internals._values:
            if isinstance(bee, HiveObject):
                child_hives.add(bee)

        # Export bees from drone-like child hives
        for child_hive in child_hives:
            # If child doesn't allow exporting
            if not child_hive._hive_allow_export_namespace:
                continue

            # Find exportable from child and save to HiveObject instance
            importable_from_child = child_hive.__class__._hive_exportable_to_parent

            # Find bees at set them on parent
            for bee_name in importable_from_child:
                assert not hasattr(externals, bee_name), bee_name
                bee = getattr(child_hive, bee_name)
                setattr(externals, bee_name, bee)

        # Exportable bees to parent if drone
        hive_object_cls._hive_exportable_to_parent = export_to_parent = set()
        for bee_name, bee in externals._items:
            if not (bee.implements(Plugin) or bee.implements(Socket)):
                continue

            if bee.identifier is not None and bee.export_to_parent:
                export_to_parent.add(bee_name)

    @classmethod
    def _hive_build_meta_args_wrapper(cls):
        cls._hive_meta_args = args_wrapper = HiveMetaArgsWrapper(cls)

        # Execute declarators
        with hive_mode_as("declare"):
            for declarator in cls._declarators:
                declarator(args_wrapper)

    @classmethod
    def _hive_get_hive_object_class(cls, args, kwargs):
        """Find appropriate HiveObject for argument values

        Extract meta args from arguments and return remainder
        """
        if cls._hive_meta_args is None:
            cls._hive_build_meta_args_wrapper()

        # Map keyword arguments to parameters, return remaining arguments
        args, kwargs, meta_arg_values = cls._hive_meta_args.extract_from_args(args, kwargs)

        # If a new combination of parameters is provided
        return args, kwargs, cls._hive_build(meta_arg_values)

    @classmethod
    def extend(cls, name, builder=None, builder_cls=None, declarator=None, is_dyna_hive=None, bases=()):
        """Extend HiveBuilder with an additional builder (and builder class)

        :param name: name of new hive class
        :param builder: optional function used to build hive
        :param builder_cls: optional Python class to bind to hive
        :param declarator: optional declarator to establish parameters
        :param is_dyna_hive: optional flag to use dyna-hive instantiation path. If omitted (None), inherit
        :param bases: optional tuple of base classes to use
        """
        # Add base hive
        bases = bases + (cls,)

        # Validate base classes
        for base_cls in bases:
            if not issubclass(base_cls, HiveBuilder):
                raise TypeError("Expected HiveBuilder subclass, received '{}'".format(base_cls.__name__))

        # Find base class declarators and builders
        base_declarators = tuple(declarator for hive_cls in bases for declarator in hive_cls._declarators)
        base_builders = tuple(builder for hive_cls in bases for builder in hive_cls._builders)
        base_is_dyna_hive = any(hive_cls._is_dyna_hive for hive_cls in bases)

        # Validate builders
        if builder is None:
            builders = base_builders

            if builder_cls is not None:
                raise ValueError("Hive cannot be given cls without defining a builder")

        else:
            if builder_cls is not None:
                if not issubclass(builder_cls, object):
                    raise TypeError("cls must be a new-style Python class, e.g. class SomeHive(object): ...")

            # Add builder
            builders = base_builders + ((builder, builder_cls),)

        # Add declarator
        if declarator is not None:
            declarators = base_declarators + (declarator,)

        else:
            declarators = base_declarators

        # Build docstring
        docstring = "\n".join([builder.__doc__ for builder, build_cls in builders if builder.__doc__ is not None])

        # If not provided, inherit from base classes
        if is_dyna_hive is None:
            is_dyna_hive = base_is_dyna_hive

        if is_dyna_hive:
            assert declarators, "cannot set is_dyna_hive to True without declarators"

        class_dict = {
            "__doc__": docstring,
            "_builders": builders,
            "_declarators": declarators,
            "_hive_meta_args": None,
            "_is_dyna_hive": is_dyna_hive,
        }

        return type(name, bases, class_dict)


# TODO options for namespaces (old frame/hive distinction)
def hive(name, builder=None, builder_cls=None, bases=()):
    return HiveBuilder.extend(name, builder, builder_cls, bases=bases)


def dyna_hive(name, builder, declarator, builder_cls=None, bases=()):
    return HiveBuilder.extend(name, builder, builder_cls, declarator=declarator, is_dyna_hive=True, bases=bases)


def meta_hive(name, builder, declarator, builder_cls=None, bases=()):
    return HiveBuilder.extend(name, builder, builder_cls, declarator=declarator, is_dyna_hive=False, bases=bases)

# ==========Hive construction path=========
# 1. Take args and kwargs for construction call.
# 2. Extract the meta-args (defined by declarators, which are called once when the Hive is called first time).
#           If None, return empty tuple
# 3. Find a HiveObject class for the given meta arg values. If None, build HiveObject
# 4. With remaining args and kwargs, if HIVE is meta hive, construct and return metahive primitive, else:
#           If in runtime mode, create HiveObject instance and instantiate it
#           If in build mode, return HiveObject instance.
# 4.1 The MetaHive primitive exposes a __new__ constructor that performs step 4.

# ==========Hive build path================
# Hive building is bottom-up after builder functions, top down before
# 1. Call all builder functions with i, ex and args wrappers (and frozen meta args)
# 2. Find all defined HiveObject bees.
# 3. If bees set _hive_allow_export_namespace true, import appropriate plugins and sockets from child HiveObject
# 4. For all plugins and sockets of current building hive, if export_to_parent, add names to class
#       set "_hive_exportable_to_parent"
# 5. If root HIVE (get_building_hive() is None after building), top-down recurse HiveObject._hive_build_connectivity
