# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: VERIFIED**  
Run `slugkit-regression-001-attest-a2-20261017T175041673933Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:50:41.674131+00:00, finished 2026-10-17T17:52:37.931315+00:00.

**Accept this patch.** All 23 sealed tests pass on the candidate in a fresh sandbox, and 12 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 23 of 23 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3). No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite (8 tests) tests the patch structurally

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 12 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 11 sealed test(s) which already passed on the base say anything about the change (E1).
- That the mutation check tested anything: no mutable sites were found on the changed lines (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 12 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | no mutable sites on the changed lines; the adversarial suite (8 tests) carries the load |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6575d4d5-d1ae-4a4e-b510-a9df88ba2689`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix the slugify function in slugkit/core.py so that it lowercases the input, collapses any maximal run of non-ASCII-alphanumeric characters (i.e., not a-z or 0-9) into a single hyphen, strips leading and trailing hyphens, returns an empty string if no ASCII letters or digits remain, treats non-ASCII letters as separators, raises TypeError for non-string input, and returns a string. The fix must not break the existing tests in tests/test_basic.py.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugify | slugify(text: str) -> str | Convert the input string to a URL-friendly slug: 1) Lowercase the entire string. 2) Replace each maximal contiguous sequence of characters that are not ASCII le | TypeError: raised if the input `text` is not an instance of str (e.g., None, int, float, list, bytes). |

Acceptance criteria:
1. 1. slugify('Hello--World') returns 'hello-world' (runs of separators collapse to one hyphen).
2. 2. slugify('a -- b') returns 'a-b' (spaces and multiple hyphens collapse).
3. 3. slugify('one , two ; three') returns 'one-two-three' (punctuation and spaces collapse).
4. 4. slugify('x___y') returns 'x-y' (underscore runs collapse).
5. 5. slugify('end!') returns 'end' (trailing separator removed).
6. 6. slugify('  padded  ') returns 'padded' (leading/trailing whitespace removed).
7. 7. slugify('--both--') returns 'both' (leading/trailing hyphens removed).
8. 8. slugify('(parens)') returns 'parens' (parentheses removed, no leading/trailing hyphen).
9. 9. slugify('') returns '' (empty input yields empty string).
10. 10. slugify('!!!') returns '' (only separators yields empty string).
11. 11. slugify('   ') returns '' (whitespace-only yields empty string).
12. 12. slugify('Hello World') returns 'hello-world' (existing behavior preserved).
13. 13. slugify('already-a-slug') returns 'already-a-slug' (existing behavior preserved).
14. 14. slugify('Python 3') returns 'python-3' (existing behavior preserved).
15. 15. slugify('MiXeD CaSe 42') returns 'mixed-case-42' (existing behavior preserved).
16. 16. slugify('café crème') returns 'caf-cr-me' (non-ASCII letters are separators).
17. 17. slugify('日本語') returns '' (non-ASCII letters only yields empty string).
18. 18. The result is always a str.
19. 19. TypeError is raised for non-string inputs such as None, 3, 2.5, ['a'], b'bytes'.
20. 20. All existing tests in tests/test_basic.py pass without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `3c562f7e5de8fd6ea9af5e9d3c3fca671450ca113d69f43343bb3cf2474bffc6`, 23 test methods, sealed at 2026-10-17T17:51:10.481835+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 23 methods: FAIL 12): 12 of 23 methods failing, 11 passing; operation `01a14afd-2e3d-75e3-923f-3bc83a4382c6`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSlugifyAcceptance.test_empty_input | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_existing_already_slug | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_existing_hello_world | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_existing_mixed_case | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_existing_python_3 | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_hello_world_double_hyphen | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_leading_trailing_hyphens | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_non_ascii_letters_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_non_ascii_only | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_only_separators | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_padded_whitespace | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_parentheses | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_punctuation_and_spaces | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_result_is_str | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_spaces_and_hyphens | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_trailing_separator | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_type_error_bytes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_type_error_float | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_type_error_int | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_type_error_list | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_type_error_none | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_underscore_runs | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSlugifyAcceptance.test_whitespace_only | FAIL (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -6,7 +6,13 @@
 
 
 def slugify(text):
-    """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
+    """Convert the input string to a URL-friendly slug."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    # Lowercase
+    lowered = text.lower()
+    # Replace any sequence of non-alnum chars with a single hyphen
+    slug = re.sub(r'[^a-z0-9]+', '-', lowered)
+    # Remove leading/trailing hyphens
+    slug = slug.strip('-')
+    return slug
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (8 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a14afe-0233-7248-bb6b-6b6d58efab12`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14afe-2763-75ce-b6f5-b8784eb3e64b`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | no mutable sites on the changed lines; the adversarial suite (8 tests) carries the load |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 0 generated, 0 evaluated: 0 killed, 0 survived, 0 unknown; mutation score - (threshold 0.5).

(none)

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `29eec4508c84dc09d32e5ad848ffcc1ad6392a7bd69f77e2c4a9106ca1b627e1`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a14afe-6a55-76eb-bb95-46be6e42f073`. Notes: Targeted Unicode combining marks, emojis, long strings, null bytes, digit preservation, subclass handling.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff correctly implements the slugify function per the specification, collapsing runs of non-ASCII-alphanumeric characters, stripping hyphens, and handling edge cases. All existing tests pass and the new behavior meets all acceptance criteria.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1393 | 2790 | 0 | 0.009763 | 9.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1695 | 815 | 0 | 0.001242 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1683 | 96 | 0 | 0.000591 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1774 | 100 | 0 | 0.000622 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1939 | 848 | 0 | 0.001345 | 6.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2115 | 1720 | 0 | 0.002182 | 9.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2443 | 108 | 0 | 0.000830 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2650 | 950 | 0 | 0.001650 | 5.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 3344 | 146 | 0 | 0.001135 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 3547 | 121 | 0 | 0.001173 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 1853 | 640 | 0 | 0.001132 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-2 | low | 1925 | 554 | 0 | 0.001076 | 4.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2172 | 2064 | 0 | 0.008364 | 7.0s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 28533/10952/0; USD: 0.031105.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14afc-e43e-7021-99ba-478dddefe826 | SUCCESS | 0 | 0.794s | retained | off | 0.0028533 |
| red-1 | 01a14afd-2e3d-75e3-923f-3bc83a4382c6 | SUCCESS | 0 | 4.999s | disposable | off | 0.04258461 |
| impl-tests-5 | 01a14afd-a9e4-7596-93c5-d608d0adbe79 | SUCCESS | 0 | 0.812s | disposable | off | 0.00281827 |
| impl-python-6 | 01a14afd-ccfd-72f4-b145-d2059297777a | SUCCESS | 0 | 0.598s | disposable | off | 0.0016017100000000001 |
| impl-tests-7 | 01a14afd-e7e8-7204-a6cb-2cd907c69145 | SUCCESS | 0 | 0.751s | disposable | off | 0.00287159 |
| verify | 01a14afe-0233-7248-bb6b-6b6d58efab12 | SUCCESS | 0 | 4.972s | disposable | off | 0.042500500000000004 |
| existing | 01a14afe-2763-75ce-b6f5-b8784eb3e64b | SUCCESS | 0 | 1.747s | disposable | off | 0.01195401 |
| breaker-tests | 01a14afe-6a55-76eb-bb95-46be6e42f073 | SUCCESS | 0 | 2.405s | disposable | off | 0.018338860000000002 |

Sandbox operations: 8, total guest duration 17.078s, retained images ['6575d4d5-d1ae-4a4e-b510-a9df88ba2689'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
