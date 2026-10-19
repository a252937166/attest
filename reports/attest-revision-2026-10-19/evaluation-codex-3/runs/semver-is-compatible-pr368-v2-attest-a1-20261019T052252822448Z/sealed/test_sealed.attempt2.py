import doctest
import io
import unittest
import warnings
from contextlib import redirect_stdout

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion
from semver.version import VersionInfo as ModuleVersionInfo


class CompatibilityAcceptanceTests(unittest.TestCase):
    def test_public_aliases_keep_their_identity(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        self.assertIs(ModuleVersionInfo, Version)
        self.assertIs(semver.VersionInfo, Version)
        self.assertIs(semver.Version(1, 2, 3).is_compatible(Version(1, 2, 3)), True)

    def test_positional_and_keyword_other_agree(self):
        old = Version(1, 2, 9)
        new = Version(1, 3, 0)
        self.assertIs(old.is_compatible(new), True)
        self.assertIs(old.is_compatible(other=new), True)

    def test_positive_major_ignores_patch_in_both_directions(self):
        low = Version(1, 2, 3)
        high = Version(1, 2, 4)
        self.assertIs(low.is_compatible(low), True)
        self.assertIs(low.is_compatible(high), True)
        self.assertIs(high.is_compatible(low), True)

    def test_positive_major_accepts_higher_minor(self):
        self.assertIs(Version(1, 2, 9).is_compatible(Version(1, 3, 0)), True)

    def test_positive_major_rejects_lower_minor(self):
        self.assertIs(Version(1, 3, 0).is_compatible(Version(1, 2, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible_in_both_directions(self):
        pairs = [
            (Version(1, 9, 9, 'rc.0'), Version(2, 0, 0, 'rc.0')),
            (Version(0, 9, 9, 'rc.0'), Version(1, 0, 0, 'rc.0')),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_matching_prerelease_allows_patch_and_minor_changes(self):
        old = Version(1, 2, 3, 'rc.0')
        self.assertIs(old.is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(old.is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_prerelease_values_must_match_exactly(self):
        pairs = [
            (Version(1, 2, 3, 'rc.1'), Version(1, 2, 3, 'rc.0')),
            (Version(1, 2, 3, 'RC.0'), Version(1, 2, 3, 'rc.0')),
            (Version(1, 2, 3), Version(1, 2, 3, 'rc1')),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_none_and_empty_prerelease_are_distinct(self):
        absent = Version(1, 2, 3)
        empty = Version(1, 2, 3, '')
        self.assertIs(absent.is_compatible(empty), False)
        self.assertIs(empty.is_compatible(absent), False)
        self.assertIs(empty.is_compatible(Version(1, 3, 0, '')), True)

    def test_major_zero_accepts_equal_fields(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)
        self.assertIs(Version(0, 0, 0).is_compatible(Version(0, 0, 0)), True)
        self.assertIs(Version(0, 1, 0, 'rc.0').is_compatible(Version(0, 1, 0, 'rc.0')), True)

    def test_major_zero_requires_equal_minor_and_patch(self):
        pairs = [
            (Version(0, 1, 0), Version(0, 1, 1)),
            (Version(0, 1, 0), Version(0, 2, 0)),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_major_zero_requires_equal_prerelease(self):
        old = Version(0, 1, 0, 'rc.0')
        new = Version(0, 1, 0, 'rc.1')
        self.assertIs(old.is_compatible(new), False)
        self.assertIs(new.is_compatible(old), False)

    def test_positive_major_ignores_build_metadata(self):
        versions = [Version(1, 2, 3), Version(1, 2, 3, build='build.1'), Version(1, 2, 3, build='build.2')]
        for old in versions:
            for new in versions:
                with self.subTest(old=old, new=new):
                    self.assertIs(old.is_compatible(new), True)

    def test_major_zero_ignores_build_metadata(self):
        versions = [Version(0, 1, 3), Version(0, 1, 3, build='build.1'), Version(0, 1, 3, build='build.2')]
        for old in versions:
            for new in versions:
                with self.subTest(old=old, new=new):
                    self.assertIs(old.is_compatible(new), True)

    def test_build_metadata_cannot_override_incompatibility(self):
        self.assertIs(Version(1, 3, 0, build='same').is_compatible(Version(1, 2, 0, build='same')), False)
        self.assertIs(Version(0, 1, 0, build='same').is_compatible(Version(0, 1, 1, build='same')), False)

    def test_non_version_arguments_raise_exact_typeerror(self):
        invalid = ['wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, 1]
        for receiver in (Version(1, 2, 3), Version(0, 1, 0)):
            for other in invalid:
                with self.subTest(receiver=receiver, other=other):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(other)
                    self.assertEqual(str(cm.exception), 'Expected a Version type but got ' + str(type(other)))

    def test_python_argument_binding_rejects_missing_extra_and_unknown_arguments(self):
        receiver = Version(1, 2, 3)
        other = Version(1, 2, 4)
        with self.assertRaises(TypeError):
            receiver.is_compatible()
        with self.assertRaises(TypeError):
            receiver.is_compatible(other, other)
        with self.assertRaises(TypeError):
            receiver.is_compatible(candidate=other)

    def test_base_and_subclass_instances_interoperate(self):
        class CustomVersion(Version):
            pass

        for major in (0, 1):
            base = Version(major, 2, 3, 'rc.0')
            custom = CustomVersion(major, 2, 3, 'rc.0')
            with self.subTest(major=major):
                self.assertIs(custom.is_compatible(base), True)
                self.assertIs(base.is_compatible(custom), True)
                self.assertIs(custom.is_compatible(CustomVersion(major, 2, 3, 'rc.0')), True)

    def test_distinct_subclasses_follow_the_same_field_rules(self):
        class FirstVersion(Version):
            pass

        class SecondVersion(Version):
            pass

        self.assertIs(FirstVersion(1, 2, 9).is_compatible(SecondVersion(1, 3, 0)), True)
        self.assertIs(SecondVersion(1, 3, 0).is_compatible(FirstVersion(1, 2, 9)), False)
        self.assertIs(FirstVersion(0, 2, 9).is_compatible(SecondVersion(0, 2, 9)), True)

    def test_successful_and_unsuccessful_checks_preserve_both_operands(self):
        pairs = [
            (Version(1, 2, 3, 'rc.0', 'old'), Version(1, 3, 0, 'rc.0', 'new')),
            (Version(0, 2, 3, 'rc.0', 'old'), Version(0, 2, 4, 'rc.0', 'new')),
        ]
        for old, new in pairs:
            with self.subTest(old=old, new=new):
                before = (old.to_tuple(), new.to_tuple())
                old.is_compatible(new)
                self.assertEqual((old.to_tuple(), new.to_tuple()), before)

    def test_invalid_argument_preserves_receiver(self):
        receiver = Version(0, 2, 3, 'rc.0', 'build.1')
        before = receiver.to_tuple()
        with self.assertRaises(TypeError):
            receiver.is_compatible('0.2.3-rc.0')
        self.assertEqual(receiver.to_tuple(), before)

    def test_docstring_describes_contract(self):
        self.assertIs(Version(1, 0, 0).is_compatible(Version(1, 0, 0)), True)
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        lowered = doc.lower()
        for term in ('major', 'minor', 'patch', 'prerelease', 'build', 'typeerror'):
            with self.subTest(term=term):
                self.assertIn(term, lowered)
        self.assertTrue('other' in lowered or 'candidate' in lowered)
        self.assertTrue('replace' in lowered or 'direction' in lowered or 'new version' in lowered)
        self.assertTrue('ignore' in lowered or 'excluded' in lowered)

    def test_docstring_contains_two_compatibility_call_examples(self):
        self.assertIs(Version(1, 0, 0).is_compatible(Version(1, 0, 0)), True)
        examples = doctest.DocTestParser().get_examples(Version.is_compatible.__doc__ or '')
        calls = [example for example in examples if 'is_compatible(' in example.source]
        self.assertGreaterEqual(len(calls), 2)
        for example in calls:
            with self.subTest(source=example.source):
                self.assertIn(example.want.strip(), ('True', 'False'))

    def test_existing_parse_behavior(self):
        parsed = Version.parse('1.2.3-rc.1+build.2')
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, 'rc.1', 'build.2'))

    def test_existing_comparison_behavior(self):
        self.assertIs(Version.parse('1.2.3-rc.1') < Version.parse('1.2.3'), True)

    def test_existing_hash_behavior(self):
        self.assertEqual(hash(Version(1, 2, 3, build='one')), hash(Version(1, 2, 3, build='two')))

    def test_existing_readonly_property_behavior(self):
        version = Version(1, 2, 3)
        with self.assertRaises(AttributeError):
            version.major = 2

    def test_existing_deprecated_compare_behavior(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            self.assertEqual(semver.compare('1.2.3', '1.2.4'), -1)

    def test_existing_cli_compare_behavior(self):
        output = io.StringIO()
        with redirect_stdout(output):
            status = semver.cli.main(['compare', '1.2.3', '1.2.4'])
        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue().strip(), '-1')
