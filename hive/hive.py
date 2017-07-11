from abc import ABC, abstractproperty
from collections import namedtuple
from inspect import currentframe, getmodule, isclass
from itertools import count, chain

from .classes import (AttributeMapping, InternalValidator, ExternalValidator, ArgWrapper, validate_args,
                      DroneClassProxy, HiveDescriptor)
from .compatability import next, validate_signature
from .contexts import (bee_register_context, get_mode, hive_mode_as, building_hive_as, run_hive_as,
                       get_building_hive, get_matchmaker_validation_enabled)
from .exception import MatchmakingPolicyError
from .interfaces import Bee, ConnectTargetDerived, ConnectSourceDerived, TriggerSource, \
    TriggerTarget, Nameable, ConnectSource, ConnectTarget, Descriptor, Plugin, Socket
from .manager import memoize
from .private import ResolveBee, ConnectionCandidate, connect
from .typing import MatchFlags, data_types_match

MatchmakerConnectivityState = namedtuple("MatchmakerConnectivityState", "active_policies plugins sockets")


def generate_anonymous_names(fmt_string='anonymous_bee_{}'):
    """Sequential generator of "bee names"""
    for i in count():
        yield fmt_string.format(i)


def get_unique_child_hive_objects(internals):
    encountered_hives = set()
    for name, bee in internals:
        if not bee.implements(HiveObject):
            continue

        if bee in encountered_hives:
            continue

        encountered_hives.add(bee)
        yield bee


def validate_external_name(attr_name):  # todo check not leading with _ somewhere
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


class HiveInternalRuntimeWrapper:
    def __init__(self, run_hive):
        self._run_hive = run_hive


class RuntimeHive(Bee, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget, Nameable):
    """Unique Hive instance that is created at runtime for a Hive object.

    Lightweight instantiation is supported through caching performed by the HiveObject instance.
    """
    _hive_i_class = None

    def __init__(self, hive_object, builders):
        super().__init__()

        self._hive_object = hive_object
        self._drone_class_to_instance = {}
        self._name_to_runtime_bee = {}
        self._drones = []
        self._hive_i = hive_i = self._hive_i_class(self)

        with run_hive_as(self):
            # Build args
            args = hive_object._hive_builder_args
            kwargs = hive_object._hive_builder_kwargs

            for builder, drone_cls in builders:
                if drone_cls is not None:
                    assert drone_cls not in self._drone_class_to_instance, drone_cls

                    # Do not initialise instance yet
                    drone = drone_cls.__new__(drone_cls)

                    self._drone_class_to_instance[drone_cls] = drone
                    self._drones.append(drone)

                    drone.__init__(*args, **kwargs)

            with building_hive_as(hive_object.__class__), hive_mode_as("build"):
                # Add external public to runtime hive
                for bee_name, bee in hive_object._hive_ex:
                    if bee.implements(Descriptor):
                        continue

                    instance = bee.bind(self)
                    if isinstance(instance, Nameable):
                        instance.register_alias(self, bee_name)

                    setattr(self, bee_name, instance)

                # Add internal public (that are hives, Callable or Stateful) to runtime hive
                for bee_name, bee in hive_object._hive_i:
                    if bee.implements(Descriptor):
                        continue

                    instance = bee.bind(self)
                    if isinstance(instance, Nameable):
                        instance.register_alias(self, bee_name)

                    setattr(hive_i, bee_name, instance)

    @staticmethod
    def _hive_can_connect_hive(other):
        return isinstance(other, RuntimeHive)

    def _hive_find_connect_sources(self):
        return self._hive_object._hive_find_connect_sources()

    def _hive_find_connect_targets(self):
        return self._hive_object._hive_find_connect_targets()

    def _hive_trigger_source(self, target_func):
        source_name = self._hive_object._hive_find_trigger_source()
        instance = self._name_to_runtime_bee[source_name]
        return instance._hive_trigger_source(target_func)

    def _hive_trigger_target(self):
        target_name = self._hive_object._hive_find_trigger_target()
        instance = self._name_to_runtime_bee[target_name]
        return instance._hive_trigger_target()

    def _hive_get_connect_source(self, target):
        source_name = self._hive_object._hive_find_connect_source(target)
        return getattr(self, source_name)

    def _hive_get_connect_target(self, source):
        target_name = self._hive_object._hive_find_connect_target(source)
        return getattr(self, target_name)


