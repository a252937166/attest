import unittest
from rle import encode, decode

class TestEncodeSealed(unittest.TestCase):
    def test_encode_aaabbc_returns_a3b2c1(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')
    
    def test_encode_single_char_returns_char1(self):
        self.assertEqual(encode('a'), 'a1')
    
    def test_encode_empty_string_returns_empty(self):
        self.assertEqual(encode(''), '')
    
    def test_encode_distinct_chars_each_with_count1(self):
        self.assertEqual(encode('abc'), 'a1b1c1')
    
    def test_encode_multi_digit_count(self):
        self.assertEqual(encode('x' * 12), 'x12')
    
    def test_encode_roundtrip_property(self):
        test_strings = ['', 'a', 'aa', 'ab', 'a'*100, 'a'*10+'b'*5, '!!!', '123', 'a1b2c3']
        for s in test_strings:
            with self.subTest(s=s):
                self.assertEqual(decode(encode(s)), s)
    
    def test_encode_returns_str_type(self):
        result = encode('hello')
        self.assertIsInstance(result, str)
    
    def test_encode_type_error_on_nonstring_int(self):
        with self.assertRaises(TypeError):
            encode(123)
    
    def test_encode_type_error_on_nonstring_list(self):
        with self.assertRaises(TypeError):
            encode([1,2,3])
    
    def test_encode_type_error_on_nonstring_none(self):
        with self.assertRaises(TypeError):
            encode(None)
    
    def test_encode_handles_unicode_characters(self):
        self.assertEqual(encode('😀😀😃'), '😀2😃1')
    
    def test_encode_mixed_runs(self):
        self.assertEqual(encode('aaabaaa'), 'a3b1a3')
