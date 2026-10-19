import unittest
from rle import encode, decode

class TestEncode(unittest.TestCase):
    def test_encode_aaabbc(self):
        self.assertEqual(encode('aaabbc'), 'a3b2c1')

    def test_encode_single_char(self):
        self.assertEqual(encode('a'), 'a1')

    def test_encode_empty(self):
        self.assertEqual(encode(''), '')

    def test_encode_each_char_one(self):
        self.assertEqual(encode('abc'), 'a1b1c1')

    def test_encode_multi_digit(self):
        self.assertEqual(encode('x' * 12), 'x12')

    def test_encode_returns_str(self):
        result = encode('hello')
        self.assertIsInstance(result, str)

    def test_encode_type_error(self):
        with self.assertRaises(TypeError):
            encode(123)

class TestDecodeUnchanged(unittest.TestCase):
    def test_decode_a3b1(self):
        self.assertEqual(decode('a3b1'), 'aaab')

    def test_decode_empty(self):
        self.assertEqual(decode(''), '')

    def test_decode_type_error(self):
        with self.assertRaises(TypeError):
            decode(123)

class TestEncodeAdditional(unittest.TestCase):
    def test_encode_multiple_runs_separated(self):
        self.assertEqual(encode('aaabba'), 'a3b2a1')

    def test_round_trip_property(self):
        test_strings = [
            '',
            'a',
            'aaabbc',
            'abc',
            'x' * 12,
            'aaabba',
            'zzzzzzzzzzzzzz',
            'abccba',
            '111222333',
            '!@#',
        ]
        for s in test_strings:
            with self.subTest(s=s):
                encoded = encode(s)
                self.assertIsInstance(encoded, str)
                decoded = decode(encoded)
                self.assertEqual(decoded, s)
