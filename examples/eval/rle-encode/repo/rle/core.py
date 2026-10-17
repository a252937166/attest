"""Run-length encoding."""


def decode(s):
    """Decode a run-length string like 'a3b1' back to 'aaab'. Already implemented."""
    if not isinstance(s, str):
        raise TypeError("decode expects a string")
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        j = i + 1
        while j < len(s) and s[j].isdigit():
            j += 1
        if j == i + 1:
            raise ValueError("missing count")
        out.append(ch * int(s[i + 1:j]))
        i = j
    return "".join(out)


def encode(s):
    raise NotImplementedError("encode is not implemented yet")
