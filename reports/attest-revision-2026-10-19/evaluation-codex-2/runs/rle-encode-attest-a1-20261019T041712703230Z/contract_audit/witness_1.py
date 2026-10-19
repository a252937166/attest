import sys
from itertools import groupby

try:
    from rle import decode
    original = 'a1'
    encoded = ''.join(ch + str(sum(1 for _ in run)) for ch, run in groupby(original))
    actual = decode(encoded)
except Exception as exc:
    print('NOT DEMONSTRATED: evaluation failed with ' + type(exc).__name__)
    sys.exit(0)

if encoded == 'a111' and actual == 'a' * 111 and actual != original:
    print(f'CONTRADICTION AC10 AC12: input {original!r} requires encoding {encoded!r}, but unchanged decode returns {actual!r} (111 copies of a) instead of {original!r}.')
    sys.exit(3)

print('NOT DEMONSTRATED: computed encoding or decoding did not establish the claimed mismatch')
sys.exit(0)
