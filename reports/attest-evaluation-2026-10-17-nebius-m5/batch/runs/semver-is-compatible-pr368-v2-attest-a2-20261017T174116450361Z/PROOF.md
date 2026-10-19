# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-v2-attest-a2-20261017T174116450361Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:41:16.450776+00:00, finished 2026-10-17T17:50:33.317894+00:00.

**Hold this patch.** Every failing test written after the patch was classified as defective by the arbiter; the corrected tests pass on the candidate and still fail on the unmodified base. Arbitration is advisory, so the hold stands until a human confirms. Defect kinds: wrong expected value.

Key evidence (E6): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests



What to do: Check the arbiter's corrections in E6 (original and corrected tests are both kept). If you agree, accept the patch on that basis or re-run with arbitration in apply mode.

Reasons: adversarial suite binding failed: child process nonzero exit: test_subclass_both_directions exit 1; model-written adversarial tests failed: 1 of 8 (test_breaker.TestIsCompatibleBreaker.test_subclass_both_directions); each failure is a bug or a contract disagreement to resolve
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; arbitration (advisory): all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 14 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 14 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
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
| E1 | Sealed tests, written before the patch | pass | bound | 14 of 14 failed on the unmodified base; 14 of 14 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 7 of 8 pass; 1 failing: test_subclass_both_directions; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `084222db-c912-4bc9-9c2e-c24b8202f9bd`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the `Version` class in `src/semver/version.py`. The method returns True when `other` (the new version) can replace `self` (the old version) under semantic versioning compatibility rules: majors must match; for major > 0, new.minor >= old.minor and prerelease parts must be identical (both None counts as equal), patch is ignored; for major == 0, versions must be identical in major, minor, patch, and prerelease. If `other` is not a `Version` instance (subclasses allowed), raise `TypeError` with message starting with "Expected a Version type but got " followed by the type representation. Include a docstring with at least two doctest examples. Do not modify tests, docs, packaging, or other public behavior; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (the candidate replacement version) is compatible with `self` (the reference version). Compatibility rules: (1) `self.major == other.m | TypeError: raised when `other` is not an instance of `Version` (or a subclass). Message must start with 'Expected a Version type but got ' followed by the type  |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease absent vs present)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease present vs absent)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. The method's docstring contains at least two doctest examples that pass when run with doctest
17. The existing pytest test suite (tests/) passes without modification

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `aef99026c62977345cfe904ee26b06521e35d22e7f1800fc3d53fd6b95dcf1d4`, 14 test methods, sealed at 2026-10-17T17:41:55.912205+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (14 of 14 methods: ERROR 14): 14 of 14 methods failing, 0 passing; operation `01a14af4-b402-727a-a4a1-714b0784429b`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_patch_diff_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_higher_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_lower_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_absent_vs_present_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_diff_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_same_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_version_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_dict_raises | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_list_raises | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_str_raises | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,35 @@
             return False
 
 
+
+    def is_compatible(self, other: 'Version') -> bool:
+        """Return True if `other` (the new version) can replace `self` (the old version) under semantic versioning compatibility rules.
+
+        Majors must match. For major > 0, new.minor >= old.minor and prerelease parts must be identical (both None counts as equal), patch is ignored.
+        For major == 0, versions must be identical in major, minor, patch, and prerelease.
+
+        Examples:
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+        True
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+        True
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        if self.major != other.major:
+            return False
+
+        if self.major == 0:
+            # For major 0, all components must match exactly (except build, which is ignored per spec? but spec says major, minor, patch, prerelease)
+            return (self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+        else:
+            # For major > 0
+            return (other.minor >= self.minor and
+                    self.prerelease == other.prerelease)
+
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (30 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (14 of 14 methods, each in its own process). Operation `01a14afa-bda6-73fa-9ebf-8cc090275de8`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 312 passed in 0.64s (312 passed of 312); operation `01a14afa-e98a-776c-bb1b-a2d4cec83532`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 312 passed in 0.64s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 8 methods: FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f2f09f847a | src/semver/version.py | 715 | remove `not` | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14afa-fbf7-762a-943b-ef046ae386b7 |
| m02-abb2bc151d | src/semver/version.py | 716 | raise -> pass | killed | test_sealed.TestIsCompatible.test_wrong_type_str_raises, test_sealed.TestIsCompatible.test_wrong_type_dict_raises, test_ | 01a14afa-fc3c-767e-a73b-c4abbab79a5a |
| m03-e2749619d9 | src/semver/version.py | 718 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14afa-fc5b-7269-8516-c2cfb176bb8e |
| m04-f1eda0baa9 | src/semver/version.py | 719 | False -> True | killed | test_sealed.TestIsCompatible.test_different_major_false | 01a14afa-fb9a-76a2-b462-d6dacf9481e0 |
| m05-bebad814dd | src/semver/version.py | 721 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.TestIsCompatible.test_patch_lower_true, test_sealed.Tes | 01a14afa-fbe0-7665-81dd-afac5f92300d |
| m06-64e217ea14 | src/semver/version.py | 721 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.TestIsCompatible.test_patch_lower_true, test_sealed.Tes | 01a14afa-fc00-76ab-91f3-9917088c3d9c |
| m07-f886a402f4 | src/semver/version.py | 723 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a14afa-fbe6-739f-9162-e87c564cb9b0 |
| m08-0f0100b0f5 | src/semver/version.py | 724 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true, test_sealed.TestIsCompatible.test_major_zero_patch_diff_fal | 01a14afa-fbfd-751a-9443-041aa75092a5 |
| m09-0f0072cf43 | src/semver/version.py | 725 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a14afb-190b-734a-9835-a029bdeb1742 |
| m10-ca13f1415b | src/semver/version.py | 723 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_patch_diff_false | 01a14afb-1aa2-74c3-8d8c-6d5767ee37e0 |
| m11-ce116c374e | src/semver/version.py | 728 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14afb-1ac4-7651-8929-c139ff44aefb |
| m12-53e78031c7 | src/semver/version.py | 729 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_higher_true, test_sealed.Te | 01a14afb-aebf-7044-8b92-3cb1c0ce7938 |

E3: model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `0d006a691371a4e0f682cc364be3d0c030049a1480601d9906f1f50b826be007`): FAILED (1 of 8 methods: FAIL 1); binding FAILED; operation `01a14afb-e3ae-7116-8b73-0b7c23fc74ea`. Notes: Targeted edge cases: build metadata ignored, complex prerelease equality, mismatched prerelease with minor changes, major=0 prerelease exactness, proper TypeError message prefix, subclass bidirectional compatibility.

| Failing adversarial test | Outcome |
| --- | --- |
| test_subclass_both_directions | FAIL |

### Counterexamples
- E3 `test_subclass_both_directions`: FAIL; AssertionError: False is not true; arbiter: Defective test, by the arbiter; contract basis: Contract: 'Returns True when `other` (the candidate replacement version) is compatible with `self` (the reference version). Compatibility rules: (1) self.major == other.major must hold. (2) If self.major > 0: other.minor >= self.minor and self.prerelease == other.prerelease; patch and build are ignored.'

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the required `is_compatible` method with correct semantics for major 0 and major >0, proper TypeError message, and a docstring containing two doctest examples. The existing pytest suite passes (312 tests), confirming no regression.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; corrected tests pass on the candidate and still fail on the base — candidate not falsified by these tests (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_subclass_both_directions | test_defect | The test expects symmetry: both a.is_compatible(b) and b.is_compatible(a) to be True. However, the contract defines compatibility directiona | Contract: 'Returns True when `other` (the candidate replacement version) is compatible with `self` (the reference version). Compatibility ru |

- `adversarial` corrected re-run: candidate OK (8 of 8 methods, each in its own process); base FAILED (8 of 8 methods: ERROR 8); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1842 | 17408 | 0.026208 | 8.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 20490 | 861 | 0 | 0.006922 | 8.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 2324 | 118 | 0 | 0.000803 | 7.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 8185 | 10461 | 0 | 0.011870 | 56.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 3568 | 139 | 0 | 0.001195 | 10.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3805 | 1488 | 0 | 0.002481 | 9.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 4137 | 16000 | 0 | 0.015641 | 91.4s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5-lowretry | low | 4144 | 1864 | 0 | 0.002921 | 10.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4881 | 3796 | 0 | 0.004881 | 52.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 5668 | 1722 | 0 | 0.003250 | 11.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 6102 | 16000 | 0 | 0.016231 | 86.6s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8-lowretry | low | 6109 | 1004 | 0 | 0.002736 | 6.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 6923 | 167 | 0 | 0.002227 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 6805 | 5814 | 0 | 0.007274 | 30.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 6492 | 99 | 0 | 0.002037 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 7233 | 100 | 0 | 0.002260 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2229 | 1030 | 0 | 0.001596 | 6.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3078 | 2560 | 0 | 0.010758 | 20.3s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | arbitrate | arbitrate-adversarial | default | 3757 | 3804 | 0 | 0.015169 | 13.0s | ok |

Model calls: 19 (2 failed, 2 malformed); tokens in/out/cached 126612/68869/17408; USD: 0.13646.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14af4-4a2a-7443-ad66-b2e979ac84f5 | SUCCESS | 0 | 3.337s | retained | on | 0.02204141 |
| red-1 | 01a14af4-b402-727a-a4a1-714b0784429b | SUCCESS | 0 | 3.813s | disposable | off | 0.031622870000000004 |
| impl-tests-11 | 01a14afa-9d9c-7572-8c7d-94b029fbd941 | SUCCESS | 0 | 1.701s | disposable | off | 0.00956853 |
| verify | 01a14afa-bda6-73fa-9ebf-8cc090275de8 | SUCCESS | 0 | 3.808s | disposable | off | 0.03110585 |
| existing | 01a14afa-e98a-776c-bb1b-a2d4cec83532 | SUCCESS | 0 | 1.723s | disposable | off | 0.00966991 |
| mutant-m01-f2f09f847a | 01a14afa-fbf7-762a-943b-ef046ae386b7 | SUCCESS | 0 | 3.521s | disposable | off | 0.02771258 |
| mutant-m02-abb2bc151d | 01a14afa-fc3c-767e-a73b-c4abbab79a5a | SUCCESS | 0 | 3.519s | disposable | off | 0.027620770000000003 |
| mutant-m03-e2749619d9 | 01a14afa-fc5b-7269-8516-c2cfb176bb8e | SUCCESS | 0 | 3.521s | disposable | off | 0.02784862 |
| mutant-m04-f1eda0baa9 | 01a14afa-fb9a-76a2-b462-d6dacf9481e0 | SUCCESS | 0 | 3.443s | disposable | off | 0.02751692 |
| mutant-m05-bebad814dd | 01a14afa-fbe0-7665-81dd-afac5f92300d | SUCCESS | 0 | 3.54s | disposable | off | 0.02791128 |
| mutant-m06-64e217ea14 | 01a14afa-fc00-76ab-91f3-9917088c3d9c | SUCCESS | 0 | 3.522s | disposable | off | 0.02784511 |
| mutant-m07-f886a402f4 | 01a14afa-fbe6-739f-9162-e87c564cb9b0 | SUCCESS | 0 | 3.522s | disposable | off | 0.02754714 |
| mutant-m08-0f0100b0f5 | 01a14afa-fbfd-751a-9443-041aa75092a5 | SUCCESS | 0 | 3.521s | disposable | off | 0.02783212 |
| mutant-m09-0f0072cf43 | 01a14afb-190b-734a-9835-a029bdeb1742 | SUCCESS | 0 | 3.358s | disposable | off | 0.02760792 |
| mutant-m10-ca13f1415b | 01a14afb-1aa2-74c3-8d8c-6d5767ee37e0 | SUCCESS | 0 | 3.551s | disposable | off | 0.02781103 |
| mutant-m11-ce116c374e | 01a14afb-1ac4-7651-8929-c139ff44aefb | SUCCESS | 0 | 3.562s | disposable | off | 0.028187889999999997 |
| mutant-m12-53e78031c7 | 01a14afb-aebf-7044-8b92-3cb1c0ce7938 | SUCCESS | 0 | 3.444s | disposable | off | 0.027598690000000002 |
| breaker-tests | 01a14afb-e3ae-7116-8b73-0b7c23fc74ea | SUCCESS | 0 | 2.655s | disposable | off | 0.02033798 |
| arbitrate-adversarial-candidate | 01a14afc-8255-7755-95a1-7a4cb1685e53 | SUCCESS | 0 | 2.658s | disposable | off | 0.020365519999999998 |
| arbitrate-adversarial-base | 01a14afc-9f0d-7693-a70d-f7e4d7f28d71 | SUCCESS | 0 | 2.656s | disposable | off | 0.020460779999999998 |

Sandbox operations: 20, total guest duration 64.375s, retained images ['084222db-c912-4bc9-9c2e-c24b8202f9bd'].

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
