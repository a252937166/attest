import unittest
from semver import Version


class TestIsCompatible(unittest.TestCase):
    def test_same_version_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_patch_ignored_higher(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_patch_ignored_lower(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_equal_prerelease_allow_minor_increase(self):
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_major_zero_identical_true(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_major_zero_identical_false_patch(self):
        self.assertFalse(
            Version(0, 1, 0).is_compatible(Version(0, 1, 1))
        )

    def test_lower_minor_false(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_different_major_false(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_different_prerelease_false(self):
        self.assertFalse(
            Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
        )

    def test_prerelease_vs_none_false(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_wrong_type_string(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_wrong_type_dict(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_wrong_type_list(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_subclass_accepted(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_docstring_has_doctests(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc, 'is_compatible method must have a docstring')
        # Count occurrences of '>>>' as doctest examples
        self.assertGreaterEqual(doc.count('>>>'), 2,
                                'Docstring must contain at least two doctest examples')

