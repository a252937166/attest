# Corrections to the reading of the M5 results (written 19 Oct 2026)

`batch/evaluation.json`, `RESULTS.md` and every run directory of this folder are the record of the frozen run and are
not modified. This note corrects how three cells were labelled and described; the labels below are the ones a reader
should use.

## The two Attest `NO CHANGE` cells and one plain-agent cell were unfinished tasks, not correct rejections

Cells 30 and 31 (`semver-long-prerelease-pr488`, Attest, attempts 1 and 2) ended `NO CHANGE` because the implementer
used all 12 turns reading `src/semver/version.py` in ranges, looking for `Version._nat_cmp`, and never edited a file
(`batch/runs/semver-long-prerelease-pr488-attest-a*/trajectory.jsonl`: twelve `read_file` actions each, no
`replace_in_file`, no `finish`). Cell 28 (the same task, plain agent, attempt 1) is the same story: the baseline
implementer did not finish and produced no patch.

The harness labelled all three `true_reject`, and the README and the Devpost draft called them "nothing shipped and
nothing correct to ship" and "correct refusals". That reading is wrong: the task is feasible (the development-profile
run `reports/attest-m4-2026-10-17/runs/semver-long-prerelease-pr488-20261017T132707Z` reached VERIFIED on it, with the
held-out pull-request tests 450 of 450 passing), so these cells are **unfinished tasks**: no patch existed to accept or
reject. They say nothing about Attest's gates, which were never reached, and they are not a success of either arm.

Corrected reading of the result table:

| | Plain agent (16 cells) | Attest (16 cells) |
| --- | --- | --- |
| Correct patch accepted (`true_accept`) | 10 | 4 |
| Broken patch shipped (`false_accept`) | 2 | 2 |
| Correct patch held for a human (`false_reject`) | 0 | 5 |
| No patch produced, task unfinished (`no_patch`, formerly counted as `true_reject`) | 1 | 2 |
| Infrastructure error (`infra_error`) | 3 | 3 |

Cause, found 19 Oct 2026: the implementer had no way to locate a symbol other than paging through a file with ranged
`read_file` calls, and nothing stopped it from repeating that until the turn budget ran out. The revised pipeline
(`reports/attest-revision-2026-10-19/README.md`) adds a `search` action, a def/class outline of the files in the write
scope, a navigation warning after three consecutive reads without an edit, and the harness label `no_patch`; the
console and PROOF.md now describe an exhausted turn budget as an unfinished task.

## Nothing else changes

The headline of the frozen run stands: on this suite Attest did not ship fewer broken patches than the plain agent, every
Attest hold was on a patch the held-out judge accepted, and the two false accepts were on the unsatisfiable rle-encode
contract. The causes of the five holds and of the two false accepts, and what the revision does about each, are in the
revision record.
