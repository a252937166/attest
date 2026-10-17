# Evaluation method (M5), frozen before the comparison run

Status: pre-registered on 17 Oct 2026; the paid comparison run has NOT started and will not start before the owner approves the
budget proposal in `reports/attest-reliability-2026-10-17/README.md` section 7. This file, the task contracts, the held-out
suites and `examples/eval/SUITE-M5.json` are frozen by the git commit that adds them; the batch records the digest of the
snapshot it executes, so a later edit cannot change what the report describes.

## Question

Does an evidence-gated agent (Attest) ship fewer incorrect patches than a plain agent with the same model, tools and turn
budget, and at what cost in held patches, time and money?

## Systems

| System | What runs |
| --- | --- |
| baseline | the implementation loop only (same model, same actions, same turn budget, same per-run cap); the patch is accepted when the implementer declares it finished |
| attest | the full pipeline: specification, sealed tests proven red, implementation, supervisor-bound verification, existing suite, mutation check, adversarial tests, drift audit, advisory arbitration; the patch is accepted only with verdict `VERIFIED` |

Arbitration stays advisory: it never changes a verdict in this evaluation. Its classifications are reported per cell.

## Tasks (8), with the ground truth for each

`examples/eval/SUITE-M5.json`. Each task's contract is its `task.json` (statement and acceptance criteria). The held-out
suite is written from the contract by the task author, is never shown to either system, and is stripped from the task
before the run; the harness's judge runs it together with the repository's own suite on the final patch in a fresh sandbox
branch from the checkpoint.

| Task | Kind | Ground truth |
| --- | --- | --- |
| roman-to-numeral | add a function | held-out suite (contract clarified 17 Oct: value-based int subclasses, bool unspecified) |
| rle-encode | add a function, unsatisfiable contract | no patch is correct; a hold (`INFEASIBLE` or `NEEDS HUMAN`) is the right outcome; the judge suite result is recorded but does not establish correctness |
| balanced-brackets | add a function | held-out suite |
| durationkit-units-001 | extend a function | held-out suite (contract clarified 17 Oct: ASCII digits; non-ASCII digits unspecified) |
| semver-is-compatible-pr368-v2 | external repository, add a method | the upstream pull request's own tests, held out |
| slugkit-regression-001 | regression repair | held-out suite |
| kvparse-refactor-001 | behaviour-preserving refactor | held-out suite (behaviour equivalence plus the two requested structural changes) |
| semver-long-prerelease-pr488 | external repository (imported at a pinned commit), bug fix | the upstream pull request's own tests, held out |

Labels per cell, from `accepted` (system) and `correct` (ground truth): true accept, false accept (shipped broken code),
false reject (held a correct patch), true reject, infrastructure error, not run.

## Schedule

2 systems x 8 tasks x 2 attempts = 32 cells, pre-registered in `schedule.json` before the first run, every cell reported
(`evaluation.json`), no merge, no best-of. Attempts are independent runs of the same cell; both are reported, never
averaged into one row. Workers: 2. Order: scheduled index.

## Models and budget (Nebius Token Factory, paid)

| Role | Attest | Baseline |
| --- | --- | --- |
| spec, audit, arbitration | Nemotron Ultra | not used |
| seal, implement, break | Nemotron Super | implement: Nemotron Super |
| summary | Nemotron Lightning | not used |

Per-run cap $0.50 (reserved before the run starts), at most 20 model calls per run, batch cap `--approve-usd` (proposal:
$9.00 for the 32 cells, see the budget proposal), concurrency 2. The harness refuses to start a Nebius batch without an
explicit `--approve-usd` and `--max-calls`. Stop conditions: batch cap reached; 3 consecutive infrastructure errors; any
transport-uncertain operation (never replayed). Codex (the development gateway) is never used in the comparison and never
pooled with it; a dry run of the same schedule on Codex is reported separately as method validation only.

## Provenance and pacing

The batch runs from an immutable snapshot of the package, the harness and the task files in a fresh process; the
schedule records the application revision, the harness digest, the examples digest, the guest-program digests and the
Python and platform; every row records the revision its bundle carries; a task whose cells did not all run the registered
revision, or whose snapshot changed during the batch, is marked invalid in the report (`provenance_check`). On the Codex
dry run the shared rate governor paces requests under the key's hourly limit and records every wait and rejection.

## What will be reported

For each system: scheduled, completed, not run, the confusion counts, shipped broken code (false accepts), holds on
correct patches (false rejects), infrastructure errors, committed USD, mean wall time, pacing waits, invalid comparisons.
Per cell: verdict, judge result and evidence class, reasons, arbitration counts, cost, wall time, revision, run directory.
Every infrastructure error stays in the table. No row is removed or replaced after the fact; a rerun, if any, is a new
pre-registered batch with its own report.

## Known limitations, stated in advance

- Eight tasks, two attempts: enough to show the mechanism and the kind of failures each system makes, not a benchmark.
- The judge suites for the five original tasks were written by the same team that wrote the tasks; the two external tasks
  use upstream pull-request tests written by other people.
- `kvparse-refactor-001`'s held-out suite distinguishes the base from a correct refactor only through the two requested
  structural changes; behaviour tests pass on the base by construction.
- The plain agent is Attest's own implementation loop with the gates removed; it is not a third-party agent.
