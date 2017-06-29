from hive import matchmaker_validation_enabled_as

from .node import Node, NodeTypes, MimicFlags
from .utils import hive_object_instance_from_import_result, hive_import_from_path, get_io_info


class BeeNodeFactory:
    """Create bee nodes from reference paths

    Bees cannot be inspected like Hives because they are the GUI primitives
    """

    def new(self, name, reference_path, params, param_info):
        """Create new Bee node with given name, reference path and params dict

        :param name: name of node
        :param reference_path: reference path of bee
        :param params: configuration data for node
        """
        root, bee_name = reference_path.split(".")
        assert root == "hive"

        builder = getattr(self, "build_{}".format(bee_name))
        node = Node(name, NodeTypes.BEE, reference_path, params, param_info)

        return builder(node)

    def build_antenna(self, node):
        node.add_output("antenna", None, "any", max_connections=1, restricted_types=['trigger'],
                        mimic_flags=MimicFlags.COLOUR, is_virtual=True, count_proxies=True)

        return node

    def build_output(self, node):
        node.add_input("output", None, "any", max_connections=1, restricted_types=['trigger'],
                       mimic_flags=MimicFlags.COLOUR, is_virtual=True, count_proxies=True)

        return node

    def build_entry(self, node):
        node.add_output("output", 'trigger', "push", max_connections=1, is_virtual=True, count_proxies=True)

        return node

    def build_hook(self, node):
        node.add_input("output", 'trigger', "push", max_connections=1, is_virtual=True, count_proxies=True)

        return node

    def build_attribute(self, node):
        return node

    def build_pull_in(self, node):
        data_type = node.params['meta_args']['data_type']

        node.add_input("value", data_type, "pull", restricted_types=['trigger'])
        node.add_input("trigger", 'trigger', "push")

        node.add_output("pre_update", 'trigger', "push", is_virtual=True)
        node.add_output("post_update", 'trigger', "push")

        return node

    def build_pull_out(self, node):
        data_type = node.params['meta_args']['data_type']

        node.add_output("value", data_type, "pull", restricted_types=['trigger'])

        node.add_output("pre_output", 'trigger', "push", is_virtual=True)
        node.add_output("post_output", 'trigger', "push")

        return node

    def build_push_in(self, node):
        data_type = node.params['meta_args']['data_type']

        node.add_input("value", data_type, "push", restricted_types=['trigger'])

        node.add_output("pre_update", 'trigger', "push", is_virtual=True)
        node.add_output("post_update", 'trigger', "push")

        return node

    def build_push_out(self, node):
        data_type = node.params['meta_args']['data_type']

        node.add_output("value", data_type, "push", restricted_types=['trigger'])
        node.add_input("trigger", 'trigger', "push")

        node.add_output("pre_output", 'trigger', "push", is_virtual=True)
        node.add_output("post_output", 'trigger', "push")

        return node

    def build_triggerfunc(self, node):
        node.add_output("trigger", 'trigger', "push")
        node.add_output("pre_trigger", 'trigger', "push", is_virtual=True)

        return node

    def build_modifier(self, node):
        node.add_input("trigger", 'trigger', "push")

        return node


class HiveNodeFactory:
    """Create Hive nodes from reference paths"""

    @classmethod
    def new(cls, name, reference_path, params, param_info):
        try:
            import_result = hive_import_from_path(reference_path)

        except (ImportError, AttributeError):
            raise ValueError("Invalid reference path: {}".format(reference_path))

        return cls._node_from_import_result(import_result, name, reference_path, params, param_info)

    @staticmethod
    def _node_from_import_result(import_result, name, reference_path, params, param_info):
        # Allow GUI to instantiate hives without connectivity validation
        with matchmaker_validation_enabled_as(False):
            hive_object = hive_object_instance_from_import_result(import_result, params)
            io_info = get_io_info(hive_object)

            # Warning later on, the args and cls_args of hive_object might not correspond to params
            # Altering the params dict from the UI is safe as it won't affect the pin-out on the HiveObject,
            # so these changes aren't mirrored to the args wrappers on this hive_object
            # Use the params dict instead of re-scraping the hive_object if reading these values

            node = Node(name, NodeTypes.HIVE, reference_path, params, param_info)

            # Set tooltip as docstring
            with node.make_writable():
                node.tooltip = hive_object.__doc__ or ""

            inputs = io_info['inputs']
            outputs = io_info['outputs']

            for pin_name in io_info['pin_order']:
                try:
                    info = inputs[pin_name]
                    node.add_input(pin_name, info['data_type'], info['mode'])

                except KeyError:
                    info = outputs[pin_name]
                    node.add_output(pin_name, info['data_type'], info['mode'])

            return node
