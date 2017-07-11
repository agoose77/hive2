from __future__ import print_function

import hive
import time

from ..sys.process import Process as _Process


class _Mainloop(object):

    @hive.types(tick_rate='int')
    def __init__(self, tick_rate=60):
        self._hive = hive.get_run_hive()
        self.tick_rate = tick_rate

        self._running = True
        self._listeners = []

    def run(self):
        self._hive.on_started()

        accumulator = 0.0
        last_time = time.clock()

        time_step = 1.0 / self.tick_rate

        while self._running:
            current_time = time.clock()
            elapsed_time = current_time - last_time
            last_time = current_time

            if elapsed_time > 0.25:
                elapsed_time = 0.25

            accumulator += elapsed_time
            while accumulator > time_step:
                accumulator -= time_step
                self.tick()

        self._hive.on_stopped()

    def get_tick_rate(self):
        return self.tick_rate

    def stop(self):
        self._running = False

    def tick(self):
        self._hive.tick()


def build_mainloop(cls, i, ex, args):
    """Blocking fixed-timestep trigger generator"""
    i.tick = hive.function() # todo

    ex.tick = i.tick.trigger
    ex.stop = cls.stop.trigger
    ex.run = cls.run.trigger

    i.tick_rate = hive.property(cls, "tick_rate", 'int')
    ex.tick_rate = i.tick_rate.pull_out

    ex.get_tick_rate = cls.get_tick_rate.plugin(identifier="app.get_tick_rate")
    ex.quit = cls.stop.plugin(identifier="app.quit")


Mainloop = _Process.extend("Mainloop", build_mainloop, _Mainloop)
