# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: VERIFIED**  
Run `slugkit-regression-001-attest-a1-20261017T151705980000Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T15:17:05.980187+00:00, finished 2026-10-17T15:22:43.882469+00:00.

**Accept this patch.** All 15 sealed tests pass on the candidate in a fresh sandbox, and 12 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 15 of 15 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: static tamper scan: 1 flagged line(s): dynamic code or decoded payload; review the patch before trusting self-reported results; mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite (10 tests) tests the patch structurally

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 15 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
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
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 15 failed on the unmodified base; 15 of 15 pass on the candidate |
| E2 | Mutation check | pass | bound | no mutable sites on the changed lines; the adversarial suite (10 tests) carries the load |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `8c3875f8-20ec-4ac1-9fac-4493503c5039`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `36369c7b57230897` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-freeze-2026-10-17/evaluation-newtasks-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix slugkit/core.py so slugify produces lowercase ASCII slugs by preserving ASCII letters and digits, replacing each maximal run of all other characters with one hyphen, and removing edge hyphens. Inputs containing no ASCII letters or digits must produce an empty string. Preserve the public import, string return type, rejection of non-string inputs, and all existing tests without modifying them.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugkit.slugify | slugify(text) | Accept a str, including str subclasses, and return a str. Retain original ASCII letters A-Z and a-z and digits 0-9, converting A-Z to lowercase. Treat every oth | TypeError when text is not an instance of str; preserve the existing message 'text must be a str'. |

Acceptance criteria:
1. 1. Separator runs collapse: slugify('Hello--World') == 'hello-world', slugify('a -- b') == 'a-b', slugify('one , two ; three') == 'one-two-three', and slugify('x___y') == 'x-y'.
2. 2. Edge separators disappear: slugify('end!') == 'end', slugify('  padded  ') == 'padded', slugify('--both--') == 'both', and slugify('(parens)') == 'parens'.
3. 3. Inputs without ASCII letters or digits return '': verify '', '!!!', '   ', '--', and '日本語'.
4. 4. Existing normal behavior remains: slugify('Hello World') == 'hello-world', slugify('already-a-slug') == 'already-a-slug', slugify('Python 3') == 'python-3', and slugify('MiXeD CaSe 42') == 'mixed-case-42'.
5. 5. Non-ASCII characters separate retained text: slugify('café crème') == 'caf-cr-me'. Original non-ASCII characters are never converted into retained ASCII letters; slugify('K') == '' and slugify('aKb') == 'a-b'.
6. 6. ASCII letters and digits remain in their original order, with uppercase ASCII letters lowercased: slugify('AZaz09') == 'azaz09'.
7. 7. Tabs and line breaks are separators: slugify('\tA\n\r B\t') == 'a-b'.
8. 8. Every successful result is a str and is either empty or matches the entire pattern [a-z0-9]+(?:-[a-z0-9]+)*.
9. 9. None, 3, 2.5, ['a'], and b'bytes' each raise TypeError with message 'text must be a str'. Instances of str subclasses are accepted and follow the same transformation rules.
10. 10. Both existing import paths expose the function, and all existing tests in tests/ pass unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `088e68aa70466ba92df62985e22c8a2f5bcf5ecc332e970d9e4cd9cd811511bd`, 15 test methods, sealed at 2026-10-17T15:18:49.093768+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 15 methods: FAIL 12): 12 of 15 methods failing, 3 passing; operation `01a14a71-b48f-7516-afe6-b359aa339092`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedSlugify.test_accented_characters_are_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_ascii_letters_and_digits_keep_their_order | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_both_public_import_paths_expose_slugify | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_edge_punctuation_disappears | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_edge_whitespace_and_hyphens_disappear | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_existing_normal_examples | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_inputs_without_ascii_alphanumerics_return_empty | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_mixed_separator_runs_collapse | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_non_string_inputs_raise_type_error_with_exact_message | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_repeated_hyphens_collapse | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_string_subclasses_are_accepted | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_successful_results_are_strings_with_slug_shape | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_tabs_and_line_breaks_are_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_underscore_runs_collapse | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedSlugify.test_unicode_lowercasing_does_not_make_characters_eligible | FAIL (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -2,11 +2,11 @@
 
 import re
 
-_NOT_ALNUM = re.compile(r"[^a-z0-9]")
+_NOT_ALNUM = re.compile(r"[^A-Za-z0-9]+")
 
 
 def slugify(text):
-    """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
+    """Return a lowercase ASCII slug, using one hyphen per separator run."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    return _NOT_ALNUM.sub("-", text).strip("-").lower()
```

Static tamper scan of the added lines: 1 flagged line(s): dynamic code or decoded payload (3 added lines checked against 19 patterns; a warning, never a gate).
| File | Line | Pattern | Added line |
| --- | --- | --- | --- |
| slugkit/core.py | 5 | dynamic code or decoded payload | _NOT_ALNUM = re.compile(r"[^A-Za-z0-9]+") |

## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a14a73-98ad-729f-a7ed-38254d896f64`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14a73-b1e7-726c-b80c-ffca0ecd0f2f`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | no mutable sites on the changed lines; the adversarial suite (10 tests) carries the load |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 0 generated, 0 evaluated: 0 killed, 0 survived, 0 unknown; mutation score - (threshold 0.5).

(none)

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `80af91329bff83c5b2725accd1f57915666506f49a02748f89e53022e7da3196`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14a74-b0bb-71f3-b0e3-a37bbce94ca9`. Notes: Targets Unicode characters with ASCII case mappings, non-ASCII digits, controls, individual punctuation, long separator runs, and additional input types.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `re.compile(r"[^A-Za-z0-9]+")` collapses runs of original non-ASCII or other separator characters, and `.sub("-", text).strip("-").lower()` trims edges and lowercases retained ASCII characters while preserving the existing type check. Changes stay within slugkit/core.py, and the observed test output supports the claim that all four existing tests pass; the additional acceptance cases were not explicitly run.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 10457 | 970 | 0 | - | 42.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 10232 | 1459 | 7040 | - | 45.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10219 | 90 | 7168 | - | 19.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 10382 | 476 | 7168 | - | 33.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 10673 | 84 | 7168 | - | 33.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 10861 | 193 | 7168 | - | 27.8s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10385 | 1477 | 0 | - | 58.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 10943 | 138 | 0 | - | 39.1s | ok |

Model calls: 8 (0 failed, 0 malformed); tokens in/out/cached 84152/4887/35712; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14a70-40cf-7013-ae1b-806f423d04bd | SUCCESS | 0 | 0.831s | retained | off | 0.00286766 |
| red-1 | 01a14a71-b48f-7516-afe6-b359aa339092 | SUCCESS | 0 | 3.69s | disposable | off | 0.02993821 |
| impl-tests-3 | 01a14a73-1e61-748a-8cdc-723f02fb1959 | SUCCESS | 0 | 0.745s | disposable | off | 0.0028393299999999997 |
| verify | 01a14a73-98ad-729f-a7ed-38254d896f64 | SUCCESS | 0 | 3.691s | disposable | off | 0.02996836 |
| existing | 01a14a73-b1e7-726c-b80c-ffca0ecd0f2f | SUCCESS | 0 | 1.77s | disposable | off | 0.01202302 |
| breaker-tests | 01a14a74-b0bb-71f3-b0e3-a37bbce94ca9 | SUCCESS | 0 | 2.797s | disposable | off | 0.021772250000000003 |

Sandbox operations: 6, total guest duration 13.524s, retained images ['8c3875f8-20ec-4ac1-9fac-4493503c5039'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
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
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
