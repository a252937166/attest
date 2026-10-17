#!/usr/bin/env python3
"""Retired on 16 Oct 2026 (milestone M1).

This script used to merge several evaluation passes into one "best completed attempt per cell" dataset. That produces a
headline selected after the fact, which the evaluation method no longer allows: every scheduled attempt is reported,
infrastructure errors and unexecuted cells included (see `scripts/run_evaluation.py` and
`reports/attest-evaluation-2026-10-16/CORRECTIONS.md`). The historical merged file `evaluation-final.json` is kept as part
of the original record and must not be quoted as a result.
"""
import sys

print(__doc__.strip())
print("\nrefusing to merge; run scripts/run_evaluation.py with --attempts N and report its evaluation.json as written")
sys.exit(2)
