import hive

class Triggerable:
    triggered = False

    def __bool__(self):
        return self.triggered

    def __call__(self):
        self.triggered = True
        return self


def triggered(self):
    self._triggered = True

def build_triggerable(i, ex, args):
    i.triggered = hive.variable('bool', False)
    ex.triggered = hive.view(i.triggered)
    i.trig = hive.modifier(triggered)
    ex.trig = hive.entry(i.trig)


TriggerableHive = hive.hive("TriggerableHive", build_triggerable)