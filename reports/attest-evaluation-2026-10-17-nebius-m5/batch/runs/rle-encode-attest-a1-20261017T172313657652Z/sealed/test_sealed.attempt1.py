import unittest
from rle import encode, decode

class TestEncode(unittest.TestCase):
    def test_encode_aaabbc(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')
    def test_encode_single_char(self):
        self.assertEqual(encode('a'), 'a1')
    def test_encode_empty(self):
        self.assertEqual(encode(''), '')
    def test_encode_all_one_counts(self):
        self.assertEqual(encode('abc'), 'a1b1c1')
    def test_encode_multi_digit_count(self):
        self.assertEqual(encode('x' * 12), 'x12')
    def test_round_trip_property(self):
        test_strings = ['', 'a', 'aa', 'ab', 'aaabbc', 'xyz'*3, '1'*100]
        for s in test_strings:
            with self.subTest(s=s):
                self.assertEqual(decode(encode(s)), s)
    def test_encode_returns_str(self):
        result = encode('hello')
        self.assertIsInstance(result, str)
    def test_encode_type_error_non_string(self):
        for bad in [None, 123, [], {}, b'bytes']:
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    encode(bad)
    def test_encode_long_run(self):
        self.assertEqual(encode('a'*1000), 'a1000')
    def test_encode_mixed_runs(self):
        self.assertEqual(encode('aaabbbcccdddde'), 'a3b3c3d4e1')
