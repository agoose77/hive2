import hive

from .classes import BindContext, get_active_bind_environments, get_bind_bases


def id_generator():
    i = 0
    while True:
        yield i
        i += 1


class BindEnvironmentClass:
    """Process environment which embeds a bound hive.

    Exposes relevant plugins
    """

    def __init__(self, context):
        self._on_stopped = []
        self._on_started = []

        self.state = 'init'

    def add_on_started(self, on_started):
        self._on_started.append(on_started)

    def add_on_stopped(self, on_stopped):
        self._on_stopped.append(on_stopped)

    def start(self):
        if self.state != 'init':
            raise RuntimeError("Hive is already running")

        self.state = 'running'

        for callback in self._on_started:
            callback()

    def stop(self):
        if self.state != 'running':
            raise RuntimeError("Hive is already stopped")

        self.state = 'stopped'

        for callback in self._on_stopped:
            callback()


def declare_build_environment(meta_args):
    meta_args.bind_meta_args = hive.parameter("object")
    meta_args.hive_class = hive.parameter("class")


def build_bind_environment(cls, i, ex, args, meta_args):
    """Provides plugins to new embedded hive instance"""
    ex.hive = meta_args.hive_class()

    # Startup / End callback
    ex.get_on_started = hive.socket(cls.add_on_started, identifier="on_started", policy=hive.MultipleOptional)
    ex.get_on_stopped = hive.socket(cls.add_on_stopped, identifier="on_stopped", policy=hive.MultipleOptional)

    i.on_started = hive.triggerable(cls.start)
    i.on_stopped = hive.triggerable(cls.stop)

    ex.on_started = hive.entry(i.on_started)
    ex.on_stopped = hive.entry(i.on_stopped)

    i.state = hive.property(cls, 'state', 'str')
    i.pull_state = hive.pull_out(i.state)
    ex.state = hive.output(i.pull_state)


class InstantiatorClass:

    def __init__(self):
        self._plugin_getters = []
        self._config_getters = []

        self._plugins = None

        self._hive = hive.get_run_hive()
        self._active_hives = {}

        self._bind_class_creation_callbacks = []
        self._process_id_generator = id_generator()

        self.last_created_process_id = None
        self.bind_meta_class = None

        # Runtime attributes
        self.hive_class = None

    def _create_context(self):
        """Create context object for new hive instances.

        Pass cached plugins, and request configuration data.
        """
        if self._plugins is None:
            self._plugins = plugins = {}

            for getter in self._plugin_getters:
                plugins.update(getter())

        config = {}
        for getter in self._config_getters:
            config.update(getter())

        return BindContext(self._plugins, config)

    def add_get_plugins(self, get_plugins):
        """Add plugin context source

        :param get_plugins: plugins context getter
        """
        self._plugin_getters.append(get_plugins)

    def add_get_config(self, get_config):
        """Add config context source

        :param get_config: config context getter
        """
        self._config_getters.append(get_config)

    def add_on_created(self, on_created):
        """Add creation callback

        :param on_created: callback
        """
        self._bind_class_creation_callbacks.append(on_created)

    @hive.types(process_id="int.process_id")
    def stop_hive(self, process_id):
        """Forget child hive when it is stopped"""
        instance = self._active_hives.pop(process_id)
        instance.on_stopped()

    def stop_all_processes(self):
        """Stop all child hives if instantiator is stopped"""
        for instance_id in list(self._active_hives.keys()):
            self.stop_hive(instance_id)

    def instantiate(self):
        context = self._create_context()

        bind_meta_args = self._hive._hive_object._hive_meta_args_frozen
        print("PRE", (self.bind_meta_class))
        bind_class = self.bind_meta_class(bind_meta_args=bind_meta_args, hive_class=self.hive_class)

        # Create Hive and track ID
        environment_hive = bind_class(context)
        process_id = next(self._process_id_generator)

        # Store ID of process
        self.last_created_process_id = process_id
        self._active_hives[process_id] = environment_hive

        # Notify bind classes of new hive instance (environment_hive)
        for callback in self._bind_class_creation_callbacks:
            callback(process_id, environment_hive)

        environment_hive.on_started()


def declare_instantiator(meta_args):
    meta_args.bind_process = hive.parameter("str", 'child', {'child', 'independent'})


def build_instantiator(cls, i, ex, args, meta_args):
    """Instantiates a Hive class at runtime"""
    # If this is built now, then it won't perform matchmaking, so use meta hive
    bind_meta_class = hive.meta_hive("BindEnvironment", build_bind_environment, declare_build_environment,
                                     builder_cls=BindEnvironmentClass)
    #assert bind_meta_class._hive_object_class
    i.bind_meta_class = hive.property(cls, "bind_meta_class", "class", bind_meta_class)

    i.trig_instantiate = hive.triggerfunc(cls.instantiate)
    i.do_instantiate = hive.triggerable(i.trig_instantiate)

    i.hive_class = hive.property(cls, "hive_class", "class")
    i.pull_hive_class = hive.pull_in(i.hive_class)
    ex.hive_class = hive.antenna(i.pull_hive_class)

    ex.create = hive.entry(i.do_instantiate)

    hive.trigger(i.trig_instantiate, i.pull_hive_class, pretrigger=True)

    ex.process_id = hive.property(cls, "last_created_process_id", "int.process_id")
    i.pull_process_id = hive.pull_out(ex.process_id)
    ex.last_process_id = hive.output(i.pull_process_id)

    i.push_stop_process = hive.push_in(cls.stop_hive)
    ex.stop_process = hive.antenna(i.push_stop_process)

    # Bind class plugin
    ex.bind_on_created = hive.socket(cls.add_on_created, identifier="bind.on_created", policy=hive.MultipleOptional)
    ex.add_get_plugins = hive.socket(cls.add_get_plugins, identifier="bind.get_plugins", policy=hive.MultipleOptional)
    ex.add_get_config = hive.socket(cls.add_get_config, identifier="bind.get_config", policy=hive.MultipleOptional)

    # Bind instantiator
    if meta_args.bind_process == 'child':
        # Add startup and stop callbacks
        ex.on_stopped = hive.plugin(cls.stop_all_processes, identifier="on_stopped")


Instantiator = hive.dyna_hive("Instantiator", build_instantiator, declare_instantiator, builder_cls=InstantiatorClass)


def create_instantiator(*bind_infos, docstring=""):
    """Create instantiator Hive for particular BindInfo sequence

    :param bind_infos: BindInfos to embed
    """
    def build_instantiator(i, ex, args, meta_args):
        bind_environments = get_active_bind_environments(bind_infos, meta_args)

        # Update bind environment to use new bases
        environment_class = i.bind_meta_class.start_value
        i.bind_meta_class.start_value = environment_class.extend("BindEnvironment", bases=tuple(bind_environments))

    build_instantiator.__doc__ = docstring

    return Instantiator.extend("Instantiator", builder=build_instantiator, bases=get_bind_bases(bind_infos))
