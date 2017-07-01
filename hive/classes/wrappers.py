from abc import ABC, abstractproperty
from collections import OrderedDict, namedtuple

from ..compatability import next
from ..protocols import Bee, Exportable, Parameter

ExtractedArguments = namedtuple("ExtractedArguments", "args kwargs parameter_values")


class MappingObject:
    def __init__(self, ordered_mapping):
        """MappingObject initialiser"""
        if not isinstance(ordered_mapping, OrderedDict):
            raise ValueError("Expected OrderedDict")
        self._ordered_mapping = OrderedDict()

    @property
    def _repr_name(self):
        return repr(self)

    def __getattr__(self, name):
        try:
            return self._ordered_mapping[name]
        except KeyError:
            raise AttributeError("{} has no attribute {!r}".format(self._repr_name, name))

    def __delattr_(self, name):
        raise AttributeError("Cannot delete attributes from {}".format(self._repr_name))

    def __setattr__(self, name, value):
        if not name.startswith("_"):
            raise AttributeError("Cannot modify attributes on {}".format(self._repr_name))
        super().__setattr__(name, value)

    def __bool__(self):
        return bool(self._ordered_mapping)

    def __dir__(self):
        return super().__dir__() + tuple(self._ordered_mapping)

    def __iter__(self):
        return iter(self._ordered_mapping.items())

    def __repr__(self):
        attributes_string = ', '.join("{}={!r}".format(k, v) for k, v in self._ordered_mapping.items())
        return "{}({})".format(self._repr_name, attributes_string)


class MutableMappingObject(MappingObject):
    def __init__(self, ordered_mapping=None, validator=None):
        """MutableMaping initialiser

        :param ordered_mapping: default values for attributes
        :param validator: validate attributes before they're set
        """
        if ordered_mapping is None:
            ordered_mapping = OrderedDict()
        super().__init__(ordered_mapping)

        self._validator = validator

    def _validate_attribute(self, name: str, value):
        if self._validator is not None:
            self._validator(name, value)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            return object.__setattr__(self, name, value)

        self._validate_attribute(name, value)
        self._ordered_mapping[name] = value

    def __delattr__(self, name):
        try:
            del self._ordered_mapping[name]
        except KeyError:
            raise AttributeError("{} has no attribute {!r}".format(self._repr_name, name))


class HiveObjectWrapperBase(MutableMappingObject, ABC):
    """Base class for wrappers belonging to HiveObject (i, ex)"""
    _wrapper_name = abstractproperty()

    def __init__(self, hive_object_class, validator=None):
        self._hive_object_class = hive_object_class

        super().__init__(validator=validator)

    @property
    def _repr_name(self):
        hive_name = self._hive_object_class._hive_parent_class.__name__
        return "{}.{}".format(hive_name, self._wrapper_name)

    def _validate_attribute(self, name: str, value):
        super()._validate_attribute(name, value)

        if value._parent_hive_object_class is None:
            raise AttributeError("{} bees must be defined inside the builder function"
                                 .format(self._repr_name, name))

        # TODO should permit ResolveBees here
        if value._parent_hive_object_class is not self._hive_object_class:
            raise AttributeError("{} bees cannot be built by a different hive".format(name))


class InternalWrapper(HiveObjectWrapperBase):
    _wrapper_name = "i"

    def _validate_attribute(self, name: str, value):
        super()._validate_attribute(name, value)

        if not isinstance(value, Bee):
            raise TypeError("{} attributes must be Bees ,not {}".format(self._repr_name, type(value)))

        if isinstance(value, Exportable):
            raise TypeError("{} attributes must not not be Exportable, Exportables should be added to ex"
                            .format(self._repr_name))


class ExternalWrapper(HiveObjectWrapperBase):
    _wrapper_name = "ex"

    def _validate_attribute(self, name: str, value):
        super()._validate_attribute(name, value)

        if not isinstance(value, Bee):
            raise TypeError("{} attributes must be Bees, not {}".format(self._repr_name, type(value)))

        if not isinstance(value, Exportable):
            raise TypeError("{} attributes must be Exportable".format(self._repr_name))


