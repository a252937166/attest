# Revision 4 (19 Oct 2026): executed witnesses, validated corrections, a navigable implementer, a ledger that survives

Owner's instruction of 19 Oct 2026, in six items: (1) fix the incorrect VERIFIED outcomes on contradictory contracts with
general checks and executable counterexamples; (2) reduce false holds safely, handling defective generated tests including
syntax errors, with corrections validated against the candidate and the unchanged base and the affected gates re-run,
never promoting a patch on an arbiter's opinion alone; (3) find out why both Nemotron attempts on the external
python-semver task exhausted their budget without a patch, improve the workflow, validate it through the development
gateway, and report NO CHANGE as an unfinished task; (4) persist usage and reservations so an interruption cannot erase
known costs, keep uncertain charges reserved, keep the never-replay protection, and fix the health message; (5) run
regression checks on the development gateway and freeze the revised version, preserving the M5 results; (6) revalidate the
export and the bundles, update the documentation and prepare the public repository.

Everything in this folder was produced with the development gateway and Nebius Token Factory Sandboxes. No paid Nebius
inference call was made; the proposal for the paid validation of this revision is at the end. The M5 results folder is
unchanged except for a pointer to its new `CORRECTIONS.md`.

## 1. What the M5 record showed, cell by cell

| M5 cell | What happened | Root cause found on 19 Oct |
| --- | --- | --- |
| rle-encode, Attest a1 and a2: VERIFIED on an unsatisfiable contract (false accept) | the sealer wrote no test that exposes the contradiction (round trip through the unchanged greedy decoder for strings containing digits), so every gate passed | the only check for contradictory requirements was the specification model's `feasible` flag, a bare opinion; nothing executed a counterexample and nothing checked that the sealed suite covered every criterion |
| durationkit a2, semver-is-compatible a1 and a2: NEEDS HUMAN on correct patches | one adversarial test each failed; the arbiter classified each as a test defect and its corrected test passed on the candidate and failed on the base | arbitration was advisory by design: a validated correction never re-ran the gate |
| kvparse-refactor a1: NEEDS HUMAN on a correct patch | the breaker returned a module with a syntax error twice; the adversarial gate was unusable | two attempts by the same model, the compile error fed back without the offending line, no escalation, no repair path |
| kvparse-refactor a2: NEEDS HUMAN on a correct patch | one sealed test asserted `('q', '"')` for `q = ""` where the contract says quotes are removed (a wrong expectation), and the drift audit was lost to a transport-uncertain call | a sealed assertion failure; the revision keeps this hold on purpose (see 3) and the drift loss is the never-replay rule |
| semver-long-prerelease-pr488, Attest a1 and a2: NO CHANGE (labelled true_reject) | the implementer spent all 12 turns on ranged `read_file` calls looking for `Version._nat_cmp` in an 839-line file and never edited | no way to locate a symbol, no outline of the file, no warning against paging; the label and the copy called an unfinished task a correct refusal |

## 2. Contract audit with executed witnesses (item 1)

A new stage runs after the specification and before sealing. The contract auditor (the `audit` role: Nemotron 3 Ultra on
the submission profile) receives the frozen contract with numbered acceptance criteria (`AC1`, `AC2`, ...), the write
scope and the repository before any change, and looks for requirements that no implementation confined to the write scope
can satisfy. For every conflict it must return a **witness program**. Attest executes each witness in a disposable sandbox
branch on the unmodified checkpoint (networking off, 60 s). A conflict counts as *demonstrated* only when the witness
prints a line starting with `CONTRADICTION <requirement ids>:` and exits with code 3; exit 0 means the witness could not
show it; anything else is a broken witness. The program, its digest, exit code, output and operation id are recorded
(`contract_audit.json`, `contract_audit/witness_N.py`), and `attest check` recomputes the digests and checks that an
INFEASIBLE verdict rests on a demonstrated witness.

Consequences, all general (no task is named anywhere in the code):

- INFEASIBLE now requires a demonstrated witness. The specification model's `feasible=false` is a claim: the auditor is
  asked to demonstrate it; when it cannot, the run ends NEEDS HUMAN with reason class `infeasibility_unproven`.
