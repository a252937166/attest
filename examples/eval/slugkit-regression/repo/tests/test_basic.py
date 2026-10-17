import unittest
from slugkit import slugify


class TestSlugify(unittest.TestCase):
    def test_simple_words(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_already_a_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3"), "python-3")

    def test_non_string_rejected(self):
        for bad in (None, 3, ["a"]):
            with self.assertRaises(TypeError):
                slugify(bad)