class HiveObject(Bee, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget):
    """Built Hive base-class responsible for creating new Hive instances.

    All public defined with the builder functions are memoized and cached for faster instantiation
    """

    _hive_parent_class = None
    _hive_runtime_class = None

    _hive_i = None
    _hive_ex = None
    _hive_args = None
    _hive_meta_args_frozen = None

    _hive_exportable_to_parent = frozenset()

    def __init__(self, *args, **kwargs):
        super().__init__()

        # Automatically import parent sockets and plugins
        self._hive_allow_import_namespace = kwargs.pop("import_namespace", True)
        self._hive_allow_export_namespace = kwargs.pop("export_namespace", True)

        # Take out args parameters
        remaining_args, remaining_kwargs, arg_wrapper_values = self._hive_args.extract_from_arguments(args, kwargs)
        self._hive_args_frozen = self._hive_args.freeze(arg_wrapper_values)

        # Args to instantiate builder-class instances
        self._hive_builder_args = remaining_args
        self._hive_builder_kwargs = remaining_kwargs

        # Check build functions are valid
        for builder, drone_cls in self._hive_parent_class._builders:
            if drone_cls is not None:
                try:
                    validate_signature(drone_cls, *self._hive_builder_args, **self._hive_builder_kwargs)

                except TypeError as err:
                    raise TypeError("{}.{}".format(drone_cls.__name__, err.args[0]))

        # Create ResolveBee wrappers for external interface
        # We do NOT use 'with building_hive_as(...):' here, because these attributes are intended for use by the
        # the parent hive. They will not enter the hive namespace unless the parent accesses them with
        # 'some_hive_object.some_bee'
        # Because ResolveBee.export() returns itself, multiple levels of indirection are supported
        with hive_mode_as("build"):
            external_bees = self._hive_ex
            for bee_name, bee in external_bees:
                resolve_bee = ResolveBee(bee, self)
                setattr(self, bee_name, resolve_bee)

    def instantiate(self):
        """Return an instance of the runtime Hive for this Hive object."""
        return self._hive_runtime_class(self, self._hive_parent_class._builders)

    @memoize
    def bind(self, run_hive):
        return self.instantiate()

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

        for bee_name, bee in external_bees:
            if isinstance(bee, TriggerTarget):
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

        for bee_name, bee in external_bees:
            if isinstance(bee, TriggerSource):
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
        for bee_name, bee in externals:
            if not bee.implements(ConnectSource):
                continue

            candidate = ConnectionCandidate(bee_name, bee.data_type)
            connect_sources.append(candidate)

        return connect_sources

    @classmethod
    def _hive_find_connect_targets(cls):
        externals = cls._hive_ex

        # Find target hive ConnectTargets
        connect_targets = []
        for bee_name, bee in externals:
            if not bee.implements(ConnectTarget):
                continue

            candidate = ConnectionCandidate(bee_name, bee.data_type)
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


class MetaHivePrimitive(ABC):
    """Primitive container to instantiate Hive with particular meta arguments"""

    _hive_object_class = abstractproperty()

    def __new__(cls, *args, **kwargs):
        hive_object = cls._hive_object_class(*args, **kwargs)

        if get_mode() == "immediate":
            return hive_object.instantiate()

        return hive_object


