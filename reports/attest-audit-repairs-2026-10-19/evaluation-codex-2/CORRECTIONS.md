# Corrections to the recorded labels of this batch (written after the batch, the recorded files are unchanged)

`evaluation.json` and `RESULTS.md` label cell 1 (`kvparse-refactor-001`, verdict INFEASIBLE) as `true_reject`. That label is
wrong and is corrected here rather than by rewriting the record.

The harness copy this batch ran (`scripts/run_evaluation.py` sha256 `6e77617bcc8a…`, frozen in `snapshot/`) had no label for an
INFEASIBLE verdict on a task whose ground truth is its held-out suite: with no patch to judge, the judge's "not correct"
describes the unmodified repository, and the generic rule (not accepted and not correct) produced `true_reject`. The task
`kvparse-refactor-001` is satisfiable (its held-out suite passed for the plain agent's patches in the M5 evaluation and for
Attest's own VERIFIED run in the 19 Oct development batch `reports/attest-revision-2026-10-19/evaluation-codex-3/`), so the
refusal was a wrong refusal. The corrected harness (sha256 `2aa28413a1ccfe42…`, pinned in `FREEZE.md`) labels this outcome
`false_refusal` (INFEASIBLE on a satisfiable task), keeps `true_reject` for INFEASIBLE on a task marked `unsatisfiable`
(cell 0 of the first batch, `rle-encode`), and the renderer carries a column for it.

Corrected reading of this batch: 1 true accept (`balanced-brackets`), 1 false refusal (`kvparse-refactor-001`), 0 of every
other label.

What the refusal rests on, for the record: the contract auditor's witness (`runs/kvparse-refactor-001-…/contract_audit/witness_1.py`)
demonstrates a contradiction between the specification's AC1 and AC2 (replace the hand-rolled loops with `str.partition` and
strip; `parse_line('a=b') == ('a', 'b')`) and its AC16 (for every string input, preserve the supplied implementation's exact
results or exception types) using a `str` subclass whose `__len__` returns 0: the original implementation raises `ValueError`
on it, the required one returns `('a', 'b')`. The contradiction is real, but it is a contradiction inside the SPECIFICATION the
specification model wrote (AC16 generalises the task's "preserve behaviour for existing inputs" to every possible string
input, pathological subclasses included), not in the task statement. This is the known limitation stated in
`reports/attest-audit-repairs-2026-10-19/README.md`: an executed witness proves that the derived contract contradicts itself,
not that the task is impossible; the remedy under consideration is to audit the task's own acceptance criteria rather than
the specification's restatement, or to hold (NEEDS HUMAN) when a demonstrated conflict involves only criteria the
specification added.
