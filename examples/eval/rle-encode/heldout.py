import unittest
from rle import encode, decode


class HeldOut(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(encode("aaabbc"), "a3b2c1")
        self.assertEqual(encode("a"), "a1")

    def test_empty(self):
        self.assertEqual(encode(""), "")

    def test_single_runs(self):
        self.assertEqual(encode("abc"), "a1b1c1")

    def test_long_run(self):
        self.assertEqual(encode("x" * 12), "x12")

    def test_roundtrip(self):
        for text in ("", "a", "aaabbc", "mississippi", "xxxxxxxxxxyz"):
            self.assertEqual(decode(encode(text)), text)

    def test_returns_str(self):
        self.assertIsInstance(encode("aa"), str)

    def test_non_string_raises_typeerror(self):
        for bad in (123, None, ["a"]):
            with self.assertRaises(TypeError):
                encode(bad)
