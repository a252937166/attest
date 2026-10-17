import unittest
from slugkit import slugify


class HeldOut(unittest.TestCase):
    def test_runs_of_separators_collapse(self):
        self.assertEqual(slugify("Hello--World"), "hello-world")
        self.assertEqual(slugify("a -- b"), "a-b")
        self.assertEqual(slugify("one , two ; three"), "one-two-three")
        self.assertEqual(slugify("x___y"), "x-y")

    def test_leading_and_trailing_separators_are_removed(self):
        self.assertEqual(slugify("end!"), "end")
        self.assertEqual(slugify("  padded  "), "padded")
        self.assertEqual(slugify("--both--"), "both")
        self.assertEqual(slugify("(parens)"), "parens")

    def test_empty_results(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")

    def test_existing_behaviour_preserved(self):
        self.assertEqual(slugify("Hello World"), "hello-world")
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")
        self.assertEqual(slugify("Python 3"), "python-3")
        self.assertEqual(slugify("MiXeD CaSe 42"), "mixed-case-42")

    def test_non_ascii_letters_are_separators(self):
        self.assertEqual(slugify("café crème"), "caf-cr-me")
        self.assertEqual(slugify("日本語"), "")

    def test_returns_str_and_rejects_non_strings(self):
        self.assertIsInstance(slugify("a"), str)
        for bad in (None, 3, 2.5, ["a"], b"bytes"):
            with self.assertRaises(TypeError):
                slugify(bad)
