import unittest

from semver import Version


class DerivedVersion(Version):
    pass


class CompatibilityBreakerTests(unittest.TestCase):
    def test_self_replacement_returns_literal_true(self):
        for version in (
            Version(0, 0, 0, prerelease="alpha.1", build="one"),
            Version(1, 0, 0),
            Version(7, 8, 9, prerelease="rc.2"),
        ):
            with self.subTest(version=version):
                self.assertIs(version.is_compatible(version), True)

    def test_minor_zero_boundary_is_directional(self):
        low = Version(3, 0, 999)
        high = Version(3, 1, 0)
        self.assertIs(low.is_compatible(high), True)
        self.assertIs(high.is_compatible(low), False)
        self.assertIs(low.is_compatible(Version(3, 0, 0)), True)

    def test_large_numeric_components_follow_the_same_rules(self):
        n = 10**20
        receiver = Version(5, n, n)
        self.assertIs(receiver.is_compatible(Version(5, n + 1, 0)), True)
        self.assertIs(receiver.is_compatible(Version(5, n, 0)), True)
        self.assertIs(receiver.is_compatible(Version(5, n - 1, n)), False)

    def test_major_zero_requires_exact_numeric_components_with_builds(self):
        receiver = Version(0, 1000, 2000, prerelease="rc.1", build="local")
        self.assertIs(receiver.is_compatible(Version(0, 1000, 2000, prerelease="rc.1")), True)
        self.assertIs(receiver.is_compatible(Version(0, 1000, 2001, prerelease="rc.1", build="local")), False)
        self.assertIs(receiver.is_compatible(Version(0, 1001, 2000, prerelease="rc.1", build="local")), False)

    def test_prerelease_equality_is_exact_across_minor_changes(self):
        receiver = Version(2, 4, 8, prerelease="alpha.10")
        self.assertIs(receiver.is_compatible(Version(2, 5, 0, prerelease="alpha.10")), True)
        self.assertIs(receiver.is_compatible(Version(2, 5, 0, prerelease="alpha.2")), False)
        self.assertIs(receiver.is_compatible(Version(2, 5, 0, prerelease="Alpha.10")), False)

    def test_builds_cannot_change_a_prerelease_decision(self):
        receiver = Version(4, 2, 9, prerelease="beta", build="old")
        self.assertIs(receiver.is_compatible(Version(4, 3, 0, prerelease="beta", build="new")), True)
        self.assertIs(receiver.is_compatible(Version(4, 3, 0, prerelease="rc", build="old")), False)

    def test_subclass_receiver_accepts_base_and_subclass_replacements(self):
        receiver = DerivedVersion(6, 2, 8)
        self.assertIs(receiver.is_compatible(Version(6, 3, 0)), True)
        self.assertIs(receiver.is_compatible(other=DerivedVersion(6, 1, 99)), False)
        zero_receiver = DerivedVersion(0, 2, 8, build="first")
        self.assertIs(zero_receiver.is_compatible(Version(0, 2, 8, build="second")), True)
        self.assertIs(zero_receiver.is_compatible(DerivedVersion(0, 2, 9)), False)

    def test_additional_invalid_types_raise_the_exact_error(self):
        invalid_values = (Version, True, 1.0, memoryview(b"1.2.3"))
        for receiver in (Version(0, 1, 0), DerivedVersion(1, 2, 3)):
            for other in invalid_values:
                with self.subTest(receiver=receiver, other_type=type(other)):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(other=other)
                    self.assertEqual(str(cm.exception), f"Expected a Version type but got {type(other)}")

    def test_cross_major_remains_false_with_large_replacement_minor(self):
        self.assertIs(Version(1, 0, 0).is_compatible(Version(2, 10**20, 0)), False)
        self.assertIs(Version(2, 10**20, 0).is_compatible(Version(1, 0, 0)), False)
