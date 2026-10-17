import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_same_version_returns_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_higher_patch_ignored_returns_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_lower_patch_ignored_returns_true(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_equal_prerelease_returns_true(self):
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))

    def test_major_zero_identical_returns_true(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_major_zero_different_patch_returns_false(self):
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_lower_minor_returns_false(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_different_major_returns_false(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_different_prerelease_returns_false(self):
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))

    def test_prerelease_vs_none_returns_false(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_wrong_type_raises_typeerror_with_exact_message(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertEqual(str(cm.exception), "Expected a Version type but got <class 'str'>")
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertEqual(str(cm.exception), "Expected a Version type but got <class 'dict'>")
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertEqual(str(cm.exception), "Expected a Version type but got <class 'list'>")

    def test_subclass_of_version_is_accepted(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_docstring_contains_at_least_two_doctest_examples(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc)
        # Count lines that start with '>>>' after stripping leading spaces
        lines = doc.splitlines()
        doctest_lines = [line for line in lines if line.lstrip().startswith('>>>')]
        self.assertGreaterEqual(len(doctest_lines), 2)

