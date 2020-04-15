from package.library import sum
import unittest

class SumTest(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_sum(self) -> None:
        result = sum(2, 3)
        self.assertEqual(result, 5)
