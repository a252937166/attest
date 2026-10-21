import unittest
from semver import Version

class TestSealedAcceptance(unittest.TestCase):
    # AC1
    def test_long_ascii_numeric_is_valid_and_equal(self):
        long_id = '1' * 5000
        ver_str = f'0.0.0-{long_id}'
        self.assertTrue(Version.is_valid(ver_str))
        v = Version.parse(ver_str)
        self.assertEqual(v.compare(ver_str), 0)
        self.assertEqual(v.compare('0.0.0-2'), 1)
        self.assertEqual(Version.parse('0.0.0-2').compare(v), -1)
    
    # AC2
    def test_ordering_long_numeric_parsed(self):
        a = '9' * 4999
        b = '1' + '0' * 4999
        va = Version.parse(f'0.0.0-{a}')
        vb = Version.parse(f'0.0.0-{b}')
        self.assertLess(va, vb)
        self.assertGreater(vb, va)
        self.assertEqual(sorted([va, vb]), [va, vb])
        
        c = '1' + '0' * 4998 + '1'
        d = '1' + '0' * 4998 + '2'
        vc = Version.parse(f'0.0.0-{c}')
        vd = Version.parse(f'0.0.0-{d}')
        self.assertLess(vc, vd)
        self.assertGreater(vd, vc)
        self.assertEqual(sorted([vc, vd]), [vc, vd])
        
        e = '1' * 5000
        f = 'alpha'
        ve = Version.parse(f'0.0.0-{e}')
        vf = Version.parse(f'0.0.0-{f}')
        self.assertLess(ve, vf)
        self.assertGreater(vf, ve)
        self.assertEqual(sorted([ve, vf]), [ve, vf])
        
        g = 'alpha.' + '1' * 5000
        h = 'alpha.' + '1' * 5000 + '.1'
        vg = Version.parse(f'0.0.0-{g}')
        vh = Version.parse(f'0.0.0-{h}')
        self.assertLess(vg, vh)
        self.assertGreater(vh, vg)
        self.assertEqual(sorted([vg, vh]), [vg, vh])
    
    # AC3
    def test_build_metadata_ignored_release_order(self):
        long_id = '1' * 5000
        v = Version.parse(f'0.0.0-{long_id}')
        self.assertEqual(v, v.replace(build='other'))
        self.assertGreater(v, Version(0, 0, 0))
    
    # AC4
    def test_constructor_legacy_prerelease_comparison(self):
        pairs = [
            (('0001', '1'), 0),
            (('000', '0'), 0),
            (('02', '10'), -1),
            (('01.2', '1.2'), 0),
            (('2a', '10a'), 1),
            (('01a', '1a'), -1),
            (('-1', '0'), 1),
            (('', None), 0),
            (('\u0661\u0662', '12'), 0),
            (('\uff11\uff12', '13'), -1),
            (('1\u0662', '12'), 0),
            (('\u0660\u0660\u0661', '1'), 0),
        ]
        for (left, right), expected in pairs:
            vl = Version(0, 0, 0, prerelease=left)
            vr = Version(0, 0, 0, prerelease=right)
            self.assertEqual(vl.compare(vr), expected)
            self.assertEqual(vr.compare(vl), -expected)
            self.assertEqual(vl.prerelease, left)
            self.assertEqual(vr.prerelease, right)
    
    # AC5
    def test_parse_rejects_non_canonical(self):
        for p in ('01', '01.2', '\u0661\u0662', '\uff11\uff12'):
            with self.subTest(p=p):
                with self.assertRaises(ValueError):
                    Version.parse(f'0.0.0-{p}')
    
    # AC6
    def test_constructor_failing_int_raises_eagerly(self):
        pairs = [
            ('\u00b2', '2'),
            ('a.\u00b2', 'b.0'),
            ('a.0', 'b.\u00b2'),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                vl = Version(0, 0, 0, prerelease=left)
                vr = Version(0, 0, 0, prerelease=right)
                with self.assertRaises(ValueError):
                    vl.compare(vr)
    
    # AC7
    def test_core_version_difference_decides_before_prerelease(self):
        v_low = Version(0, 0, 0, prerelease='\u00b2')
        v_high = Version(1, 0, 0, prerelease='\u00b2')
        self.assertLess(v_low, v_high)
        # Ensure no ValueError
        try:
            v_low.compare(v_high)
        except ValueError:
            self.fail('ValueError raised unexpectedly')
    
    # AC8: assume existing pytest suite passes; we just ensure no regression by importing and maybe running a simple test
    def test_import_and_basic_functionality(self):
        self.assertEqual(Version.parse('1.0.0').compare('2.0.0'), -1)
        self.assertEqual(Version.parse('2.0.0').compare('1.0.0'), 1)
        self.assertEqual(Version.parse('2.0.0').compare('2.0.0'), 0)

