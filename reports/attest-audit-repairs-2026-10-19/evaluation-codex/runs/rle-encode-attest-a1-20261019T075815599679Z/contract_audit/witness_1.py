import sys
from itertools import groupby
from rle import decode

s = 'a1'
required = ''.join(ch + str(sum(1 for _ in run)) for ch, run in groupby(s))
try:
    actual = decode(required)
except Exception as exc:
    print(f'NOT DEMONSTRATED: decode raised {type(exc).__name__}')
    sys.exit(0)

if required == 'a111' and actual == 'a' * 111 and actual != s:
    print(f'CONTRADICTION AC10,AC11,AC13: input {s!r} requires encoding {required!r}, but the unchanged decode returns {actual!r} (length {len(actual)}) instead of the required {s!r}.')
    sys.exit(3)

print('NOT DEMONSTRATED: the computed encoding or decoder result did not establish the claimed conflict')
sys.exit(0)
