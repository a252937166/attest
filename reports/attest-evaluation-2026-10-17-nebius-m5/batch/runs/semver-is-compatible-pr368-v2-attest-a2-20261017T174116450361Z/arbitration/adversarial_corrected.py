import unittest
from semver import Version

class TestIsCompatibleBreaker(unittest.TestCase):
    def test_build_metadata_ignored_major_gt0(self):
        v1 = Version(2, 5, 1, None, 'build.1')
        v2 = Version(2, 5, 3, None, 'build.2')
        self.assertTrue(v1.is_compatible(v2))
        self.assertTrue(v2.is_compatible(v1))  # minor equal, patch ignored
    
    def test_build_metadata_ignored_major_eq0(self):
        v1 = Version(0, 4, 2, None, 'build.x')
        v2 = Version(0, 4, 2, None, 'build.y')
        self.assertTrue(v1.is_compatible(v2))
        self.assertTrue(v2.is_compatible(v1))
    
    def test_prerelease_complex_equality(self):
        v1 = Version(1, 0, 0, 'alpha.1.2')
        v2 = Version(1, 0, 0, 'alpha.1.2')
        v3 = Version(1, 0, 0, 'alpha.1.3')
        self.assertTrue(v1.is_compatible(v2))
        self.assertFalse(v1.is_compatible(v3))
    
    def test_major_gt0_minor_equal_prerelease_none_vs_string(self):
        v1 = Version(3, 2, 0, None)
        v2 = Version(3, 2, 5, 'rc.1')
        self.assertFalse(v1.is_compatible(v2))
        self.assertFalse(v2.is_compatible(v1))
    
    def test_major_gt0_higher_minor_but_prerelease_mismatch(self):
        v1 = Version(1, 2, 0, 'beta')
        v2 = Version(1, 3, 0, None)
        self.assertFalse(v1.is_compatible(v2))
    
    def test_major_eq0_requires_exact_prerelease(self):
        v1 = Version(0, 0, 1, 'dev')
        v2 = Version(0, 0, 1, None)
        self.assertFalse(v1.is_compatible(v2))
        self.assertFalse(v2.is_compatible(v1))
    
    def test_type_error_message_prefix(self):
        v = Version(1,2,3)
        for bad in ('str', 42, ['a'], {'b':1}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError) as cm:
                    v.is_compatible(bad)
                self.assertTrue(str(cm.exception).startswith('Expected a Version type but got '))
    
    def test_subclass_both_directions(self):
        class MyVer(Version):
            pass
        # Subclass as other (new version) with higher minor -> compatible
        old_base = Version(1, 1, 0)
        new_sub = MyVer(1, 2, 0)
        self.assertTrue(old_base.is_compatible(new_sub))
        # Subclass as self (old version) with lower minor -> compatible
        old_sub = MyVer(1, 1, 0)
        new_base = Version(1, 2, 0)
        self.assertTrue(old_sub.is_compatible(new_base))
        # Subclass as self with higher minor -> not compatible
        old_sub2 = MyVer(1, 2, 0)
        new_base2 = Version(1, 1, 0)
        self.assertFalse(old_sub2.is_compatible(new_base2))