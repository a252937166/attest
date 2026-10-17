import unittest
from rle import decode


class TestDecode(unittest.TestCase):
    def test_decode(self):
        self.assertEqual(decode("a3b1"), "aaab")
        self.assertEqual(decode(""), "")

    def test_decode_type(self):
        with self.assertRaises(TypeError):
            decode(123)
