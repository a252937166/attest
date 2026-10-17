import unittest
from semver import Version


class TestIsCompatible(unittest.TestCase):
    def test_is_compatible_same_version(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_higher_patch_ignored(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_is_compatible_lower_patch_ignored(self):
        """Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_is_compatible_same_prerelease(self):
        """Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)"""
        self.assertTrue(
            Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
        )

    def test_is_compatible_major_zero_identical(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)"""
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_is_compatible_major_zero_different_patch_false(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)"""
        self.assertFalse(
            Version(0, 1, 0).is_compatible(Version(0, 1, 1))
        )

    def test_is_compatible_lower_minor_false(self):
        """Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)"""
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_is_compatible_different_major_false(self):
        """Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)"""
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_is_compatible_different_prerelease_false(self):
        """Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)"""
        self.assertFalse(
            Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
        )

    def test_is_compatible_self_has_prerelease_other_none_false(self):
        """Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)"""
        self.assertFalse(
            Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
        )

    def test_is_compatible_self_none_other_has_prerelease_false(self):
        """Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)"""
        self.assertFalse(
            Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
        )

    def test_is_compatible_wrong_type_str_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class \'str\'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            msg=f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_is_compatible_wrong_type_dict_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class \'dict\'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            msg=f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_is_compatible_wrong_type_list_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class \'list\'>'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(
            str(cm.exception).startswith('Expected a Version type but got '),
            msg=f"Exception message does not start with expected string: {cm.exception}"
        )

    def test_is_compatible_subclass_accepted(self):
        """class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)"""
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_is_compatible_docstring_has_two_doctest_examples(self):
        """Method docstring contains at least two doctest examples"""
        docstring = Version.is_compatible.__doc__
        self.assertIsNotNone(docstring, "Method is_compatible has no docstring")
        lines = docstring.splitlines()
        count = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('>>>'):
                count += 1
        self.assertGreaterEqual(
            count, 2,
            f"Expected at least two doctest examples in docstring, found {count}"
        )

