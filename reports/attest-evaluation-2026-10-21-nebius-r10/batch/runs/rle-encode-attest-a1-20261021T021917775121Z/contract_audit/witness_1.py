import sys
from rle import decode

# According to the task statement, encode must run-length encode: each maximal run becomes character + decimal count.
# For input '12', the runs are '1' (length 1) and '2' (length 1), so the required encoding is '11' + '21' = '1121'.
required_encoding = '1121'
decoded = decode(required_encoding)
if decoded != '12':
    print(f"CONTRADICTION TC5: decode(encode('12')) == '{decoded}' != '12'")
    sys.exit(3)
else:
    print("NOT DEMONSTRATED: round-trip holds for '12'")
    sys.exit(0)
