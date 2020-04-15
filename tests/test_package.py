from package import __version__

from package.library import sum
import unittest

class SumTest(unittest.TestCase):

    def test_version(self) -> None:
        assert __version__ == '0.1.0'

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_sum(self) -> None:
        result = sum(2, 3)
        self.assertEqual(result, 5)

