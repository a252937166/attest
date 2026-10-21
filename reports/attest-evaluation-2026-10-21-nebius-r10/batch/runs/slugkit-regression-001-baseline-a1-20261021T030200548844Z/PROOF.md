# Attest Proof Bundle: Regression: slugify keeps separator runs and edge hyphens

**Verdict: BASELINE**  
Run `slugkit-regression-001-baseline-a1-20261021T030200548844Z` · profile `eval-baseline-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:02:00.549464+00:00, finished 2026-10-21T03:04:10.843891+00:00.

**Baseline run: no verification.** This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, and the candidate was judged only by the harness. It certifies nothing.

Key evidence (trajectory): candidate produced for the independent judge; no gates recorded



What to do: Compare with the Attest run of the same task in the evaluation report.

Reasons: all gates passed


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
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `slugkit-regression-001`, spec digest `a3f86579452e1665bb1b8e00e0a8c1a47f4408175e57f59bf6ab33a6265141f9`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `49fe2a8c-0825-4ad0-a5ea-8f20685ad8fb`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

## 2. Specification and contract
Feasible: True. Regression report for slugkit.slugify(text). Since the last change the function returns 'hello--world' for 'Hello--World', 'a---b' for 'a -- b' and 'end-' for 'end!'. The intended behaviour, which the existing tests only partly cover, is: lower-case the text; every maximal run of one or more characters that are not ASCII letters a-z or ASCII digits 0-9 becomes exactly one hyphen; leading and trailing hyphens are removed; an input with no ASCII letters or digits (including the empty string and whitespace-only text) returns ''. Non-ASCII letters such as 'é' are separators, not kept characters (so 'café crème' is 'caf-cr-me'). Keep raising TypeError for non-string input, keep returning a str, and keep the existing tests in tests/ passing without modifying them. Fix the regression in slugkit/core.py.

(none)

Acceptance criteria:
AC1. slugify('Hello--World') == 'hello-world', slugify('a -- b') == 'a-b', slugify('one , two ; three') == 'one-two-three', slugify('x___y') == 'x-y' (runs of separators collapse to one hyphen).
AC2. slugify('end!') == 'end', slugify('  padded  ') == 'padded', slugify('--both--') == 'both', slugify('(parens)') == 'parens' (no leading or trailing hyphen).
AC3. slugify('') == '', slugify('!!!') == '', slugify('   ') == '' (nothing to keep gives the empty string).
AC4. Existing behaviour is preserved: slugify('Hello World') == 'hello-world', slugify('already-a-slug') == 'already-a-slug', slugify('Python 3') == 'python-3', slugify('MiXeD CaSe 42') == 'mixed-case-42'.
AC5. Non-ASCII letters are separators: slugify('café crème') == 'caf-cr-me' and slugify('日本語') == ''.
AC6. The result is a str; TypeError for non-string input such as None, 3, 2.5, ['a'] and b'bytes'.

## 2b. Contract audit (executed witnesses)
Not run (bundle predates the contract audit, or the run ended before the specification).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


## 4. Candidate patch
1 changed path(s); scope check passed; 13 implementer turn(s).

```diff
--- a/slugkit/core.py
+++ b/slugkit/core.py
@@ -2,11 +2,14 @@
 
 import re
 
-_NOT_ALNUM = re.compile(r"[^a-z0-9]")
+_NOT_ALNUM = re.compile(r"[^a-z0-9]+")
 
 
 def slugify(text):
     """Lower-case ASCII slug of `text`: letters and digits are kept, everything else becomes a hyphen."""
     if not isinstance(text, str):
         raise TypeError("text must be a str")
-    return _NOT_ALNUM.sub("-", text.lower())
+    # Replace any sequence of non-alnum with a single hyphen and strip leading/trailing hyphens
+    slug = _NOT_ALNUM.sub("-", text.lower())
+    slug = slug.strip('-')
+    return slug
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1423 | 88 | 0 | 0.000506 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1509 | 145 | 0 | 0.000583 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1684 | 2196 | 0 | 0.002482 | 17.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1914 | 2123 | 0 | 0.002485 | 15.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2169 | 102 | 0 | 0.000742 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2371 | 815 | 0 | 0.001445 | 6.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 2561 | 559 | 0 | 0.001271 | 4.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 2773 | 1172 | 0 | 0.001887 | 10.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 3039 | 5319 | 0 | 0.005699 | 31.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 3340 | 601 | 0 | 0.001543 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 3348 | 188 | 0 | 0.001174 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 3380 | 1132 | 0 | 0.002033 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | medium | 3618 | 191 | 0 | 0.001257 | 3.4s | ok |

Model calls: 13 (0 failed, 0 malformed); tokens in/out/cached 33129/14631/0; Inference USD: 0.023107.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c68-b793-7736-a147-d7efdfb3f61d | SUCCESS | 0 | 0.786s | retained | off | 0.0029004 |
| impl-tests-5 | 01a15c69-647c-71eb-b4c2-8f1320b25756 | SUCCESS | 0 | 0.839s | disposable | off | 0.00291125 |
| impl-tests-11 | 01a15c6a-624f-73e4-8377-1a59fc1bbe95 | SUCCESS | 0 | 0.8s | disposable | off | 0.00288377 |
| impl-python-12 | 01a15c6a-8bc3-71d8-a5dd-bb24c561b6e0 | SUCCESS | 0 | 0.644s | disposable | off | 0.00166786 |

Sandbox operations: 4, total guest duration 3.069s, retained images ['49fe2a8c-0825-4ad0-a5ea-8f20685ad8fb'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
