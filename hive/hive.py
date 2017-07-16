from abc import ABC, abstractproperty
from inspect import currentframe, getmodule
from itertools import count, chain
from typing import List, Generator, NamedTuple, Callable, Type, Dict, Union, Tuple, Any, Optional

from .classes import (AttributeMapping, InternalValidator, ExternalValidator, ArgWrapper, validate_args, HiveDescriptor)
from .compatability import next
from .contexts import (bee_register_context, get_mode, hive_mode_as, building_hive_as, run_hive_as,
                       get_building_hive, get_matchmaker_validation_enabled, HiveMode)
from .exception import MatchmakingPolicyError, HiveBuilderError
from .interfaces import (BeeBase, ConnectTargetDerived, ConnectSourceDerived, TriggerSource, TriggerTarget, Nameable,
                         ConnectSource, ConnectTarget, Descriptor, Plugin, Socket)
from .manager import memoize
from .parameter import Parameter
from .policies import MatchmakingPolicy
from .private import ResolveBee, ConnectCandidate, connect
from .typing import MatchFlags, data_types_match

BuilderType = Callable[[AttributeMapping, AttributeMapping, AttributeMapping, Optional[AttributeMapping]], None]
ConfigurerType = Callable[[AttributeMapping], None]
BasesType = Tuple[Type['HiveBuilder'], ...]


class TrackedPolicy(NamedTuple):
    bee: Union[Plugin, Socket]
    policy: MatchmakingPolicy


class MatchmakerConnectivityState(NamedTuple):
    active_policies: List[TrackedPolicy]
    plugins: Dict[Plugin, List[TrackedPolicy]]
    sockets: Dict[Socket, List[TrackedPolicy]]


def get_previous_module_name() -> str:
    frame = currentframe()
    this_mod = getmodule(frame)
    while getmodule(frame) is this_mod:
        frame = frame.f_back
    return getmodule(frame).__name__


def generate_anonymous_names(fmt_string: str = 'anonymous_bee_{}') -> Generator[str, None, None]:
    """Sequential generator of "bee names"""
    for i in count():
        yield fmt_string.format(i)


def get_unique_child_hive_objects(internals: AttributeMapping) -> Generator['HiveObject', None, None]:
    """Yield each first-encountered HiveObject instance on the interals wrapper"""
    encountered_hives = set()
    for name, bee in internals:
        if not isinstance(bee, HiveObject):
            continue

        if bee in encountered_hives:
            continue

        encountered_hives.add(bee)
        yield bee


def validate_external_name(attr_name: str):
    """Raise AttributeError if attribute name belongs to HiveObject or RuntimeHive"""
    if hasattr(HiveObject, attr_name):
        raise AttributeError('Cannot overwrite special attribute HiveObject.{}'.format(attr_name))

    if hasattr(RuntimeHive, attr_name):
        raise AttributeError('Cannot overwrite special attribute RuntimeHive.{}'.format(attr_name))


def validate_internal_name(attr_name: str):
    """Raise AttributeError if attribute name prefixed with underscore belongs to HiveObject or RuntimeHive"""
    internal_name = "_{}".format(attr_name)

    if hasattr(HiveObject, internal_name):
        raise AttributeError('Cannot overwrite special attribute HiveObject.{}'.format(attr_name))

    if hasattr(RuntimeHive, internal_name):
        raise AttributeError('Cannot overwrite special attribute RuntimeHive.{}'.format(attr_name))


def resolve_arguments(run_hive, arg_values):
    resolve_parameter = run_hive._hive_object._hive_args_frozen.resolve_parameter
    return (resolve_parameter(a) if isinstance(a, Parameter) else a for a in arg_values)


class RuntimeHive(BeeBase, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget, Nameable):
    """Unique Hive instance that is created at runtime for a Hive object.

    Lightweight instantiation is supported through caching performed by the HiveObject instance.
    """
    _hive_i_class = None

    def __init__(self, hive_object: 'HiveObject', hive_args_resolved: tuple):
        super().__init__()

        self._hive_object = hive_object
        self._name_to_runtime_bee = {}
        self._hive_i = hive_i = self._hive_i_class(self)
        self._hive_args_frozen = hive_args_resolved

        with run_hive_as(self):
            with building_hive_as(hive_object.__class__), hive_mode_as(HiveMode.BUILD):
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

    def _hive_find_connect_sources(self) -> List[ConnectCandidate]:
        return self._hive_object._hive_find_connect_sources()

    def _hive_find_connect_targets(self) -> List[ConnectCandidate]:
        return self._hive_object._hive_find_connect_targets()

    def _hive_trigger_source(self, target_func: Callable[[], None]):
        source_name = self._hive_object._hive_find_trigger_source()
        instance = self._name_to_runtime_bee[source_name]
        return instance._hive_trigger_source(target_func)

    def _hive_trigger_target(self) -> Callable[[], None]:
        target_name = self._hive_object._hive_find_trigger_target()
        instance = self._name_to_runtime_bee[target_name]
        return instance._hive_trigger_target()

    def _hive_get_connect_source(self, target: ConnectTarget) -> ConnectSource:
        source_name = self._hive_object._hive_find_connect_source(target)
        return getattr(self, source_name)

    def _hive_get_connect_target(self, source: ConnectSource) -> ConnectTarget:
        target_name = self._hive_object._hive_find_connect_target(source)
        return getattr(self, target_name)


