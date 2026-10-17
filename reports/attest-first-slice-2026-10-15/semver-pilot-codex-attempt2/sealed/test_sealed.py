import ast
import doctest
import inspect
import re
import unittest

import semver
from semver import Version
from semver.version import Version as ModuleVersion


class CustomVersion(Version):
    pass


class CompatibilityTests(unittest.TestCase):
    def test_method_is_available_through_both_public_imports(self):
        self.assertIs(Version, ModuleVersion)
        self.assertTrue(callable(Version.is_compatible))
        self.assertTrue(callable(ModuleVersion.is_compatible))

    def test_signature_requires_one_positional_or_keyword_other(self):
        parameters = list(inspect.signature(Version.is_compatible).parameters.values())
        self.assertEqual([parameter.name for parameter in parameters], ['self', 'other'])
        self.assertEqual(parameters[1].kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertIs(parameters[1].default, inspect.Parameter.empty)
        self.assertIs(Version(1, 2, 3).is_compatible(other=Version(1, 2, 3)), True)

    def test_identical_versions_return_actual_bool(self):
        result = Version(1, 2, 3).is_compatible(Version(1, 2, 3))
        self.assertIs(result, True)

    def test_patch_is_ignored_for_nonzero_major_in_both_directions(self):
        lower = Version(1, 2, 3)
        higher = Version(1, 2, 4)
        self.assertIs(lower.is_compatible(higher), True)
        self.assertIs(higher.is_compatible(lower), True)

    def test_higher_minor_can_replace_lower_minor_only(self):
        original = Version(1, 2, 9)
        replacement = Version(1, 3, 0)
        self.assertIs(original.is_compatible(replacement), True)
        self.assertIs(replacement.is_compatible(original), False)

    def test_lower_minor_cannot_replace_nonzero_major(self):
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_in_both_directions(self):
        for left, right in [(Version(0, 1, 0), Version(1, 1, 0)),
                            (Version(2, 0, 0), Version(1, 5, 0)),
                            (Version(1, 2, 3, 'rc.0'), Version(2, 9, 9, 'rc.0'))]:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_matching_prereleases_allow_nonzero_patch_change(self):
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')), True)

    def test_matching_prereleases_allow_nonzero_minor_increase(self):
        self.assertIs(Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_unequal_prereleases_are_incompatible_even_with_higher_minor(self):
        for left, right in [('rc.1', 'rc.0'), ('RC.0', 'rc.0'), (None, 'rc1')]:
            with self.subTest(left=left, right=right):
                original = Version(1, 2, 3, left)
                replacement = Version(1, 3, 0, right)
                self.assertIs(original.is_compatible(replacement), False)
                self.assertIs(replacement.is_compatible(original), False)

    def test_empty_prerelease_matches_only_empty_prerelease(self):
        for major in (0, 1):
            with self.subTest(major=major):
                empty = Version(major, 2, 3, '')
                another_empty = Version(major, 2, 3, '')
                absent = Version(major, 2, 3)
                self.assertEqual(empty.prerelease, '')
                self.assertIs(empty.is_compatible(another_empty), True)
                self.assertIs(empty.is_compatible(absent), False)
                self.assertIs(absent.is_compatible(empty), False)
                self.assertIs(absent.is_compatible(Version(major, 2, 3)), True)

    def test_major_zero_identical_components_are_compatible(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)

    def test_major_zero_requires_equal_minor_and_patch_in_both_directions(self):
        original = Version(0, 1, 0)
        for changed in (Version(0, 2, 0), Version(0, 1, 1)):
            with self.subTest(changed=changed):
                self.assertIs(original.is_compatible(changed), False)
                self.assertIs(changed.is_compatible(original), False)

    def test_major_zero_requires_exact_prerelease(self):
        original = Version(0, 1, 0, 'rc.0')
        self.assertIs(original.is_compatible(Version(0, 1, 0, 'rc.0')), True)
        for changed in (Version(0, 1, 0, 'rc.1'), Version(0, 1, 0)):
            with self.subTest(changed=changed):
                self.assertIs(original.is_compatible(changed), False)
                self.assertIs(changed.is_compatible(original), False)

    def test_build_metadata_is_ignored_for_both_major_categories(self):
        for major in (0, 1):
            with self.subTest(major=major):
                absent = Version(major, 2, 3, 'rc.0')
                first = Version(major, 2, 3, 'rc.0', 'build.1')
                second = Version(major, 2, 3, 'rc.0', 'build.2')
                for left, right in ((absent, first), (first, absent),
                                    (first, second), (second, first)):
                    self.assertIs(left.is_compatible(right), True)

    def test_build_metadata_does_not_override_incompatible_fields(self):
        for original, replacement in [
            (Version(0, 1, 0, build='a'), Version(0, 1, 1, build='b')),
            (Version(1, 2, 0, build='a'), Version(1, 1, 0, build='b')),
            (Version(1, 2, 0, 'rc.0', 'a'), Version(1, 3, 0, 'rc.1', 'b')),
        ]:
            with self.subTest(original=original, replacement=replacement):
                self.assertIs(original.is_compatible(replacement), False)

    def test_invalid_other_raises_typeerror_for_nonzero_major(self):
        original = Version(1, 2, 3)
        for other in ('wrongtype', '1.2.3', b'1.2.3', {'a': 2},
                      {'major': 1}, [], (1, 2, 3), 1, None, object()):
            with self.subTest(other=other):
                with self.assertRaises(TypeError) as caught:
                    original.is_compatible(other)
                self.assertTrue(str(caught.exception).startswith('Expected a Version type'))

    def test_invalid_other_raises_typeerror_for_major_zero(self):
        original = Version(0, 1, 0)
        for other in ('wrongtype', '1.2.3', b'1.2.3', {'a': 2},
                      {'major': 1}, [], (1, 2, 3), 1, None, object()):
            with self.subTest(other=other):
                with self.assertRaises(TypeError) as caught:
                    original.is_compatible(other)
                self.assertTrue(str(caught.exception).startswith('Expected a Version type'))

    def test_base_and_subclass_operands_work_in_every_combination(self):
        base = Version(1, 2, 3)
        subclass = CustomVersion(1, 2, 4)
        another_subclass = CustomVersion(1, 2, 5)
        self.assertIs(base.is_compatible(subclass), True)
        self.assertIs(subclass.is_compatible(base), True)
        self.assertIs(subclass.is_compatible(another_subclass), True)

    def test_subclass_operands_follow_the_same_incompatibility_rules(self):
        original = CustomVersion(1, 2, 3, 'rc.0')
        self.assertIs(original.is_compatible(CustomVersion(1, 3, 0, 'rc.1')), False)
        self.assertIs(Version(0, 1, 0).is_compatible(CustomVersion(0, 1, 1)), False)
        self.assertIs(CustomVersion(1, 2, 3).is_compatible(Version(2, 2, 3)), False)

    def test_valid_calls_leave_all_components_of_both_operands_unchanged(self):
        original = Version(1, 2, 3, 'rc.0', 'build.a')
        compatible = Version(1, 3, 0, 'rc.0', 'build.b')
        incompatible = Version(1, 3, 0, 'rc.1', 'build.c')
        snapshots = [value.to_tuple() for value in (original, compatible, incompatible)]
        self.assertIs(original.is_compatible(compatible), True)
        self.assertIs(original.is_compatible(incompatible), False)
        self.assertEqual([value.to_tuple() for value in (original, compatible, incompatible)], snapshots)

    def test_invalid_call_leaves_receiver_components_unchanged(self):
        original = Version(0, 1, 0, 'rc.0', 'build.a')
        before = original.to_tuple()
        with self.assertRaises(TypeError):
            original.is_compatible('0.1.0')
        self.assertEqual(original.to_tuple(), before)

    def test_docstring_explains_the_contract(self):
        doc = inspect.getdoc(Version.is_compatible)
        self.assertIsInstance(doc, str)
        for term in ('other', 'Version', 'major', 'minor', 'patch',
                     'prerelease', 'build', 'TypeError', 'return'):
            with self.subTest(term=term):
                self.assertIn(term.lower(), doc.lower())
        self.assertRegex(doc.lower(), r'replac')

    def test_docstring_has_two_executable_compatibility_doctests(self):
        doc = Version.is_compatible.__doc__ or ''
        parser = doctest.DocTestParser()
        examples = parser.get_examples(doc)
        compatibility_examples = []
        for example in examples:
            calls = [node for node in ast.walk(ast.parse(example.source))
                     if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)
                     and node.func.attr == 'is_compatible']
            if calls and example.want.strip() in ('True', 'False'):
                compatibility_examples.append(example)
        self.assertGreaterEqual(len(compatibility_examples), 2)
        test = parser.get_doctest(doc, {'Version': Version, 'semver': semver},
                                  'Version.is_compatible', None, None)
        result = doctest.DocTestRunner().run(test)
        self.assertEqual(result.failed, 0)


class ExistingBehaviorTests(unittest.TestCase):
    def test_parsing_and_formatting_still_preserve_components(self):
        version = Version.parse('1.2.3-rc.1+build.2')
        self.assertEqual(version.to_tuple(), (1, 2, 3, 'rc.1', 'build.2'))
        self.assertEqual(str(version), '1.2.3-rc.1+build.2')

    def test_existing_comparison_and_hash_behavior_remain_available(self):
        first = Version(1, 2, 3, build='a')
        second = Version(1, 2, 3, build='b')
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertLess(first, Version(1, 2, 4))

    def test_existing_read_only_properties_remain_read_only(self):
        version = Version(1, 2, 3)
        with self.assertRaises(AttributeError):
            version.major = 4
