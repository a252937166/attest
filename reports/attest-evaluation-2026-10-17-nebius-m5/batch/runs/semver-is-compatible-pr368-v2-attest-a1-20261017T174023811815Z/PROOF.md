# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261017T174023811815Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:40:23.812253+00:00, finished 2026-10-17T17:43:45.036304+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms. Defect kinds: wrong expected value.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_major_positive_minor_equal_patch_any exit 1; model-written adversarial tests failed: 1 of 7 (test_breaker.TestIsCompatibleBreaker.test_major_positive_minor_equal_patch_any); each failure is a bug or a contract disagreement to resolve
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 15 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 15 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 15 of 15 failed on the unmodified base; 15 of 15 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 6 of 7 pass; 1 failing: test_major_positive_minor_equal_patch_any; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e2b3ebe3-52b2-4041-ac54-aa5409389dcb`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other) -> bool` to the Version class in src/semver/version.py. The method implements semantic version compatibility checking: `old.is_compatible(new)` returns True when `new` can replace `old`. Compatibility requires equal major versions, new.minor >= old.minor, equal prerelease parts (both None counts as equal), and ignores patch. Major 0 versions are special: only compatible with an identical version (major, minor, patch, prerelease all equal). Raise TypeError with message 'Expected a Version type but got <type>' for non-Version arguments (subclasses allowed). Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging files; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True if `other` (the candidate replacement version) is compatible with `self` (the baseline version). Compatibility rules: (1) If self.major == 0: retur | Raise TypeError with message starting with 'Expected a Version type but got ' followed by the type of `other` (e.g., "Expected a Version type but got <class 'st |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, symmetric for patch)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires exact match including patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs None)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (None vs prerelease)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message 'Expected a Version type but got <class 'str'>'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got'
15. Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `77917e26ee8c22cfc764ed4ff29c253852494a8bac69b316fc87e5d72a2217a0`, 15 test methods, sealed at 2026-10-17T17:40:58.784158+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 15 methods: ERROR 15): 15 of 15 methods failing, 0 passing; operation `01a14af3-d69e-71b7-b55b-c2ba1b44a776`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_docstring_exists | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_patch_diff_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_higher_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_lower_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_equal_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_vs_none_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_version_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_dict_raises | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_list_raises | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_str_raises | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,35 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """Return True if `other` is compatible with `self`.
+
+        Compatibility requires equal major versions, new.minor >= old.minor,
+        equal prerelease parts (both None counts as equal), and ignores patch.
+        Major 0 versions are special: only compatible with an identical version
+        (major, minor, patch, prerelease all equal).
+
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+        True
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f'Expected a Version type but got {type(other)}')
+
+        if self.major == 0:
+            return (other.major == 0 and
+                    other.minor == self.minor and
+                    other.patch == self.patch and
+                    other.prerelease == self.prerelease)
+        else:
+            return (other.major == self.major and
+                    other.minor >= self.minor and
+                    other.prerelease == self.prerelease)
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (30 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a14af4-9160-7227-b03e-c4fa54c265e9`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 312 passed in 0.64s (312 passed of 312); operation `01a14af4-ba18-7152-8573-a30061e25170`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 312 passed in 0.64s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 7 methods: ERROR 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-48ba192d58 | src/semver/version.py | 719 | remove `not` | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-d2e4-7001-ae04-64fe3cfb6e20 |
| m02-1b562f25aa | src/semver/version.py | 720 | raise -> pass | killed | test_sealed.TestIsCompatible.test_wrong_type_str_raises, test_sealed.TestIsCompatible.test_wrong_type_dict_raises, test_ | 01a14af4-d23a-70bd-b830-c8e239abeb89 |
| m03-bb58730726 | src/semver/version.py | 722 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-d2d9-7450-86b7-e908c68ada59 |
| m04-efb4abe612 | src/semver/version.py | 722 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-d294-75e8-9fff-0a53619f2614 |
| m05-5185fe76e9 | src/semver/version.py | 723 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a14af4-d2e9-73bb-85a9-3d2c1a6d9f4f |
| m06-65f14109b6 | src/semver/version.py | 723 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a14af4-d2ae-7458-a080-169fde84d4b7 |
| m07-96df62efb7 | src/semver/version.py | 725 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true, test_sealed.TestIsCompatible.test_major_zero_patch_diff_fal | 01a14af4-d2ec-7283-beb8-508bb17b740c |
| m08-f21df192cb | src/semver/version.py | 726 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a14af4-d316-73e5-a11d-ea1c705a0e78 |
| m09-6222a741ec | src/semver/version.py | 723 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_patch_diff_false | 01a14af4-f2d3-7575-882b-384102cd02a7 |
| m10-0ad997984c | src/semver/version.py | 728 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-f910-7332-9b78-9d289e80c20c |
| m11-1bac564c2f | src/semver/version.py | 729 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-faf9-7370-a531-7fa6896da402 |
| m12-7d13a58fd9 | src/semver/version.py | 730 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14af4-faf4-7746-acd0-13287d745dbf |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `51953aafcce845af547968bb0cbe89f2360cd3f8c4dc9409cd2ed1c23508b904`): FAILED (1 of 7 methods: ERROR 1); binding FAILED; operation `01a14af5-c004-76f6-9ccd-353ba927ef5e`. Notes: Added adversarial tests covering edge cases: major zero exactness, patch ignored extremes, large numbers, error message format, subclass behavior, immutability.

| Failing adversarial test | Outcome |
| --- | --- |
| test_major_positive_minor_equal_patch_any | ERROR |

### Counterexamples
- E3 `test_major_positive_minor_equal_patch_any`: ERROR; ValueError: 'patch' is negative. A version can only be positive.; arbiter: Defective test, by the arbiter; contract basis: The Version class in src/semver/version.py validates that major, minor, patch are non-negative integers. The compatibility method's contract only specifies that patch is ignored for compatibility, not that negative patch values are allowed.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the required is_compatible method with correct semantics for major 0 and major > 0 versions, proper TypeError messaging, and a docstring containing four doctest examples. The existing test suite passes without modification, confirming no regression.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_major_positive_minor_equal_patch_any | test_defect | The test attempts to create Version instances with negative patch values (range -5 to 10), but the Version constructor rejects negative patc | The Version class in src/semver/version.py validates that major, minor, patch are non-negative integers. The compatibility method's contract |

- `adversarial` corrected re-run: candidate OK (7 of 7 methods, each in its own process); base FAILED (7 of 7 methods: ERROR 7); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1499 | 0 | 0.025179 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 20460 | 904 | 0 | 0.006952 | 7.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 2310 | 179 | 0 | 0.000854 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 8175 | 3323 | 0 | 0.005443 | 18.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 3271 | 175 | 0 | 0.001139 | 3.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 4243 | 108 | 0 | 0.001370 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2204 | 1283 | 0 | 0.001816 | 8.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2551 | 3505 | 0 | 0.013066 | 17.0s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 4205 | 3531 | 0 | 0.014798 | 11.7s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 68101/14507/0; USD: 0.070617.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14af3-77bf-7245-9b06-f49e49c8f646 | SUCCESS | 0 | 3.37s | retained | on | 0.02218339 |
| red-1 | 01a14af3-d69e-71b7-b55b-c2ba1b44a776 | SUCCESS | 0 | 4.082s | disposable | off | 0.03335425 |
| impl-tests-3 | 01a14af4-6fc1-75f5-8305-85d769486b9b | SUCCESS | 0 | 1.677s | disposable | off | 0.00953977 |
| verify | 01a14af4-9160-7227-b03e-c4fa54c265e9 | SUCCESS | 0 | 3.986s | disposable | off | 0.033015060000000006 |
| existing | 01a14af4-ba18-7152-8573-a30061e25170 | SUCCESS | 0 | 1.807s | disposable | off | 0.009792839999999999 |
| mutant-m01-48ba192d58 | 01a14af4-d2e4-7001-ae04-64fe3cfb6e20 | SUCCESS | 0 | 3.743s | disposable | off | 0.02939121 |
| mutant-m03-bb58730726 | 01a14af4-d2d9-7450-86b7-e908c68ada59 | SUCCESS | 0 | 3.735s | disposable | off | 0.02957252 |
| mutant-m02-1b562f25aa | 01a14af4-d23a-70bd-b830-c8e239abeb89 | SUCCESS | 0 | 3.744s | disposable | off | 0.029536249999999997 |
| mutant-m04-efb4abe612 | 01a14af4-d294-75e8-9fff-0a53619f2614 | SUCCESS | 0 | 3.736s | disposable | off | 0.02937698 |
| mutant-m06-65f14109b6 | 01a14af4-d2ae-7458-a080-169fde84d4b7 | SUCCESS | 0 | 3.732s | disposable | off | 0.02970657 |
| mutant-m07-96df62efb7 | 01a14af4-d2ec-7283-beb8-508bb17b740c | SUCCESS | 0 | 3.743s | disposable | off | 0.02949106 |
| mutant-m05-5185fe76e9 | 01a14af4-d2e9-73bb-85a9-3d2c1a6d9f4f | SUCCESS | 0 | 3.733s | disposable | off | 0.029285989999999998 |
| mutant-m08-f21df192cb | 01a14af4-d316-73e5-a11d-ea1c705a0e78 | SUCCESS | 0 | 3.734s | disposable | off | 0.029712679999999998 |
| mutant-m09-6222a741ec | 01a14af4-f2d3-7575-882b-384102cd02a7 | SUCCESS | 0 | 3.635s | disposable | off | 0.029398070000000002 |
| mutant-m10-0ad997984c | 01a14af4-f910-7332-9b78-9d289e80c20c | SUCCESS | 0 | 3.715s | disposable | off | 0.029949200000000002 |
| mutant-m11-1bac564c2f | 01a14af4-faf9-7370-a531-7fa6896da402 | SUCCESS | 0 | 3.726s | disposable | off | 0.02966607 |
| mutant-m12-7d13a58fd9 | 01a14af4-faf4-7746-acd0-13287d745dbf | SUCCESS | 0 | 3.725s | disposable | off | 0.029672030000000002 |
| breaker-tests | 01a14af5-c004-76f6-9ccd-353ba927ef5e | SUCCESS | 0 | 2.467s | disposable | off | 0.018628079999999998 |
| arbitrate-adversarial-candidate | 01a14af6-4763-7491-aed6-39062196471c | SUCCESS | 0 | 2.489s | disposable | off | 0.018609419999999998 |
| arbitrate-adversarial-base | 01a14af6-5e5e-70a8-9be9-e3d4967e2671 | SUCCESS | 0 | 2.456s | disposable | off | 0.01857395 |

Sandbox operations: 20, total guest duration 67.035s, retained images ['e2b3ebe3-52b2-4041-ac54-aa5409389dcb'].

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
