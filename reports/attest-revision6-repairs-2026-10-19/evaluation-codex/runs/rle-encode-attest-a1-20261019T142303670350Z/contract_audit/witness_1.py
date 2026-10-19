import sys
from rle import decode

x = 'a1'
# The authoritative task requires character + decimal count for each run.
# The two singleton runs therefore require 'a1' followed by '11'.
required_encoding = 'a1' + '11'
actual = decode(required_encoding)
if actual != x:
    print('CONTRADICTION TC5: input ' + repr(x) + ' requires encoding ' + repr(required_encoding) + ', but unchanged decode returns ' + repr(actual) + ' instead of ' + repr(x) + '.')
    sys.exit(3)
else:
    print('NOT DEMONSTRATED: the required encoding decodes to the original input.')
    sys.exit(0)
