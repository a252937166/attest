import unittest
from rle import encode, decode

class TestEncode(unittest.TestCase):
    def test_encode_aaabbc_returns_a3b2c1(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')
    def test_encode_single_char_returns_char1(self):
        self.assertEqual(encode('a'), 'a1')
    def test_encode_empty_string_returns_empty(self):
        self.assertEqual(encode(''), '')
    def test_encode_abc_returns_a1b1c1(self):
        self.assertEqual(encode('abc'), 'a1b1c1')
    def test_encode_multi_digit_count(self):
        self.assertEqual(encode('x' * 12), 'x12')
    def test_encode_returns_str_type(self):
        result = encode('hello')
        self.assertIsInstance(result, str)
    def test_encode_type_error_nonstring(self):
        for bad in (123, None, ['a'], {'a':1}, b'bytes'):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    encode(bad)
    def test_round_trip_property(self):
        test_strings = [
            '',
            'a',
            'aa',
            'ab',
            'a'*100,
            'a'*10 + 'b'*5,
            '!!!@@@###',
            '😀😀😃',
            'a1b2c3',  # contains digits
            'a\nb\tc',
        ]
        for s in test_strings:
            with self.subTest(s=s):
                encoded = encode(s)
                decoded = decode(encoded)
                self.assertEqual(decoded, s)
    def test_encode_then_decode_matches_original_for_special_chars(self):
        # ensure digits in original are handled correctly
        s = 'a3b1c2'
        self.assertEqual(decode(encode(s)), s)

