import unittest
from semver import Version

class TestNatCmpAcceptance(unittest.TestCase):
    def test_long_numeric_is_valid_and_orders(self):
        v = "0.0.0-" + "1" * 5000
        self.assertTrue(Version.is_valid(v))
        parsed = Version.parse(v)
        self.assertEqual(parsed.compare(v), 0)
        self.assertEqual(parsed.compare("0.0.0-2"), 1)
        self.assertEqual(Version.parse("0.0.0-2").compare(parsed), -1)

    def test_ordering_long_numeric(self):
        low = "0.0.0-" + "9" * 4999
        high = "0.0.0-" + "1" + "0" * 4999
        self.assertLess(Version.parse(low), Version.parse(high))
        self.assertGreater(Version.parse(high), Version.parse(low))
        self.assertEqual(sorted([Version.parse(low), Version.parse(high)]), [Version.parse(low), Version.parse(high)])
        low2 = "0.0.0-" + "1" + "0" * 4998 + "1"
        high2 = "0.0.0-" + "1" + "0" * 4998 + "2"
        self.assertLess(Version.parse(low2), Version.parse(high2))
        self.assertGreater(Version.parse(high2), Version.parse(low2))
        self.assertEqual(sorted([Version.parse(low2), Version.parse(high2)]), [Version.parse(low2), Version.parse(high2)])
        low3 = "0.0.0-" + "1" * 5000
        high3 = "0.0.0-alpha"
        self.assertLess(Version.parse(low3), Version.parse(high3))
        self.assertGreater(Version.parse(high3), Version.parse(low3))
        self.assertEqual(sorted([Version.parse(low3), Version.parse(high3)]), [Version.parse(low3), Version.parse(high3)])
        low4 = "0.0.0-alpha" + "." + "1" * 5000
        high4 = "0.0.0-alpha" + "." + "1" * 5000 + ".1"
        self.assertLess(Version.parse(low4), Version.parse(high4))
        self.assertGreater(Version.parse(high4), Version.parse(low4))
        self.assertEqual(sorted([Version.parse(low4), Version.parse(high4)]), [Version.parse(low4), Version.parse(high4)])

    def test_build_metadata_ignored_and_release_order(self):
        base = Version.parse("0.0.0-" + "1" * 5000)
        with_build = base.replace(build="other")
        self.assertEqual(base, with_build)
        self.assertLess(base, Version(0,0,0))

    def test_constructor_prerelease_compare_legacy_rules(self):
        cases = [
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
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                lv = Version(0,0,0, prerelease=left if left is not None else None)
                rv = Version(0,0,0, prerelease=right if right is not None else None)
                self.assertEqual(lv.compare(rv), expected)
                self.assertEqual(rv.compare(lv), -expected)
                self.assertEqual(lv.prerelease, left if left is not None else None)
                self.assertEqual(rv.prerelease, right if right is not None else None)

    def test_parse_raises_value_error_for_non_ascii_numeric_with_leading_zero(self):
        for p in ("01", "01.2", "\u0661\u0662", "\uff11\uff12"):
            with self.subTest(p=p):
                with self.assertRaises(ValueError):
                    Version.parse("0.0.0-" + p)

    def test_compare_raises_value_error_for_non_ascii_numeric_failing_int(self):
        pairs = [("\u00b2", "2"), ("a.\u00b2", "b.0"), ("a.0", "b.\u00b2")]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                lv = Version(0,0,0, prerelease=left)
                rv = Version(0,0,0, prerelease=right)
                with self.assertRaises(ValueError):
                    lv.compare(rv)
                with self.assertRaises(ValueError):
                    rv.compare(lv)

    def test_core_version_decides_before_prerelease_for_superscript(self):
        self.assertTrue(Version(0,0,0, prerelease="\u00b2") < Version(1,0,0, prerelease="\u00b2"))

if __name__ == "__main__":
    unittest.main()
