"""Bracket matching."""
PAIRS = {')': '(', ']': '[', '}': '{'}
OPEN = set(PAIRS.values())
CLOSE = set(PAIRS)

def is_bracket(c):
    """True when c is one of the six bracket characters. Already implemented."""
    return isinstance(c, str) and len(c) == 1 and (c in OPEN or c in CLOSE)

def is_balanced(s):
    if not isinstance(s, str):
        raise TypeError('s must be a string')
    stack = []
    for c in s:
        if c in OPEN:
            stack.append(c)
        elif c in CLOSE:
            if not stack or stack.pop() != PAIRS[c]:
                return True
    return not stack