- A conflict the auditor claims but cannot demonstrate never ends the run; it is handed to the sealer as a suspicion
  ("write at least one sealed test that exercises exactly this interaction") and recorded as a weak spot of a VERIFIED verdict.
- The sealer returns a coverage map (which test methods check which criterion). The pipeline checks that every criterion is
  claimed by at least one existing test method and sends gaps back; after the last attempt the gaps are recorded
  (`sealed_tests.coverage_gaps`) and shown as a weak spot. The map is the sealer's own claim; the check only makes it complete.
- The sealer and the breaker are told to stress requirements that relate two operations (round trips, inverses) with
  inputs the other operation treats specially. This is guidance, not a rule; the witness is the rule.

What the witness mechanism does not do: the program's reasoning is the model's. Attest guarantees only that it ran on the
unmodified repository and what it printed. A wrong witness that exits 3 produces a false INFEASIBLE (a hold-type verdict,
nothing shipped), which the recorded program and output let a reader catch.

## 3. Validated corrections re-run their gate; a sealed assertion is never overridden (item 2)

The arbiter still classifies every failing generated test (implementation bug, test defect, contract dispute) and offers a
corrected module for pure test defects. New: a correction **counts** only after mechanical validation, in this order, each
step recorded in `arbitration.json`:

1. it keeps every test method (same class and method names, none added or removed);
2. it changes only the methods that failed (imports may be added; any other module-level change is rejected);
3. at most 3 tests are corrected (more is a human's review);
4. the corrected module passes on the candidate under the supervisor (nonce, digests, canaries);
5. it still discriminates: every corrected sealed test fails on the unmodified base (the red check preserved); a corrected
   adversarial module fails on the base, or, when the base already behaves correctly (a refactor), at least one mutant of
   the patch that the sealed suite caught makes a corrected test fail (up to 3 mutants tried).

A validated correction **re-runs the affected gate**: the adversarial gate becomes the corrected module's executed result;
a corrected sealed suite is the re-verification itself, and the breaker (mutants and adversarial tests) then runs against
the corrected suite because it had been skipped. The verdict is derived again from the gates by the same rule; the gate
record carries `corrected: true`, the original failure, the corrected module's digest and the discrimination evidence;
`verdict.before_corrections` keeps the first derivation. The arbiter's classification alone changes nothing: a rejected
correction (steps 1 to 5) leaves the hold with the rejection reason in E6.

**A sealed test that failed by assertion or by an exception raised in the code under test is never overridden.** The pre-registered acceptance test disagreed with the
candidate on a concrete value; whether the test or the candidate is wrong is exactly the judgement the owner said must
never promote a patch on its own, and execution cannot settle it (each side passes its own test). The arbiter's view and
its validated correction are recorded for the human (reason class `sealed_assertion_hold`), the hold stands. A sealed test
that crashed in its own body, timed out or used a Python 3.12 incompatibility (outcomes ERROR and TIMEOUT) can be
corrected under the same five steps, because no oracle value was disproven. This is the one place where the revision
deliberately leaves a known false hold (the kvparse a2 pattern) in place; `--arbitration-advisory` turns all re-runs off.

Syntax errors in generated tests: the sealer already had three attempts with compile feedback. The breaker now has three
attempts, the compile error names the offending line, and the third attempt escalates to the arbiter's model (recorded as
`escalated: true`, with the author role and model in the bundle).

## 4. The implementer can find things, and an exhausted budget is an unfinished task (item 3)

- New action `search`: a symbol, snippet or regular expression, optionally within one file, returns matching lines with
  file and line number (bounded to 60 lines).
- The repository tree in the prompt carries a def/class outline with line numbers for the files in the write scope
  (budgeted at 6,000 characters); a truncated `read_file` ends with the same outline.
- A refused `replace_in_file` whose snippet occurs zero times names the closest lines of the file.
- After three consecutive turns that only read, list or search, the prompt carries a navigation warning.
- `NO CHANGE` distinguishes "finished without editing" from "turn budget exhausted without a patch" (`candidate.unfinished`,
  reason class `unfinished_no_patch`); PROOF.md, the console and the harness label (`no_patch`, counted separately, neither
  rejection nor acceptance) say so. The M5 folder has a corrections note for the three cells this affects.

