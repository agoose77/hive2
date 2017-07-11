from abc import ABC, abstractmethod
from collections import OrderedDict, namedtuple

from ..compatability import next
from ..interfaces import Bee, Exportable
from ..parameter import Parameter

ExtractedArguments = namedtuple("ExtractedArguments", "args kwargs parameter_values")


class ImmutableAttributeMapping:
    def __init__(self, name: str, ordered_mapping: OrderedDict):
        """ImmutableAttributeMapping initialiser"""
        if not isinstance(ordered_mapping, OrderedDict):
            raise ValueError("Expected OrderedDict")
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_ordered_mapping', ordered_mapping)

    def __getattr__(self, name):
        try:
            return self._ordered_mapping[name]
        except KeyError:
            raise AttributeError("{} has no attribute {!r}".format(self._name, name))

    def __delattr__(self, name):
        raise AttributeError("Cannot delete attributes from {}".format(self._name))

    def __setattr__(self, name, value):
        raise AttributeError("Cannot modify attributes on {}".format(self._name))

    def __bool__(self):
        return bool(self._ordered_mapping)

    def __dir__(self):
        return object.__dir__(self) + list(self._ordered_mapping)

    def __iter__(self):
        return iter(self._ordered_mapping.items())

    def __str__(self):
        if self._ordered_mapping:
            attributes_string = ', '.join("\n  .{} = {!r}".format(k, v) for k, v in self._ordered_mapping.items())
            return "{}{}".format(self._name, attributes_string)
        else:
            return self._name


class AttributeMapping(ImmutableAttributeMapping):
    def __init__(self, name: str, ordered_mapping: OrderedDict = None, validator=None):
        """MutableMaping initialiser

        :param ordered_mapping: default values for attributes
        :param validator: validate attributes before they're set
        """
        object.__setattr__(self, '_validator', validator)

        if ordered_mapping is None:
            ordered_mapping = OrderedDict()

        super().__init__(name, ordered_mapping)

    def _validate_attribute(self, name: str, value):
        if self._validator is not None:
            try:
                self._validator(self, name, value)
            except ValueError as err:
                raise AttributeError("Error setting attribute {}.{}".format(self._name, name)) from err

    def __setattr__(self, name, value):
        self._validate_attribute(name, value)
        self._ordered_mapping[name] = value

    def __delattr__(self, name):
        try:
            del self._ordered_mapping[name]
        except KeyError:
            raise AttributeError("{} has no attribute {!r}".format(self._name, name))


class ValidatorBase(ABC):
    @abstractmethod
    def __call__(self, wrapper: AttributeMapping, name: str, value):
        pass


class BaseBeeValidator(ValidatorBase):
    """Validator for Bees which are associated with a HiveObject builder hive"""

    def __init__(self, hive_object_class):
        self._hive_object_class = hive_object_class

    def __call__(self, wrapper: AttributeMapping, name: str, value):
        if name.startswith("_"):
            raise ValueError("BeeBase names cannot start with underscores")

        if not isinstance(value, Bee):
            raise ValueError("Invalid attribute data type {}, expected a BeeBase instance".format(type(value)))

        if value._hive_parent_hive_object_class is None:
            raise ValueError("Bees must be defined inside the builder function")

        # TODO should permit ResolveBees here
        if value._hive_parent_hive_object_class is not self._hive_object_class:
            raise ValueError("Bees cannot be built by a different hive")


class InternalValidator(BaseBeeValidator):
    def __call__(self, wrapper, name: str, value):
        super().__call__(wrapper, name, value)

        if not isinstance(value, Bee):
            raise ValueError("Attribute must be Bees not {}".format(type(value)))


class ExternalValidator(BaseBeeValidator):
    def __call__(self, wrapper, name: str, value):
        super().__call__(wrapper, name, value)

        if not isinstance(value, Bee):
            raise ValueError("Attribute must be BeeBase, not {}".format(type(value)))

        if not isinstance(value, Exportable):
            raise ValueError("Attribute must be Exportable")


class ArgWrapper(AttributeMapping):
    """Base class for hive argument wrappers"""

    def freeze(self, parameters: dict):
        """Resolve all parameter values with their parameter objects and return FrozenHiveArgs view

        :param parameters: dictionary of parameter values
        """
        parameter_dict = {}

        for name, param in self._ordered_mapping.items():
            parameter = self._ordered_mapping[name]
            options = parameter.options

            value = parameters[name]
            if options is not None and value not in options:
                raise ValueError("Invalid value for {}: {!r} is not in the permitted options {}"
                                 .format(name, value, options))

            parameter_dict[name] = value

        name_to_param = self._ordered_mapping.copy()
        name = "{}(resolved)".format(self._name)
        return ResolvedArgWrapper(name, name_to_param, parameter_dict)

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

            try:
                value = next(iter_args)
            except StopIteration:
                break

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


def validate_args(wrapper: ArgWrapper, name: str, value):
    if not isinstance(value, Parameter):
        raise ValueError("AttributeMapping must be a Parameters, not '{}'".format(name, value.__class__))


class ResolvedArgWrapper(ImmutableAttributeMapping):
    """Read-only view of true values of an args wrapper"""

    def __init__(self, name: str, name_to_param: dict, name_to_value: dict):
        """Initialiser for a read-only view of the resolved values of an args wrapper

        :param wrapper: name of args wrapper 
        :param resolved_mapping: OrderedDict mapping """
        object.__setattr__(self, '_param_to_name', {p: n for n, p in name_to_param.items()})
        ordered_name_to_value = OrderedDict(((n, name_to_value[n]) for n, p in name_to_param.items()))
        super().__init__(name, ordered_name_to_value)

    def resolve_parameter(self, parameter):
        """Retrieve the value associated with the given parameter

        :param parameter: HiveParameter instance
        """
        name = self._param_to_name[parameter]
        return self._ordered_mapping[name]
