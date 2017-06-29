from collections import OrderedDict

from hive import matchmaker_validation_enabled_as
from .utils import hive_import_from_path, get_bind_class_args


class InspectorOption:
    """Configurable named field"""

    class NoValue:
        """Unique object used to indicate no value"""
        pass

    def __init__(self, data_type="", default=NoValue, options=None):
        self.data_type = data_type
        self.default = default
        self.options = options


def no_inspector():
    """Call to return no-op generator"""
    return
    yield


class BeeNodeInspector:
    """Inspect bee nodes for configurable parameters"""

    def __init__(self, find_by_reference_path):
        self._find_by_reference_path = find_by_reference_path

    def _find_attributes(self):
        return self._find_by_reference_path("hive.attribute")

    def inspect(self, reference_path):
        """Inspect the UI attributes available for a bee with the given reference path"""
        root, bee_name = reference_path.split(".")
        assert root == "hive"

        inspector = getattr(self, "inspect_{}".format(bee_name))
        return inspector()

    def inspect_configured(self, reference_path, params):
        """Associate inspection options with assigned values.

        :param reference_path: reference path of bee
        :param params: assigned parameters for each inspection stage
        """
        inspector = self.inspect(reference_path)
        param_info = {}

        # Find first stage values
        previous_values = None
        while True:
            try:
                stage_name, stage_options = inspector.send(previous_values)

            except StopIteration:
                break

            param_info[stage_name] = stage_options
            previous_values = params[stage_name]

        return param_info

    def inspect_antenna(self):
        return no_inspector()

    def inspect_output(self):
        return no_inspector()

    def inspect_entry(self):
        return no_inspector()

    def inspect_hook(self):
        return no_inspector()

    def inspect_modifier(self):
        args_options = OrderedDict()
        args_options["code"] = InspectorOption('str.code', "")
        yield ("args", args_options)

    def inspect_triggerfunc(self):
        return no_inspector()

    def inspect_attribute(self):
        # Configure meta args
        meta_arg_options = OrderedDict()
        meta_arg_options["data_type"] = InspectorOption('str', "int")
        meta_args = yield ("meta_args", meta_arg_options)

        data_type = meta_args['data_type']

        # Configure ARGS
        arg_options = OrderedDict()
        arg_options["export"] = InspectorOption('bool', False)
        arg_options["start_value"] = InspectorOption(data_type)

        yield ("args", arg_options)

    def inspect_pull_in(self):
        attributes = self._find_attributes()

        # Configure meta args
        meta_arg_options = OrderedDict()
        meta_arg_options["attribute_name"] = InspectorOption('str', options=set(attributes))
        meta_args = yield ("meta_args", meta_arg_options)

        attribute_name = meta_args['attribute_name']

        try:
            attribute_node = attributes[attribute_name]

        except KeyError:
            pass

        else:
            # TODO how can this better be supported so attributes can be renamed
            # Find bound attribute and save data type to meta_args
            meta_args['data_type'] = attribute_node.params['meta_args']['data_type']

    inspect_pull_out = inspect_pull_in
    inspect_push_out = inspect_pull_in
    inspect_push_in = inspect_pull_in


class HiveNodeInspector:
    """Inspect Hive nodes for configurable parameters"""

    def inspect(self, reference_path):
        """Inspect the UI attribute available for a hive with the given reference path

        :param reference_path: reference path of Hive class
        """
        return self._inspect_generator(reference_path)

    def inspect_configured(self, reference_path, params):
        """Associate inspection options with assigned values.

        :param reference_path: reference path of Hive class
        :param params: assigned parameters for each inspection stage
        """
        inspector = self.inspect(reference_path)
        param_info = {}

        # Find first stage values
        previous_values = None
        while True:
            try:
                stage_name, stage_options = inspector.send(previous_values)

            except StopIteration:
                break

            param_info[stage_name] = stage_options
            previous_values = params[stage_name]

        return param_info

    def _scrape_wrapper(self, wrapper):
        """Scrape parameters from a HiveArgs wrapper

        :param wrapper: HiveArgs wrapper instance
        """
        wrapper_options = OrderedDict()

        for arg_name, param in wrapper._items:
            data_type = param.data_type if param.data_type else ''
            options = param.options

            # If default is defined
            default = param.start_value
            if default is param.NoValue:
                option = InspectorOption(data_type, options=options)

            else:
                option = InspectorOption(data_type, default, options)

            wrapper_options[arg_name] = option

        return wrapper_options

    def _inspect_generator(self, reference_path):
        """An iterable inspection-stage generator.

        Yields each inspection stage as a name, OrderedDict pair.

        :param reference_path: reference path of Hive class
        """
        with matchmaker_validation_enabled_as(False):
            # Import and prepare hive
            import_result = hive_import_from_path(reference_path)

            # If it is a meta-hive-primitive, don't have to get meta args
            if import_result.is_meta_primitive:
                hive_object_cls = import_result.cls._hive_object_cls
                hive_cls = hive_object_cls._hive_parent_class

            # Otherwise, determine if the hive-builder needs meta args to produce hiveobject class
            else:
                hive_cls = import_result.cls

                # Build the meta-args wrapper
                hive_cls._hive_build_meta_args_wrapper()

                # If the meta-args wrapper is not empty
                meta_args_wrapper = hive_cls._hive_meta_args
                if meta_args_wrapper:
                    meta_args = yield ("meta_args", self._scrape_wrapper(meta_args_wrapper))

                    # Create HiveObject class
                    _, _, hive_object_cls = hive_cls._hive_get_hive_object_class((), meta_args)

                else:
                    hive_object_cls = hive_cls._hive_build(())

            args_wrapper = hive_object_cls._hive_args
            if args_wrapper:
                yield ("args", self._scrape_wrapper(args_wrapper))

            builder_args = get_bind_class_args(hive_cls)
            if builder_args:
                # Convert options into InspectorOptions
                options = OrderedDict()
                for name, arg_data in builder_args.items():
                    if arg_data.optional:
                        options[name] = InspectorOption(arg_data.data_type, default=arg_data.default,
                                                        options=arg_data.options)

                    else:
                        options[name] = InspectorOption(arg_data.data_type, options=arg_data.options)

                yield ("cls_args", options)
