import doctest
import inspect
import unittest

import semver
from semver import Version, VersionInfo
from semver.version import Version as ModuleVersion


class CompatibilityAcceptanceTests(unittest.TestCase):
    def assert_compatible(self, receiver, other, expected):
        result = receiver.is_compatible(other)
        self.assertIs(result, expected)

    def test_public_aliases_expose_the_method(self):
        self.assertIs(Version, ModuleVersion)
        self.assertIs(VersionInfo, Version)
        for cls in (semver.Version, ModuleVersion, VersionInfo):
            with self.subTest(cls=cls):
                self.assert_compatible(cls(1, 0, 0), cls(1, 0, 0), True)

    def test_method_signature(self):
        signature = inspect.signature(Version.is_compatible)
        self.assertEqual(list(signature.parameters), ["self", "other"])
        self.assertEqual(signature.parameters["other"].annotation, "Version")
        self.assertIs(signature.return_annotation, bool)

    def test_other_can_be_passed_by_keyword(self):
        self.assertIs(Version(1, 2, 3).is_compatible(other=Version(1, 3, 0)), True)

    def test_positive_major_ignores_patch_in_both_directions(self):
        for left, right in ((3, 3), (3, 4), (4, 3)):
            with self.subTest(left=left, right=right):
                self.assert_compatible(Version(1, 2, left), Version(1, 2, right), True)

    def test_positive_major_minor_is_directional(self):
        cases = ((Version(1, 2, 9), Version(1, 3, 0), True),
                 (Version(1, 3, 0), Version(1, 2, 9), False),
                 (Version(1, 1, 0), Version(1, 0, 0), False))
        for receiver, other, expected in cases:
            with self.subTest(receiver=receiver, other=other):
                self.assert_compatible(receiver, other, expected)

    def test_different_majors_are_incompatible_both_ways(self):
        pairs = ((Version(1, 9, 9), Version(2, 0, 0)),
                 (Version(0, 9, 9, "rc"), Version(1, 0, 0, "rc")))
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assert_compatible(left, right, False)
                self.assert_compatible(right, left, False)

    def test_equal_prerelease_allows_patch_and_higher_minor(self):
        receiver = Version(1, 2, 3, "rc.0")
        self.assert_compatible(receiver, Version(1, 2, 4, "rc.0"), True)
        self.assert_compatible(receiver, Version(1, 3, 0, "rc.0"), True)
        self.assert_compatible(receiver, Version(1, 1, 9, "rc.0"), False)

    def test_prerelease_requires_exact_stored_value(self):
        cases = (("rc.1", "rc.0"), ("RC.0", "rc.0"))
        for left, right in cases:
            with self.subTest(left=left, right=right):
                self.assert_compatible(Version(1, 2, 3, left), Version(1, 3, 0, right), False)

    def test_absent_and_present_prereleases_differ_both_ways(self):
        stable = Version(1, 2, 3)
        candidate = Version(1, 3, 0, "rc1")
        self.assert_compatible(stable, candidate, False)
        self.assert_compatible(candidate, stable, False)

    def test_empty_prerelease_is_distinct_from_none(self):
        empty = Version(1, 2, 3, "")
        absent = Version(1, 2, 3)
        self.assert_compatible(empty, Version(1, 3, 0, ""), True)
        self.assert_compatible(empty, absent, False)
        self.assert_compatible(absent, empty, False)

    def test_zero_major_identical_versions_are_compatible(self):
        self.assert_compatible(Version(0, 1, 0), Version(0, 1, 0), True)
        self.assert_compatible(Version(0, 0, 0), Version(0, 0, 0), True)

    def test_zero_major_minor_must_match_both_ways(self):
        left, right = Version(0, 1, 0), Version(0, 2, 0)
        self.assert_compatible(left, right, False)
        self.assert_compatible(right, left, False)

    def test_zero_major_patch_must_match_both_ways(self):
        left, right = Version(0, 1, 0), Version(0, 1, 1)
        self.assert_compatible(left, right, False)
        self.assert_compatible(right, left, False)

    def test_zero_major_prerelease_must_match(self):
        receiver = Version(0, 1, 0, "rc.0")
        self.assert_compatible(receiver, Version(0, 1, 0, "rc.0"), True)
        self.assert_compatible(receiver, Version(0, 1, 0, "rc.1"), False)
        self.assert_compatible(receiver, Version(0, 1, 0), False)

    def test_positive_major_ignores_build_metadata(self):
        receiver = Version(1, 2, 3, build="a")
        self.assert_compatible(receiver, Version(1, 2, 9, build="b"), True)
        self.assert_compatible(receiver, Version(1, 2, 9), True)
        self.assert_compatible(Version(1, 2, 3), Version(1, 2, 9, build="b"), True)

    def test_zero_major_ignores_build_metadata(self):
        receiver = Version(0, 1, 0, build="a")
        self.assert_compatible(receiver, Version(0, 1, 0, build="b"), True)
        self.assert_compatible(receiver, Version(0, 1, 0), True)
        self.assert_compatible(Version(0, 1, 0), Version(0, 1, 0, build="b"), True)

    def assert_invalid_types(self, receiver):
        invalid = ("wrongtype", "1.2.3", b"1.2.3", {"a": 2},
                   {"major": 1, "minor": 2, "patch": 3}, [],
                   (1, 2, 3), None, 3, object(), Version)
        for other in invalid:
            with self.subTest(other=repr(other)):
                with self.assertRaises(TypeError) as raised:
                    receiver.is_compatible(other)
                self.assertIs(type(raised.exception), TypeError)
                self.assertTrue(str(raised.exception).startswith("Expected a Version type"))

    def test_positive_major_rejects_every_non_version_type(self):
        self.assert_invalid_types(Version(1, 2, 3))

    def test_zero_major_rejects_every_non_version_type(self):
        self.assert_invalid_types(Version(0, 1, 0))

    def test_base_and_subclass_mix_for_positive_major(self):
        class CustomVersion(Version):
            pass

        base, custom = Version(1, 0, 0), CustomVersion(1, 0, 0)
        self.assert_compatible(custom, base, True)
        self.assert_compatible(base, custom, True)

    def test_distinct_subclasses_follow_zero_major_rule(self):
        class FirstVersion(Version):
            pass

        class SecondVersion(Version):
            pass

        first = FirstVersion(0, 1, 0)
        second = SecondVersion(0, 1, 0)
        base = Version(0, 1, 0)
        self.assert_compatible(first, second, True)
        self.assert_compatible(second, first, True)
        self.assert_compatible(first, base, True)
        self.assert_compatible(base, second, True)
        self.assert_compatible(first, SecondVersion(0, 1, 1), False)

    def test_successful_calls_preserve_all_components(self):
        receiver = Version(1, 2, 3, "rc.0", "a")
        compatible = Version(1, 3, 9, "rc.0", "b")
        incompatible = Version(1, 1, 0, "rc.0", "c")
        before = tuple(item.to_tuple() for item in (receiver, compatible, incompatible))
        self.assert_compatible(receiver, compatible, True)
        self.assert_compatible(receiver, incompatible, False)
        self.assertEqual(tuple(item.to_tuple() for item in (receiver, compatible, incompatible)), before)

    def test_invalid_call_preserves_receiver_components(self):
        receiver = Version(0, 1, 0, "rc.0", "a")
        before = receiver.to_tuple()
        with self.assertRaises(TypeError):
            receiver.is_compatible("0.1.0")
        self.assertEqual(receiver.to_tuple(), before)

    def test_docstring_explains_the_contract(self):
        doc = inspect.getdoc(Version.is_compatible)
        self.assertIsNotNone(doc)
        text = doc.lower()
        for term in ("replac", "other", "major", "minor", "patch", "prerelease", "build"):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertTrue("typeerror" in text or "type error" in text)

    def test_docstring_contains_two_passing_compatibility_doctests(self):
        doc = Version.is_compatible.__doc__
        self.assertIsNotNone(doc)
        parser = doctest.DocTestParser()
        examples = [example for example in parser.get_examples(doc)
                    if ".is_compatible(" in example.source
                    and example.want.strip() in ("True", "False")]
        self.assertGreaterEqual(len(examples), 2)
        test = parser.get_doctest(doc, {"Version": Version, "semver": semver},
                                  "Version.is_compatible", None, None)
        result = doctest.DocTestRunner().run(test)
        self.assertEqual(result.failed, 0)

    def test_existing_parse_and_format_behavior(self):
        version = Version.parse("1.2.3-rc.1+build.2")
        self.assertEqual(version.to_tuple(), (1, 2, 3, "rc.1", "build.2"))
        self.assertEqual(str(version), "1.2.3-rc.1+build.2")

    def test_existing_comparison_and_hash_behavior(self):
        self.assertLess(Version(1, 2, 3), Version(1, 2, 4))
        self.assertEqual(Version(1, 2, 3, build="a"), Version(1, 2, 3, build="b"))
        self.assertEqual(hash(Version(1, 2, 3, build="a")),
                         hash(Version(1, 2, 3, build="b")))

    def test_existing_readonly_properties_remain_readonly(self):
        version = Version(1, 2, 3)
        with self.assertRaises(AttributeError):
            version.major = 9
