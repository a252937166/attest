import unittest
from rle import encode, decode

class BreakerTests(unittest.TestCase):
    def test_unicode_characters(self):
        self.assertEqual(encode('😀😀😃'), '😀2😃1')
        self.assertEqual(decode(encode('😀😀😃')), '😀😀😃')
    def test_null_byte(self):
        self.assertEqual(encode('\x00\x00\x01'), '\x002\x011')
        self.assertEqual(decode(encode('\x00\x00\x01')), '\x00\x00\x01')
    def test_very_long_run(self):
        s = 'z' * 10000
        self.assertEqual(encode(s), 'z10000')
        self.assertEqual(decode(encode(s)), s)
    def test_alternating_chars(self):
        s = 'ab' * 5000
        expected = ''.join(f'{c}1' for c in s)
        self.assertEqual(encode(s), expected)
        self.assertEqual(decode(encode(s)), s)
    def test_mixed_ascii_and_unicode(self):
        s = 'aa😀bb😀😀c'
        self.assertEqual(encode(s), 'a2😀1b2😀2c1')
        self.assertEqual(decode(encode(s)), s)
    def test_encode_returns_new_str_instance(self):
        s = 'hello'
        result = encode(s)
        self.assertIsInstance(result, str)
        self.assertNotEqual(id(result), id(s))
    def test_type_error_subclasses(self):
        class MyStr(str):
            pass
        # subclass of str should be accepted
        self.assertEqual(encode(MyStr('aa')), 'a2')
        # non-str subclass should raise
        class NotStr:
            pass
        with self.assertRaises(TypeError):
            encode(NotStr())
    def test_encode_with_leading_zeros_in_count_not_allowed(self):
        # ensure we never produce leading zeros
        s = 'a' * 10
        self.assertEqual(encode(s), 'a10')
        self.assertFalse(encode(s).startswith('a010'))
    def test_round_trip_for_all_lengths_up_to_20(self):
        for length in range(0, 21):
            s = 'x' * length
            self.assertEqual(decode(encode(s)), s)
    def test_encode_preserves_order_of_runs(self):
        s = 'aaabbbcccdddde'
        self.assertEqual(encode(s), 'a3b3c3d4e1')
        self.assertEqual(decode(encode(s)), s)
