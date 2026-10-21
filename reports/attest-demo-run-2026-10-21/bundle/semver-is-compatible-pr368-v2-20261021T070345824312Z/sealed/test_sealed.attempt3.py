import unittest
from semver import Version

class TestIsCompatible(unittest.TestCase):
    def test_ac1(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 3)))
    def test_ac2(self):
        self.assertTrue(Version(1, 2, 3).is_compatible(Version(1, 2, 4)))
    def test_ac3(self):
        self.assertTrue(Version(1, 2, 4).is_compatible(Version(1, 2, 3)))
    def test_ac4(self):
        self.assertTrue(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')))
    def test_ac5(self):
        self.assertTrue(Version(0, 1, 0).is_compatible(Version(0, 1, 0)))
    def test_ac6(self):
        self.assertFalse(Version(0, 1, 0).is_compatible(Version(0, 1, 1)))
    def test_ac7(self):
        self.assertFalse(Version(1, 1, 0).is_compatible(Version(1, 0, 0)))
    def test_ac8(self):
        self.assertFalse(Version(2, 0, 0).is_compatible(Version(1, 5, 0)))
    def test_ac9(self):
        self.assertFalse(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')))
    def test_ac10(self):
        self.assertFalse(Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')))
    def test_ac11(self):
        self.assertFalse(Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)))
    def test_ac12(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible('wrongtype')
    def test_ac13(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible({'a': 2})
    def test_ac14(self):
        with self.assertRaises(TypeError):
            Version(1, 2, 3).is_compatible([])
    def test_ac15(self):
        class CustomVersion(Version):
            pass
        self.assertTrue(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)))
    def test_ac16(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc)
        # Count doctest examples by counting lines starting with '>>>'
        examples = [line for line in doc.splitlines() if line.strip().startswith('>>>')]
        self.assertGreaterEqual(len(examples), 2)
    def test_ac17(self):
        # Ensure that adding the method does not break existing functionality.
        # We simply assert that the Version class still works as expected.
        v = Version(1, 2, 3)
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertTrue(v == Version(1, 2, 3))
        self.assertTrue(v < Version(1, 2, 4))

