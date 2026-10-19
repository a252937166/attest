import unittest
from semver import Version


class TestIsCompatible(unittest.TestCase):
    def test_is_compatible_same_version(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_patch_ignored_higher(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_is_compatible_patch_ignored_lower(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_same_prerelease_different_patch(self):
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_is_compatible_major_zero_identical(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_is_compatible_major_zero_different_patch_false(self):
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
        self.assertFalse(
            Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
        )
        self.assertFalse(
            Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
        )

    def test_is_compatible_wrong_type_str(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'str\'>')
        )

    def test_is_compatible_wrong_type_dict(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'dict\'>')
        )

    def test_is_compatible_wrong_type_list(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'list\'>')
        )

    def test_is_compatible_subclass_accepted(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(
            CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0))
        )

    def test_is_compatible_docstring_has_two_doctest_examples(self):
        docstring = Version.is_compatible.__doc__
        self.assertIsNotNone(docstring, "Method is_compatible must have a docstring")
        lines = docstring.splitlines()
        count = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('>>>'):
                count += 1
        self.assertGreaterEqual(
            count, 2, "Docstring must contain at least two doctest examples"
        )
