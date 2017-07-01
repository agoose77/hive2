from unittest import TestCase, main

import hive
from .helpers import Triggerable, TriggerableHive


def build_nofunc_hive(i, ex, args):
    i.triggerable = TriggerableHive()

    i.trig = hive.triggerfunc()
    hive.trigger(i.trig, i.triggerable.trig)

    i.entry = hive.triggerable(i.trig)

    ex.trig = hive.entry(i.entry)
    ex.get_triggered = hive.output(i.triggerable.get_triggered)


NoFuncHive = hive.hive("NoFuncHive", build_nofunc_hive)


def build_func_hive(i, ex, args):
    i.triggerable = TriggerableHive()

    i.trig = hive.triggerfunc(i.triggerable.trig)

    i.entry = hive.triggerable(i.trig)

    ex.trig = hive.entry(i.entry)
    ex.get_triggered = hive.output(i.triggerable.get_triggered)


FuncHive = hive.hive("FuncHive", build_func_hive)


class TestTriggerFunc(TestCase):

    # def test_nofunc_immediate(self):
    #     triggerable = Triggerable()
    #     trig = hive.triggerfunc()
    #     hive_pong = hive.triggerable(triggerable)
    #     hive.trigger(trig, hive_pong)
    #
    #     trig()
    #     self.assertTrue(triggerable)

    # def test_func_immediate(self):
    #     triggerable = Triggerable()
    #     trig = hive.triggerfunc(triggerable)
    #     trig()
    #     self.assertTrue(triggerable)
    #
    # def test_nofunc_build(self):
    #     h = NoFuncHive()
    #     h.trig()
    #     self.assertTrue(h.get_triggered.pull())

    def test_func_build(self):
        h = FuncHive()
        h.trig()
        self.assertTrue(h.get_triggered.pull())


if __name__ == "__main__":
    main()