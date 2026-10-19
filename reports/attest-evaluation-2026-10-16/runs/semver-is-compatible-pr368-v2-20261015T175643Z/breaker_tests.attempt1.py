import unittest
from semver import Version

class TestIsCompatibleBreaker(unittest.TestCase):
    def test_zero_major_prerelease_diff(self):
        v = Version(0, 1, 0, 'rc1')
        w = Version(0, 1, 0, 'rc2')
        self.assertFalse(v.is_compatible(w))
        self.assertFalse(w.is_compatible(v))

    def test_zero_major_build_ignored(self):
        v = Version(0, 1, 0, None, 'build.a')
        w = Version(0, 1, 0, None, 'build.b')
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))

    def test_zero_major_subclass_extra_attr(self):
        class Vsub(Version):
            def __init__(self, major, minor, patch, prerelease=None, build=None):
                super().__init__(major, minor, patch, prerelease, build)
                self.extra = 42
        v = Version(0, 0, 0)
        w = Vsub(0, 0, 0)
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))

    def test_major_ge1_prerelease_same_minor_less(self):
        v = Version(2, 5, 0, 'beta')
        w = Version(2, 4, 9, 'beta')
        self.assertFalse(v.is_compatible(w))

    def test_major_ge1_prerelease_same_minor_greater(self):
        v = Version(2, 5, 0, 'beta')
        w = Version(2, 6, 0, 'beta')
        self.assertTrue(v.is_compatible(w))

    def test_major_ge1_prerelease_same_minor_equal_patch_any(self):
        v = Version(1, 2, 100, 'alpha')
        w = Version(1, 2, 0, 'alpha')
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))

    def test_major_ge1_prerelease_none_minor_equal_patch_any(self):
        v = Version(1, 2, 100)
        w = Version(1, 2, 0)
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))

    def test_type_error_message_various(self):
        v = Version(1,0,0)
        for obj in ('str', 123, [], {}, set()):
            with self.subTest(obj=obj):
                with self.assertRaises(TypeError) as cm:
                    v.is_compatible(obj)
                self.assertTrue(str(cm.exception).startswith("Expected a Version type but got "))

    def test_subclass_overrides_eq_still_works(self):
        class Vsub(Version):
            def __eq__(self, other):
                return True
        v = Version(1,0,0)
        w = Vsub(2,0,0)
        self.assertFalse(v.is_compatible(w))
        self.assertFalse(w.is_compatible(v))

    def test_major_zero_identical_except_build(self):
        v = Version(0,0,0,None,'build1')
        w = Version(0,0,0,None,'build2')
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))

    def test_major_zero_identical_except_prerelease_none_vs_string(self):
        v = Version(0,0,0)
        w = Version(0,0,0,'')
        self.assertFalse(v.is_compatible(w))
        self.assertFalse(w.is_compatible(v))

    def test_major_ge1_prerelease_both_none_minor_equal_patch_ignored_large(self):
        v = Version(1,1,10**6)
        w = Version(1,1,0)
        self.assertTrue(v.is_compatible(w))
        self.assertTrue(w.is_compatible(v))
