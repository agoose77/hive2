from unittest import TestCase, main

import hive


# On triggered
def calc_sum(i, ex):
    i.c.value = i.a.value + i.b.value


def build_myhive(i, ex, args):
    i.a = hive.attribute("int", 0)
    i.b = hive.attribute("int", 0)

    i.c = hive.attribute('int')

    ex.a = i.a.push_in
    ex.b = i.b.push_in

    i.calc_sum = hive.modifier(calc_sum)
    i.a.push_in.after.connect(i.calc_sum.trigger)
    i.b.push_in.after.connect(i.calc_sum.trigger)

    ex.c = i.c.property(hive.READ)
    ex.result = i.c.push_out
    i.calc_sum.triggered.connect(ex.result.trigger)

    ##############################

    ex.a_pull = i.a.pull_in
    ex.b_pull = i.b.pull_in
    ex.c_pull = i.c.pull_out

    i.c.pull_out.before.connect(ex.a_pull.trigger,
                                ex.b_pull.trigger,
                                i.calc_sum.trigger)


Hive = hive.hive("MyHive", build_myhive)


class TestIO(TestCase):
    def setUp(self):
        self.hive = Hive()

    def test_push(self):
        h = self.hive

        h.a.push(1)
        self.assertEqual(h.c, 1)

        h.b.push(1)
        self.assertEqual(h.c, 2)

        h.a.push(8)
        self.assertEqual(h.c, 9)

        h.a.push(-8)
        self.assertEqual(h.c, -7)

        var = hive.attribute("int", 100)
        var.push_out.connect(h.a)
        var.push_out()

        self.assertEqual(h.c, 100 + 1)

    def test_pull(self):
        h = self.hive

        a = hive.attribute("int", 1)
        b = hive.attribute("int", 9)
        a.pull_out.connect(h.a_pull)
        b.pull_out.connect(h.b_pull)

        self.assertEqual(h.c_pull(), 10)

        a.value = 9
        self.assertEqual(h.c_pull(), 18)

        b.value = 3
        self.assertEqual(h.c_pull(), 12)


if __name__ == "__main__":
    main()
