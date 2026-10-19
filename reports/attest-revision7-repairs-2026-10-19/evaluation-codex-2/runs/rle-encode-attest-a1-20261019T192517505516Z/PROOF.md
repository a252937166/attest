# Attest Proof Bundle: rle-encode

**Verdict: NEEDS HUMAN**  
Run `rle-encode-attest-a1-20261019T192517505516Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T19:25:17.505954+00:00, finished 2026-10-19T19:27:06.983790+00:00.

**Hold this patch.** The contract auditor's witness program demonstrated a conflict between requirements TC5, AC8, AC13 when Attest ran it on the unmodified repository, but the conflict is not grounded: it rests on criteria the specification model derived, not only on the requester's own. A model's restatement of the task, or a witness that compares one implementation of its own choosing, cannot establish that the task itself is impossible, so the run stops here as a hold rather than an INFEASIBLE verdict. No sealed tests were written and no implementation was attempted.

Key evidence (contract_audit): CONTRADICTION TC5 AC8 AC13: input 'a1' requires encoding 'a111', but unchanged decode returns 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' instead of 'a1'.



What to do: Read the witness program, its output and the requirement ids in contract_audit/; decide whether the requester's criteria really conflict. If they do, record the contradiction in the task; if the specification over-read the task, clarify the statement and run again.

Reasons: contract conflict demonstrated but not grounded (mixed criteria TC5, AC8, AC13): The required encoding of 'a1' is 'a111', but the unchanged decoder returns 111 copies of 'a', violating universal round-trip equality.; a model's restatement of the task cannot establish that the task is impossible, so a human decides whether the requirement conflict is real


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- nothing: no gate was reached

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `rle-encode`, spec digest `e64da208acc97bfcb964f579c1a5687bc6340ce7531452982870487fe1231c41`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6a43e97f-d82b-4300-a90a-1c5152eb18e4`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.8.0 revision `68e9de49df5b22b8` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision7-repairs-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most 2 times after 2/6 s, each attempt recorded; transport-uncertain failures (the request was written) never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

The rle package exposes decode (already implemented) and a stub encode(s). Implement encode(s) so that it run-length encodes a string: each maximal run of one character becomes that character followed by the decimal count of the run (the count is always written, even when it is 1). For example encode('aaabbc') is 'a3b2c1', encode('abc') is 'a1b1c1', encode('') is ''. encode must return a str and must round-trip with decode (decode(encode(x)) == x for every string x). Raise TypeError when s is not a string. Do not change decode or the tests.

## 2. Specification and contract
Feasible: False. Implement the publicly exported encode(s) to return a str containing each maximal run's character followed by its decimal length, including counts of 1; return an empty string for empty input and raise TypeError for non-string input. Preserve decode and existing tests. The additional requirement that every string round-trip through decode conflicts with the specified format and existing decoder.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| rle.encode | encode(s) | Accept str instances, including subclasses. Process characters as Python string elements, without normalization. Emit each maximal contiguous run in order as it | TypeError: s is not an instance of str; no particular exception message is required. |
| rle.decode | decode(s) | Remain unchanged. Read one character followed by the maximal sequence of characters accepted by str.isdigit(), convert that sequence with int(), and append the  | TypeError: s is not an instance of str.; ValueError: a character is not followed by a count.; ValueError: the consumed count cannot be converted by int(), inclu |

Acceptance criteria:
AC1. 1. encode('aaabbc') == 'a3b2c1' and encode('a') == 'a1'.
AC2. 2. encode('') == ''.
AC3. 3. encode('abc') == 'a1b1c1'.
AC4. 4. encode('x' * 12) == 'x12'.
AC5. 5. encode('aba') == 'a1b1a1'; separated runs of the same character remain separate.
AC6. 6. encode('  \n\n') == ' 2\n2'; whitespace characters are preserved.
AC7. 7. encode('éé🙂') == 'é2🙂1'; Unicode characters are preserved.
AC8. 8. encode('a1') == 'a111' under the required run format.
AC9. 9. Every successful encode call returns a str, including for empty input and str subclass input.
AC10. 10. encode raises TypeError for non-string inputs, including None, 123, b'abc', and ['a'].
AC11. 11. The requested property decode(encode(x)) == x for every str x is unsatisfiable: criterion 8 yields decode(encode('a1')) == 'a' * 111.
AC12. 12. Preserve decode('a3b1') == 'aaab', decode('') == '', and TypeError for decode(123); existing tests remain unchanged and pass.
AC13. 13. Preserve the public import from rle import encode and leave decode's implementation unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: conflict demonstrated on derived criteria or by an unconstrained witness. Auditor `gpt-6-astra`; consistent=False. The witness tests the specification stage's claim without calling the encode stub. Under the provenance rule, this conflict is held for a human because it cites derived criteria; it does not authorize an authoritative infeasibility termination. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

| Requirements | Claimed conflict | Witness result | Exit | First output line | Operation |
| --- | --- | --- | --- | --- | --- |
| TC5, AC8, AC13 | The required encoding of 'a1' is 'a111', but the unchanged decoder returns 111 copies of 'a', violating universal round-trip equality. | demonstrated on mixed criteria (a model's restatement is involved); held for a human, not infeasible | 3 | CONTRADICTION TC5 AC8 AC13: input 'a1' requires encoding 'a111', but unchanged decode returns 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 01a155a1-cf19-70f7-b7a8-f87749afdf23 |

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
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10215 | 919 | 0 | - | 36.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11988 | 627 | 0 | - | 61.6s | ok |

Model calls: 2 (0 failed, 0 malformed); tokens in/out/cached 22203/1546/0; Inference USD: n/a (development gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a155a0-38f5-77d0-96d0-8a44a61e8192 | SUCCESS | 0 | 0.814s | retained | off | 0.0028726999999999997 |
| witness-1 | 01a155a1-cf19-70f7-b7a8-f87749afdf23 | SUCCESS | 0 | 0.602s | disposable | off | 0.0012308 |

Sandbox operations: 2, total guest duration 1.416s, retained images ['6a43e97f-d82b-4300-a90a-1c5152eb18e4'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

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
