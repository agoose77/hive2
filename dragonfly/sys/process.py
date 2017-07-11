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
    ex.get_on_started = cls.add_on_started.socket(identifier="on_started", policy=hive.MultipleOptional)
    ex.get_on_stopped = cls.add_on_stopped.socket(identifier="on_stopped", policy=hive.MultipleOptional)

    ex.on_started = cls.start.trigger
    ex.on_stopped = cls.stop.trigger


Process = hive.hive("Process", build_process, drone_class=ProcessClass)
