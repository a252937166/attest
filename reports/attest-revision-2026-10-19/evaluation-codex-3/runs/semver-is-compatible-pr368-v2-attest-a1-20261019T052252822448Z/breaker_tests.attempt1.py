import unittest

from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class CompatibilityBreakerTests(unittest.TestCase):
    def test_patch_extremes_with_positive_major(self):
        huge = 2 ** 64
        pairs = [
            (Version(1, 7, 0), Version(1, 7, huge)),
            (Version(1, 7, huge), Version(1, 7, 0)),
            (Version(1, 7, huge), Version(1, 8, 0)),
        ]
        for old, new in pairs:
            with self.subTest(old=old, new=new):
                result = old.is_compatible(new)
                self.assertIs(type(result), bool)
                self.assertTrue(result)

    def test_minor_boundary_determines_direction_even_with_patch_changes(self):
        huge = 2 ** 64
        cases = [
            (Version(3, 0, huge), Version(3, 1, 0), True),
            (Version(3, 1, 0), Version(3, 0, huge), False),
            (Version(3, huge, 0), Version(3, huge - 1, huge), False),
            (Version(3, huge - 1, huge), Version(3, huge, 0), True),
        ]
        for old, new, expected in cases:
            with self.subTest(old=old, new=new):
                self.assertIs(old.is_compatible(new), expected)

    def test_major_zero_requires_all_non_build_fields_at_large_values(self):
        huge = 2 ** 64
        baseline = Version(0, huge, huge, 'rc.0', 'first')
        self.assertIs(baseline.is_compatible(Version(0, huge, huge, 'rc.0', 'second')), True)
        alternatives = [
            Version(0, huge - 1, huge, 'rc.0', 'first'),
            Version(0, huge, huge - 1, 'rc.0', 'first'),
            Version(0, huge, huge, 'rc.1', 'first'),
        ]
        for alternative in alternatives:
            with self.subTest(alternative=alternative):
                self.assertIs(baseline.is_compatible(alternative), False)
                self.assertIs(alternative.is_compatible(baseline), False)

    def test_prerelease_text_is_exact_even_when_minor_increases(self):
        old = Version(4, 2, 999, 'rc.2')
        for prerelease in ('rc.10', 'RC.2', 'rc.2.0', None, ''):
            with self.subTest(prerelease=prerelease):
                self.assertIs(old.is_compatible(Version(4, 3, 0, prerelease)), False)
        self.assertIs(old.is_compatible(Version(4, 3, 0, 'rc.2')), True)

    def test_empty_prerelease_remains_distinct_from_absence_with_builds(self):
        empty = Version(2, 1, 5, '', 'alpha')
        absent = Version(2, 8, 0, None, 'beta')
        self.assertIs(empty.is_compatible(absent), False)
        self.assertIs(absent.is_compatible(empty), False)
        self.assertIs(empty.is_compatible(Version(2, 8, 0, '', 'beta')), True)

    def test_build_cannot_change_directional_minor_result(self):
        old = Version(5, 6, 900, build='old')
        higher = Version(5, 7, 0, build='new')
        self.assertIs(old.is_compatible(higher), True)
        self.assertIs(higher.is_compatible(old), False)
        self.assertIs(old.is_compatible(Version(5, 7, 0)), True)
        self.assertIs(Version(5, 7, 0).is_compatible(old), False)

    def test_aliases_and_plain_subclasses_share_field_rules(self):
        class FirstVersion(Version):
            pass

        class SecondVersion(Version):
            pass

        self.assertIs(VersionInfo, Version)
        self.assertIs(ModuleVersion, Version)
        old = FirstVersion(0, 3, 4, 'rc.0', 'one')
        candidate = SecondVersion(0, 3, 4, 'rc.0', 'two')
        self.assertIs(VersionInfo.is_compatible(old, candidate), True)
        self.assertIs(ModuleVersion.is_compatible(candidate, other=old), True)
        self.assertIs(Version.is_compatible(Version(1, 3, 4), SecondVersion(1, 4, 0)), True)

    def test_additional_invalid_argument_types_have_exact_error(self):
        invalid = (True, 1.5, Version, object(), range(3))
        for receiver in (Version(0, 0, 0), Version(2, 0, 0)):
            for other in invalid:
                with self.subTest(receiver=receiver, other_type=type(other)):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(other=other)
                    self.assertEqual(
                        str(cm.exception),
                        'Expected a Version type but got ' + str(type(other)),
                    )

    def test_checks_preserve_fields_across_mixed_outcomes(self):
        versions = [
            Version(0, 2, 3, 'rc.0', 'a'),
            Version(0, 2, 3, 'rc.0', 'b'),
            Version(0, 2, 4, 'rc.0', 'a'),
            Version(1, 2, 3, 'rc.0', 'a'),
            Version(1, 3, 0, 'rc.0', 'b'),
            Version(1, 3, 0, 'rc.1', 'b'),
        ]
        fields = ('major', 'minor', 'patch', 'prerelease', 'build')
        before = [tuple(getattr(version, field) for field in fields) for version in versions]
        for old in versions:
            for new in versions:
                self.assertIs(type(old.is_compatible(new)), bool)
        after = [tuple(getattr(version, field) for field in fields) for version in versions]
        self.assertEqual(after, before)
