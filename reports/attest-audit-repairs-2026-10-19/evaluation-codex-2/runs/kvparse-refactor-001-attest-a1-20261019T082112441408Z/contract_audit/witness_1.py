import sys
from kvparse import parse_line

class ZeroLengthString(str):
    def __len__(self):
        return 0

line = ZeroLengthString('a=b')

def required_parse_line(value):
    key, separator, rest = str.partition(value, '=')
    key = key.strip()
    rest = rest.strip()
    if not separator or not key:
        raise ValueError
    if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in ('"', "'"):
        rest = rest[1:-1]
    return key, rest

def outcome(function):
    try:
        return ('return', function(line))
    except Exception as error:
        return ('exception', type(error).__name__)

original = outcome(parse_line)
required = outcome(required_parse_line)
if isinstance(line, str) and original == ('exception', 'ValueError') and required == ('return', ('a', 'b')):
    print("CONTRADICTION AC1 AC2 AC16: For ZeroLengthString('a=b') with __len__ returning 0, the original outcome is %r while the required partition-and-strip outcome is %r." % (original, required))
    sys.exit(3)
print('NOT DEMONSTRATED: observed outcomes do not establish the stated conflict')
sys.exit(0)
