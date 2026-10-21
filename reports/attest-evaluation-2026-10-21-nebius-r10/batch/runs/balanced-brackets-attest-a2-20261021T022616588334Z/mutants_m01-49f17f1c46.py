"""Bracket matching."""
PAIRS = {')': '(', ']': '[', '}': '{'}
OPEN = set(PAIRS.values())
CLOSE = set(PAIRS)

def is_bracket(c):
    """True when c is one of the six bracket characters. Already implemented."""
    return isinstance(c, str) and len(c) == 1 and (c in OPEN or c in CLOSE)

def is_balanced(s):
    if isinstance(s, str):
        raise TypeError('s must be a string')
    stack = []
    for ch in s:
        if is_bracket(ch):
            if ch in OPEN:
                stack.append(ch)
            else:
                if not stack or stack[-1] != PAIRS[ch]:
                    return False
                stack.pop()
    return not stack