class HiveObject(BeeBase, ConnectSourceDerived, ConnectTargetDerived, TriggerSource, TriggerTarget):
    """Built Hive base-class responsible for creating new Hive instances.

    All public defined with the builder functions are memoized and cached for faster instantiation
    """

    _hive_parent_class = None
    _hive_runtime_class = None

    # Wrappers
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

        # Take out args required by _hive_args wrapper
        remaining_args, remaining_kwargs, arg_wrapper_values = self._hive_args.extract_from_arguments(args, kwargs)

        assert not remaining_args
        assert not remaining_kwargs

        # Store extracted hive args, but don't build wrapper yet (as need to resolve Parameters from parent)
        self._hive_arg_values = arg_wrapper_values

        # Create ResolveBee wrappers for external interface
        # We do NOT use 'with building_hive_as(...):' here, because these attributes are intended for use by the
        # the parent hive. They will not enter the hive namespace unless the parent accesses them with
        # 'some_hive_object.some_bee'
        # Because ResolveBee.export() returns itself, multiple levels of indirection are supported
        with hive_mode_as(HiveMode.BUILD):
            external_bees = self._hive_ex
            for bee_name, bee in external_bees:
                resolve_bee = ResolveBee(bee, self)
                setattr(self, bee_name, resolve_bee)

    def instantiate(self) -> RuntimeHive:
        """Return an instance of the runtime Hive for this Hive object."""
        return self._hive_runtime_class(self, self._hive_args.freeze(self._hive_arg_values))

    @memoize
    def bind(self, run_hive: RuntimeHive) -> RuntimeHive:
        from .parameter import Parameter
        arg_values = resolve_arguments(run_hive, self._hive_arg_values)
        return self._hive_runtime_class(self, self._hive_args.freeze(arg_values))

    @classmethod
    def _hive_find_trigger_target(cls) -> str:
        """Find name of single external bee that supported TriggerTarget interface.

        Raise TypeError if such a condition cannot be met
        """
        external_bees = cls._hive_ex
        trigger_targets = []

        for bee_name, bee in external_bees:
            if bee.implements(TriggerTarget):
                trigger_targets.append(bee_name)

        if not trigger_targets:
            raise TypeError("No trigger targets in %s" % cls)
        elif len(trigger_targets) > 1:
            raise TypeError("Multiple trigger targets in {}: {}".format(cls, trigger_targets))

        return trigger_targets[0]

    @classmethod
    def _hive_find_trigger_source(cls) -> str:
        """Find and return name of single external bee that supported TriggerSource interface.

        Raise TypeError if such a condition cannot be met
        """
        external_bees = cls._hive_ex
        trigger_sources = []

        for bee_name, bee in external_bees:
            if bee.implements(TriggerSource):
                trigger_sources.append(bee_name)

        if not trigger_sources:
            raise TypeError("No TriggerSources in %s" % cls)
        elif len(trigger_sources) > 1:
            raise TypeError("Multiple TriggerSources in %s: %s" % (cls, trigger_sources))

        return trigger_sources[0]

    @classmethod
    def _hive_find_connect_sources(cls) -> List[ConnectCandidate]:
        externals = cls._hive_ex

        # Find source hive ConnectSources
        connect_sources = []
        for bee_name, bee in externals:
            if not bee.implements(ConnectSource):
                continue

            candidate = ConnectCandidate(bee_name, bee.data_type)
            connect_sources.append(candidate)

        return connect_sources

    @classmethod
    def _hive_find_connect_targets(cls) -> List[ConnectCandidate]:
        externals = cls._hive_ex

        # Find target hive ConnectTargets
        connect_targets = []
        for bee_name, bee in externals:
            if not bee.implements(ConnectTarget):
                continue

            candidate = ConnectCandidate(bee_name, bee.data_type)
            connect_targets.append(candidate)

        return connect_targets

    @classmethod
    def _hive_find_connect_source(cls, target: ConnectTarget) -> str:
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
    def _hive_find_connect_target(cls, source: ConnectSource) -> str:
        """Find and return the name of a suitable connect target within this hive
F
        :param source: source to connect to
        """
        assert isinstance(source, ConnectSource)  # TODO don't want implements but do want to handle resolvebee

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

    def _hive_get_trigger_target(self) -> TriggerTarget:
        """Return single external bee that supported TriggerTarget interface"""
        trigger_name = self._hive_find_trigger_target()
        return getattr(self, trigger_name)

    def _hive_get_trigger_source(self) -> TriggerSource:
        """Return single external bee that supported TriggerSource interface"""
        trigger_name = self._hive_find_trigger_source()
        return getattr(self, trigger_name)

    def _hive_get_connect_target(self, source) -> ConnectTarget:
        """Return single external bee that supported ConnectTarget interface"""
        target_name = self._hive_find_connect_target(source)
        return getattr(self, target_name)

    def _hive_get_connect_source(self, target) -> ConnectSource:
        """Return single external bee that supported ConnectSource interface"""
        source_name = self._hive_find_connect_source(target)
        return getattr(self, source_name)


