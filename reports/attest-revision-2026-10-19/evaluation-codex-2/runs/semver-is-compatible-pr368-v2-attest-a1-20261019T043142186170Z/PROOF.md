# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: ERROR**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261019T043142186170Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:31:42.187050+00:00, finished 2026-10-19T04:40:39.739531+00:00.

**This run did not complete.** The inference provider failed at stage error. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): inference provider error after 6 model call(s): model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 18 of 21 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the inference provider at stage error; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 18 of 21 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | inference provider failed at stage error: model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not ... |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ca79c07c-b918-417d-a718-5c3142c525ba`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Accept Version instances and subclasses only. For nonzero majors, require equal majors, an equal or higher replacement minor, and exactly equal prerelease values; ignore patch. For major zero, require equal major, minor, patch and prerelease values. Ignore build metadata in all cases. Include at least two executable doctest examples in the method docstring, preserve existing public behavior, and leave all files other than src/semver/version.py unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | An instance method accessible through semver.version.Version, semver.Version and the existing VersionInfo alias, and inherited by subclasses. The required other | TypeError: other is not an instance of Version or any Version subclass. The exact message is f"Expected a Version type but got {type(other)}". Do not parse or c |

Acceptance criteria:
AC1. 1. The method is callable through semver.Version and semver.version.Version, and through the existing VersionInfo alias. Calling with other= produces the same result as a positional argument.
AC2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
AC3. 3. Version(1, 1, 9).is_compatible(Version(1, 2, 0)) returns True; reversing those operands returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
AC4. 4. Unequal majors return False in either direction, including pairs 2.0.0 and 1.5.0, and 0.1.0 and 1.1.0.
AC5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) returns True. Equal prereleases also permit an increased minor when majors are equal and nonzero.
AC6. 6. Different prereleases return False even when the replacement minor increases. In particular, rc.1 versus rc.0, rc.1 versus RC.1, and None versus rc1 are incompatible in both directions.
AC7. 7. Prerelease comparison uses stored values exactly: None versus an empty string returns False, while two empty strings match, subject to the numeric compatibility rules.
AC8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) returns True. Changing only patch, minor, or prerelease returns False in either direction. Identical 0.0.0 versions and identical major-zero prerelease versions return True.
AC9. 9. Build metadata is ignored for both zero and nonzero majors: otherwise compatible operands remain compatible with differing builds or with a build present on only one operand. Build changes cannot make an otherwise incompatible pair compatible.
AC10. 10. For each of 'wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, 1, and the Version class itself, calling is_compatible raises TypeError with exactly 'Expected a Version type but got ' followed by str(type(other)). This holds for both major-zero and nonzero receivers.
AC11. 11. For ordinary subclasses inheriting Version behavior, base-to-subclass, subclass-to-base, and subclass-to-distinct-subclass calls are accepted and follow the same compatibility rules, including major zero. CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) returns True.
AC12. 12. Every successful call returns the actual bool singleton True or False, and both operands retain all five component values after the call.
AC13. 13. The method has a docstring explaining direction, numeric rules, prerelease equality, ignored build metadata, return value and invalid-type error. It contains at least two executable doctest examples invoking the method with expected results; those examples pass.
AC14. 14. Only src/semver/version.py is changed. Existing public behavior, including constructors, parsing, comparisons, aliases, subclass behavior, and immutability, remains unchanged, and the entire existing tests/ pytest suite passes.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements can be satisfied by adding only the method and its docstring in src/semver/version.py. Existing aliases expose the same class, the constructor preserves None versus empty prerelease strings, and direct component comparisons can implement the rules without changing existing comparison or subclass behavior. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `4ef13b2996c780d4f4b9b83eef1205e7db1cce551ccf5a743a96faf28a51287e`, 21 test methods, sealed at 2026-10-19T04:39:59.384453+00:00 by `gpt-6-sol`; attempts: 2.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 21 methods: ERROR 18): 18 of 21 methods failing, 3 passing; operation `01a15275-881e-7133-a9b4-6482538c82b1`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestCompatibility.test_base_and_distinct_subclasses_are_accepted | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_build_metadata_cannot_rescue_incompatible_pairs | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_build_metadata_is_ignored_for_compatible_pairs | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_different_majors_are_incompatible_both_ways | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_equal_prerelease_allows_minor_increase | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_equal_prerelease_allows_patch_change | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_existing_comparison_and_alias_behavior | ok (1 ev) | - |
| test_sealed.TestCompatibility.test_existing_constructor_and_parse_behavior | ok (1 ev) | - |
| test_sealed.TestCompatibility.test_existing_readonly_properties | ok (1 ev) | - |
| test_sealed.TestCompatibility.test_invalid_other_raises_exact_type_error | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_keyword_other_matches_positional_call | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_major_zero_identical_components_are_compatible | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_major_zero_requires_exact_minor_patch_and_prerelease | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_method_docstring_explains_contract_and_contains_examples | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_neither_operand_is_mutated | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_none_and_empty_prerelease_remain_distinct | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_nonzero_major_ignores_patch_in_both_directions | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_nonzero_major_minor_direction | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_public_aliases_expose_method | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_successful_results_are_bool_singletons | ERROR (1 ev) | - |
| test_sealed.TestCompatibility.test_unequal_prereleases_are_incompatible_both_ways | ERROR (1 ev) | - |


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
| codex_gateway:gpt-6-astra | spec | spec | low | 28683 | 1294 | 0 | - | 83.2s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 29291 | 121 | 0 | - | 55.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | - | - | - | - | 266.7s | error |
| codex_gateway:gpt-6-sol | seal | seal-2 | medium | 28404 | 3735 | 0 | - | 70.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11988 | 120 | 7168 | - | 28.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | - | - | - | - | 11.4s | error |

Model calls: 6 (2 failed, 0 malformed); tokens in/out/cached 98366/5270/7168; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1526e-1c64-73cd-b523-c2809aab438f | SUCCESS | 0 | 3.381s | retained | on | 0.02259954 |
| red-2 | 01a15275-881e-7133-a9b4-6482538c82b1 | SUCCESS | 0 | 5.199s | disposable | off | 0.044480570000000004 |

Sandbox operations: 2, total guest duration 8.58s, retained images ['ca79c07c-b918-417d-a718-5c3142c525ba'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion is never overridden. The classification itself remains a model judgement.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 12. E7 Failure record
Component: inference provider; stage: error; model calls 6 (2 failed); sandbox operations 2; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- model provider: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried (outcome uncertain; not retried)

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
