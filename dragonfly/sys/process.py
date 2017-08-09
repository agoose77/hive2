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


def build_process(i, ex, args):
    # Startup / End callback
    i.drone = hive.drone(ProcessClass)
    
    ex.get_on_started = i.drone.add_on_started.socket(identifier="on_started", policy=hive.MultipleOptional)
    ex.get_on_stopped = i.drone.add_on_stopped.socket(identifier="on_stopped", policy=hive.MultipleOptional)

    ex.on_started = i.drone.start.trigger
    ex.on_stopped = i.drone.stop.trigger


Process = hive.hive("Process", build_process)
