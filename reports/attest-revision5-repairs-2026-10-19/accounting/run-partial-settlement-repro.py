#!/usr/bin/env python3
"""Run the review's partial-settlement reproduction from its byte-identical scratch copy against the repaired tree.

The review's script locates the project root as `Path(__file__).resolve().parents[2]` (two directories below the root). The scratch
copy lives one level deeper (`reports/<folder>/accounting/`), so this runner executes the copy's unmodified source with `__file__`
set to a path at the review's depth; nothing else is changed. The copy's sha256 is printed next to the original's so the two can be
compared. Offline: the script itself blocks socket connections; it only writes a temporary journal.
"""

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "reports" / "attest-revision5-review-2026-10-19" / "partial-settlement-repro.py"
COPY = Path(__file__).resolve().parent / "partial-settlement-repro-scratch-copy.py"

if __name__ == "__main__":
    source = COPY.read_bytes()
    print("# original sha256:", hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), file=sys.stderr)
    print("# scratch copy sha256:", hashlib.sha256(source).hexdigest(), file=sys.stderr)
    assert hashlib.sha256(source).hexdigest() == hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), "the scratch copy differs from the review's script"
    pretend = ROOT / "reports" / "attest-revision5-review-2026-10-19" / "partial-settlement-repro.py"  # the depth the script expects
    namespace = {"__name__": "__main__", "__file__": str(pretend)}
    exec(compile(source, str(pretend), "exec"), namespace)
