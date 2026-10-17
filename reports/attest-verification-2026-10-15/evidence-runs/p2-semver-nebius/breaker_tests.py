import unittest
import doctest
from semver import Version

class TestVersionIsCompatible(unittest.TestCase):
    def test_build_metadata_ignored(self):
        v1 = Version(1, 2, 3)
        v2 = Version(1, 2, 3, None, 'build1')
        v3 = Version(1, 2, 3, None, 'build2')
        self.assertTrue(v1.is_compatible(v2))
        self.assertTrue(v2.is_compatible(v3))
        self.assertTrue(v1.is_compatible(v3))

    def test_prerelease_none_vs_empty_string(self):
        v1 = Version(1, 0, 0)
        v2 = Version(1, 0, 0, '')
        self.assertFalse(v1.is_compatible(v2))
        self.assertFalse(v2.is_compatible(v1))

    def test_prerelease_complex_equal_allows_minor_increase(self):
        v1 = Version(1, 2, 3, 'alpha-1')
        v2 = Version(1, 2, 5, 'alpha-1')
        self.assertTrue(v1.is_compatible(v2))

    def test_prerelease_complex_different(self):
        v1 = Version(1, 2, 3, 'alpha-1')
        v2 = Version(1, 2, 3, 'beta-1')
        self.assertFalse(v1.is_compatible(v2))

    def test_major_zero_build_ignored(self):
        v1 = Version(0, 1, 2, 'rc', 'build1')
        v2 = Version(0, 1, 2, 'rc', 'build2')
        self.assertTrue(v1.is_compatible(v2))
        self.assertTrue(v2.is_compatible(v1))

    def test_major_zero_prerelease_none_vs_empty(self):
        v1 = Version(0, 1, 2)
        v2 = Version(0, 1, 2, '')
        self.assertFalse(v1.is_compatible(v2))
        self.assertFalse(v2.is_compatible(v1))

    def test_wrong_type_tuple(self):
        v = Version(1, 2, 3)
        with self.assertRaises(TypeError) as cm:
            v.is_compatible((1, 2, 3))
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_wrong_type_set(self):
        v = Version(1, 2, 3)
        with self.assertRaises(TypeError) as cm:
            v.is_compatible({1, 2, 3})
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_subclass_reverse(self):
        class MyVer(Version):
            pass
        v1 = MyVer(1, 0, 0)
        v2 = Version(1, 0, 0)
        self.assertTrue(v1.is_compatible(v2))
        self.assertTrue(v2.is_compatible(v1))

    def test_docstring_doctests(self):
        # Run doctest on the method to ensure at least two examples succeed
        finder = doctest.DocTestFinder()
        tests = finder.find(Version.is_compatible)
        # Filter to only the tests from the method (there may be others)
        method_tests = [t for t in tests if t.obj is Version.is_compatible]
        self.assertGreaterEqual(len(method_tests), 1, "No doctests found for is_compatible")
        runner = doctest.DocTestRunner(verbose=False)
        for test in method_tests:
            result = runner.run(test)
            self.assertEqual(result.failed, 0, f"Doctest failed: {test}")

    def test_major_gt_zero_minor_equal_patch_lower(self):
        v_old = Version(2, 5, 7)
        v_new = Version(2, 5, 0)
        self.assertTrue(v_old.is_compatible(v_new))

    def test_major_gt_zero_minor_higher_patch_any(self):
        v_old = Version(2, 5, 7)
        v_new = Version(2, 6, 100)
        self.assertTrue(v_old.is_compatible(v_new))
