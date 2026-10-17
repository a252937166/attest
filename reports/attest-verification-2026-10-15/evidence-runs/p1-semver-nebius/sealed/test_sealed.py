import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_identical_versions(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))

    def test_patch_ignored_higher(self):
        """Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))

    def test_patch_ignored_lower(self):
        """Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)"""
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))

    def test_equal_prerelease(self):
        """Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)"""
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))

    def test_major_zero_identical(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)"""
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))

    def test_major_zero_different_patch_false(self):
        """Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)"""
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))

    def test_lower_minor_false(self):
        """Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)"""
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))

    def test_different_major_false(self):
        """Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)"""
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))

    def test_different_prerelease_false(self):
        """Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)"""
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))

    def test_prerelease_vs_none_false(self):
        """Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)"""
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))

    def test_none_vs_prerelease_false(self):
        """Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)"""
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))

    def test_type_error_string(self):
        """Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible('wrongtype')
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_type_error_dict(self):
        """Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible({'a': 2})
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_type_error_list(self):
        """Version(1, 2, 3).is_compatible([]) raises TypeError with message starting 'Expected a Version type'"""
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible([])
        self.assertTrue(str(cm.exception).startswith('Expected a Version type'))

    def test_subclass_accepted(self):
        """class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)"""
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))

    def test_docstring_has_at_least_two_doctest_examples(self):
        """The method's docstring contains at least two doctest examples"""
        docstring = Version.is_compatible.__doc__
        self.assertIsNotNone(docstring, "Docstring is missing")
        # Count the number of lines that start with '>>> ' (doctest example lines)
        lines = docstring.split('\n')
        doctest_lines = [line for line in lines if line.strip().startswith('>>>')]
        self.assertGreaterEqual(len(doctest_lines), 2, \
            f"Expected at least two doctest examples in docstring, found {len(doctest_lines)}")

if __name__ == '__main__':
    unittest.main()
