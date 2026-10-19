"""Run-length encoding."""

def decode(s):
    """Decode a run-length string like 'a3b1' back to 'aaab'. Already implemented."""
    if not isinstance(s, str):
        raise TypeError('decode expects a string')
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        j = i + 1
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i + 1:
            raise ValueError('missing count')
        out.append(ch * int(s[i + 1:j]))
        i = j
    return ''.join(out)

def encode(s):
    if not isinstance(s, str):
        raise TypeError('encode expects a string')
    if not s:
        return ''
    result = []
    current_char = s[0]
    count = 2
    for ch in s[1:]:
        if ch == current_char:
            count += 1
        else:
            result.append(current_char + str(count))
            current_char = ch
            count = 1
    result.append(current_char + str(count))
    return ''.join(result)
