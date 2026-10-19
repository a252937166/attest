import sys
import unittest
import warnings

import semver
from semver import Version, VersionInfo


class TestSealedPrereleaseComparison(unittest.TestCase):
    def test_long_canonical_identifier_parses_and_deprecated_compare_warns(self):
        value = "0.0.0-" + "1" * 5000
        self.assertTrue(Version.is_valid(value))
        self.assertEqual(Version.parse(value).prerelease, "1" * 5000)
        self.assertEqual(Version.parse(value).compare(value), 0)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", PendingDeprecationWarning)
            self.assertEqual(semver.compare(value, "0.0.0-2"), 1)
            self.assertEqual(semver.compare("0.0.0-2", value), -1)
        self.assertEqual(len(caught), 2)
        self.assertTrue(all(issubclass(w.category, PendingDeprecationWarning) for w in caught))

    def test_long_parsed_identifiers_order_in_both_directions_and_sort(self):
        pairs = (
            ("9" * 4999, "1" + "0" * 4999),
            ("1" + "0" * 4998 + "1", "1" + "0" * 4998 + "2"),
            ("1" * 5000, "alpha"),
            ("alpha." + "1" * 5000, "alpha." + "1" * 5000 + ".1"),
        )
        for low_tag, high_tag in pairs:
            with self.subTest(low=low_tag[:20], high=high_tag[:20]):
                low = Version.parse("0.0.0-" + low_tag)
                high = Version.parse("0.0.0-" + high_tag)
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertEqual(sorted([high, low]), [low, high])

    def test_build_metadata_does_not_affect_long_prerelease_precedence_or_values(self):
        tag = "1" * 5000
        version = Version.parse("0.0.0-" + tag)
        with_build = version.replace(build="other")
        self.assertEqual(version, with_build)
        self.assertLess(version, Version(0, 0, 0))
        self.assertEqual(version.prerelease, tag)
        self.assertIsNone(version.build)
        self.assertEqual(with_build.prerelease, tag)
        self.assertEqual(with_build.build, "other")

    def test_constructor_identifiers_keep_legacy_ordering_and_spelling(self):
        cases = (
            ("0001", "1", 0),
            ("000", "0", 0),
            ("02", "10", -1),
            ("01.2", "1.2", 0),
            ("2a", "10a", 1),
            ("01a", "1a", -1),
            ("-1", "0", 1),
            ("", None, 0),
            ("\u0661\u0662", "12", 0),
            ("\uff11\uff12", "13", -1),
            ("1\u0662", "12", 0),
            ("\u0660\u0660\u0661", "1", 0),
        )
        for left_tag, right_tag, expected in cases:
            with self.subTest(left=left_tag, right=right_tag):
                left = Version(0, 0, 0, left_tag)
                right = Version(0, 0, 0, right_tag)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)
                self.assertEqual(left.prerelease, left_tag)
                self.assertEqual(right.prerelease, right_tag)

    def test_long_leading_zero_identifiers_compare_with_ascii_and_unicode(self):
        cases = (
            ("0" * 5000, "0", 0),
            ("0" * 5000 + "1", "1", 0),
            ("0" * 5000 + "12", "\u0661\u0662", 0),
            ("1" * 5000, "\uff11\uff12", 1),
        )
        for left_tag, right_tag, expected in cases:
            with self.subTest(left_length=len(left_tag), right=right_tag):
                left = Version(0, 0, 0, left_tag)
                right = Version(0, 0, 0, right_tag)
                self.assertEqual(left.compare(right), expected)
                self.assertEqual(right.compare(left), -expected)

    def test_parse_rejects_invalid_prereleases_accepted_by_constructor(self):
        for tag in ("01", "01.2", "\u0661\u0662", "\uff11\uff12"):
            with self.subTest(tag=tag):
                self.assertEqual(Version(0, 0, 0, tag).prerelease, tag)
                with self.assertRaises(ValueError):
                    Version.parse("0.0.0-" + tag)
                self.assertFalse(Version.is_valid("0.0.0-" + tag))

    def test_unicode_conversion_errors_are_eager_across_both_full_lists(self):
        cases = (
            ("\u00b2", "2"),
            ("a.\u00b2", "b.0"),
            ("a.0", "b.\u00b2"),
            ("a", "a.\u00b2"),
            ("\u00b2", None),
        )
        for left_tag, right_tag in cases:
            with self.subTest(left=left_tag, right=right_tag):
                left = Version(0, 0, 0, left_tag)
                right = Version(0, 0, 0, right_tag)
                with self.assertRaises(ValueError):
                    left.compare(right)
                with self.assertRaises(ValueError):
                    right.compare(left)

    def test_different_core_components_short_circuit_bad_prereleases(self):
        for low_core, high_core in (
            ((0, 0, 0), (1, 0, 0)),
            ((0, 0, 0), (0, 1, 0)),
            ((0, 0, 0), (0, 0, 1)),
        ):
            with self.subTest(low=low_core, high=high_core):
                low = Version(*low_core, prerelease="\u00b2")
                high = Version(*high_core, prerelease="\u00b2")
                self.assertEqual(low.compare(high), -1)
                self.assertEqual(high.compare(low), 1)
                self.assertTrue(low < high)
                self.assertTrue(high > low)

    def test_empty_identifiers_keep_string_and_list_length_semantics(self):
        self.assertEqual(Version._nat_cmp("", None), 0)
        self.assertEqual(Version._nat_cmp("a", "a."), -1)
        self.assertEqual(Version._nat_cmp("a.0", "a."), -1)
        self.assertEqual(Version._nat_cmp("a.", "a"), 1)

    def test_absent_prereleases_are_equivalent_and_follow_nonempty_ones(self):
        absent_none = Version(0, 0, 0, None)
        absent_empty = Version(0, 0, 0, "")
        prerelease = Version(0, 0, 0, "alpha")
        self.assertEqual(absent_none.compare(absent_empty), 0)
        self.assertEqual(absent_empty.compare(absent_none), 0)
        self.assertEqual(prerelease.compare(absent_none), -1)
        self.assertEqual(prerelease.compare(absent_empty), -1)
        self.assertEqual(absent_none.compare(prerelease), 1)
        self.assertEqual(absent_empty.compare(prerelease), 1)

    def test_all_rich_operators_follow_long_numeric_compare(self):
        low = Version.parse("0.0.0-" + "9" * 4999)
        high = Version.parse("0.0.0-" + "1" + "0" * 4999)
        self.assertNotEqual(low, high)
        self.assertTrue(low != high)
        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertFalse(low > high)
        self.assertFalse(low >= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertFalse(high < low)
        self.assertFalse(high <= low)
        self.assertTrue(low == low.replace(build="ignored"))
        self.assertFalse(low != low.replace(build="ignored"))

    def test_compare_accepts_existing_operand_forms(self):
        version = Version(1, 2, 3, "alpha.2")
        forms = (
            "1.2.3-alpha.10",
            b"1.2.3-alpha.10",
            {"major": 1, "minor": 2, "patch": 3, "prerelease": "alpha.10"},
            (1, 2, 3, "alpha.10"),
            [1, 2, 3, "alpha.10"],
            Version(1, 2, 3, "alpha.10"),
        )
        for other in forms:
            with self.subTest(type=type(other)):
                self.assertEqual(version.compare(other), -1)
                self.assertTrue(version < other)

    def test_unsupported_operands_and_invalid_collections_keep_operator_fallback(self):
        version = Version(1, 2, 3)
        with self.assertRaises(TypeError):
            version.compare(object())
        for other in (object(), {}, (), [], {"major": "bad"}):
            with self.subTest(other=other):
                for name in ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__"):
                    self.assertIs(getattr(version, name)(other), NotImplemented)

    def test_compare_propagates_supported_operand_parse_and_construction_errors(self):
        version = Version(1, 2, 3)
        with self.assertRaises(ValueError):
            version.compare("not a version")
        with self.assertRaises(ValueError):
            version.compare(b"not a version")
        with self.assertRaises(TypeError):
            version.compare({"major": 1, "unexpected": 2})
        with self.assertRaises(ValueError):
            version.compare(("bad", 2, 3))

    def test_subclass_parse_and_versioninfo_alias_remain_available(self):
        class DerivedVersion(Version):
            pass

        self.assertIs(VersionInfo, Version)
        version = DerivedVersion.parse("1.2.3-alpha.2+build")
        self.assertIsInstance(version, DerivedVersion)
        self.assertEqual(version.prerelease, "alpha.2")
        self.assertEqual(version.build, "build")
        self.assertEqual(version.compare("1.2.3-alpha.10"), -1)
        self.assertEqual(version.compare({"major": 1, "minor": 2, "patch": 3, "prerelease": "alpha.10"}), -1)

    def test_parse_keeps_bytes_decoding_and_optional_minor_patch_rules(self):
        parsed = Version.parse(b"1.2.3-alpha.4+build")
        self.assertEqual(parsed.to_tuple(), (1, 2, 3, "alpha.4", "build"))
        self.assertEqual(Version.parse("1", optional_minor_and_patch=True).to_tuple()[:3], (1, 0, 0))
        self.assertEqual(Version.parse("1.2", optional_minor_and_patch=True).to_tuple()[:3], (1, 2, 0))
        with self.assertRaises(ValueError):
            Version.parse("1.2")
        with self.assertRaises(TypeError):
            Version.parse(123)
        with self.assertRaises(TypeError):
            Version.is_valid(123)

    def test_constructor_keeps_core_conversion_and_permissive_metadata(self):
        version = Version("1", "2", "3", 4, 5)
        self.assertEqual(version.to_tuple(), (1, 2, 3, "4", "5"))
        with self.assertRaises(ValueError):
            Version(-1)
        with self.assertRaises(ValueError):
            Version("bad")
        with self.assertRaises(TypeError):
            Version(object())

    def test_legacy_unicode_integer_limit_and_ascii_comparison_with_limit_enabled(self):
        if not hasattr(sys, "get_int_max_str_digits"):
            self.skipTest("interpreter has no integer-string conversion limit")
        previous_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(4300)
            self.assertEqual(sys.get_int_max_str_digits(), 4300)
            long_ascii = "1" * 5000
            self.assertEqual(Version._nat_cmp(long_ascii, long_ascii), 0)
            self.assertEqual(Version._nat_cmp(long_ascii, "\u0661\u0662"), 1)
            self.assertEqual(Version._nat_cmp("0" * 5000 + "12", "\u0661\u0662"), 0)
            long_unicode = "\u0661" * 5000
            with self.assertRaises(ValueError):
                Version._nat_cmp(long_unicode, "2")
            with self.assertRaises(ValueError):
                Version._nat_cmp("a", "b." + long_unicode)
            self.assertEqual(Version(0, prerelease=long_unicode).compare(Version(1)), -1)
        finally:
            sys.set_int_max_str_digits(previous_limit)

    def test_numeric_tags_precede_text_and_normalized_decimal_order_is_exact(self):
        cases = (
            ("2", "10", -1),
            ("0002", "2", 0),
            ("0002", "0003", -1),
            ("9", "alpha", -1),
            ("01a", "1a", -1),
            ("a.2", "a.10", -1),
            ("a.2", "a.2.0", -1),
        )
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(Version._nat_cmp(left, right), expected)
                self.assertEqual(Version._nat_cmp(right, left), -expected)

    def test_rich_operators_propagate_equal_core_unicode_conversion_error(self):
        bad = Version(0, 0, 0, "\u00b2")
        other = Version(0, 0, 0, "2")
        for name in ("__eq__", "__ne__", "__lt__", "__le__", "__gt__", "__ge__"):
            with self.subTest(operator=name):
                with self.assertRaises(ValueError):
                    getattr(bad, name)(other)
                with self.assertRaises(ValueError):
                    getattr(other, name)(bad)
