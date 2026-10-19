# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: VERIFIED**  
Run `slugkit-regression-001-attest-a1-20261019T054052323841Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:40:52.325115+00:00, finished 2026-10-19T05:50:50.782268+00:00.

**Accept this patch.** All 12 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 12 of 12 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite (9 tests) tests the patch structurally

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 12 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 3 sealed test(s) which already passed on the base say anything about the change (E1).
- That the mutation check tested anything: no mutable sites were found on the changed lines (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 12 failed on the unmodified base; 12 of 12 pass on the candidate |
| E2 | Mutation check | pass | bound | no mutable sites on the changed lines; the adversarial suite (9 tests) carries the load |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `9fca4148-18cd-4da1-9c53-67df1c4725b4`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-slugkit/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix slugkit/core.py so slugify converts ASCII uppercase letters to lowercase, preserves ASCII letters and digits, replaces each maximal run of all other characters with one hyphen, and removes edge hyphens. Inputs containing no ASCII letters or digits must return an empty string. Preserve the public import, string return type, non-string TypeError behavior, and all existing tests without modifying them.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugkit.slugify | slugify(text) | Accept a str, including str subclasses, and return a str. Retain original ASCII letters A-Z and a-z and ASCII digits 0-9, converting A-Z to a-z. Treat every oth | TypeError: text is not an instance of str; preserve the existing message 'text must be a str'. |

Acceptance criteria:
AC1. 1. Separator runs collapse: 'Hello--World' returns 'hello-world'; 'a -- b' returns 'a-b'; 'one , two ; three' returns 'one-two-three'; 'x___y' returns 'x-y'.
AC2. 2. Edge separators disappear: 'end!' returns 'end'; '  padded  ' returns 'padded'; '--both--' returns 'both'; '(parens)' returns 'parens'.
AC3. 3. Inputs '', '!!!', '   ', and '--__\t\n' each return ''.
AC4. 4. Existing normal behavior is preserved: 'Hello World' returns 'hello-world'; 'already-a-slug' returns 'already-a-slug'; 'Python 3' returns 'python-3'; 'MiXeD CaSe 42' returns 'mixed-case-42'.
AC5. 5. Non-ASCII characters are separators: 'café crème' returns 'caf-cr-me'; '日本語' returns ''; 'aé日b' returns 'a-b'; non-ASCII digits such as '１２٣' return ''.
AC6. 6. Non-ASCII characters are not converted into retained ASCII letters through Unicode casing: 'K' returns ''; 'İ' returns ''; 'aKb' returns 'a-b'.
AC7. 7. ASCII letters and digits are retained in order with only ASCII uppercase letters lowercased: 'AZaz019' returns 'azaz019'.
AC8. 8. Every successful result is a str and is either empty or consists of nonempty lowercase ASCII alphanumeric groups separated by single hyphens.
AC9. 9. None, 3, 2.5, ['a'], and b'bytes' each raise TypeError with message 'text must be a str'.
AC10. 10. A str subclass instance containing 'Hello--World' is accepted and produces 'hello-world'.
AC11. 11. Both public import paths continue to expose slugify(text), supporting positional and text keyword arguments.
AC12. 12. All existing tests in tests/ pass unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only slugkit/core.py: classify original characters by ASCII eligibility, lowercase retained ASCII uppercase letters, collapse separator runs, and trim edge hyphens. This preserves the existing exports, signature, TypeError behavior, str-subclass acceptance, and all supplied tests. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `93b02d8243494c4ffc88f3c68b3f1856f2058de2c17963a553c34d3e1f21bc12`, 12 test methods, sealed at 2026-10-19T05:44:18.494424+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 12 methods: FAIL 9): 9 of 12 methods failing, 3 passing; operation `01a152b0-762e-70ca-adc0-7059bbbcdc1e`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSlugifyAcceptance.test_ascii_letters_and_digits_keep_their_order | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_core_import_accepts_positional_and_text_keyword_arguments | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_edge_separators_disappear | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_existing_normal_cases | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_inputs_without_ascii_alphanumerics_return_empty | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_non_ascii_characters_are_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_non_string_inputs_raise_typeerror_with_existing_message | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_package_import_accepts_positional_and_text_keyword_arguments | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_results_are_strings_with_valid_slug_shape | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_separator_runs_collapse_to_one_hyphen | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_string_subclass_is_accepted | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_unicode_casing_does_not_make_non_ascii_characters_eligible | FAIL (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -2,11 +2,11 @@
 
 import re
 
-_NOT_ALNUM = re.compile(r"[^a-z0-9]")
+_NOT_ALNUM = re.compile(r"[^A-Za-z0-9]+")
 
 
 def slugify(text):
     """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    return _NOT_ALNUM.sub("-", text).strip("-").lower()
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (2 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| slugkit/core.py | 5 | dynamic code or decoded payload | _NOT_ALNUM = re.compile(r"[^A-Za-z0-9]+") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (12 of 12 methods, each in its own process). Operation `01a152b4-ce09-734c-9142-faec0caf89bd`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a152b4-e601-71e6-aea9-1a71586f1c46`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | no mutable sites on the changed lines; the adversarial suite (9 tests) carries the load |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 0 generated, 0 evaluated: 0 killed, 0 survived, 0 unknown; mutation score - (threshold 0.5).

