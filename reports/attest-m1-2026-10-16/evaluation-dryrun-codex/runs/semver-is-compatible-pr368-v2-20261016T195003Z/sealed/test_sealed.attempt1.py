import doctest
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion
from semver.version import VersionInfo as ModuleVersionInfo


class CustomVersion(Version):
    pass


class VersionLike:
    major = 1
    minor = 2
    patch = 3
    prerelease = None
    build = None


class CompatibilityAcceptanceTests(unittest.TestCase):
    def test_public_aliases_and_keyword_call_return_bool(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        self.assertIs(ModuleVersionInfo, Version)
        old = semver.Version(1, 2, 3)
        new = VersionInfo(1, 2, 4)
        self.assertIs(old.is_compatible(new), True)
        self.assertIs(old.is_compatible(other=new), True)

    def test_nonzero_major_ignores_patch_in_both_directions(self):
        low = Version(1, 2, 3)
        high = Version(1, 2, 4)
        self.assertIs(low.is_compatible(low), True)
        self.assertIs(low.is_compatible(high), True)
        self.assertIs(high.is_compatible(low), True)

    def test_nonzero_major_minor_is_directional(self):
        self.assertIs(Version(1, 2, 9).is_compatible(Version(1, 3, 0)), True)
        self.assertIs(Version(1, 3, 0).is_compatible(Version(1, 2, 9)), False)
        self.assertIs(Version(1, 1, 0).is_compatible(Version(1, 0, 0)), False)

    def test_different_majors_are_incompatible(self):
        for left, right in [(Version(1, 2, 3), Version(2, 2, 3)),
                            (Version(0, 1, 0), Version(1, 1, 0)),
                            (Version(2, 0, 0), Version(1, 5, 0))]:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_equal_prerelease_allows_patch_and_minor_increases(self):
        old = Version(1, 2, 3, 'rc.0')
        self.assertIs(old.is_compatible(Version(1, 2, 4, 'rc.0')), True)
        self.assertIs(old.is_compatible(Version(1, 3, 0, 'rc.0')), True)

    def test_different_prereleases_are_incompatible_both_ways(self):
        pairs = [
            (Version(1, 2, 3, 'rc.0'), Version(1, 3, 4, 'rc.1')),
            (Version(1, 2, 3, 'RC.0'), Version(1, 3, 4, 'rc.0')),
            (Version(1, 2, 3), Version(1, 3, 4, 'rc1')),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertIs(left.is_compatible(right), False)
                self.assertIs(right.is_compatible(left), False)

    def test_prerelease_compares_stored_none_and_empty_string(self):
        absent = Version(1, 2, 3)
        empty = Version(1, 2, 3, '')
        self.assertIs(absent.is_compatible(Version(1, 2, 4)), True)
        self.assertIs(empty.is_compatible(Version(1, 2, 4, '')), True)
        self.assertIs(absent.is_compatible(empty), False)
        self.assertIs(empty.is_compatible(absent), False)

    def test_major_zero_identical_parts_are_compatible(self):
        self.assertIs(Version(0, 1, 0).is_compatible(Version(0, 1, 0)), True)
        self.assertIs(Version(0, 1, 0, 'rc.0').is_compatible(
            Version(0, 1, 0, 'rc.0')), True)

    def test_major_zero_rejects_each_changed_part_in_both_directions(self):
        old = Version(0, 1, 0, 'rc.0')
        changed = [Version(0, 2, 0, 'rc.0'),
                   Version(0, 1, 1, 'rc.0'),
                   Version(0, 1, 0, 'rc.1')]
        for new in changed:
            with self.subTest(new=new):
                self.assertIs(old.is_compatible(new), False)
                self.assertIs(new.is_compatible(old), False)

    def test_build_metadata_is_ignored_for_both_major_rules(self):
        pairs = [
            (Version(1, 2, 3, build='a'), Version(1, 3, 9, build='b')),
            (Version(1, 2, 3, build='a'), Version(1, 2, 3)),
            (Version(0, 1, 0, build='a'), Version(0, 1, 0, build='b')),
            (Version(0, 1, 0, build='a'), Version(0, 1, 0)),
        ]
        for old, new in pairs:
            with self.subTest(old=old, new=new):
                self.assertIs(old.is_compatible(new), True)

    def test_equal_build_cannot_rescue_incompatible_versions(self):
        self.assertIs(Version(1, 3, 0, build='same').is_compatible(
            Version(1, 2, 0, build='same')), False)
        self.assertIs(Version(0, 1, 0, build='same').is_compatible(
            Version(0, 1, 1, build='same')), False)

    def test_invalid_types_raise_exact_typeerror_for_both_major_rules(self):
        invalid = ['wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [],
                   (1, 2, 3), None, 7, object(), VersionLike()]
        for receiver in (Version(0, 1, 0), Version(1, 2, 3)):
            for other in invalid:
                with self.subTest(receiver=receiver, other_type=type(other)):
                    with self.assertRaises(TypeError) as cm:
                        receiver.is_compatible(other)
                    self.assertEqual(str(cm.exception),
                                     'Expected a Version type but got ' + str(type(other)))

    def test_subclasses_are_accepted_across_both_receiver_types(self):
        pairs = [
            (Version(1, 0, 0), CustomVersion(1, 1, 0)),
            (CustomVersion(1, 0, 0), Version(1, 0, 0)),
            (CustomVersion(1, 0, 0), CustomVersion(1, 1, 0)),
            (Version(0, 1, 0), CustomVersion(0, 1, 0)),
            (CustomVersion(0, 1, 0), Version(0, 1, 0)),
            (CustomVersion(0, 1, 0), CustomVersion(0, 1, 0)),
        ]
        for old, new in pairs:
            with self.subTest(old=old, new=new):
                self.assertIs(old.is_compatible(new), True)
        self.assertIs(CustomVersion(1, 2, 0).is_compatible(Version(1, 1, 0)), False)
        self.assertIs(CustomVersion(0, 1, 0).is_compatible(Version(0, 1, 1)), False)

    def test_successful_and_unsuccessful_calls_do_not_mutate_operands(self):
        pairs = [
            (Version(1, 2, 3, 'rc.0', 'a'), Version(1, 3, 4, 'rc.0', 'b')),
            (Version(1, 3, 3, 'rc.0', 'a'), Version(1, 2, 4, 'rc.0', 'b')),
            (Version(0, 1, 0, 'rc.0', 'a'), Version(0, 1, 0, 'rc.0', 'b')),
            (Version(0, 1, 0, 'rc.0', 'a'), Version(0, 1, 1, 'rc.0', 'b')),
        ]
        for old, new in pairs:
            with self.subTest(old=old, new=new):
                before = (old.to_tuple(), new.to_tuple())
                old.is_compatible(new)
                self.assertEqual((old.to_tuple(), new.to_tuple()), before)

    def test_invalid_type_call_does_not_mutate_receiver(self):
        for old in (Version(0, 1, 0, 'rc.0', 'a'),
                    Version(1, 2, 3, 'rc.0', 'b')):
            before = old.to_tuple()
            with self.assertRaises(TypeError):
                old.is_compatible('1.2.3')
            self.assertEqual(old.to_tuple(), before)

    def test_method_docstring_describes_contract_and_has_two_doctest_examples(self):
        doc = Version.is_compatible.__doc__
        self.assertIsInstance(doc, str)
        lower = doc.lower()
        for term in ('replac', 'major', 'minor', 'patch', 'prerelease',
                     'build', 'typeerror'):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertTrue('zero' in lower or '0' in lower)
        examples = [example for example in doctest.DocTestParser().get_examples(doc)
                    if 'is_compatible(' in example.source]
        self.assertGreaterEqual(len(examples), 2)
        for example in examples:
            self.assertIn(example.want.strip(), ('True', 'False'))

    def test_existing_parse_and_construction_behavior(self):
        parsed = Version.parse('1.2.3-rc.1+build.2')
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, 'rc.1', 'build.2'))
        self.assertEqual(str(parsed), '1.2.3-rc.1+build.2')

    def test_existing_comparison_equality_ordering_and_hash_behavior(self):
        low = Version(1, 2, 3)
        high = Version(1, 2, 4)
        self.assertEqual(low.compare(high), -1)
        self.assertTrue(low < high)
        self.assertTrue(low == Version(1, 2, 3, build='different'))
        self.assertEqual(hash(low), hash(Version(1, 2, 3, build='different')))
