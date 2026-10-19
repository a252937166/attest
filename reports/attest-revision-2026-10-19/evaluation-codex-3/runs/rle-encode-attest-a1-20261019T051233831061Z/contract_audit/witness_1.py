import sys
from rle import decode

x = 'a1'
mandated_encoding = 'a111'
try:
    actual = decode(mandated_encoding)
except Exception as exc:
    print('NOT DEMONSTRATED: direct evaluation raised ' + type(exc).__name__)
    sys.exit(0)
if actual == 'a' * 111 and actual != x:
    print(f'CONTRADICTION AC9 AC10 AC11: input {x!r} must encode as {mandated_encoding!r}, but unchanged decode returns {actual!r}, whereas universal round-trip requires {x!r}.')
    sys.exit(3)
print('NOT DEMONSTRATED: the decoder did not produce the predicted conflicting result')
sys.exit(0)
