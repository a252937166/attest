import re
import unittest

from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class TestCompatibility(unittest.TestCase):
    def test_public_aliases_expose_method(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        for cls in (Version, ModuleVersion, VersionInfo):
            self.assertIs(cls(1, 2, 3).is_compatible(cls(1, 2, 4)), True)

    def test_keyword_other_matches_positional_call(self):
        receiver = Version(1, 2, 3)
        replacement = Version(1, 3, 0)
        self.assertIs(receiver.is_compatible(other=replacement), receiver.is_compatible(replacement))

    def test_nonzero_major_ignores_patch_in_both_directions(self):
        for left, right in ((Version(1, 2, 3), Version(1, 2, 3)), (Version(1, 2, 3), Version(1, 2, 4)), (Version(1, 2, 4), Version(1, 2, 3))):
            self.assertIs(left.is_compatible(right), True)

    def test_nonzero_major_minor_direction(self):
        self.assertIs(Version(1, 1, 9).is_compatible(Version(1, 2, 0)), True)
        self.assertIs(Version(1, 2, 0).is_compatible(Version(1, 1, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_both_ways(self):
        for left, right in ((Version(2, 0, 0), Version(1, 5, 0)), (Version(0, 1, 0), Version(1, 1, 0))):
            self.assertIs(left.is_compatible(right), False)
            self.assertIs(right.is_compatible(left), False)

    def test_equal_prerelease_allows_patch_change(self):
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')), True)

    def test_equal_prerelease_allows_minor_increase(self):
        self.assertIs(Version(1, 2, 9, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_unequal_prereleases_are_incompatible_both_ways(self):
        for first, second in (('rc.1', 'rc.0'), ('rc.1', 'RC.1'), (None, 'rc1')):
            left = Version(1, 2, 3, first)
            right = Version(1, 2, 4, second)
            self.assertIs(left.is_compatible(right), False)
            self.assertIs(right.is_compatible(left), False)
            self.assertIs(left.is_compatible(Version(1, 3, 0, second)), False)

    def test_none_and_empty_prerelease_remain_distinct(self):
        self.assertIs(Version(1, 2, 3).is_compatible(Version(1, 2, 3, '')), False)
        self.assertIs(Version(1, 2, 3, '').is_compatible(Version(1, 2, 3)), False)
        self.assertIs(Version(1, 2, 3, '').is_compatible(Version(1, 3, 0, '')), True)

    def test_major_zero_identical_components_are_compatible(self):
        for version in (Version(0, 1, 0), Version(0, 0, 0), Version(0, 1, 0, 'rc.1')):
            self.assertIs(version.is_compatible(Version(*version.to_tuple())), True)

    def test_major_zero_requires_exact_minor_patch_and_prerelease(self):
        baseline = Version(0, 1, 0, 'rc.1')
        for changed in (Version(0, 2, 0, 'rc.1'), Version(0, 1, 1, 'rc.1'), Version(0, 1, 0, 'rc.2')):
            self.assertIs(baseline.is_compatible(changed), False)
            self.assertIs(changed.is_compatible(baseline), False)

    def test_build_metadata_is_ignored_for_compatible_pairs(self):
        pairs = ((Version(1, 2, 9, 'rc.1', 'a'), Version(1, 3, 0, 'rc.1', 'b')), (Version(1, 2, 3, build='a'), Version(1, 2, 4)), (Version(0, 1, 0, build='a'), Version(0, 1, 0, build='b')), (Version(0, 1, 0), Version(0, 1, 0, build='b')))
        for left, right in pairs:
            self.assertIs(left.is_compatible(right), True)

    def test_build_metadata_cannot_rescue_incompatible_pairs(self):
        self.assertIs(Version(1, 3, 0, build='a').is_compatible(Version(1, 2, 0, build='b')), False)
        self.assertIs(Version(0, 1, 0, build='a').is_compatible(Version(0, 1, 1, build='b')), False)

    def test_invalid_other_raises_exact_type_error(self):
        invalid = ('wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, 1, Version)
        for receiver in (Version(0, 1, 0), Version(1, 2, 3)):
            for other in invalid:
                with self.subTest(receiver=receiver, other=other):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(other)
                    self.assertEqual(str(cm.exception), f'Expected a Version type but got {type(other)}')

    def test_base_and_distinct_subclasses_are_accepted(self):
        class CustomVersion(Version):
            pass

        class AnotherVersion(Version):
            pass

        self.assertIs(Version(1, 0, 0).is_compatible(CustomVersion(1, 1, 0)), True)
        self.assertIs(CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)), True)
        self.assertIs(CustomVersion(1, 0, 0).is_compatible(AnotherVersion(1, 1, 0)), True)
        self.assertIs(CustomVersion(0, 1, 0).is_compatible(AnotherVersion(0, 1, 0)), True)
        self.assertIs(CustomVersion(0, 1, 0).is_compatible(AnotherVersion(0, 1, 1)), False)

    def test_successful_results_are_bool_singletons(self):
        for left, right, expected in ((Version(1, 2, 3), Version(1, 3, 0), True), (Version(1, 3, 0), Version(1, 2, 3), False), (Version(0, 1, 0), Version(0, 1, 0), True), (Version(0, 1, 0), Version(0, 1, 1), False)):
            self.assertIs(left.is_compatible(right), expected)

    def test_neither_operand_is_mutated(self):
        for left, right in ((Version(1, 2, 3, 'rc.1', 'build.a'), Version(1, 3, 4, 'rc.1', 'build.b')), (Version(0, 1, 0, 'rc.1', 'build.a'), Version(0, 1, 1, 'rc.1', 'build.b'))):
            before = (left.to_tuple(), right.to_tuple())
            left.is_compatible(right)
            self.assertEqual((left.to_tuple(), right.to_tuple()), before)

    def test_method_docstring_explains_contract_and_contains_examples(self):
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        lower = doc.lower()
        for term in ('replace', 'major', 'minor', 'patch', 'prerelease', 'build', 'return', 'typeerror'):
            self.assertIn(term, lower)
        examples = re.findall(r'^\s*>>>\s+.*\.is_compatible\(.*\)\s*\n\s*(?:True|False)\s*$', doc, re.MULTILINE)
        self.assertGreaterEqual(len(examples), 2)

    def test_existing_constructor_and_parse_behavior(self):
        value = Version.parse('1.2.3-rc.1+build.2')
        self.assertEqual(value.to_tuple(), (1, 2, 3, 'rc.1', 'build.2'))
        self.assertEqual(str(value), '1.2.3-rc.1+build.2')
        self.assertEqual(Version(1, 2, 3).to_tuple(), (1, 2, 3, None, None))

    def test_existing_comparison_and_alias_behavior(self):
        self.assertEqual(Version(1, 2, 3).compare(Version(1, 2, 4)), -1)
        self.assertTrue(Version(1, 2, 3) < Version(1, 2, 4))
        self.assertIs(VersionInfo, Version)

    def test_existing_readonly_properties(self):
        value = Version(1, 2, 3, 'rc.1', 'build.1')
        for name, replacement in (('major', 9), ('minor', 9), ('patch', 9), ('prerelease', 'rc.2'), ('build', 'build.2')):
            with self.assertRaises(AttributeError):
                setattr(value, name, replacement)
