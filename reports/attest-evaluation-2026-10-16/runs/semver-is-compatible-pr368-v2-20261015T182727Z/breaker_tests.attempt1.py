import unittest
from semver import Version

class TestIsCompatibleBreaker(unittest.TestCase):
    def test_major_zero_different_minor_returns_false(self):
        self.assertFalse(Version(0, 1, 2).is_compatible(Version(0, 2, 2)))

    def test_major_zero_different_prerelease_returns_false(self):
        self.assertFalse(Version(0, 1, 2, 'dev').is_compatible(Version(0, 1, 2, 'alpha')))

    def test_major_zero_same_minor_patch_different_prerelease_returns_false(self):
        self.assertFalse(Version(0, 1, 2, None).is_compatible(Version(0, 1, 2, 'dev')))

    def test_major_positive_both_prerelease_none_returns_true(self):
        self.assertTrue(Version(1, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_major_positive_other_minor_greater_prerelease_differs_returns_false(self):
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 2, 0, 'beta')))

    def test_major_positive_other_minor_equal_prerelease_same_returns_true(self):
        self.assertTrue(Version(2, 3, 4, 'rc').is_compatible(Version(2, 3, 9, 'rc')))

    def test_wrong_type_none_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(None)
        self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))

    def test_wrong_type_int_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(5)
        self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))

    def test_wrong_type_float_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(3.14)
        self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))

    def test_wrong_type_bool_raises_typeerror(self):
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(True)
        self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))

    def test_wrong_type_custom_object_raises_typeerror(self):
        class Obj: pass
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(Obj())
        self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))