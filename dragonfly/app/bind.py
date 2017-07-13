import hive

from ..bind import BindInfo, BindClassDefinition


definition = BindClassDefinition()
definition.forward_plugin("app.quit")
definition.forward_plugin("app.get_tick_rate")

factory = definition.build("BindApp")

_AppEnvironment = hive.meta_hive("AppEnvironment", factory.environment_builder, factory.environment_configurer,
                                 drone_class=factory.create_environment_class())


class AppBindClass(factory.create_external_class()):

    def on_started(self):
        pass

    def on_stopped(self):
        pass


_BindApp = hive.dyna_hive("BindApp", factory.external_builder, configurer=factory.external_configurer,
                          drone_class=AppBindClass)


def get_environment(meta_args):
    return _AppEnvironment


bind_info = BindInfo("App", _BindApp, get_environment)
