import doctest
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class TestVersionCompatibility(unittest.TestCase):
    def test_public_exports_and_alias(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        self.assertIs(semver.Version, Version)
        self.assertIs(semver.version.Version, Version)
        self.assertIs(semver.VersionInfo, VersionInfo)
        self.assertIs(VersionInfo(1, 0, 0).is_compatible(Version(1, 0, 0)), True)

    def test_keyword_argument_and_literal_bool(self):
        self.assertIs(Version(1, 2, 3).is_compatible(other=Version(1, 2, 4)), True)
        self.assertIs(Version(1, 2, 3).is_compatible(other=Version(2, 2, 3)), False)

    def test_positive_major_ignores_patch_in_both_directions(self):
        for left, right in [(3, 4), (4, 3)]:
            with self.subTest(left=left, right=right):
                self.assertIs(Version(1, 2, left).is_compatible(Version(1, 2, right)), True)
        self.assertIs(Version(1, 2, 3).is_compatible(Version(1, 2, 3)), True)

    def test_higher_candidate_minor_is_compatible_despite_patch(self):
        self.assertIs(Version(1, 2, 9).is_compatible(Version(1, 3, 0)), True)

    def test_lower_candidate_minor_is_incompatible(self):
        self.assertIs(Version(1, 3, 0).is_compatible(Version(1, 2, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_positive_majors_in_both_directions(self):
        for receiver, candidate in [(Version(1, 9, 9), Version(2, 0, 0)), (Version(2, 0, 0), Version(1, 9, 9))]:
            with self.subTest(receiver=receiver, candidate=candidate):
                self.assertIs(receiver.is_compatible(candidate), False)

    def test_zero_and_positive_majors_in_both_directions(self):
        for receiver, candidate in [(Version(0, 9, 9, 'rc'), Version(1, 9, 9, 'rc')), (Version(1, 9, 9, 'rc'), Version(0, 9, 9, 'rc'))]:
            with self.subTest(receiver=receiver, candidate=candidate):
                self.assertIs(receiver.is_compatible(candidate), False)

    def test_equal_prerelease_allows_patch_and_minor_changes(self):
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(Version(1, 2, 9, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_different_prerelease_identifiers_are_incompatible(self):
        self.assertIs(Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 3, 0, 'rc.0')), False)
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.1')), False)

    def test_release_and_prerelease_are_incompatible_in_both_directions(self):
        for receiver, candidate in [(Version(1, 2, 3), Version(1, 3, 0, 'rc1')), (Version(1, 2, 3, 'rc1'), Version(1, 3, 0))]:
            with self.subTest(receiver=receiver, candidate=candidate):
                self.assertIs(receiver.is_compatible(candidate), False)

    def test_prerelease_comparison_is_case_sensitive(self):
        for major in (0, 1):
            with self.subTest(major=major):
                self.assertIs(Version(major, 2, 3, 'RC.1').is_compatible(Version(major, 2, 3, 'rc.1')), False)

    def test_empty_prerelease_differs_from_none(self):
        for major in (0, 1):
            with self.subTest(major=major):
                self.assertIs(Version(major, 2, 3, '').is_compatible(Version(major, 2, 3)), False)
                self.assertIs(Version(major, 2, 3).is_compatible(Version(major, 2, 3, '')), False)

    def test_zero_major_exact_match(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)
        self.assertIs(Version(0, 0, 0).is_compatible(Version(0, 0, 0)), True)
        self.assertIs(Version(0, 1, 0, 'rc.1').is_compatible(Version(0, 1, 0, 'rc.1')), True)

    def test_zero_major_requires_matching_patch_in_both_directions(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 1)), False)
        self.assertIs(Version(0, 1, 1).is_compatible(Version(0, 1, 0)), False)

    def test_zero_major_requires_matching_minor_in_both_directions(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 2, 0)), False)
        self.assertIs(Version(0, 2, 0).is_compatible(Version(0, 1, 0)), False)

    def test_zero_major_requires_matching_prerelease(self):
        self.assertIs(Version(0, 1, 0, 'rc.0').is_compatible(Version(0, 1, 0, 'rc.1')), False)
        self.assertIs(Version(0, 1, 0, 'rc.1').is_compatible(Version(0, 1, 0)), False)

    def test_build_is_ignored_for_compatible_versions(self):
        for receiver, candidate in [
            (Version(1, 2, 9, build='old'), Version(1, 3, 0, build='new')),
            (Version(1, 2, 9), Version(1, 3, 0, build='new')),
            (Version(0, 1, 0, 'rc.1', 'old'), Version(0, 1, 0, 'rc.1', 'new')),
            (Version(0, 1, 0, build='old'), Version(0, 1, 0)),
        ]:
            with self.subTest(receiver=receiver, candidate=candidate):
                self.assertIs(receiver.is_compatible(candidate), True)

    def test_matching_build_cannot_override_incompatibility(self):
        self.assertIs(Version(1, 3, 0, build='same').is_compatible(Version(1, 2, 0, build='same')), False)
        self.assertIs(Version(0, 1, 0, build='same').is_compatible(Version(0, 1, 1, build='same')), False)
        self.assertIs(Version(1, 2, 0, 'rc.0', 'same').is_compatible(Version(1, 2, 0, 'rc.1', 'same')), False)

    def test_non_version_operands_raise_typeerror_for_each_major(self):
        class VersionLike:
            major = 1
            minor = 2
            patch = 3
            prerelease = None
            build = None

        invalid = ['wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, 123, VersionLike()]
        for major in (0, 1):
            for other in invalid:
                with self.subTest(major=major, other=repr(other)):
                    with self.assertRaises(TypeError) as caught:
                        Version(major, 1, 0).is_compatible(other)
                    self.assertTrue(str(caught.exception).startswith('Expected a Version type'))

    def test_base_and_subclass_operands_in_both_directions(self):
        class CustomVersion(Version):
            pass

        self.assertIs(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)), True)
        self.assertIs(Version(1, 0, 0).is_compatible(CustomVersion(1, 0, 0)), True)
        self.assertIs(CustomVersion(0, 1, 2).is_compatible(Version(0, 1, 2)), True)
        self.assertIs(Version(0, 1, 2).is_compatible(CustomVersion(0, 1, 2)), True)

    def test_distinct_subclasses_follow_same_rules(self):
        class FirstVersion(Version):
            pass

        class SecondVersion(Version):
            pass

        self.assertIs(FirstVersion(1, 2, 9).is_compatible(SecondVersion(1, 3, 0)), True)
        self.assertIs(SecondVersion(1, 3, 0).is_compatible(FirstVersion(1, 2, 9)), False)
        self.assertIs(FirstVersion(0, 2, 9).is_compatible(SecondVersion(0, 2, 9)), True)
        self.assertIs(FirstVersion(0, 2, 9).is_compatible(SecondVersion(0, 2, 8)), False)

    def test_operands_are_not_mutated(self):
        for receiver, candidate in [
            (Version(1, 2, 9, 'rc.1', 'old'), Version(1, 3, 0, 'rc.1', 'new')),
            (Version(0, 2, 9, 'rc.1', 'old'), Version(0, 2, 8, 'rc.0', 'new')),
        ]:
            with self.subTest(receiver=receiver, candidate=candidate):
                before_receiver = receiver.to_tuple()
                before_candidate = candidate.to_tuple()
                receiver.is_compatible(candidate)
                self.assertEqual(receiver.to_tuple(), before_receiver)
                self.assertEqual(candidate.to_tuple(), before_candidate)

    def test_docstring_describes_contract(self):
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        lowered = doc.lower()
        for term in ('other', 'replace', 'minor', 'prerelease', 'build', 'typeerror'):
            with self.subTest(term=term):
                self.assertIn(term, lowered)
        self.assertIn('0', lowered)
        self.assertTrue('bool' in lowered or ('true' in lowered and 'false' in lowered))
        self.assertTrue('ignor' in lowered or 'disregard' in lowered)

    def test_docstring_has_two_working_compatibility_doctests(self):
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        parser = doctest.DocTestParser()
        examples = parser.get_examples(doc)
        compatibility_examples = [example for example in examples if '.is_compatible(' in example.source]
        self.assertGreaterEqual(len(compatibility_examples), 2)
        test = parser.get_doctest(doc, {'Version': Version, 'semver': semver}, 'Version.is_compatible', None, 0)
        result = doctest.DocTestRunner().run(test)
        self.assertEqual(result.failed, 0)
