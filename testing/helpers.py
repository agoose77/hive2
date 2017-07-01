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
    i.get_triggered = hive.pull_out(i.triggered)
    ex.get_triggered = hive.output(i.get_triggered)

    i.trig = hive.modifier(triggered)
    ex.trig = hive.entry(i.trig)


TriggerableHive = hive.hive("TriggerableHive", build_triggerable)