Validation through the development gateway: see section 7 (the external task with the usual implementer model and with the
weaker `gpt-6-luna` as implementer).

## 5. Reliability and cost accounting (item 4)

- Every run directory gets `ledger.jsonl`, an append-only journal: a reservation line is written before a Nebius request
  leaves, the call record as soon as it is known (closing the reservation), sandbox operations as they start. A process
  that dies mid-run leaves known costs and open reservations behind; `read_journal` sums them (open reservations at their
  bound). `ledger.json` with the totals is still written at the end.
- Call records carry a `settlement`: `known` (usage returned), `unsettled` (transport-uncertain; the reservation stays
  committed until reconciled against the provider's billing) or `none` (the development gateway's allowance). The per-run
  cap binds on known costs plus unsettled and open reservations.
- The console updates the run row after every reservation and every call, not only on log events, and its restart
  reconciliation reads the journal of an interrupted run (known costs plus open reservations) instead of charging the
  whole per-run cap; without a journal the cap still applies.
- The evaluation harness, on resume, reads the journals of run directories that no completed row owns (cells in flight when
  the process died), adds their committed USD to the batch total and lists them under `interrupted`; the cell runs again.
- The never-replay rule is untouched: a transport-uncertain POST (inference or sandbox spawn) is still never retried.
- Health: `/api/health` of an idle service reported "1 active reservation(s)" because the execution-time recheck counts the
  running row itself; the health endpoint now counts only rows that are queued or running.

## 6. Regression tests (offline, no credentials)

`python3 -m unittest discover -s tests -t .` ran 179 tests at the end of the day (145 before the revision). New in
`tests/test_revision4.py` and the extended fakes of `tests/test_verification.py`: a demonstrated witness ends INFEASIBLE
with the witness recorded and checked; a claimed conflict without a demonstration does not stop the run; a specification's
infeasibility without a demonstrated witness is a hold; a validated adversarial correction re-runs the gate (VERIFIED,
`corrected` gate, `before_corrections` kept); advisory mode records but does not re-run; corrections that drop a test, touch
a passing test or change nothing are rejected without a sandbox run; a correction that passes on the base must be caught by
a mutant; a sealed test that failed by assertion or by an exception raised in the code under test is never overridden; a sealed test that crashed in its own body is corrected and the
breaker reruns; breaker syntax errors escalate; an exhausted turn budget is an unfinished NO CHANGE; coverage gaps are
recorded; ledger journal and reservations; the Nebius client's unsettled reservation; the console's reconciliation from the
journal and the meters a dying worker leaves behind; the harness's `no_patch` label and interrupted cells; workspace
search, outline and closest-line hints; `methods_changed` and `coverage_gaps`; `attest check` on bundles with corrected
modules and witnesses (and failing it when a corrected module or a witness is edited); recorded bundles of earlier
revisions still check. All schemas remain strict-mode compatible for Token Factory.

## 7. Validation runs on the development gateway (Codex) and real Sandboxes

