import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_same_version_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))
    def test_patch_higher_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))
    def test_patch_lower_true(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))
    def test_prerelease_same_true(self):
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))
    def test_major_zero_identical_true(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))
    def test_major_zero_patch_diff_false(self):
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))
    def test_lower_minor_false(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))
    def test_different_major_false(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))
    def test_prerelease_diff_false(self):
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))
    def test_prerelease_absent_vs_present_false(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))
    def test_wrong_type_str_raises(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible('wrongtype')
    def test_wrong_type_dict_raises(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible({'a': 2})
    def test_wrong_type_list_raises(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible([])
    def test_subclass_accepted_true(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

if __name__ == '__main__':
    unittest.main()
