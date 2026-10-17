import unittest
from semver import Version


class TestVersionIsCompatible(unittest.TestCase):
    def test_is_compatible_same_version_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_higher_patch_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_is_compatible_lower_patch_true(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_equal_prerelease_true(self):
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_is_compatible_major0_identical_true(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_is_compatible_major0_different_patch_false(self):
        self.assertFalse(
            Version(0, 1, 0).is_compatible(Version(0, 1, 1))
        )

    def test_is_compatible_lower_minor_false(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_is_compatible_different_major_false(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_is_compatible_different_prerelease_false(self):
        self.assertFalse(
            Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
        )

    def test_is_compatible_prerelease_vs_none_false(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_is_compatible_typeerror_str(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(
            cm.exception.message.startswith(
                'Expected a Version type but got <class \'str\'>'
            )
        )

    def test_is_compatible_typeerror_dict(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(
            cm.exception.message.startswith(
                'Expected a Version type but got <class \'dict\'>'
            )
        )

    def test_is_compatible_typeerror_list(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(
            cm.exception.message.startswith(
                'Expected a Version type but got <class \'list\'>'
            )
        )

    def test_is_compatible_subclass_accepted_true(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(
            CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0))
        )

    def test_docstring_contains_at_least_two_doctest_examples(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc)
        # Count occurrences of '>>>' as a simple proxy for doctest examples
        self.assertGreaterEqual(doc.count('>>>'), 2)

