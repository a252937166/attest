# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: ERROR**  
Run `slugkit-regression-001-attest-a1-20261019T053141300768Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:31:41.302085+00:00, finished 2026-10-19T05:36:51.634069+00:00.

**This run did not complete.** The sandbox executor failed at stage implement. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): sandbox executor error after 6 model call(s): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 9 of 15 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the sandbox executor at stage implement; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 9 of 15 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage implement: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `72dfb684-4519-400e-866c-28317de69710`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix slugkit/core.py so slugify lowercases its string input, replaces each maximal run of characters outside ASCII a-z and 0-9 with one hyphen, and removes leading and trailing hyphens. Return an empty string when nothing remains, preserve the public import and string return type, continue rejecting non-string inputs with TypeError, and keep all existing tests passing without modifying them.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugkit.slugify | slugify(text) | Accept a str, including str subclasses, and return a str. Apply Python str.lower() first. In the resulting text, retain only ASCII a-z and 0-9; replace each max | TypeError when text is not an instance of str, including None, 3, 2.5, ['a'], and b'bytes'; preserve the existing message 'text must be a str'.; TypeError for m |

Acceptance criteria:
AC1. 1. Separator runs collapse: slugify('Hello--World') == 'hello-world', slugify('a -- b') == 'a-b', slugify('one , two ; three') == 'one-two-three', and slugify('x___y') == 'x-y'.
AC2. 2. Edge separators disappear: slugify('end!') == 'end', slugify('  padded  ') == 'padded', slugify('--both--') == 'both', and slugify('(parens)') == 'parens'.
AC3. 3. Empty or separator-only inputs return '': verify '', '!!!', '   ', '--', and '\t\n'.
AC4. 4. Existing outputs remain unchanged: 'Hello World' becomes 'hello-world', 'already-a-slug' remains 'already-a-slug', 'Python 3' becomes 'python-3', and 'MiXeD CaSe 42' becomes 'mixed-case-42'.
AC5. 5. Non-ASCII characters remaining after lowercasing are separators: slugify('café crème') == 'caf-cr-me', slugify('日本語') == '', and slugify('a１２b') == 'a-b'.
AC6. 6. Lowercasing precedes ASCII classification: slugify('K') == 'k' and slugify('İ') == 'i', following Python str.lower() mappings without additional normalization.
AC7. 7. ASCII letters and digits are preserved in order after lowercasing: slugify('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') == 'abcdefghijklmnopqrstuvwxyz0123456789'.
AC8. 8. Mixed separator types form a single run: slugify('a \t\n_!é--b') == 'a-b'.
AC9. 9. Every successful result is a str and is either empty or consists of nonempty ASCII lowercase alphanumeric groups separated by single hyphens, with no edge hyphens.
AC10. 10. Each of None, 3, 2.5, ['a'], and b'bytes' raises TypeError with message 'text must be a str'; string subclass instances are accepted.
AC11. 11. Both public import paths remain usable, and slugify(text='Hello World') returns 'hello-world'.
AC12. 12. All existing tests in tests/ pass unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only slugkit/core.py: validate the input type, apply str.lower(), collapse runs outside ASCII a-z and 0-9, and strip edge hyphens. This preserves both import paths and satisfies the unchanged tests, including the specified Unicode lowercase behavior. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `761f49ed97899534bbf504c8f274fd8b0418b2619f40d6fb43697427c5669b34`, 15 test methods, sealed at 2026-10-19T05:34:39.693755+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 15 methods: FAIL 9): 9 of 15 methods failing, 6 passing; operation `01a152a7-a0fd-75eb-9b4b-107612800b20`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedSlugify.test_additional_argument_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSealedSlugify.test_ascii_letters_and_digits_preserve_order | ok (1 ev) | - |
| test_sealed.TestSealedSlugify.test_both_public_import_paths_work | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_edge_separators_disappear | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_empty_and_separator_only_inputs | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_existing_outputs | ok (1 ev) | - |
| test_sealed.TestSealedSlugify.test_lowercase_precedes_ascii_classification | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_missing_text_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSealedSlugify.test_mixed_separator_types_form_one_run | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_non_ascii_after_lowercase_is_separator | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_non_string_inputs_raise_type_error_with_existing_message | ok (1 ev) | - |
| test_sealed.TestSealedSlugify.test_separator_runs_collapse | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_string_subclass_is_accepted | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_successful_results_are_strings_with_valid_slug_shape | FAIL (1 ev) | - |
| test_sealed.TestSealedSlugify.test_text_keyword_argument | ok (1 ev) | - |


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
| codex_gateway:gpt-6-astra | spec | spec | low | 10455 | 976 | 7680 | - | 43.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11154 | 115 | 0 | - | 66.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10448 | 1852 | 7168 | - | 55.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10395 | 102 | 7168 | - | 71.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10560 | 283 | 7168 | - | 29.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10855 | 85 | 7168 | - | 26.7s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 63867/3413/36352; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a152a5-05a9-779d-8b8a-2a01a674e77b | SUCCESS | 0 | 0.762s | retained | off | 0.00283383 |
| red-1 | 01a152a7-a0fd-75eb-9b4b-107612800b20 | SUCCESS | 0 | 3.618s | disposable | off | 0.029723029999999998 |
| impl-tests-3 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 3, total guest duration 4.38s, retained images ['72dfb684-4519-400e-866c-28317de69710'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: sandbox executor; stage: implement; model calls 6 (0 failed); sandbox operations 3; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay

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
