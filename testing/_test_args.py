import hive
from unittest import TestCase, main


def build_child(i, ex, args):
    args.age = hive.parameter("int", 0)
    i.age = hive.attribute("int", args.age)
    ex.age = i.age.proxy(hive.READ)

Child = hive.hive("Child", build_child)


def build_hive(i, ex, args):
    args.age = hive.parameter("int", 12)
    i.child = Child(args.age)
    ex.age = i.child.age


Hive = hive.hive("Hive", build_hive)


class TestArgs(TestCase):

    def setUp(self):
        pass

    def test_args(self):
        h = Hive(14)
        self.assertEqual(h.age, 14)


if __name__ == "__main__":
    main()