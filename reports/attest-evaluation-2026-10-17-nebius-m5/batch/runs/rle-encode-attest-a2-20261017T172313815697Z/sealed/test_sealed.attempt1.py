import unittest
from rle import encode, decode

class TestEncode(unittest.TestCase):
    def test_encode_aaabbc(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')
    
    def test_encode_single_char(self):
        self.assertEqual(encode('a'), 'a1')
    
    def test_encode_empty(self):
        self.assertEqual(encode(''), '')
    
    def test_encode_abc(self):
        self.assertEqual(encode('abc'), 'a1b1c1')
    
    def test_encode_long_run_multi_digit(self):
        self.assertEqual(encode('x' * 12), 'x12')
    
    def test_encode_returns_str(self):
        result = encode('test')
        self.assertIsInstance(result, str)
    
    def test_encode_type_error_int(self):
        with self.assertRaises(TypeError):
            encode(123)
    
    def test_encode_type_error_list(self):
        with self.assertRaises(TypeError):
            encode(['a'])
    
    def test_round_trip_simple1(self):
        self.assertEqual(decode(encode('')), '')
    
    def test_round_trip_simple2(self):
        self.assertEqual(decode(encode('a')), 'a')
    
    def test_round_trip_simple3(self):
        self.assertEqual(decode(encode('aa')), 'aa')
    
    def test_round_trip_complex(self):
        original = 'aaabbcaaa'
        self.assertEqual(decode(encode(original)), original)
    
    def test_encode_counts_no_leading_zero(self):
        # count 10 should produce 'a10' not 'a010'
        self.assertEqual(encode('a' * 10), 'a10')
    
    def test_encode_mixed_runs(self):
        self.assertEqual(encode('!!??!!'), '!2?2!2')
