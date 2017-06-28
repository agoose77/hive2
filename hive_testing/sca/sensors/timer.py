from time import clock

import hive


def build_timer(i, ex, args):
    i.dt = hive.variable("float", 0.0)
    ex.step = hive.variable("float", 1 / 60)

    def start(self):
        last = clock()
        while True:
            now = clock()
            self._dt += now - last

            if self._dt > self.step:
                self._dt -= self.step
                self.tick()

            last = now

    i.start = hive.modifier(start)
    ex.start = hive.entry(i.start)

    i.tick = hive.triggerfunc()
    ex.tick = hive.hook(i.tick)


Timer = hive.hive("Timer", build_timer)