(none)

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `5cfef9548dc75f71dfe0614ce5e157333bd50b5589f4f2b14f4192c6cccecbad`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a152b5-f42b-70b6-9c92-4796ee8c5e48`. Notes: Targets ASCII boundaries, Unicode case and number traps, unusual separators, long runs, idempotence, type errors, and str subclasses.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `re.compile(r"[^A-Za-z0-9]+")` collapses runs based on original ASCII eligibility, and `.sub("-", text).strip("-").lower()` removes edge separators and lowercases retained letters while preserving the signature and TypeError behavior. Only slugkit/core.py changes; observed output supports all 4 existing tests passing and reports targeted edge checks passing, although their script is not shown.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 10455 | 990 | 0 | - | 47.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 11090 | 113 | 0 | - | 85.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10389 | 2191 | 7168 | - | 59.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10338 | 98 | 7168 | - | 83.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10500 | 443 | 7168 | - | 54.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10791 | 82 | 7168 | - | 45.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10981 | 468 | 7168 | - | 51.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11415 | 174 | 7168 | - | 36.4s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10391 | 1842 | 0 | - | 63.0s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10961 | 149 | 7552 | - | 32.1s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 107311/6550/50560; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a152ad-6eb7-74ac-a2ad-ddf21f746687 | SUCCESS | 0 | 0.778s | retained | off | 0.00284973 |
| red-1 | 01a152b0-762e-70ca-adc0-7059bbbcdc1e | SUCCESS | 0 | 3.177s | disposable | off | 0.02498979 |
| impl-tests-3 | 01a152b3-5964-7126-9aba-665dc740f59e | SUCCESS | 0 | 0.756s | disposable | off | 0.0028505099999999997 |
| impl-python-4 | 01a152b4-32da-71f8-8469-8452f3716ef1 | SUCCESS | 0 | 0.624s | disposable | off | 0.00162138 |
| verify | 01a152b4-ce09-734c-9142-faec0caf89bd | SUCCESS | 0 | 3.2s | disposable | off | 0.02509011 |
| existing | 01a152b4-e601-71e6-aea9-1a71586f1c46 | SUCCESS | 0 | 1.778s | disposable | off | 0.011993589999999998 |
| breaker-tests | 01a152b5-f42b-70b6-9c92-4796ee8c5e48 | SUCCESS | 0 | 2.61s | disposable | off | 0.02010578 |

Sandbox operations: 7, total guest duration 12.923s, retained images ['9fca4148-18cd-4da1-9c53-67df1c4725b4'].

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
