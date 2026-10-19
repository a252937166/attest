import unittest
from rle import encode, decode

class TestBreakerRLE(unittest.TestCase):
    def test_unicode_characters(self):
        self.assertEqual(encode('😀😀😃'), '😀2😃1')
        self.assertEqual(decode(encode('😀😀😃')), '😀😀😃')
    def test_mixed_ascii_and_unicode(self):
        s = 'aa😀bb😀😀c'
        self.assertEqual(encode(s), 'a2😀1b2😀2c1')
        self.assertEqual(decode(encode(s)), s)
    def test_very_long_string(self):
        s = 'z' * 10000
        self.assertEqual(encode(s), 'z10000')
        self.assertEqual(decode(encode(s)), s)
    def test_alternating_chars(self):
        s = 'ab' * 5000  # length 10000
        expected = ''.join(f'{ch}1' for ch in s)
        self.assertEqual(encode(s), expected)
        self.assertEqual(decode(encode(s)), s)
    def test_non_string_types_varied(self):
        for val in [None, 0, 3.14, b'bytes', bytearray(), {'a':1}, [1,2], set() ]:
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    encode(val)
    def test_encode_returns_new_str_instance(self):
        s = 'hello'
        res = encode(s)
        self.assertIsInstance(res, str)
        self.assertNotEqual(id(res), id(s))
    def test_round_trip_with_newlines_and_tabs(self):
        s = 'a\na\tb\tb\tc'
        self.assertEqual(decode(encode(s)), s)
