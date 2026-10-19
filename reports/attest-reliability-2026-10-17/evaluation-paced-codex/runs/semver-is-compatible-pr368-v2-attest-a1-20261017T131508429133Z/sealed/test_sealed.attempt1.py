import doctest
import unittest

from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion
from semver.version import VersionInfo as ModuleVersionInfo


class CustomVersion(Version):
    pass


class FieldTrap:
    @property
    def major(self):
        raise AssertionError('version fields were accessed before type validation')


class TestCompatibility(unittest.TestCase):
    def test_public_imports_and_aliases(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        self.assertIs(ModuleVersionInfo, Version)
        for cls in (Version, ModuleVersion, VersionInfo, ModuleVersionInfo):
            with self.subTest(cls=cls):
                self.assertIs(cls(1, 2, 3).is_compatible(cls(1, 2, 4)), True)

    def test_positional_and_keyword_other(self):
        receiver = Version(1, 2, 3)
        for replacement in (Version(1, 3, 0), Version(1, 1, 9)):
            with self.subTest(replacement=replacement):
                self.assertIs(receiver.is_compatible(replacement), receiver.is_compatible(other=replacement))

    def test_nonzero_major_ignores_patch_in_both_directions(self):
        for left, right in ((Version(1, 2, 3), Version(1, 2, 3)),
                            (Version(1, 2, 3), Version(1, 2, 4)),
                            (Version(1, 2, 4), Version(1, 2, 3))):
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), True)

    def test_nonzero_major_minor_rule_is_directional(self):
        self.assertIs(Version(1, 2, 9).is_compatible(Version(1, 3, 0)), True)
        self.assertIs(Version(1, 3, 0).is_compatible(Version(1, 2, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_both_directions(self):
        for left, right in ((Version(1, 9, 9, 'rc'), Version(2, 9, 9, 'rc')),
                            (Version(0, 9, 9, 'rc'), Version(1, 9, 9, 'rc'))):
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_equal_prerelease_allows_patch_and_minor_changes(self):
        receiver = Version(1, 2, 3, 'rc.0')
        self.assertIs(receiver.is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(receiver.is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_different_prereleases_are_incompatible(self):
        pairs = ((Version(1, 2, 3, 'rc.1'), Version(1, 3, 0, 'rc.0')),
                 (Version(1, 2, 3), Version(1, 3, 0, 'rc1')),
                 (Version(1, 2, 3, 'rc1'), Version(1, 3, 0)),
                 (Version(1, 2, 3, 'RC'), Version(1, 3, 0, 'rc')))
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)

    def test_none_and_empty_prerelease_are_distinct(self):
        plain = Version(1, 2, 3)
        empty = Version(1, 2, 3, '')
        self.assertIs(plain.is_compatible(empty), False)
        self.assertIs(empty.is_compatible(plain), False)

    def test_major_zero_identical_required_fields_are_compatible(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)
        self.assertIs(Version(0, 1, 0, 'rc.1').is_compatible(Version(0, 1, 0, 'rc.1')), True)

    def test_major_zero_requires_exact_patch_minor_and_prerelease(self):
        original = Version(0, 1, 0, 'rc.1')
        for changed in (Version(0, 1, 1, 'rc.1'),
                        Version(0, 2, 0, 'rc.1'),
                        Version(0, 1, 0, 'rc.2'),
                        Version(0, 1, 0)):
            with self.subTest(changed=changed):
                self.assertIs(original.is_compatible(changed), False)
                self.assertIs(changed.is_compatible(original), False)

    def test_build_metadata_is_ignored_for_both_major_rules(self):
        pairs = ((Version(1, 2, 3, 'rc', 'one'), Version(1, 3, 9, 'rc', 'two')),
                 (Version(1, 2, 3, build='one'), Version(1, 2, 4)),
                 (Version(0, 1, 3, 'rc', 'one'), Version(0, 1, 3, 'rc', 'two')),
                 (Version(0, 1, 3, build='one'), Version(0, 1, 3)))
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), True)

    def test_equal_build_cannot_override_incompatible_fields(self):
        self.assertIs(Version(1, 3, 0, build='same').is_compatible(Version(1, 2, 0, build='same')), False)
        self.assertIs(Version(0, 1, 0, build='same').is_compatible(Version(0, 1, 1, build='same')), False)

    def test_invalid_argument_types_for_nonzero_major(self):
        receiver = Version(1, 2, 3)
        invalid = ('wrongtype', {'a': 2}, [], '1.2.3', b'1.2.3', (1, 2, 3), None, 1, object())
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    receiver.is_compatible(value)
                self.assertEqual(str(cm.exception), f'Expected a Version type but got {type(value)}')

    def test_invalid_argument_types_for_major_zero(self):
        receiver = Version(0, 1, 0)
        invalid = ('wrongtype', {'a': 2}, [], '1.2.3', b'1.2.3', (1, 2, 3), None, 1, object())
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(TypeError) as cm:
                    receiver.is_compatible(other=value)
                self.assertEqual(str(cm.exception), f'Expected a Version type but got {type(value)}')

    def test_invalid_argument_is_rejected_before_field_access(self):
        value = FieldTrap()
        with self.assertRaises(TypeError) as cm:
            Version(1, 2, 3).is_compatible(value)
        self.assertEqual(str(cm.exception), f'Expected a Version type but got {type(value)}')

    def test_base_and_subclass_arguments_are_accepted(self):
        base = Version(1, 0, 0)
        custom = CustomVersion(1, 0, 0)
        self.assertIs(base.is_compatible(custom), True)
        self.assertIs(custom.is_compatible(base), True)
        self.assertIs(custom.is_compatible(CustomVersion(1, 1, 7)), True)
        self.assertIs(CustomVersion(1, 1, 7).is_compatible(base), False)

    def test_subclass_arguments_follow_major_zero_rule(self):
        base = Version(0, 1, 3, 'rc')
        custom = CustomVersion(0, 1, 3, 'rc')
        self.assertIs(base.is_compatible(custom), True)
        self.assertIs(custom.is_compatible(base), True)
        self.assertIs(custom.is_compatible(CustomVersion(0, 1, 4, 'rc')), False)

    def test_every_successful_result_is_a_bool_singleton(self):
        receiver = Version(1, 2, 3)
        self.assertIs(receiver.is_compatible(Version(1, 3, 0)), True)
        self.assertIs(receiver.is_compatible(Version(1, 1, 0)), False)

    def test_calls_do_not_mutate_either_operand(self):
        cases = ((Version(1, 2, 3, 'rc', 'one'), Version(1, 3, 4, 'rc', 'two')),
                 (Version(0, 1, 3, 'rc', 'one'), Version(0, 1, 4, 'rc', 'two')))
        for receiver, replacement in cases:
            with self.subTest(receiver=receiver):
                before = (receiver.to_tuple(), replacement.to_tuple())
                receiver.is_compatible(replacement)
                self.assertEqual((receiver.to_tuple(), replacement.to_tuple()), before)

    def test_docstring_describes_rules_and_contains_two_result_examples(self):
        self.assertIs(Version(1, 0, 0).is_compatible(Version(1, 0, 1)), True)
        doc = Version.is_compatible.__doc__
        self.assertTrue(doc)
        for word in ('minor', 'patch', 'prerelease', 'build', 'return', 'TypeError'):
            with self.subTest(word=word):
                self.assertIn(word.lower(), doc.lower())
        examples = doctest.DocTestParser().get_examples(doc)
        results = [example.want.strip() for example in examples if example.want.strip() in ('True', 'False')]
        self.assertGreaterEqual(len(results), 2)

    def test_existing_parse_behavior(self):
        self.assertEqual(Version.parse('1.2.3-rc+build').to_tuple(), (1, 2, 3, 'rc', 'build'))

    def test_existing_comparison_behavior(self):
        self.assertLess(Version(1, 2, 3).compare(Version(1, 2, 4)), 0)

    def test_existing_readonly_property_behavior(self):
        version = Version(1, 2, 3)
        with self.assertRaises(AttributeError):
            version.major = 9
