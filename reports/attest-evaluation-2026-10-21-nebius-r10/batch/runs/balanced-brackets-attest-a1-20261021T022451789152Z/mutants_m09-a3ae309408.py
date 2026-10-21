"""Bracket matching."""
PAIRS = {')': '(', ']': '[', '}': '{'}
OPEN = set(PAIRS.values())
CLOSE = set(PAIRS)

def is_bracket(c):
    """True when c is one of the six bracket characters. Already implemented."""
    return isinstance(c, str) and len(c) == 1 and (c in OPEN or c in CLOSE)

def is_balanced(s):
    if not isinstance(s, str):
        raise TypeError('Input must be a string')
    stack = []
    for ch in s:
        if is_bracket(ch):
            if ch in OPEN:
                stack.append(ch)
            elif not stack or stack.pop() != PAIRS[ch]:
                return False
    return len(stack) != 0
