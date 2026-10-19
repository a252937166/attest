import sys
from rle import decode

original = 'a1'
required_encoding = 'a111'
actual = decode(required_encoding)
if actual != original:
    print(f"CONTRADICTION TC5 AC8 AC12: input {original!r} requires encoding {required_encoding!r}, whose unchanged decode result is {actual!r}, whereas TC5 requires {original!r}.")
    sys.exit(3)
print('NOT DEMONSTRATED: the required encoding decoded to the original input')
sys.exit(0)
