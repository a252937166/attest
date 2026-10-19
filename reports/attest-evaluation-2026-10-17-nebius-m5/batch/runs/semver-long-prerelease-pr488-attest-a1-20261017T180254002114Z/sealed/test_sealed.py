import unittest
from semver import Version

class TestNatCmpAcceptance(unittest.TestCase):
    def test_long_numeric_is_valid(self):
        s = '0.0.0-' + '1'*5000
        self.assertTrue(Version.is_valid(s))
    def test_long_numeric_parse_equal(self):
        s = '0.0.0-' + '1'*5000
        v = Version.parse(s)
        self.assertEqual(v.compare(s), 0)
    def test_long_vs_short_numeric(self):
        low = '0.0.0-2'
        high = '0.0.0-' + '1'*5000
        v_low = Version.parse(low)
        v_high = Version.parse(high)
        self.assertEqual(v_low.compare(high), -1)
        self.assertEqual(v_high.compare(low), 1)
    def test_ordering_long_numeric(self):
        a = '9'*4999
        b = '1' + '0'*4999
        self.assertLess(Version.parse('0.0.0-'+a).compare(Version.parse('0.0.0-'+b)), 0)
        self.assertGreater(Version.parse('0.0.0-'+b).compare(Version.parse('0.0.0-'+a)), 0)
        self.assertEqual(sorted([Version.parse('0.0.0-'+a), Version.parse('0.0.0-'+b)], key=lambda v: v), [Version.parse('0.0.0-'+a), Version.parse('0.0.0-'+b)])
        c = '1'+'0'*4998+'1'
        d = '1'+'0'*4998+'2'
        self.assertLess(Version.parse('0.0.0-'+c).compare(Version.parse('0.0.0-'+d)), 0)
        self.assertGreater(Version.parse('0.0.0-'+d).compare(Version.parse('0.0.0-'+c)), 0)
        e = '1'*5000
        f = 'alpha'
        self.assertLess(Version.parse('0.0.0-'+e).compare(Version.parse('0.0.0-'+f)), 0)
        g = 'alpha.'+'1'*5000
        h = 'alpha.'+'1'*5000+'.1'
        self.assertLess(Version.parse('0.0.0-'+g).compare(Version.parse('0.0.0-'+h)), 0)
        self.assertGreater(Version.parse('0.0.0-'+h).compare(Version.parse('0.0.0-'+g)), 0)
    def test_build_metadata_ignored(self):
        base = '0.0.0-' + '1'*5000
        v1 = Version.parse(base)
        v2 = v1.replace(build='other')
        self.assertEqual(v1.compare(v2), 0)
        self.assertLess(v1.compare(Version(0,0,0)), -1)  # prerelease lower than release
    def test_constructor_legacy_comparison(self):
        cases = [
            (('0001','1'),0),
            (('000','0'),0),
            (('02','10'),-1),
            (('01.2','1.2'),0),
            (('2a','10a'),1),
            (('01a','1a'),-1),
            (('-1','0'),1),
            (('',None),0),
            (('\u0661\u0662','12'),0),
            (('\uff11\uff12','13'),-1),
            (('1\u0662','12'),0),
            (('\u0660\u0660\u0661','1'),0),
        ]
        for (left,right),expected in cases:
            vl = Version(0,0,0, prerelease=left)
            vr = Version(0,0,0, prerelease=right)
            self.assertEqual(vl.compare(vr), expected)
            self.assertEqual(vr.compare(vl), -expected)
            self.assertEqual(vl.prerelease, left)
            self.assertEqual(vr.prerelease, right)
    def test_parse_raises_on_non_ascii_digit(self):
        for p in ('01', '01.2', '\u0661\u0662', '\uff11\uff12'):
            with self.assertRaises(ValueError):
                Version.parse('0.0.0-'+p)
    def test_constructor_raises_on_non_ascii_digit(self):
        for left,right in [('\u00b2','2'), ('a.\u00b2','b.0'), ('a.0','b.\u00b2')]:
            with self.assertRaises(ValueError):
                Version(0,0,0, prerelease=left).compare(Version(0,0,0, prerelease=right))
    def test_core_decides_before_prerelease(self):
        self.assertTrue(Version(0,0,0, prerelease='\u00b2') < Version(1,0,0, prerelease='\u00b2'))
        self.assertFalse(Version(0,0,0, prerelease='\u00b2') > Version(1,0,0, prerelease='\u00b2'))

if __name__ == '__main__':
    unittest.main()