class HiveBuilder:
    """Deferred Builder for constructing Hive classes.

    Perform building once for multiple instances of the same Hive.
    """

    _builders = ()
    _declarators = ()
    _is_dyna_hive = False

    _hive_meta_args = None

    @classmethod
    @memoize
    def _instantiate_hive_object(cls, hive_object_class, args, kwarg_items):
        kwargs = dict(kwarg_items)
        return hive_object_class(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        # If MetaHive and not DynaHive
        if cls._declarators and not cls._is_dyna_hive:
            return cls._create_meta_primitive(*args, **kwargs)

        args, kwargs, hive_object_class = cls._build_hive_object_from_arguments(args, kwargs)
        hive_object = cls._instantiate_hive_object(hive_object_class, args, tuple(kwargs.items()))

        if get_mode() == "immediate":
            return hive_object.instantiate()

        else:
            return hive_object

    @classmethod
    def _create_meta_primitive(cls, *args, **kwargs):
        """Return the MetaHivePrimitive subclass associated with the HiveObject class produced for these meta args"""
        args, kwargs, hive_object_class = cls._build_hive_object_from_arguments(args, kwargs)
        assert not args or kwargs, "Meta primitive cannot be passed any runtime-arguments"

        return cls._get_meta_primitive_class(hive_object_class)

    @classmethod
    @memoize
    def _get_meta_primitive_class(cls, hive_object_class):
        """Return the MetaHivePrimitive subclass associated with this HiveObject class """
        return type("MetaHivePrimitive::{}".format(cls.__name__), (MetaHivePrimitive,),
                    {'_hive_object_class': hive_object_class})

    @classmethod
    @memoize
    def _build(cls, meta_arg_values: tuple):
        """Build a HiveObject for this Hive, with appropriate Args instance

        :param meta_arg_values: ordered tuple of meta arg parameter values
        """
        hive_name = cls.__name__
        hive_object_dict = {'__doc__': cls.__doc__, "_hive_parent_class": cls, "__module__": cls.__module__}
        hive_object_class_name = "{}(HiveObject)".format(hive_name)
        hive_object_class = type(hive_object_class_name, (HiveObject,), hive_object_dict)

        validate_internal = InternalValidator(hive_object_class)
        validate_external = ExternalValidator(hive_object_class)

        hive_object_class._hive_i = internals = AttributeMapping("{}.i".format(hive_name), validator=validate_internal)
        hive_object_class._hive_ex = externals = AttributeMapping("{}.ex".format(hive_name),
                                                                  validator=validate_external)
        hive_object_class._hive_args = args = ArgWrapper("{}.args".format(hive_name), validator=validate_args)

        # Get frozen meta args
        frozen_meta_args = cls._hive_meta_args.freeze(dict(meta_arg_values))
        hive_object_class._hive_meta_args_frozen = frozen_meta_args

        is_root = get_building_hive() is None
        is_meta_hive = bool(cls._declarators)

        with hive_mode_as("build"), building_hive_as(hive_object_class), bee_register_context() as registered_bees:
            # Invoke builder functions to build wrappers
            for builder, drone_cls in cls._builders:
                # Call builder with appropriate arguments depending upon Hive type
                if drone_cls is not None:
                    wrapper = DroneClassProxy(drone_cls)
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

            cls._build_namespace(hive_object_class)

            # Root hives build
            if is_root:
                cls._do_matchmaking(hive_object_class)

        # Find "anonymous (non-stored)" public (using the anonymous register API) which aren't held by any wrappers,
        # anonymous_bees must be ordered to ensure execution ordering
        all_wrapper_bees = frozenset(b for n, b in chain(internals, externals))
        anonymous_bees = tuple((b for b in registered_bees if b not in all_wrapper_bees))

        # Save anonymous public to internal wrapper, with unique names
        sequential_bee_names = generate_anonymous_names()
        for bee in anonymous_bees:
            # Find unique name for bee
            while True:
                bee_name = next(sequential_bee_names)
                if not hasattr(internals, bee_name):
                    break

            setattr(internals, bee_name, bee)

        # TODO: auto-remove connections/triggers for which the source/target has been deleted
        # TODO: this implies that public must be registered on wrappers to "work"

        # Build runtime hive class
        run_hive_cls_name = "{}(RuntimeHive)".format(cls.__name__)

        # For internal public
        internal_proxy_dict = {name: HiveDescriptor(bee, instance_is_internal=True)
                               for name, bee in internals
                               if bee.implements(Descriptor)}

        hive_i_class = type("{}._hive_i".format(run_hive_cls_name),
                            (HiveInternalRuntimeWrapper,), internal_proxy_dict)
        run_hive_class_dict = {"__doc__": cls.__doc__, "__module__": cls.__module__, '_hive_i_class': hive_i_class}

        # For external public
        for bee_name, bee in externals:
            # If the bee requires a property interface, build a property
            if bee.implements(Descriptor):
                run_hive_class_dict[bee_name] = HiveDescriptor(bee)  #

        hive_object_class._hive_runtime_class = type(run_hive_cls_name, (RuntimeHive,), run_hive_class_dict)
        return hive_object_class

    @staticmethod
    def _build_matchmaking_layer(resolved_hive_object, connectivity_state: MatchmakerConnectivityState):
        """Build the matchmaking connections for a ResolveBee referring to a HiveObject instance

        :param resolved_hive_object: ResolveBee instance referring to a HiveObject instance bee
        :param connectivity_state: MatchmakingConnectivityState instance
        """
        # These public will have already been handled by parent (as this method is called top-down)
        active_policies, plugins, sockets = connectivity_state
        exportable_to_parent = resolved_hive_object._hive_exportable_to_parent \
            if getattr(resolved_hive_object,'_hive_allow_export_namespace',None) else frozenset()

        # TLDR fix this
        print("BUILD",resolved_hive_object)
        # Find sockets and plugins that are exportable
        for bee_name, _ in resolved_hive_object._hive_ex:
            if bee_name in exportable_to_parent:
                continue

            # Get fully resolvable bee reference (relative to root hive)
            # Stateful descriptors fail this
            try:
                resolved_bee = getattr(resolved_hive_object, bee_name)
            except AttributeError:
                continue

            if resolved_bee.implements(Plugin):
                register_dict = plugins
                lookup_dict = sockets
                connect_bees = connect

            elif resolved_bee.implements(Socket):
                register_dict = sockets
                lookup_dict = plugins

                def connect_bees(target, source):
                    return connect(source, target)
            else:
                continue

            identifier = resolved_bee.identifier
            if identifier is None:
                continue
            policy = resolved_bee.policy()
            match_info = resolved_bee, policy
            # Store in map of plugins or sockets
            register_dict.setdefault(identifier, []).append(match_info)
            # Keep track of instantiated policies
            active_policies.append(match_info)

            # Can we connect to a socket?
            try:
                other_bees = lookup_dict[identifier]
            except KeyError:
                continue

            for other_bee, other_policy in other_bees:
                try:
                    policy.pre_connected()
                    other_policy.pre_connected()

                    connect_bees(resolved_bee, other_bee)

                    policy.on_connected()
                    other_policy.on_connected()

                except MatchmakingPolicyError as err:
                    raise MatchmakingPolicyError(
                        "An error occurred during matchmaking {}, {}".format(bee_name, identifier)) from err

    @classmethod
    def _do_matchmaking(cls, resolved_hive_object_or_class, connectivity_state: MatchmakerConnectivityState = None):
        """Connect plugins and sockets together by identifier.

        If children allow importing of namespace, pass namespace to children.

        :param resolved_hive_object_or_class: the HiveObject class if root, else HiveObject() instance
        :param connectivity_state: state of matchmaking
        """
        internals = resolved_hive_object_or_class._hive_i

        # The first time this function is called, we are building the root hive
        is_root = connectivity_state is None
        # If root, importing/exporting from/to parent has no meaning
        if is_root:
            active_policies = []
            plugins = {}
            sockets = {}
            connectivity_state = MatchmakerConnectivityState(active_policies, plugins, sockets)
            resolved_child_hive_objects = get_unique_child_hive_objects(internals)

        # Otherwise method call applies to a HiveObject instance (resolved_bee_source)
        else:
            active_policies, plugins, sockets = connectivity_state
            # Get the external public' ResolveBee instead of raw bee, so that connect() resolves bee relative to root
            # Due to chaining of resolve public, this works
            resolved_child_hive_objects = (ResolveBee(b, resolved_hive_object_or_class) for b in
                                           get_unique_child_hive_objects(internals))
        cls._build_matchmaking_layer(resolved_hive_object_or_class, connectivity_state)

        print(resolved_hive_object_or_class, resolved_child_hive_objects)
        # Now export to child hives
        for hive_object in resolved_child_hive_objects:
            if hive_object._hive_allow_import_namespace:
                child_connectivity_state = MatchmakerConnectivityState(active_policies, plugins.copy(), sockets.copy())
                print("DO")
                cls._do_matchmaking(hive_object, child_connectivity_state)

        # Validate policies at the very end
        if is_root and get_matchmaker_validation_enabled():
            for resolved_bee, policy in active_policies:
                try:
                    policy.validate()

                except MatchmakingPolicyError as err:
                    raise MatchmakingPolicyError("Error in validating policy of {}".format(resolved_bee)) from err

    @classmethod
    def _build_namespace(cls, hive_object_cls):
        """Build namespace of plugins and sockets within a given HiveObject class

        Requires that child HiveObjects have already performed this step

        :param hive_object_cls: HiveObject class being built
        """
        externals = hive_object_cls._hive_ex
        internals = hive_object_cls._hive_i

        # Export public from drone-like child hives
        for child_hive in get_unique_child_hive_objects(internals):
            if not child_hive._hive_allow_export_namespace:
                continue

            # Find exportable from child and save to HiveObject instance
            importable_from_child = child_hive._hive_exportable_to_parent

            # Find public at set them on parent
            for bee_name in importable_from_child:
                assert not hasattr(externals, bee_name), bee_name
                bee = getattr(child_hive, bee_name)
                setattr(externals, bee_name, bee)

        # Exportable public to parent if drone
        exportable_to_parent = frozenset((n for n, b in externals if (b.implements(Plugin) or b.implements(Socket))
                                          and b.identifier is not None and b.export_to_parent))
        hive_object_cls._hive_exportable_to_parent = exportable_to_parent

    @classmethod
    def _hive_build_meta_args_wrapper(cls):
        cls._hive_meta_args = args_wrapper = ArgWrapper("{}.meta_args".format(cls), validator=validate_args)

        # Execute declarators
        with hive_mode_as("declare"):
            for declarator in cls._declarators:
                declarator(args_wrapper)

    @classmethod
    def _build_hive_object_from_arguments(cls, args: tuple, kwargs: dict) -> tuple:
        """Find appropriate HiveObject for argument values
    
        Extract meta args from arguments and return remainder
        """
        if cls._hive_meta_args is None:
            cls._hive_build_meta_args_wrapper()

        # Map keyword arguments to parameters, return remaining arguments
        args, kwargs, meta_args = cls._hive_meta_args.extract_from_arguments(args, kwargs)

        # Create ordered tuple of meta arg parameters
        meta_args_items = tuple((n, meta_args[n]) for n, p in cls._hive_meta_args)

        # If a new combination of parameters is provided
        return args, kwargs, cls._build(meta_args_items)

    @classmethod
    def extend(cls, name, builder=None, drone_class=None, declarator=None, is_dyna_hive=None, bases=(), module=None):
        """Extend HiveBuilder with an additional builder (and builder class)
    
        :param name: name of new hive class
        :param builder: optional function used to build hive
        :param drone_class: optional Python class to bind to hive
        :param declarator: optional declarator to establish parameters
        :param is_dyna_hive: optional flag to use dyna-hive instantiation path. If omitted (None), inherit
        :param bases: optional tuple of base classes to use
        """
        # Ugly frame hack to find the name of the module in which this give was created
        if module is None:
            frame = currentframe()
            this_mod = getmodule(frame)
            while getmodule(frame) is this_mod:
                frame = frame.f_back
            module = getmodule(frame).__name__

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

        if drone_class is not None and not isclass(drone_class):
            raise TypeError("cls must be a Python class, e.g. class SomeHive(object): ...")

        # Validate builders
        if builder is None:
            builders = base_builders

            if drone_class is not None:
                raise ValueError("Hive cannot be given cls without defining a builder")

        else:
            # Add builder
            builders = base_builders + ((builder, drone_class),)

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
            "__module__": module
        }
        return type(name, bases, class_dict)


def hive(name, builder=None, drone_class=None, bases=()):
    return HiveBuilder.extend(name, builder, drone_class, bases=bases)


def dyna_hive(name, builder, declarator, drone_class=None, bases=()):
    return HiveBuilder.extend(name, builder, drone_class, declarator=declarator, is_dyna_hive=True, bases=bases)


def meta_hive(name, builder, declarator, drone_class=None, bases=()):
    return HiveBuilder.extend(name, builder, drone_class, declarator=declarator, is_dyna_hive=False, bases=bases)

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
# 2. Find all defined HiveObject public.
# 3. If public set _hive_allow_export_namespace true, import appropriate plugins and sockets from child HiveObject
# 4. For all plugins and sockets of current building hive, if export_to_parent, add names to class
#       set "_hive_exportable_to_parent"
# 5. If root HIVE (get_building_hive() is None after building), top-down recurse HiveObject._hive_build_connectivity
