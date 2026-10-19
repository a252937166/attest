# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: ERROR**  
Run `slugkit-regression-001-attest-a1-20261017T174609241816Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:46:09.242436+00:00, finished 2026-10-17T17:48:31.999455+00:00.

**This run did not complete.** The sandbox executor failed at stage implement. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): sandbox executor error after 9 model call(s): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 12 of 23 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
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
| E1 | Sealed tests, written before the patch | not run | bound | 12 of 23 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage implement: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ca39f8a9-e363-425e-921e-75fc335fa02d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Fix the regression in slugkit.slugify so that it lowercases the input, replaces each maximal run of non-ASCII-alphanumeric characters (i.e., characters not in a-z or 0-9) with a single hyphen, strips leading and trailing hyphens, and returns an empty string when the input contains no ASCII letters or digits. Non-ASCII letters (e.g., é, 日) are treated as separators. The function must continue to raise TypeError for non-string inputs and return a string. All existing tests in tests/test_basic.py must pass without modification.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| slugify | slugify(text: str) -> str | Returns a lowercase ASCII slug derived from `text`. The algorithm: (1) Convert `text` to lowercase. (2) Replace every maximal contiguous sequence of characters  | TypeError: raised if `text` is not an instance of str (e.g., None, int, float, list, bytes). |

Acceptance criteria:
1. 1. slugify('Hello--World') == 'hello-world' (runs of hyphens collapse to one).
2. 2. slugify('a -- b') == 'a-b' (spaces and hyphens collapse to one hyphen).
3. 3. slugify('one , two ; three') == 'one-two-three' (punctuation and spaces collapse).
4. 4. slugify('x___y') == 'x-y' (underscore runs collapse).
5. 5. slugify('end!') == 'end' (trailing separator removed).
6. 6. slugify('  padded  ') == 'padded' (leading/trailing whitespace removed).
7. 7. slugify('--both--') == 'both' (leading/trailing hyphens removed).
8. 8. slugify('(parens)') == 'parens' (parentheses removed, no leading/trailing hyphen).
9. 9. slugify('') == '' (empty string returns empty).
10. 10. slugify('!!!') == '' (only separators returns empty).
11. 11. slugify('   ') == '' (whitespace-only returns empty).
12. 12. slugify('Hello World') == 'hello-world' (existing basic behavior preserved).
13. 13. slugify('already-a-slug') == 'already-a-slug' (existing slug unchanged).
14. 14. slugify('Python 3') == 'python-3' (digits kept).
15. 15. slugify('MiXeD CaSe 42') == 'mixed-case-42' (mixed case lowercased).
16. 16. slugify('café crème') == 'caf-cr-me' (non-ASCII letters treated as separators).
17. 17. slugify('日本語') == '' (CJK characters are separators, no alphanumerics yields empty).
18. 18. slugify(None) raises TypeError.
19. 19. slugify(3) raises TypeError.
20. 20. slugify(2.5) raises TypeError.
21. 21. slugify(['a']) raises TypeError.
22. 22. slugify(b'bytes') raises TypeError.
23. 23. The return value is always a str instance.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0cc7da7d998e02c318b8b21ac20b08d210d47699329d7f233ba1d69eb249e03a`, 23 test methods, sealed at 2026-10-17T17:46:39.582251+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (12 of 23 methods: FAIL 12): 12 of 23 methods failing, 11 passing; operation `01a14af9-0048-72b8-a036-b1a278a53213`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSlugifyAcceptance.test_already_a_slug_unchanged | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_bytes_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_cjk_characters_yield_empty | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_digits_kept | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_empty_string_returns_empty | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_existing_basic_behavior_preserved | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_float_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_hello_world_hyphens_collapse | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_int_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_leading_trailing_hyphens_removed | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_leading_trailing_whitespace_removed | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_list_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_mixed_case_lowercased | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_non_ascii_letters_as_separators | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_none_raises_type_error | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_only_separators_returns_empty | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_parentheses_removed_no_extra_hyphen | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_punctuation_and_spaces_collapse | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_return_value_is_str | ok (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_spaces_and_hyphens_collapse | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_trailing_separator_removed | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_underscore_runs_collapse | FAIL (1 ev) | - |
| test_sealed.TestSlugifyAcceptance.test_whitespace_only_returns_empty | FAIL (1 ev) | - |

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1393 | 1659 | 0 | 0.006370 | 6.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 1721 | 899 | 0 | 0.001325 | 6.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1699 | 88 | 0 | 0.000589 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1790 | 87 | 0 | 0.000615 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1954 | 2723 | 0 | 0.003037 | 22.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2306 | 2635 | 0 | 0.003063 | 19.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2513 | 2501 | 0 | 0.003005 | 14.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 3303 | 3786 | 0 | 0.004398 | 21.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 4468 | 2138 | 0 | 0.003265 | 11.9s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 21147/16516/0; USD: 0.025667.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14af8-bc39-7057-aff8-92dab1b0389e | SUCCESS | 0 | 0.738s | retained | off | 0.00285278 |
| red-1 | 01a14af9-0048-72b8-a036-b1a278a53213 | SUCCESS | 0 | 5.012s | disposable | off | 0.042728880000000004 |
| impl-tests-4 | 01a14af9-e39b-72b6-94e3-602496159aa4 | SUCCESS | 0 | 0.745s | disposable | off | 0.00285197 |
| impl-python-5 | 01a14afa-2a75-7113-9c12-1fc3b91f449a | SUCCESS | 0 | 0.534s | disposable | off | 0.00119955 |
| impl-python-6 | 01a14afa-8efb-7159-9304-b551acc442bd | SUCCESS | 0 | 0.538s | disposable | off | 0.0012002199999999999 |
| impl-python-7 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 6, total guest duration 7.567s, retained images ['ca39f8a9-e363-425e-921e-75fc335fa02d'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: sandbox executor; stage: implement; model calls 9 (0 failed); sandbox operations 6; committed cost USD 0.025667; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

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
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
