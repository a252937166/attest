import unittest
from semver import Version


class TestIsCompatible(unittest.TestCase):
    def test_is_compatible_same_version(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_patch_ignored_higher(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_is_compatible_patch_ignored_lower(self):
        """Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)"""
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_equal_prerelease(self):
        """Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)"""
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_is_compatible_major0_identical(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (identical major-0)"""
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_is_compatible_major0_not_identical(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical version)"""
        self.assertFalse(
            Version(0, 1, 0).is_compatible(Version(0, 1, 1))
        )

    def test_is_compatible_lower_minor(self):
        """Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)"""
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_is_compatible_different_major(self):
        """Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)"""
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_is_compatible_different_prerelease(self):
        """Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)"""
        self.assertFalse(
            Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
        )

    def test_is_compatible_prerelease_vs_none(self):
        """Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)"""
        self.assertFalse(
            Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
        )

    def test_is_compatible_none_vs_prerelease(self):
        """Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)"""
        self.assertFalse(
            Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
        )

    def test_is_compatible_wrong_type_str(self):
        """Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'str\'>')
        )

    def test_is_compatible_wrong_type_dict(self):
        """Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'dict\'>')
        )

    def test_is_compatible_wrong_type_list(self):
        """Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got <class \'list\'>')
        )

    def test_is_compatible_subclass_accepted(self):
        """Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True"""
        class CustomVersion(Version):
            pass
        self.assertTrue(
            CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0))
        )

    def test_docstring_has_two_doctest_examples(self):
        """Method docstring contains at least two doctest examples"""
        method = Version.is_compatible
        self.assertIsNotNone(method.__doc__, "Docstring is missing")
        lines = method.__doc__.splitlines()
        count = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('>>>'):
                count += 1
        self.assertGreaterEqual(
            count, 2, "Docstring must contain at least two doctest examples"
        )

