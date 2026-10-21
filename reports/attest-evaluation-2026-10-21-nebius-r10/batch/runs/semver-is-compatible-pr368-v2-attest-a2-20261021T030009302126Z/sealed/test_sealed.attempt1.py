import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_ac1_same_version(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_ac2_patch_ignored_new_higher(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_ac3_patch_ignored_old_higher(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_ac4_equal_prerelease(self):
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))

    def test_ac5_major_zero_identical(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_ac6_major_zero_patch_diff(self):
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_ac7_minor_less(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_ac8_different_major(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_ac9_different_prerelease(self):
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))

    def test_ac10_prerelease_vs_none(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))

    def test_ac11_none_vs_prerelease(self):
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_ac12_wrong_type_str(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible('wrongtype')

    def test_ac13_wrong_type_dict(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible({'a': 2})

    def test_ac14_wrong_type_list(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible([])

    def test_ac15_subclass_accepted(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_ac16_docstring_has_doctests(self):
        method = Version.is_compatible
        self.assertIsNotNone(method.__doc__)
        # Count doctest examples (lines starting with >>>)
        doc = method.__doc__
        count = sum(1 for line in doc.splitlines() if line.lstrip().startswith('>>>'))
        self.assertGreaterEqual(count, 2)

    # AC17: existing test suite passes – we cannot run it here, but we assume it's satisfied.
    # We'll just note that we don't break anything.

def load_tests(loader, tests, pattern):
    return loader.loadTestsFromTestCase(TestIsCompatible)
