# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: ERROR**  
Run `durationkit-units-001-attest-a2-20261021T024104094554Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:41:04.095163+00:00, finished 2026-10-21T02:42:19.651481+00:00.

**This run stopped for reconciliation.** At stage red-1 an operation's outcome became uncertain (sandbox executor), so Attest sent nothing further, replayed nothing and certified nothing. The repository was not changed by this run.

Key evidence (E7): 1 operation(s) to reconcile: stopped for reconciliation at red-1: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref d20a6d56]; it was ...



What to do: Reconcile the listed operations against the providers' records (each item names its read-only check) before this task is run again; nothing of this run is ever sent again.

Reasons: stopped for reconciliation at red-1: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref d20a6d56]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The run failed in the sandbox executor at stage red-1; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage red-1: stopped for reconciliation at red-1: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref ... |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e1346287-5257-474e-b9bd-7d388c8a03a2`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non‑negative integer followed by a unit (d, h, m, s, ms) in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed input with ValueError, and reject non‑string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: 1. A plain non‑negative integer (ASCII digits) optionally surrou | TypeError: if text is not a str.; ValueError: if text is empty or whitespace‑only after stripping.; ValueError: if any component contains a negative number (e.g |

Acceptance criteria:
AC1. 1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
AC2. 2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
AC3. 3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
AC4. 4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
AC5. 5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
AC6. 6. Return type is float for every accepted input.
AC7. 7. ValueError for empty string '' and whitespace‑only '   '.
AC8. 8. ValueError for negative numbers: '-1h'.
AC9. 9. ValueError for fractional numbers: '1.5h'.
AC10. 10. ValueError for unknown units: '1x'.
AC11. 11. ValueError for repeated units: '1h1h'.
AC12. 12. ValueError for components out of descending order: '30m1h'.
AC13. 13. ValueError for unit without a number: 'h'.
AC14. 14. ValueError for number without a unit when other components have units: '1h30'.
AC15. 15. ValueError for completely malformed text: 'abc'.
AC16. 16. TypeError for non‑string input such as 90 or None.
AC17. 17. Existing tests in tests/test_parse.py must continue to pass without modification.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. All authoritative criteria (TC1-TC9) are mutually compatible and align with the existing test suite. The plain-integer form and the new component form operate on disjoint input patterns (all-ASCII-digits vs. containing unit letters), with whitespace handling clearly partitioned. No concrete input satisfies two requirements demanding different outcomes, and no requirement conflicts with the frozen test file. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```




## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1918 | 0 | 0.007491 | 6.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 3816 | 14690 | 0 | 0.047886 | 49.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2223 | 1414 | 0 | 0.001940 | 7.4s | ok |

Model calls: 3 (0 failed, 0 malformed); tokens in/out/cached 7776/18022/0; Inference USD: 0.057317.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c55-8c35-72e6-a63a-3ff952456425 | SUCCESS | 0 | 1.958s | retained | off | 0.0028775899999999997 |
| red-1 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 2, total guest duration 1.958s, retained images ['e1346287-5257-474e-b9bd-7d388c8a03a2'], 1 operation(s) with an unknown outcome (never replayed).

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: sandbox executor; stage: red-1; model calls 3 (0 failed); sandbox operations 2; committed inference USD 0.057317; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- stopped for reconciliation at red-1: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref d20a6d56]; it was not sent again (outcome uncertain; not retried; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it

## 12b. Reconciliation (nothing of this run is sent again)
The run stopped at stage `red-1` (uncertain_operation) at 2026-10-21T02:42:19.642542+00:00: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref d20a6d56]; it was not sent again. Each item below is settled by a human with the read-only check it names.

| Item | Service | Stage | Operation | State | Started | How to settle it |
| --- | --- | --- | --- | --- | --- | --- |
| sandbox_spawn | sandboxes | red-1 | s2 | UNCERTAIN | 2026-10-21T02:42:17.917072+00:00 | GET /operations?kind=instance with since/until around started_at, matching image_uuid (the spawn request carries no client id); it is never sent again |

Rule: once an operation's outcome is uncertain (a request that may have been executed and whose answer is unknown, an accepted operation whose outcome was not read, an answer that could not be priced) or a record of the run could not be made durable, the run sends nothing further: no model call, no sandbox operation, no poll; it ends ERROR with every such operation listed here with the read-only check that settles it, and none of them is ever sent again

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
