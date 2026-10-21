import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_ac1_same_version_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_ac2_patch_higher_true(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_ac3_patch_lower_true(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_ac4_equal_prerelease_true(self):
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))

    def test_ac5_major_zero_identical_true(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_ac6_major_zero_different_false(self):
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_ac7_lower_minor_false(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_ac8_different_major_false(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_ac9_different_prerelease_false(self):
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))

    def test_ac10_prerelease_vs_none_false(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))

    def test_ac11_none_vs_prerelease_false(self):
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_ac12_wrong_type_str_raises_typeerror(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible('wrongtype')

    def test_ac13_wrong_type_dict_raises_typeerror(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible({'a': 2})

    def test_ac14_wrong_type_list_raises_typeerror(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible([])

    def test_ac15_subclass_accepted_true(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_ac16_docstring_has_doctest_examples(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc)
        # Count lines that look like doctest (>>> )
        lines = doc.split('
')
        doctest_lines = [l for l in lines if l.strip().startswith('>>>')]
        self.assertGreaterEqual(len(doctest_lines), 2)

if __name__ == '__main__':
    unittest.main()
", 