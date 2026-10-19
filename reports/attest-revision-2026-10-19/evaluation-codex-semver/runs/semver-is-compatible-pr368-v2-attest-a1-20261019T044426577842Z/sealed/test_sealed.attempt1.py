import doctest
import re
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class TestVersionCompatibility(unittest.TestCase):
    def test_public_entry_points_and_keyword_argument(self):
        self.assertIs(semver.Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        for cls in (semver.Version, ModuleVersion, VersionInfo):
            with self.subTest(cls=cls):
                receiver = cls(1, 2, 3)
                candidate = Version(1, 2, 4)
                self.assertIs(receiver.is_compatible(candidate), True)
                self.assertIs(receiver.is_compatible(other=candidate), True)
                self.assertIs(receiver.is_compatible(Version(1, 1, 9)), False)

    def test_nonzero_major_self_compatibility(self):
        version = Version(1, 2, 3)
        self.assertIs(version.is_compatible(version), True)

    def test_nonzero_major_ignores_patch_in_both_directions(self):
        lower = Version(1, 2, 3)
        higher = Version(1, 2, 4)
        self.assertIs(lower.is_compatible(higher), True)
        self.assertIs(higher.is_compatible(lower), True)

    def test_nonzero_major_minor_is_directional(self):
        lower = Version(1, 2, 9)
        higher = Version(1, 3, 0)
        self.assertIs(lower.is_compatible(higher), True)
        self.assertIs(higher.is_compatible(lower), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_in_both_directions(self):
        for left, right in ((Version(2, 0, 0), Version(1, 5, 0)), (Version(0, 1, 0), Version(1, 1, 0))):
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_equal_prerelease_allows_patch_and_minor_changes(self):
        receiver = Version(1, 2, 3, 'rc.0')
        self.assertIs(receiver.is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(receiver.is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_different_prerelease_values_are_incompatible(self):
        for left, right in (('rc.1', 'rc.0'), ('rc.0', 'RC.0')):
            with self.subTest(left=left, right=right):
                self.assertIs(Version(1, 2, 3, left).is_compatible(Version(1, 3, 4, right)), False)
                self.assertIs(Version(1, 3, 4, right).is_compatible(Version(1, 2, 3, left)), False)

    def test_absent_and_present_prereleases_are_incompatible(self):
        plain = Version(1, 2, 3)
        prerelease = Version(1, 2, 4, 'rc.0')
        self.assertIs(plain.is_compatible(prerelease), False)
        self.assertIs(prerelease.is_compatible(plain), False)

    def test_prerelease_uses_exact_stored_values(self):
        for major in (0, 1):
            with self.subTest(major=major):
                absent = Version(major, 2, 3, None)
                empty = Version(major, 2, 3, '')
                self.assertIs(absent.is_compatible(Version(major, 2, 3, None)), True)
                self.assertIs(empty.is_compatible(Version(major, 2, 3, '')), True)
                self.assertIs(absent.is_compatible(empty), False)
                self.assertIs(empty.is_compatible(absent), False)

    def test_zero_major_identical_versions_are_compatible(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)
        zero = Version(0, 0, 0)
        self.assertIs(zero.is_compatible(zero), True)

    def test_zero_major_requires_equal_minor_patch_and_prerelease(self):
        base = Version(0, 1, 0, 'rc.0')
        for changed in (Version(0, 1, 1, 'rc.0'), Version(0, 2, 0, 'rc.0'), Version(0, 1, 0, 'rc.1')):
            with self.subTest(changed=changed):
                self.assertIs(base.is_compatible(changed), False)
                self.assertIs(changed.is_compatible(base), False)

    def test_build_metadata_is_ignored_for_both_major_rules(self):
        for major in (0, 1):
            left = Version(major, 2, 3, 'rc.0', 'first')
            right = Version(major, 2, 3, 'rc.0', 'second')
            absent = Version(major, 2, 3, 'rc.0')
            with self.subTest(major=major):
                self.assertIs(left.is_compatible(right), True)
                self.assertIs(right.is_compatible(left), True)
                self.assertIs(left.is_compatible(absent), True)
                self.assertIs(absent.is_compatible(left), True)

    def test_build_differences_do_not_hide_other_incompatibilities(self):
        cases = (
            (Version(1, 2, 3, build='a'), Version(2, 2, 3, build='b')),
            (Version(1, 3, 3, build='a'), Version(1, 2, 3, build='b')),
            (Version(0, 2, 3, build='a'), Version(0, 2, 4, build='b')),
            (Version(0, 2, 3, build='a'), Version(0, 3, 3, build='b')),
            (Version(1, 2, 3, 'rc.0', 'a'), Version(1, 2, 3, 'rc.1', 'b')),
        )
        for receiver, candidate in cases:
            with self.subTest(receiver=receiver, candidate=candidate):
                self.assertIs(receiver.is_compatible(candidate), False)

    def test_version_subclasses_are_accepted_as_either_operand(self):
        class First(Version):
            pass

        class Second(Version):
            pass

        self.assertIs(Version(1, 2, 9).is_compatible(First(1, 3, 0)), True)
        self.assertIs(First(1, 2, 9).is_compatible(Version(1, 3, 0)), True)
        self.assertIs(First(1, 2, 9).is_compatible(Second(1, 3, 0)), True)
        self.assertIs(Second(1, 3, 0).is_compatible(First(1, 2, 9)), False)
        self.assertIs(First(0, 2, 3).is_compatible(Second(0, 2, 3)), True)
        self.assertIs(First(0, 2, 3).is_compatible(Second(0, 2, 4)), False)

    def test_invalid_other_types_raise_typeerror_with_exact_message(self):
        invalid_values = ('1.2.3', 'not a version', b'1.2.3', {}, [], (), 12, None, object())
        for major in (0, 1):
            receiver = Version(major, 2, 3)
            for value in invalid_values:
                with self.subTest(major=major, value_type=type(value)):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(value)
                    self.assertEqual(str(cm.exception), 'Expected a Version type but got ' + str(type(value)))

    def test_successful_call_does_not_mutate_operands(self):
        receiver = Version(1, 2, 9, 'rc.0', 'first')
        candidate = Version(1, 3, 0, 'rc.0', 'second')
        before = (receiver.to_tuple(), candidate.to_tuple())
        self.assertIs(receiver.is_compatible(candidate), True)
        self.assertEqual((receiver.to_tuple(), candidate.to_tuple()), before)

    def test_incompatible_call_does_not_mutate_operands(self):
        receiver = Version(0, 2, 3, 'rc.0', 'first')
        candidate = Version(0, 2, 4, 'rc.0', 'second')
        before = (receiver.to_tuple(), candidate.to_tuple())
        self.assertIs(receiver.is_compatible(candidate), False)
        self.assertEqual((receiver.to_tuple(), candidate.to_tuple()), before)

    def test_invalid_type_call_does_not_mutate_receiver(self):
        receiver = Version(0, 2, 3, 'rc.0', 'first')
        before = receiver.to_tuple()
        with self.assertRaises(TypeError):
            receiver.is_compatible('0.2.3-rc.0+first')
        self.assertEqual(receiver.to_tuple(), before)

    def test_method_docstring_describes_contract_and_has_two_doctests(self):
        self.assertIs(Version(1, 2, 3).is_compatible(Version(1, 2, 4)), True)
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        normalized = doc.lower()
        for term in ('other', 'replace', 'major', 'minor', 'patch', 'prerelease', 'build', 'version', 'typeerror'):
            with self.subTest(term=term):
                self.assertIn(term, normalized)
        self.assertRegex(normalized, r'zero|\b0\b')
        self.assertRegex(normalized, r'higher|greater|at least|equal or|>=')
        self.assertRegex(normalized, r'ignor|disregard|not affect')
        examples = [part for part in doctest.DocTestParser().parse(doc) if isinstance(part, doctest.Example) and 'is_compatible(' in part.source and re.fullmatch(r'(True|False)\s*', part.want)]
        self.assertGreaterEqual(len(examples), 2)
        for example in examples:
            compile(example.source, '<compatibility doctest>', 'exec')

    def test_existing_comparison_behavior_remains_available(self):
        self.assertLess(Version(1, 2, 3, 'rc.1').compare(Version(1, 2, 3)), 0)
        self.assertGreater(Version(1, 2, 4).compare(Version(1, 2, 3)), 0)

    def test_existing_parsing_behavior_remains_available(self):
        parsed = Version.parse('1.2.3-rc.1+build.7')
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, 'rc.1', 'build.7'))
        self.assertIs(type(parsed), Version)

    def test_existing_constructor_normalization_remains_available(self):
        version = Version('1', '2', '3', 4, 5)
        self.assertEqual(version.to_tuple(), (1, 2, 3, '4', '5'))

    def test_existing_readonly_properties_remain_readonly(self):
        version = Version(1, 2, 3)
        with self.assertRaises(AttributeError):
            version.minor = 8
        self.assertEqual(version.to_tuple(), (1, 2, 3, None, None))
