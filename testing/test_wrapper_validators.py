from unittest import TestCase, main

import hive


class TestWrappers(TestCase):
    def test_exportable(self):
        def build_h(i, ex, args):
            i.attrib = hive.attribute()
            ex.attrib = hive.attribute()

        Hive = hive.hive("Hive", build_h)
        with self.assertRaises(hive.HiveBuilderError) as ctx:
            Hive()

        cause = ctx.exception.__cause__
        self.assertIsInstance(cause, AttributeError)
        self.assertIn("Error setting attribute", str(cause))

        cause = cause.__cause__
        self.assertIsInstance(cause, ValueError)
        self.assertEqual(str(cause), "Attribute must be Exportable")

    def test_bee(self):
        def build_h(i, ex, args):
            i.attrib = 12

        Hive = hive.hive("Hive", build_h)
        with self.assertRaises(hive.HiveBuilderError) as ctx:
            Hive()

        cause = ctx.exception.__cause__
        self.assertIsInstance(cause, AttributeError)
        self.assertIn("Error setting attribute", str(cause))

        cause = cause.__cause__
        self.assertIsInstance(cause, ValueError)
        self.assertIn("expected a BeeBase instance", str(cause))

    def test_args(self):
        def build_h(i, ex, args):
            args.attrib = 12

        Hive = hive.hive("Hive", build_h)
        with self.assertRaises(hive.HiveBuilderError) as ctx:
            Hive()

        cause = ctx.exception.__cause__
        self.assertIsInstance(cause, AttributeError)
        self.assertIn("Error setting attribute", str(cause))

        cause = cause.__cause__
        self.assertIsInstance(cause, ValueError)
        self.assertIn("expected a Parameter instance", str(cause))


if __name__ == "__main__":
    main()