All inference below is the team's development gateway (allowance, not a Nebius charge: `gpt-6-astra` for spec, contract
audit, drift audit and arbitration; `gpt-6-sol` for sealing, implementation and breaking; `gpt-6-luna` where stated);
execution is Nebius Token Factory Sandboxes. Every batch ran from an immutable snapshot through `scripts/run_evaluation.py`
(Attest arm only, one attempt per task, the judge's held-out suite stripped from the system under test); the tables are
rendered cell by cell in each batch's `RESULTS.md` and every bundle passes `python -m attest check`.

| Run | Revision | Result |
| --- | --- | --- |
| `evaluation-codex/` (04:06 UTC, stopped by the operator after three cells) | `5f9dc8ad…` (before the journal fix) | roman VERIFIED (correct), rle-encode INFEASIBLE on an executed witness, brackets VERIFIED (correct). Stopped because the judge's sandbox operation was being appended to `ledger.jsonl` after the manifest had fixed its digest, so these three bundles fail `manifest_digests` on that one file; the fix seals the journal before the manifest. Kept privately (the public export excludes this directory); the finding is the point. |
| `runs-luna/` (04:06 UTC, CLI, no judge) | `5f9dc8ad…`, implementer `gpt-6-luna` | the external python-semver task, VERIFIED in 6 turns: one ranged read of lines 180 to 210 (the outline named `_nat_cmp`), one `replace_in_file`, `run_tests`, two `run_python` checks, `finish`; held-out pull-request tests 450 of 450 (stdout class), mutation 1.0 on 12 mutants, 9 adversarial tests pass, drift 0.0. The M5 implementer (Nemotron Super) had used all 12 turns on `read_file` of the same file. |
| `evaluation-codex-2/` (04:17 UTC, 8 cells, one transport-uncertain stop, resumed 04:44 UTC) | `87aa03b9…` | 6 true accepts, 1 true reject, 1 infrastructure error, 0 false holds, 0 false accepts (table below). |
| `evaluation-codex-semver/` (04:44 UTC, the cell that ended ERROR above, registered again) | `87aa03b9…` | semver-is-compatible VERIFIED (correct), no arbitration needed. |
| `evaluation-codex-3/` (05:3x UTC, 8 cells on the final tree) | `b27a1c07…` (pinned) | see the paragraph after the table. |

`evaluation-codex-2`, cell by cell:

| Task | Verdict | Judge | What happened |
| --- | --- | --- | --- |
| roman-to-numeral | VERIFIED | correct | 5 implementer turns, all gates passed |
| rle-encode (unsatisfiable) | INFEASIBLE | no patch counts as correct | the auditor claimed AC10 and AC12 conflict; its witness computed the mandated encoding of `'a1'` (`'a111'`), ran the unchanged decoder on it (111 copies of `'a'`) and exited 3; no sealing, no implementation |
| balanced-brackets | VERIFIED | correct | 4 turns, all gates passed |
| durationkit-units-001 | VERIFIED | correct | two adversarial tests failed (they demanded a guarantee against intermediate overflow for 10**309 milliseconds, which the contract excludes); the arbiter classified both as defects (unspecified behaviour); the corrected tests pass on the candidate and 2 of 2 fail on the unmodified base; the adversarial gate was re-run on the corrected module (10 of 10) and the verdict derived again. In M5 the same pattern was a hold. |
| semver-is-compatible-pr368-v2 | ERROR | not judged | a transport-uncertain inference call (TLS EOF from the gateway) during sealing; never retried; the batch stopped by rule and the other cells were resumed; the task was registered again (`evaluation-codex-semver`): VERIFIED, correct |
| slugkit-regression-001 | VERIFIED | correct | 6 turns, all gates passed |
| kvparse-refactor-001 | VERIFIED | correct | 5 turns, all gates passed; no breaker syntax error this time |
| semver-long-prerelease-pr488 (external, pinned commit) | VERIFIED | correct (450 of 450 held-out) | 8 turns; one sealed test failed with a `TypeError` raised inside `Version.compare` (the test expected a subclass instance to compare with a base-class instance); the arbiter called it a wrong expectation, the corrected test passed on the candidate and failed on the base, and under the rule of revision `87aa03b9…` the sealed gate was re-run (mutation 0.857 on 7 mutants, 8 adversarial tests pass). The judge agrees with the patch. This cell changed the rule: see below. |

What `evaluation-codex-2` changed. The pr488 cell showed that "failed by assertion" was too narrow a definition of a sealed
oracle disagreement: the sealed test's expectation was contradicted by an exception raised in the code under test, which
the supervisor records as ERROR, not FAIL. The final tree (`b27a1c07…`) therefore treats a sealed failure as an oracle
disagreement unless the test could not run for a reason of its own (a crash inside the test body of the kinds the red
check already recognises, or a timeout): only those may be corrected. Under the final rule the pr488 cell above would
have been a hold with the arbiter's validated correction recorded for the human; that is the deliberate price of the
principle, and the judge's agreement with the patch is exactly the kind of evidence a human would use to lift it.
`evaluation-codex-3` ran the eight tasks again on the final tree:

(results of evaluation-codex-3 follow)

## 8. Deployment, freeze and what is still open

(filled in at the end of the day)