class MetaHivePrimitive(ABC):
    """Primitive container to instantiate Hive with particular meta arguments"""

    _hive_object_class: Type[HiveObject] = abstractproperty()

    def __new__(cls, *args, **kwargs) -> Union[HiveObject, RuntimeHive]:
        hive_object = cls._hive_object_class(*args, **kwargs)

        if get_mode() == HiveMode.IMMEDIATE:
            return hive_object.instantiate()
        return hive_object


# TODO should this be the special AttributeMapping wrapper?
class HiveInternalRuntimeWrapper:
    """Base class for _hive_i runtime wrapper"""

    def __init__(self, run_hive: RuntimeHive):
        self._run_hive = run_hive


class HiveBuilder:
    """Deferred Builder for constructing Hive classes.

    Perform building once for multiple instances of the same Hive.
    """

    _builders: Tuple[BuilderType, ...] = ()
    _configurers: Tuple[ConfigurerType, ...] = ()
    _is_dyna_hive: bool = False
    _hive_meta_args: ArgWrapper = None

    def __new__(cls, *new_args, **new_kwargs) -> Union[Type[MetaHivePrimitive], HiveObject, RuntimeHive]:
        # Meta hives receive their meta args, and normal args in two separate calls (so don't try and parse args yet)
        if cls._configurers and not cls._is_dyna_hive:
            return cls._create_meta_primitive(*new_args, **new_kwargs)

        args, kwargs, hive_object_class = cls._hive_object_class_from_args(new_args, new_kwargs)
        hive_object = cls._new(hive_object_class, args, tuple(kwargs.items()))

        if get_mode() == HiveMode.IMMEDIATE:
            return hive_object.instantiate()

        return hive_object

    @classmethod
    def extend(cls, name, builder: BuilderType = None, configurer: ConfigurerType = None,
               is_dyna_hive: bool = None, bases: BasesType = (), module_name: str = None) -> Type['HiveBuilder']:
        """Extend HiveBuilder with an additional builder (and builder class)

        :param name: name of new hive class
        :param builder: optional function used to build hive
        :param configurer: optional configurer to establish meta-parameters
        :param is_dyna_hive: optional flag to use dyna-hive instantiation path. If omitted (None), inherit
        :param bases: optional tuple of base classes to use
        :param module_name: name of module in which hive is defined. If not provided, a frame hack will be used
        """
        # Ugly frame hack to find the name of the module in which this give was created
        if module_name is None:
            module_name = get_previous_module_name()

        # Validate base classes
        bases = bases + (cls,)
        for base_cls in bases:
            if not issubclass(base_cls, HiveBuilder):
                raise TypeError("Expected HiveBuilder subclass, received '{}'".format(base_cls.__name__))

        # Find base class configurers and builders
        base_configurers = tuple(configurer for hive_cls in bases for configurer in hive_cls._configurers)
        base_builders = tuple(builder for hive_cls in bases for builder in hive_cls._builders)
        base_is_dyna_hive = any(hive_cls._is_dyna_hive for hive_cls in bases)

        # Validate builders
        if builder is None:
            builders = base_builders
        else:
            # Add builder
            builders = base_builders + (builder,)

        # Add configurer
        configurers = base_configurers
        if configurer is not None:
            configurers += (configurer,)

        # Build docstring
        docstring = "\n".join([builder.__doc__ for builder in builders if builder.__doc__ is not None])

        # If not provided, inherit from base classes
        if is_dyna_hive is None:
            is_dyna_hive = base_is_dyna_hive

        if is_dyna_hive and not configurers:
            raise ValueError("Cannot set is_dyna_hive to True without any meta configurers")

        class_dict = {
            "__doc__": docstring,
            "_builders": builders,
            "_configurers": configurers,
            "_hive_meta_args": None,
            "_is_dyna_hive": is_dyna_hive,
            "__module__": module_name
        }
        builder_class: Type[HiveBuilder] = type(name, bases, class_dict)
        return builder_class

    @classmethod
    def _create_meta_primitive(cls, *args, **kwargs) -> Type[MetaHivePrimitive]:
        """Return the MetaHivePrimitive subclass associated with the HiveObject class produced for these meta args"""
        args, kwargs, hive_object_class = cls._hive_object_class_from_args(args, kwargs)
        assert not args or kwargs, "Meta primitive cannot be passed any runtime-arguments"

        return cls._get_meta_primitive_class(hive_object_class)

    @classmethod
    @memoize
    def _new(cls, hive_object_class: Type[HiveObject], args: tuple,
             kwarg_items: Tuple[Tuple[str, Any], ...]) -> HiveObject:
        kwargs = dict(kwarg_items)
        return hive_object_class(*args, **kwargs)

    @classmethod
    @memoize
    def _get_meta_primitive_class(cls, hive_object_class: Type[HiveObject]) -> Type[MetaHivePrimitive]:
        """Return the MetaHivePrimitive subclass associated with this HiveObject class """
        meta_primitive_class: Type[MetaHivePrimitive] = type("MetaHivePrimitive::{}".format(cls.__name__),
                                                             (MetaHivePrimitive,),
                                                             {'_hive_object_class': hive_object_class})

        return meta_primitive_class

    @classmethod
    @memoize
    def _build(cls, meta_arg_items: Tuple[Tuple[str, Any], ...]) -> Type[HiveObject]:
        """Build a HiveObject for this Hive, with appropriate Args instance

        :param meta_arg_values: ordered tuple of meta arg parameter values
        """
        hive_name = cls.__name__
        hive_object_class_name = "{}(HiveObject)".format(hive_name)
        hive_object_dict = {'__doc__': cls.__doc__, "_hive_parent_class": cls, "__module__": cls.__module__}
        hive_object_class: Type[HiveObject] = type(hive_object_class_name, (HiveObject,), hive_object_dict)

        validate_internal = InternalValidator(hive_object_class)
        validate_external = ExternalValidator(hive_object_class)

        hive_object_class._hive_i = internals = AttributeMapping("{}._hive_i".format(hive_name),
                                                                 validator=validate_internal)
        hive_object_class._hive_ex = externals = AttributeMapping("{}._hive_ex".format(hive_name),
                                                                  validator=validate_external)
        hive_object_class._hive_args = args = ArgWrapper("{}._hive_args".format(hive_name), validator=validate_args)
        hive_object_class._hive_meta_args_frozen = meta_args_frozen = cls._hive_meta_args.freeze(dict(meta_arg_items))

        is_root = get_building_hive() is None
        is_meta_hive = bool(cls._configurers)

        with hive_mode_as(HiveMode.BUILD), building_hive_as(hive_object_class), \
             bee_register_context() as registered_bees:
            # Invoke builder functions to build wrappers
            for builder in cls._builders:
                # Call builder with appropriate arguments depending upon Hive type
                builder_args = internals, externals, args

                if is_meta_hive:
                    builder_args = builder_args + (meta_args_frozen,)

                try:
                    builder(*builder_args)

                except Exception as err:
                    raise HiveBuilderError("Unable to invoke builder {!r}".format(builder)) from err

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

        hive_i_class = type("{}._hive_i".format(run_hive_cls_name), (HiveInternalRuntimeWrapper,), internal_proxy_dict)
        run_hive_class_dict = {"__doc__": cls.__doc__, "__module__": cls.__module__, '_hive_i_class': hive_i_class}

        # For external public
        for bee_name, bee in externals:
            # If the bee requires a property interface, build a property
            if bee.implements(Descriptor):
                run_hive_class_dict[bee_name] = HiveDescriptor(bee)  #

        hive_object_class._hive_runtime_class = type(run_hive_cls_name, (RuntimeHive,), run_hive_class_dict)
        return hive_object_class

    @classmethod
    def _build_namespace(cls, hive_object_cls: Type[HiveObject]):
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
    def _do_matchmaking(cls, resolved_hive_object_or_class: Union[ResolveBee, Type[HiveObject], HiveObject],
                        connectivity_state: MatchmakerConnectivityState = None):
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
            bees = ((n, b) for n, b in resolved_hive_object_or_class._hive_ex if
                    b.implements(Plugin) or b.implements(Socket))

        # Otherwise method call applies to a HiveObject instance (resolved_bee_source)
        else:
            active_policies, plugins, sockets = connectivity_state
            # Get the external public' ResolveBee instead of raw bee, so that connect() resolves bee relative to root
            # Due to chaining of resolve public, this works
            resolved_child_hive_objects = (ResolveBee(b, resolved_hive_object_or_class) for b in
                                           get_unique_child_hive_objects(internals))
            if resolved_hive_object_or_class._hive_allow_export_namespace:
                handled_by_parent = resolved_hive_object_or_class._hive_exportable_to_parent
            else:
                handled_by_parent = frozenset()
            bees = [(n, getattr(resolved_hive_object_or_class, n)) for n, b in resolved_hive_object_or_class._hive_ex
                    if (b.implements(Plugin) or b.implements(Socket)) and not n in handled_by_parent]

        # These public will have already been handled by parent (as this method is called top-down)
        cls._perform_matchmaking(bees, connectivity_state)

        # Now export to child hives
        for hive_object in resolved_child_hive_objects:
            if hive_object._hive_allow_import_namespace:
                child_connectivity_state = MatchmakerConnectivityState(active_policies, plugins.copy(), sockets.copy())
                cls._do_matchmaking(hive_object, child_connectivity_state)

        # Validate policies at the very end
        if is_root and get_matchmaker_validation_enabled():
            for resolved_bee, policy in active_policies:
                try:
                    policy.validate()

                except MatchmakingPolicyError as err:
                    raise MatchmakingPolicyError("Error in validating policy of {}".format(resolved_bee)) from err

    @classmethod
    def _hive_build_meta_args_wrapper(cls) -> ArgWrapper:
        args_wrapper = ArgWrapper("{}.meta_args".format(cls), validator=validate_args)

        # Execute configurers
        with hive_mode_as(HiveMode.DECLARE):
            for configurer in cls._configurers:
                configurer(args_wrapper)

        return args_wrapper

    @classmethod
    def _hive_object_class_from_args(cls, args: tuple, kwargs: Dict[str, Any]
                                     ) -> Tuple[tuple, Dict[str, Any], Type[HiveObject]]:
        """Find appropriate HiveObject for argument values
    
        Extract meta args from arguments and return remainder
        """
        if cls._hive_meta_args is None:
            cls._hive_meta_args = cls._hive_build_meta_args_wrapper()

        # Map keyword arguments to parameters, return remaining argumentss
        args, kwargs, meta_args = cls._hive_meta_args.extract_from_arguments(args, kwargs)
        return args, kwargs, cls._build(tuple(meta_args.items()))

    @staticmethod
    def _perform_matchmaking(bees: List[Tuple[str, Any]], connectivity_state: MatchmakerConnectivityState):
        """Build the matchmaking connections for a ResolveBee referring to a HiveObject instance

        :param resolved_hive_object: ResolveBee instance referring to a HiveObject instance bee
        :param connectivity_state: MatchmakingConnectivityState instance
        """
        # These public will have already been handled by parent (as this method is called top-down)
        active_policies, plugins, sockets = connectivity_state
        # Find sockets and plugins that are exportable
        for bee_name, resolved_bee in bees:
            if resolved_bee.implements(Plugin):
                register_dict = plugins
                lookup_dict = sockets
                connect_bees = connect

            else:
                register_dict = sockets
                lookup_dict = plugins

                def connect_bees(target, source):
                    return connect(source, target)

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


def hive(name, builder: BuilderType = None, bases: BasesType = ()) -> Type[HiveBuilder]:
    return HiveBuilder.extend(name, builder, bases=bases)


def dyna_hive(name, builder: BuilderType, configurer: ConfigurerType, bases: BasesType = ()) -> Type[HiveBuilder]:
    return HiveBuilder.extend(name, builder, configurer=configurer, is_dyna_hive=True, bases=bases)


def meta_hive(name, builder: BuilderType, configurer: ConfigurerType, bases: BasesType = ()) -> Type[HiveBuilder]:
    return HiveBuilder.extend(name, builder, configurer=configurer, is_dyna_hive=False, bases=bases)

# ==========Hive construction path=========
# 1. Take args and kwargs for construction call.
# 2. Extract the meta-args (defined by configurers, which are called once when the Hive is called first time).
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
