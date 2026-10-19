import unittest
from rle import encode, decode

class TestBreaker(unittest.TestCase):
    def test_encode_digit_char_sequence(self):
        self.assertEqual(encode('a1'), 'a111')

    def test_encode_digit_char_sequence_reverse(self):
        self.assertEqual(encode('1a'), '11a1')

    def test_encode_mixed_digits_and_letters(self):
        self.assertEqual(encode('a12b3'), 'a11121b131')

    def test_roundtrip_with_digits(self):
        for s in ['a1', '1a', '111', 'a1b2c3', '', '😀1😀']:
            with self.subTest(s=s):
                self.assertEqual(decode(encode(s)), s)

    def test_encode_unicode_repeated(self):
        self.assertEqual(encode('😀😀😃'), '😀2😃1')

    def test_encode_unicode_mixed(self):
        self.assertEqual(encode('😀a😀'), '😀1a1😀1')

    def test_encode_newline_and_tab(self):
        self.assertEqual(encode('\\n\\n\\t'), '\\n2\\t1')

    def test_encode_large_run(self):
        self.assertEqual(encode('z' * 10000), 'z10000')

    def test_encode_type_error_variants(self):
        for val in [3.14, {'a':1}, {1,2}, True]:
            with self.subTest(val=val):
                with self.assertRaises(TypeError):
                    encode(val)