class ArgWrapperBase(MappingObject):
    """Base class for hive argument wrappers"""

    def _validate_attribute(self, name: str, value):
        super()._validate_attribute(name, value)

        if not isinstance(value, Parameter):
            raise TypeError(self._format_message("attribute '{}' must be a Parameter, not '{}'"
                                                 .format(name, value.__class__)))

    def freeze(self, parameters: dict):
        """Resolve all parameter values with their parameter objects and return FrozenHiveArgs view

        :param parameters: dictionary of parameter values
        """
        parameter_dict = {}

        for name, param in self._ordered_mapping.items():
            value = parameters[name]

            parameter = self._ordered_mapping[name]

            options = parameter.options
            if options is not None and value not in options:
                raise ValueError("Invalid value for {}: {!r} is not in the permitted options {}"
                                 .format(name, value, options))

            parameter_dict[name] = value

        return ResolvedArgWrapper(self, parameter_dict)

    def extract_from_arguments(self, args: tuple, kwargs: dict) -> ExtractedArguments:
        """Extract parameter values from arguments and keyword arguments provided to the building hive.

        Return the new args and kwargs wrappers, and an dict of extracted parameter values

        :param args: tuple of argument values
        :param kwargs: dict of keyword name value pairs
        """
        iter_args = iter(args)
        remaining_kwargs = kwargs.copy()
        found_param_values = {}

        # Extract args
        for name, parameter in self._ordered_mapping.items():
            # If param name in kwargs dict, switch to kwargs
            if name in kwargs:
                break

            value = next(iter_args)  # TODO error
            found_param_values[name] = value

        remaining_args = tuple(iter_args)

        # Extract kwargs
        for name in kwargs:
            if name not in self._ordered_mapping:
                continue

            if name in found_param_values:
                raise ValueError("Multiple values for {}".format(name))

            found_param_values[name] = remaining_kwargs.pop(name)

        # Build defaults
        all_param_values = {}

        for name, parameter in self._ordered_mapping.items():
            try:
                value = found_param_values[name]
            except KeyError:
                # Check if we can omit the value
                if parameter.start_value is Parameter.no_value:
                    raise ValueError(self._format_message("No value for '{}' can be resolved".format(name)))
                else:
                    value = parameter.start_value

            all_param_values[name] = value

        return ExtractedArguments(remaining_args, remaining_kwargs, all_param_values)


class ArgsWrapper(HiveObjectWrapperBase, ArgWrapperBase):
    """Hive 'args' wrapper"""
    _wrapper_name = "args"


class HiveParentWrapperBase(MutableMappingObject, ABC):
    """Base class for wrapper which refers to its parent hive class"""
    _wrapper_name = abstractproperty()

    def __init__(self, hive_parent_cls, validator=None):
        self._hive_parent_cls = hive_parent_cls

        super().__init__(validator=validator)

    @property
    def _repr_name(self):
        return "{}.{}".format(self._hive_parent_cls.__name__, self._wrapper_name)


class MetaArgsWrapper(HiveParentWrapperBase, ArgWrapperBase):
    _wrapper_name = "meta_args"



class ResolvedArgWrapper(MappingObject):
    """Read-only view of true values of an args wrapper"""

    def __init__(self, wrapper, name_to_value):
        """Initialiser for a read-only view of the resolved values of an args wrapper

        :param wrapper: name of args wrapper 
        :param resolved_mapping: OrderedDict mapping """
        ordered_name_to_value = OrderedDict(((n, name_to_value[n]) for n, p in wrapper))
        super().__init__(ordered_name_to_value)

        self._wrapper = wrapper
        self._param_to_name = {p: n for n, p in wrapper}

    @property
    def _repr_name(self):
        return "{}(resolved)".format(self._wrapper._repr_name)

    def resolve_parameter(self, parameter):
        """Retrieve the value associated with the given parameter

        :param parameter: HiveParameter instance
        """
        name = self._param_to_name[parameter]
        return self._ordered_mapping[name]
