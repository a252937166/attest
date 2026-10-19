import unittest
from rle import encode, decode

class TestEncodeAcceptance(unittest.TestCase):
    def test_encode_aaabbc_returns_a3b2c1(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')
    def test_encode_single_char_returns_char_plus_one(self):
        self.assertEqual(encode('a'), 'a1')
    def test_encode_empty_string_returns_empty(self):
        self.assertEqual(encode(''), '')
    def test_encode_abc_returns_a1b1c1(self):
        self.assertEqual(encode('abc'), 'a1b1c1')
    def test_encode_long_run_returns_char_and_count(self):
        self.assertEqual(encode('x' * 12), 'x12')
    def test_roundtrip_empty_string(self):
        self.assertEqual(decode(encode('')), '')
    def test_roundtrip_single_character(self):
        self.assertEqual(decode(encode('z')), 'z')
    def test_roundtrip_multiple_runs(self):
        self.assertEqual(decode(encode('aaabbc')), 'aaabbc')
    def test_roundtrip_multi_digit_counts(self):
        self.assertEqual(decode(encode('x' * 12)), 'x' * 12)
    def test_encode_returns_str_type(self):
        result = encode('test')
        self.assertIsInstance(result, str)
    def test_encode_type_error_on_int(self):
        with self.assertRaises(TypeError):
            encode(123)
    def test_encode_type_error_on_list(self):
        with self.assertRaises(TypeError):
            encode([1, 2, 3])
    def test_encode_type_error_on_none(self):
        with self.assertRaises(TypeError):
            encode(None)
