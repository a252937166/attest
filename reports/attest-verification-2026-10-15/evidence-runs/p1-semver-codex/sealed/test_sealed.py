import doctest
import inspect
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class CustomVersion(Version):
    pass


class OtherCustomVersion(Version):
    pass


class VersionCompatibilityTests(unittest.TestCase):
    def test_public_names_and_keyword_argument(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        for cls in (ModuleVersion, Version, VersionInfo):
            self.assertIs(cls(1, 2, 3).is_compatible(other=Version(1, 2, 3)), True)
            self.assertIs(cls(1, 2, 3).is_compatible(other=Version(2, 2, 3)), False)

    def test_nonzero_major_ignores_patch_in_both_directions(self):
        for old, replacement in ((Version(1, 2, 3), Version(1, 2, 3)),
                                 (Version(1, 2, 3), Version(1, 2, 4)),
                                 (Version(1, 2, 4), Version(1, 2, 3))):
            with self.subTest(old=old, replacement=replacement):
                self.assertIs(old.is_compatible(replacement), True)

    def test_nonzero_major_allows_only_equal_or_higher_minor(self):
        cases = ((Version(1, 2, 9), Version(1, 3, 0), True),
                 (Version(1, 3, 0), Version(1, 2, 9), False),
                 (Version(1, 1, 0), Version(1, 0, 0), False))
        for old, replacement, expected in cases:
            with self.subTest(old=old, replacement=replacement):
                self.assertIs(old.is_compatible(replacement), expected)

    def test_different_majors_are_incompatible_in_both_directions(self):
        for first, second in ((Version(2, 0, 0), Version(1, 5, 0)),
                              (Version(0, 1, 0), Version(1, 1, 0))):
            with self.subTest(first=first, second=second):
                self.assertIs(first.is_compatible(second), False)
                self.assertIs(second.is_compatible(first), False)

    def test_matching_prerelease_allows_patch_and_minor_changes(self):
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(Version(1, 2, 9, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_different_prereleases_are_incompatible_even_with_higher_minor(self):
        for first_pre, second_pre in (('rc.1', 'rc.0'), (None, 'rc1')):
            first = Version(1, 2, 3, first_pre)
            second = Version(1, 3, 0, second_pre)
            with self.subTest(first_pre=first_pre, second_pre=second_pre):
                self.assertIs(first.is_compatible(second), False)
                self.assertIs(second.is_compatible(first), False)

    def test_prerelease_comparison_is_case_sensitive(self):
        upper = Version(1, 2, 3, 'RC.1')
        lower = Version(1, 2, 3, 'rc.1')
        self.assertIs(upper.is_compatible(lower), False)
        self.assertIs(lower.is_compatible(upper), False)

    def test_empty_prerelease_matches_itself_but_not_none(self):
        for major in (0, 1):
            empty = Version(major, 2, 3, '')
            another_empty = Version(major, 2, 3, '')
            absent = Version(major, 2, 3)
            with self.subTest(major=major):
                self.assertIs(empty.is_compatible(another_empty), True)
                self.assertIs(empty.is_compatible(absent), False)
                self.assertIs(absent.is_compatible(empty), False)

    def test_major_zero_identical_versions_are_compatible(self):
        for version in (Version(0, 1, 0), Version(0, 0, 0)):
            with self.subTest(version=version):
                self.assertIs(version.is_compatible(Version(*version.to_tuple())), True)

    def test_major_zero_requires_equal_minor_and_patch(self):
        reference = Version(0, 1, 2)
        for changed in (Version(0, 2, 2), Version(0, 1, 3)):
            with self.subTest(changed=changed):
                self.assertIs(reference.is_compatible(changed), False)
                self.assertIs(changed.is_compatible(reference), False)

    def test_major_zero_requires_equal_prerelease(self):
        first = Version(0, 1, 2, 'rc.1')
        same = Version(0, 1, 2, 'rc.1')
        changed = Version(0, 1, 2, 'rc.2')
        self.assertIs(first.is_compatible(same), True)
        self.assertIs(first.is_compatible(changed), False)
        self.assertIs(changed.is_compatible(first), False)

    def test_build_metadata_is_ignored_for_both_major_rules(self):
        for major in (0, 1):
            a = Version(major, 1, 0, build='a')
            b = Version(major, 1, 0, build='b')
            absent = Version(major, 1, 0)
            with self.subTest(major=major):
                self.assertIs(a.is_compatible(b), True)
                self.assertIs(b.is_compatible(a), True)
                self.assertIs(a.is_compatible(absent), True)
                self.assertIs(absent.is_compatible(a), True)

    def test_invalid_arguments_raise_typeerror_with_required_prefix(self):
        class VersionLike:
            major = 1
            minor = 2
            patch = 3
            prerelease = None
            build = None

        invalid = ('wrongtype', '1.2.3', b'1.2.3', {'a': 2},
                   {'major': 1}, [], (1, 2, 3), None, 7, object(), VersionLike())
        for old in (Version(0, 1, 0), Version(1, 2, 3)):
            before = old.to_tuple()
            for value in invalid:
                with self.subTest(old=old, value=value):
                    with self.assertRaises(TypeError) as caught:
                        old.is_compatible(value)
                    self.assertTrue(str(caught.exception).startswith('Expected a Version type'))
                    self.assertEqual(old.to_tuple(), before)

    def test_subclasses_are_accepted_independently_of_receiver_class(self):
        pairs = ((Version(1, 0, 0), CustomVersion(1, 0, 0)),
                 (CustomVersion(1, 0, 0), Version(1, 0, 0)),
                 (CustomVersion(1, 0, 0), OtherCustomVersion(1, 0, 0)),
                 (Version(0, 1, 0), CustomVersion(0, 1, 0)),
                 (CustomVersion(0, 1, 0), Version(0, 1, 0)),
                 (CustomVersion(0, 1, 0), OtherCustomVersion(0, 1, 0)))
        for old, replacement in pairs:
            with self.subTest(old=type(old), replacement=type(replacement)):
                self.assertIs(old.is_compatible(replacement), True)

    def test_compatibility_checks_do_not_mutate_either_operand(self):
        cases = ((Version(1, 2, 3, 'rc.1', 'a'), Version(1, 3, 0, 'rc.1', 'b')),
                 (Version(0, 1, 2, 'rc.1', 'a'), Version(0, 1, 3, 'rc.1', 'b')))
        for old, replacement in cases:
            before_old, before_replacement = old.to_tuple(), replacement.to_tuple()
            old.is_compatible(replacement)
            with self.subTest(old=old, replacement=replacement):
                self.assertEqual(old.to_tuple(), before_old)
                self.assertEqual(replacement.to_tuple(), before_replacement)

    def test_docstring_explains_contract_and_has_two_passing_doctests(self):
        doc = inspect.getdoc(Version.is_compatible)
        self.assertIsNotNone(doc)
        for term in ('replac', 'major', 'minor', 'patch', 'prerelease', 'build', 'typeerror'):
            with self.subTest(term=term):
                self.assertIn(term, doc.lower())
        example = doctest.DocTestParser().get_doctest(
            doc, {'Version': Version, 'semver': semver},
            'Version.is_compatible', '<docstring>', 0)
        self.assertGreaterEqual(len(example.examples), 2)
        result = doctest.DocTestRunner().run(example, out=lambda text: None)
        self.assertEqual(result.failed, 0)
