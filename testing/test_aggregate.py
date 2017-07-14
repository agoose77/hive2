import hive
from unittest import TestCase, main


def build_a(i, ex, args):
    i.b = hive.attribute('int', 1)
    ex.a = i.b.property()


def build_b(i, ex, args):
    i.b = hive.attribute('int', 2)
    ex.b = i.b.property()


A = hive.hive("A", build_a)
B = hive.hive("B", build_b)


def mod_c(i, ex):
    i.c.value = ex.a + ex.b


def build_c(i, ex, args):
    i.c = hive.attribute('int', 0)
    i.set_c = hive.modifier(mod_c)
    ex.get_c = i.c.pull_out

    ex.get_c.before.connect(i.set_c.trigger)


C = hive.hive("C", build_c, bases=(A, B))
D = C.extend("D")


class Case(TestCase):

    def test_a(self):
        a = A()
        self.assertEqual(a.a, 1)

    def test_b(self):
        b = B()
        self.assertEqual(b.b, 2)

    def test_c(self):
        c = C()
        self.assertEqual(c.get_c(), 3)

    def test_d(self):
        d = D()
        self.assertEqual(d.get_c(), 3)

if __name__ == "__main__":
    main()