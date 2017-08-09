from unittest import TestCase, main

import hive


def build_drone(i, ex, args):
    args.name = hive.parameter("str")
    i.name = hive.attribute("str", args.name)

    ex.name_in = i.name.pull_in
    ex.name_out = i.name.push_out
    ex.name_out.before.connect(ex.name_in.trigger)

    ex.trigger_push = ex.name_out.trigger.plugin(identifier="push_name", export_to_parent=True)


PluginHive = hive.hive("PluginHive", build_drone)


class SocketHiveClass:
    def set_plugin(self, plugin):
        self.plugin = plugin

    def call_plugin(self):
        self.plugin()


def build_inner(i, ex, args):
    def get_plugin(i, ex, plugin):
        print(plugin)

    i.drone_class = hive.drone(SocketHiveClass)
    ex.sock = i.drone_class.set_plugin.socket(identifier="push_name")
    ex.do_push = i.drone_class.call_plugin.trigger


SocketHive = hive.hive("SocketHive", build_inner)


def build_container(i, ex, args):
    args.name = hive.parameter("str")
    i.plugin_hive = PluginHive(args.name)
    i.socket_hive = SocketHive()

    ex.name_out = i.plugin_hive.name_out
    ex.name_in = i.plugin_hive.name_in
    ex.do_push = i.socket_hive.do_push


ContainerHive = hive.hive("Hive", build_container)


class TestDroneNesting(TestCase):
    def test_nested(self):
        h = ContainerHive("bob")

        name_result = hive.attribute("str")
        name_source = hive.attribute("str", "fred")

        name_source.pull_out.connect(h.name_in)
        h.name_out.connect(name_result.push_in)

        self.assertEqual(name_result.value, None)
        h.do_push()
        self.assertEqual(name_result.value, name_source.value)


if __name__ == "__main__":
    main()
