import hive


class ProcessClass:

    def __init__(self, *args, **kwargs):
        # Callbacks
        self._on_stopped = []
        self._on_started = []

    def add_on_started(self, on_started):
        self._on_started.append(on_started)

    def add_on_stopped(self, on_stopped):
        self._on_stopped.append(on_stopped)

    def start(self):
        for callback in self._on_started:
            callback()

    def stop(self):
        for callback in self._on_stopped:
            callback()


def build_process(cls, i, ex, args):
    # Startup / End callback
    ex.get_on_started = hive.socket(cls.add_on_started, identifier="on_started", policy=hive.MultipleOptional)
    ex.get_on_stopped = hive.socket(cls.add_on_stopped, identifier="on_stopped", policy=hive.MultipleOptional)

    i.on_started = hive.triggerable(cls.start)
    i.on_stopped = hive.triggerable(cls.stop)

    ex.on_started = hive.entry(i.on_started)
    ex.on_stopped = hive.entry(i.on_stopped)


Process = hive.hive("Process", build_process, drone_class=ProcessClass)
