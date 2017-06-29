from unittest import TestCase, main

import hive
from helpers import Triggerable, TriggerableHive


def build_nofunc_hive(i, ex, args):
    i.triggerable = TriggerableHive()

    i.trig = hive.triggerfunc()
    hive.trigger(i.trig, i.triggerable.trig)

    i.entry = hive.triggerable(i.trig)

    ex.trig = hive.entry(i.entry)
    ex.triggered = hive.view(i.triggerable.triggered)


NoFuncHive = hive.hive("NoFuncHive", build_nofunc_hive)


class TestTriggerFunc(TestCase):

    def test_nofunc_immediate(self):
        triggerable = Triggerable()
        trig = hive.triggerfunc()
        hive_pong = hive.triggerable(triggerable)
        hive.trigger(trig, hive_pong)

        trig()
        self.assertTrue(triggerable)

    def test_func_immediate(self):
        triggerable = Triggerable()
        trig = hive.triggerfunc(triggerable)
        trig()
        self.assertTrue(triggerable)

    def test_nofunc_build(self):
        h = NoFuncHive()
        print(dir(h))
        h.trig()
        self.assertTrue(h.triggered)


if __name__ == "__main__":
    main()