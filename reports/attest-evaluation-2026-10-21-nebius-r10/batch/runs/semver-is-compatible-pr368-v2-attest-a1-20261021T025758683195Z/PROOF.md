# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NO CHANGE**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261021T025758683195Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T02:57:58.683884+00:00, finished 2026-10-21T03:05:42.933063+00:00.

**The implementer did not produce a patch.** The implementer used its whole turn budget (12 turn(s)) without finishing and without changing a file. This is an unfinished task, not a judgement that no change was needed and not a repair: there is no candidate, so nothing was verified and nothing was certified.

Key evidence (trajectory): unfinished: the turn budget (12 turns) was exhausted without a patch; the implementer neither finished nor changed a file



What to do: Read the implementer's action trail (the Activity tab) to see where the turns went. Run again with a larger turn budget or a narrower task; a task the model cannot navigate in the budget stays unfinished.

Reasons: unfinished: the turn budget (12 turns) was exhausted without a patch; the implementer neither finished nor changed a file


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 16 of 17 sealed tests fail on the unmodified base; the candidate was never run against them (E1).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 16 of 17 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `36b0461f-0b01-4348-ad69-47e7c8579af2`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other) -> bool` to the Version class in src/semver/version.py. The method returns True when `new` (the argument) can be used in place of `old` (self). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major 0 versions are special: only compatible with an identical version (major, minor, patch, prerelease all equal). If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting with 'Expected a Version type but got' followed by the type. Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging files; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True if `other` is compatible with `self` per semantic versioning compatibility rules. Compatibility is defined as: (1) self.major == other.major; (2) o | TypeError: raised when `other` is not an instance of Version (or a subclass). Message format: 'Expected a Version type but got <class '...'>' (e.g., "Expected a |

Acceptance criteria:
AC1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
AC2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
AC3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, symmetric for patch)
AC4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
AC5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
AC6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires exact match including patch)
AC7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
AC8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
AC9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)
AC10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease absent vs present)
AC11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease present vs absent)
AC12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got'
AC13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got'
AC14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got'
AC15. Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True
AC16. Method docstring contains at least two doctest examples
AC17. Existing pytest test suite (tests/) passes without modification

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract requirements for Version.is_compatible are internally consistent: the major-0 special case explicitly overrides the general 'patch ignored' rule, and all type-checking, subclass, and error-message requirements align. No existing public method in Version creates a round-trip constraint that would conflict with the new method. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `ed0b39f6f5519d8e587caaf6ec28883fae64422060cf18797f9463cfac5d0b54`, 17 test methods, sealed at 2026-10-21T02:58:45.371709+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 17 methods: ERROR 16): 16 of 17 methods failing, 1 passing; operation `01a15c65-95c9-73f1-b366-cbb22297fced`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_ac10_prerelease_absent_vs_present | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac11_prerelease_present_vs_absent | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac12_wrong_type_str | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac13_wrong_type_dict | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac14_wrong_type_list | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac15_subclass_accepted | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac16_docstring_exists | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac17_existing_tests_pass | ok (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac1_self_compat | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac2_patch_up | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac3_patch_down | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac4_prerelease_eq | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac5_major0_identical | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac6_major0_diff_patch | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac7_lower_minor | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac8_different_major | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac9_prerelease_diff | ERROR (1 ev) | - |


## 4. Candidate patch
0 changed path(s); scope check passed; 12 implementer turn(s).

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1462 | 0 | 0.025068 | 6.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 22380 | 1348 | 0 | 0.026424 | 7.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 20607 | 1250 | 0 | 0.007307 | 15.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 3494 | 143 | 0 | 0.001177 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 3593 | 273 | 0 | 0.001324 | 5.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 3831 | 1123 | 0 | 0.002160 | 11.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 4004 | 254 | 0 | 0.001430 | 5.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 4124 | 202 | 0 | 0.001419 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4364 | 264 | 0 | 0.001547 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 4690 | 5341 | 0 | 0.006214 | 41.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 4832 | 15952 | 0 | 0.015806 | 146.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 5025 | 1787 | 0 | 0.003116 | 14.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 5104 | 2914 | 0 | 0.004154 | 22.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 5088 | 7987 | 0 | 0.008715 | 49.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 5176 | 16000 | 0 | 0.015953 | 104.3s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12-lowretry | low | 5183 | 949 | 0 | 0.002409 | 7.4s | ok |

Model calls: 16 (1 failed, 1 malformed); tokens in/out/cached 122177/57249/0; Inference USD: 0.124223.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c65-0888-715b-a41a-d108fcecc6ca | SUCCESS | 0 | 3.238s | retained | on | 0.02193498 |
| red-1 | 01a15c65-95c9-73f1-b366-cbb22297fced | SUCCESS | 0 | 4.537s | disposable | off | 0.03744553 |

Sandbox operations: 2, total guest duration 7.775s, retained images ['36b0461f-0b01-4348-ad69-47e7c8579af2'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
