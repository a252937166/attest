import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_same_version_true(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_same_major_minor_higher_patch_true(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_same_major_minor_lower_patch_true(self):
        """Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_same_major_minor_patch_same_prerelease_true(self):
        """Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)"""
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))

    def test_major_zero_exact_match_true(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True"""
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_major_zero_exact_match_false(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical version)"""
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_major_positive_lower_minor_false(self):
        """Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)"""
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_major_positive_different_major_false(self):
        """Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)"""
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_same_major_minor_patch_different_prerelease_false(self):
        """Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)"""
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))

    def test_prerelease_absent_vs_present_false_old_without_new_with(self):
        """Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease absent vs present)"""
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))

    def test_prerelease_absent_vs_present_false_old_with_new_without(self):
        """Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease present vs absent)"""
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_wrong_type_string_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_wrong_type_dict_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_wrong_type_list_raises_typeerror(self):
        """Version(1, 2, 3).is_compatible([]) raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_subclass_accepted_true(self):
        """class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)"""
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_docstring_has_two_doctest_examples(self):
        """The method's docstring contains at least two doctest examples"""
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc, "Docstring is missing")
        # Count lines that start with '>>>' after stripping whitespace
        lines = doc.splitlines()
        count = 0
        for line in lines:
            if line.lstrip().startswith('>>>'):
                count += 1
        self.assertGreaterEqual(count, 2, "Docstring must contain at least two doctest examples")

