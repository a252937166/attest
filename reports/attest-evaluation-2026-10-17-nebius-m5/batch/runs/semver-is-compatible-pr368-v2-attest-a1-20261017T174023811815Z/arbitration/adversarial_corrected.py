import unittest
from semver import Version

class TestIsCompatibleBreaker(unittest.TestCase):
    def test_major_zero_exact_match_all_fields(self):
        v = Version(0, 0, 0, 'dev')
        self.assertTrue(v.is_compatible(Version(0, 0, 0, 'dev')))
        self.assertFalse(v.is_compatible(Version(0, 0, 0, 'dev2')))
        self.assertFalse(v.is_compatible(Version(0, 0, 1, 'dev')))
        self.assertFalse(v.is_compatible(Version(0, 1, 0, 'dev')))
        self.assertFalse(v.is_compatible(Version(1, 0, 0, 'dev')))

    def test_major_positive_minor_equal_patch_any(self):
        base = Version(2, 5, 7, 'beta')
        for patch in range(0, 15):  # patch ignored, can be any non-negative int
            self.assertTrue(base.is_compatible(Version(2, 5, patch, 'beta')))
        # lower minor fails
        self.assertFalse(base.is_compatible(Version(2, 4, 100, 'beta')))
        # higher minor passes
        self.assertTrue(base.is_compatible(Version(2, 6, 0, 'beta')))
        # different major fails
        self.assertFalse(base.is_compatible(Version(3, 5, 0, 'beta')))
        self.assertFalse(base.is_compatible(Version(1, 5, 0, 'beta')))
        # prerelease mismatch fails
        self.assertFalse(base.is_compatible(Version(2, 5, 0, 'beta.2')))
        self.assertFalse(base.is_compatible(Version(2, 5, 0, None)))

    def test_prerelease_both_none_equals(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 3, 5)))
        self.assertFalse(Version(1, 2, 3).is_compatible(Version(1, 1, 5)))

    def test_large_numbers(self):
        big = Version(999999, 999999, 999999)
        self.assertTrue(big.is_compatible(Version(999999, 999999, 0)))
        self.assertTrue(big.is_compatible(Version(999999, 1000000, 0)))
        self.assertFalse(big.is_compatible(Version(999999, 999998, 0)))
        self.assertFalse(big.is_compatible(Version(1000000, 0, 0)))

    def test_error_message_format(self):
        v = Version(1, 0, 0)
        with self.assertRaises(TypeError) as cm:
            v.is_compatible(42)
        self.assertIn('Expected a Version type but got', str(cm.exception))
        self.assertIn("<class 'int'>", str(cm.exception))
        with self.assertRaises(TypeError) as cm:
            v.is_compatible(None)
        self.assertIn('Expected a Version type but got', str(cm.exception))
        self.assertIn("<class 'NoneType'>", str(cm.exception))

    def test_subclass_behavior(self):
        class MyVer(Version):
            pass
        a = MyVer(1, 2, 3)
        b = Version(1, 2, 4)
        self.assertTrue(a.is_compatible(b))
        self.assertTrue(b.is_compatible(a))
        c = MyVer(1, 1, 0)
        self.assertFalse(a.is_compatible(c))

    def test_immutability(self):
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 4)
        # calling should not change attributes
        maj, min, pat, pre = v1.major, v1.minor, v1.patch, v1.prerelease
        v1.is_compatible(v2)
        self.assertEqual(v1.major, maj)
        self.assertEqual(v1.minor, min)
        self.assertEqual(v1.patch, pat)
        self.assertEqual(v1.prerelease, pre)
        maj2, min2, pat2, pre2 = v2.major, v2.minor, v2.patch, v2.prerelease
        v2.is_compatible(v1)
        self.assertEqual(v2.major, maj2)
        self.assertEqual(v2.minor, min2)
        self.assertEqual(v2.patch, pat2)
        self.assertEqual(v2.prerelease, pre2)
