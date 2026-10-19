import unittest
from semver import Version


class TestIsCompatible(unittest.TestCase):
    def test_same_version_returns_true(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_patch_ignored_when_new_patch_higher(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_patch_ignored_when_old_patch_higher(self):
        """Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)"""
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_equal_prerelease_returns_true(self):
        """Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)"""
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_major_zero_identical_returns_true(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (identical major-0 versions)"""
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_major_zero_different_patch_returns_false(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)"""
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_new_minor_less_than_old_returns_false(self):
        """Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (new minor < old minor)"""
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_different_major_returns_false(self):
        """Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)"""
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_prerelease_differs_returns_false(self):
        """Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)"""
        self.assertFalse(
            Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
        )

    def test_prerelease_none_vs_string_returns_false(self):
        """Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease differs: None vs 'rc1')"""
        self.assertFalse(
            Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
        )

    def test_prerelease_string_vs_none_returns_false(self):
        """Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease differs: 'rc1' vs None)"""
        self.assertFalse(
            Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
        )

    def test_wrong_type_string_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got '"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_wrong_type_dict_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got '"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_wrong_type_list_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got '"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_subclass_accepted(self):
        """Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True"""
        class CustomVersion(Version):
            pass
        self.assertTrue(
            CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0))
        )

    def test_docstring_has_at_least_two_doctest_examples(self):
        """Method docstring contains at least two doctest examples"""
        docstring = Version.is_compatible.__doc__
        self.assertIsNotNone(docstring, "Docstring should exist for is_compatible method")
        lines = docstring.splitlines()
        count = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('>>>'):
                count += 1
        self.assertGreaterEqual(
            count,
            2,
            f"Docstring should contain at least two doctest examples, found {count}"
        )
