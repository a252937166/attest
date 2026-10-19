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

## Correction of the paragraph above (19 Oct 2026, revision 6, after the independent follow-up review)

The paragraph above is kept as written; two of its claims are wrong and are corrected here.

1. **The quantifier is the requester's, not the specification model's.** The paragraph says that AC16 "generalises the
   task's 'preserve behaviour for existing inputs' to every possible string input" and that the contradiction lies "not in the
   task statement". The frozen task statement (`examples/eval/kvparse-refactor/task.json`, unchanged since M5) itself says:
   "The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input". The
   specification model restated that sentence; it did not introduce the quantifier. What the task does not say is whether a
   `str` subclass with an inconsistent `__len__` is a "str input" in the requester's sense; its `contract_resolution` note
   scopes the preserved behaviour to `str` inputs, and TC8 leaves only non-string arguments unspecified.

2. **The witness disproves one implementation, not every implementation the task allows.** `witness_1.py` compares the
   original parser with one particular `str.partition` implementation and shows that the two disagree on a `str` subclass
   whose `__len__` returns 0. That is a conflict between the original parser and that one candidate, not a proof that no
   implementation confined to `kvparse/**` can satisfy TC1 to TC8: the task constrains the structure of `parse_line`
   (`str.partition`, no `while` loop), not its treatment of pathological subclasses, so a candidate may guard the subclass
   case and still meet every criterion. The review's bounded counterexample (`reports/attest-revision5-review-2026-10-19/core-review.md`)
   shows such a candidate.

The recorded outcome therefore stays a **false refusal**: a demonstrated conflict on the specification's derived criteria
(AC1, AC2, AC16), executed by an unconstrained witness (it defines a class and a function and so chooses its own
implementation), that revision 5 accepted as task impossibility. Revision 6 (`reports/attest-revision5-repairs-2026-10-19/README.md`)
changes the rule: INFEASIBLE needs a conflict grounded in the task's own criteria (TC ids) and demonstrated by a constrained
witness (no definitions, no dynamic types, no `exec`/`eval`) inside the declared input domain; a demonstrated conflict that is
derived, mixed or unconstrained is held for a person (NEEDS HUMAN, reason class `contract_conflict_held`). Under that rule
this run's witness classifies as `provenance: derived`, `witness_constrained: false` (`tests/test_audit_core.py::R503GroundedInfeasibility`).
The recorded bundle is unchanged and still checks under its own protocol (2).
