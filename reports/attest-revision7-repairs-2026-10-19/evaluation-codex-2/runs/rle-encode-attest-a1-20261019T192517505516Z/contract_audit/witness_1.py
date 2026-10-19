import sys
from rle import decode

original = 'a1'
required_encoding = 'a111'
actual = decode(required_encoding)
if actual != original:
    print('CONTRADICTION TC5 AC8 AC13: input ' + repr(original) + ' requires encoding ' + repr(required_encoding) + ', but unchanged decode returns ' + repr(actual) + ' instead of ' + repr(original) + '.')
    sys.exit(3)
else:
    print('NOT DEMONSTRATED: the required encoding round-trips for input ' + repr(original))
    sys.exit(0)
