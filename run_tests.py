import unittest

loader = unittest.TestLoader()
suite = loader.discover('testing')

runner = unittest.TextTestRunner()
runner.run(suite)