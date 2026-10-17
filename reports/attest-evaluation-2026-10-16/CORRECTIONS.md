# Corrections to the 16 Oct 2026 evaluation (recorded 16 Oct 2026, M1)

`README.md`, `METHOD.md`, the `evaluation-*.json` files and every run directory in this folder are the original record
and are left unchanged. This note records what an audit of the harness found the same day and how each finding changes
the reading of the numbers. Nothing in the original report may be quoted without these corrections.

## 1. The held-out judge was not independent for four of the five tasks

`rle-encode`, `roman-to-numeral`, `balanced-brackets` and `semver-is-compatible-pr368-v2` configure `heldout_tests` in
their `task.json` pointing at the same file that `SUITE.json` hands to the "independent" judge. Inside Attest the
held-out gate therefore ran the judge's own suite, and Attest could not have returned `VERIFIED` for a patch that
failed it. Only `durationkit-units-001` had a judge the gates never saw.

Consequence: the reported "zero false acceptances" is valid as **"Attest never certified a patch that failed its own
gates"**, not as an independent measurement of false acceptance. The plain agent's numbers are unaffected (it never saw
the suite either way).

Fix (implemented in `scripts/run_evaluation.py`): the harness strips `heldout_tests` from the task it hands to both
systems and keeps the judge suite separate; the judge now records its evidence class and the suite digest.

## 2. The headline table is a best-of merge

`evaluation-final.json` was produced by `scripts/merge_eval.py`, which kept the best completed attempt per
(task, system) cell across `evaluation-attempt1-baselinebug.json`, `evaluation-attempt2-partial.json` and
`evaluation-attempt3-3infra.json`. The merge is labelled as such in the file and in `README.md`, but a merged
best-of is not a result that can be compared across systems or quoted as a rate.

Consequence: the aggregate table ("5 of 5 cells completed cleanly", costs, latencies) describes selected attempts,
not scheduled ones. The per-task observations (which verdicts occurred, what the breaker found) stand as observations.

Fix: the harness now pre-registers every scheduled attempt (`schedule.json`) before execution and reports every one of
them, infrastructure errors and unexecuted cells included; `merge_eval.py` refuses to run.

## 3. The `rle-encode` finding is a contract defect, not an implementation bug

`decode` in `examples/eval/rle-encode/repo/rle/core.py` reads every digit after a character as part of the run count.
No `encode` can therefore round-trip a string that contains a digit while `decode` stays fixed: `encode('a1')` is
`'a111'`, which decodes to `'a' * 111`. The task statement nevertheless requires `decode(encode(x)) == x` for every
string. The requirement is unsatisfiable under the task's own constraints ("do not change decode").

Consequence: `README.md` finding 2 ("Attest caught a real bug that the plain agent shipped") must read: **Attest held a
patch for a requirement that no implementation could satisfy, which the plain agent shipped silently.** The hold was
right. The arbiter's label `implementation_bug` was wrong; the correct classification is `contract_dispute`. The
breaker's counterexample (a digit-containing input) remains the useful artifact: it is the concrete input that shows the
contract cannot hold.

Fix: the next evaluation design (M5) either changes the task to a satisfiable contract or keeps it deliberately as an
infeasibility case and scores "held" as the correct outcome; the specification prompt gains a satisfiability question so
that an unsatisfiable requirement can end as `INFEASIBLE` before implementation.

## 4. Usage figures

The $2.13 quoted earlier on 16 Oct 2026 double-counted run directories copied into `reports/`. Keyed by bundle `run_id`
the local Nebius usage is 46 unique runs, $1.62 committed; with the three runs that exist only on the server, 49 unique
runs, $1.80 committed (three uncertain calls counted at their reservation). `scripts/usage_report.py` reproduces the
local figure; the Token Factory console is the authoritative invoice.
