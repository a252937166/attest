# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261019T044426577842Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:44:26.578656+00:00, finished 2026-10-19T05:00:34.226461+00:00.

**Accept this patch.** All 23 sealed tests pass on the candidate in a fresh sandbox, and 19 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 23 of 23 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 19 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 4 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 19 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bc852347-45d3-492b-9b9f-3f875a576c4f`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-semver/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require equal majors and prerelease values; for nonzero majors permit an equal or higher candidate minor and ignore patch, while major zero requires equal minor and patch as well. Ignore build metadata in all cases, accept Version subclass instances, reject other types with the specified TypeError, and document the method with at least two executable doctest examples. Preserve existing public behavior and restrict implementation changes to src/semver/version.py.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Instance method also available through semver.Version and the existing VersionInfo alias. Accept other positionally or by keyword. For Version instances, includ | TypeError: whenever other is not an instance of Version or a Version subclass, with exact message 'Expected a Version type but got ' followed by str(type(other) |

Acceptance criteria:
AC1. 1. The method is callable through semver.Version, semver.version.Version, and the existing VersionInfo alias, with either a positional other argument or other=; successful calls return True or False as built-in bool values.
AC2. 2. Version(1, 2, 3) is compatible with itself and Version(1, 2, 4); Version(1, 2, 4) is compatible with Version(1, 2, 3).
AC3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) is True, and the reverse call is False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False.
AC4. 4. Different majors always produce False in both directions, including the pairs Version(2, 0, 0)/Version(1, 5, 0) and Version(0, 1, 0)/Version(1, 1, 0).
AC5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True. Equal prereleases also permit a higher candidate minor for nonzero majors.
AC6. 6. Different prerelease values produce False even with an otherwise compatible minor and patch. Verify 'rc.1' versus 'rc.0', case differences, and absent versus present prerelease in both directions.
AC7. 7. Prerelease comparisons use stored values without normalization: None versus None matches, an empty string versus an empty string matches, and None versus an empty string does not match.
AC8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True. Changing only the candidate patch, minor, or prerelease produces False; verify these mismatches in both directions. Version(0, 0, 0) is compatible with itself.
AC9. 9. Build metadata is ignored for both nonzero and zero majors: otherwise matching versions with different builds, or with one build absent, remain compatible. Build differences do not override an incompatible major, minor, patch where relevant, or prerelease.
AC10. 10. An unmodified Version subclass is accepted as either operand, including base-to-subclass, subclass-to-base, and calls between different Version subclasses. The same compatibility rules apply for zero and nonzero majors.
AC11. 11. For receivers with zero and nonzero majors, strings (including valid version strings), bytes, dictionaries, lists, tuples, integers, None, and unrelated objects raise TypeError. For each input, the exact message equals 'Expected a Version type but got ' plus str(type(input)); in particular a string produces "Expected a Version type but got <class 'str'>".
AC12. 12. Successful, incompatible, and invalid-type calls leave all five stored version components of each applicable operand unchanged.
AC13. 13. The method docstring explains directionality, the nonzero-major rule, the major-zero exception, ignored build metadata, accepted argument type, and TypeError behavior. It includes at least two executable compatibility-call doctest examples with expected boolean output, and those examples pass.
AC14. 14. Only src/semver/version.py is changed. Existing public behavior, including comparison, parsing, aliases, constructor normalization, and immutability, remains unchanged, and the entire existing tests/ pytest suite passes without modifying its files.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements can be satisfied by adding only the method and its docstring in src/semver/version.py. The constructor preserves None versus empty prerelease strings, existing exports and aliases expose the same class, and compatibility can compare stored components independently of existing equality and ordering behavior; no code was changed or tests executed. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `e48c44302241600e2befb12b03f60874cdad6ed8c3a9b8bef6f89975f99cc4da`, 23 test methods, sealed at 2026-10-19T04:51:15.272127+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (19 of 23 methods: ERROR 19): 19 of 23 methods failing, 4 passing; operation `01a1527f-d1d0-7356-9cd0-627f02d0e893`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestVersionCompatibility.test_absent_and_present_prereleases_are_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_build_differences_do_not_hide_other_incompatibilities | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_build_metadata_is_ignored_for_both_major_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_different_majors_are_incompatible_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_different_prerelease_values_are_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_equal_prerelease_allows_patch_and_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_existing_comparison_behavior_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_existing_constructor_normalization_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_existing_parsing_behavior_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_existing_readonly_properties_remain_readonly | ok (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_incompatible_call_does_not_mutate_operands | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_invalid_other_types_raise_typeerror_with_exact_message | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_invalid_type_call_does_not_mutate_receiver | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_method_docstring_describes_contract_and_has_two_doctests | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_nonzero_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_nonzero_major_minor_is_directional | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_nonzero_major_self_compatibility | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_prerelease_uses_exact_stored_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_successful_call_does_not_mutate_operands | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_version_subclasses_are_accepted_as_either_operand | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_identical_versions_are_compatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_requires_equal_minor_patch_and_prerelease | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -374,6 +374,33 @@
         build = cls._increment_string(build)
         return cls(self._major, self._minor, self._patch, self._prerelease, build)
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        Compatibility is directional. Both versions must have the same major
+        and exactly equal prerelease values. For a nonzero major, the candidate
+        may have an equal or higher minor; patch values are ignored. For major
+        zero, minor and patch must both match. Build metadata is always ignored.
+
+        ``other`` must be a :class:`Version` instance (subclasses are accepted).
+        A different type raises :class:`TypeError`.
+
+        >>> Version(1, 2, 9).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(1, 3, 0).is_compatible(Version(1, 2, 9))
+        False
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type but got " + str(type(other)))
+
+        if self.major != other.major or self.prerelease != other.prerelease:
+            return False
+        if self.major == 0:
+            return self.minor == other.minor and self.patch == other.patch
+        return other.minor >= self.minor
+
     def compare(self, other: Comparable) -> int:
         """
         Compare self with other.
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (27 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a15285-d5c5-739a-bd94-1a3bda94191c`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 312 passed in 0.63s (312 passed of 312); operation `01a15286-02d4-74ed-8ed0-6ee828e00636`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 312 passed in 0.63s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ae6ff37298 | src/semver/version.py | 395 | remove `not` | killed | test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument, test_sealed.TestVersionCompatibility | 01a15286-1769-7246-9998-a059c0150a86 |
| m02-0393fdabc8 | src/semver/version.py | 396 | Add -> Sub | killed | test_sealed.TestVersionCompatibility.test_invalid_other_types_raise_typeerror_with_exact_message | 01a15286-1731-7235-94da-76ec9229987e |
| m03-3b255390c8 | src/semver/version.py | 396 | raise -> pass | killed | test_sealed.TestVersionCompatibility.test_invalid_other_types_raise_typeerror_with_exact_message, test_sealed.TestVersio | 01a15286-17e0-74fa-aea6-1dd87999305c |
| m04-6bcc205e59 | src/semver/version.py | 398 | NotEq -> Eq | killed | test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument, test_sealed.TestVersionCompatibility | 01a15286-1733-70a2-944d-33ff5443b752 |
| m05-5f41089758 | src/semver/version.py | 398 | NotEq -> Eq | killed | test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument, test_sealed.TestVersionCompatibility | 01a15286-175e-7434-ba7d-798230c4620b |
| m06-6a29d7d579 | src/semver/version.py | 398 | Or -> And | killed | test_sealed.TestVersionCompatibility.test_different_majors_are_incompatible_in_both_directions, test_sealed.TestVersionC | 01a15286-1780-73bf-8571-464510700edb |
| m07-5d29cd421f | src/semver/version.py | 399 | False -> True | killed | test_sealed.TestVersionCompatibility.test_different_majors_are_incompatible_in_both_directions, test_sealed.TestVersionC | 01a15286-1765-760e-85b1-c13edb2b3be2 |
| m08-fb8df84d1d | src/semver/version.py | 400 | 0 -> 1 | killed | test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument, test_sealed.TestVersionCompatibility | 01a15286-17bd-73de-b6d0-25bfe81d98b3 |
| m09-00ddfb2aab | src/semver/version.py | 400 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_public_entry_points_and_keyword_argument, test_sealed.TestVersionCompatibility | 01a15286-46a6-75a5-a620-32d9385d39bc |
| m10-7807bb5eae | src/semver/version.py | 401 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_prerelease_uses_exact_stored_values, test_sealed.TestVersionCompatibility.test | 01a15286-484d-7319-a6dc-bc750799236d |
| m11-22c1cb653a | src/semver/version.py | 401 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_prerelease_uses_exact_stored_values, test_sealed.TestVersionCompatibility.test | 01a15286-4ae7-71ee-93c7-1e16cc0f25b3 |
| m12-befc7b61f3 | src/semver/version.py | 401 | And -> Or | killed | test_sealed.TestVersionCompatibility.test_zero_major_requires_equal_minor_patch_and_prerelease, test_sealed.TestVersionC | 01a15286-4b55-757a-abc7-fa7d672bd380 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `e1c274f92d8c8fc5be4928b0d5157ded35a98b562e2ef1d9cef7b456a698c866`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a15287-5b40-7475-8b12-c0b212469d9d`. Notes: Targets broad compatibility truth tables, exact prerelease and type handling, build invariance, subclass entry points, and operand immutability.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(other, Version)` enforces the exact type error, major/prerelease checks precede the major-zero minor/patch rule, and `return other.minor >= self.minor` implements directional compatibility while ignoring builds. Only src/semver/version.py changes; the docstring supplies three examples, and observed output supports 312 passing existing tests and passing method doctests/focused checks despite two unsuccessful broader doctest attempts.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 28679 | 1283 | 0 | - | 119.1s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 29281 | 130 | 7552 | - | 63.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28388 | 4377 | 7168 | - | 199.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11975 | 108 | 7168 | - | 48.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12565 | 500 | 0 | - | 68.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 12921 | 87 | 7168 | - | 43.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 13738 | 482 | 7168 | - | 29.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 14442 | 465 | 7168 | - | 43.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 15218 | 450 | 7168 | - | 26.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 15467 | 122 | 7168 | - | 90.8s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11188 | 2849 | 7040 | - | 57.3s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11926 | 152 | 0 | - | 68.1s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 205788/11005/64768; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15279-c9b2-7210-82fb-6e328916ab54 | SUCCESS | 0 | 3.348s | retained | on | 0.022346369999999997 |
| red-1 | 01a1527f-d1d0-7356-9cd0-627f02d0e893 | SUCCESS | 0 | 6.336s | disposable | off | 0.05516318 |
| impl-tests-3 | 01a15282-8ae8-728c-b32d-62198a90e968 | SUCCESS | 0 | 1.692s | disposable | off | 0.009549760000000001 |
| impl-python-4 | 01a15283-2a56-76f7-a8a9-7dad28b5008c | SUCCESS | 0 | 0.823s | disposable | off | 0.0035572000000000004 |
| impl-python-5 | 01a15283-e667-7187-aa1a-11c5d3ecb26c | SUCCESS | 0 | 0.801s | disposable | off | 0.00333807 |
| impl-python-6 | 01a15284-6025-74ab-8c32-b98be17d4789 | SUCCESS | 0 | 0.785s | disposable | off | 0.0031791400000000004 |
| verify | 01a15285-d5c5-739a-bd94-1a3bda94191c | SUCCESS | 0 | 6.298s | disposable | off | 0.05485807 |
| existing | 01a15286-02d4-74ed-8ed0-6ee828e00636 | SUCCESS | 0 | 1.648s | disposable | off | 0.009672630000000002 |
| mutant-m01-ae6ff37298 | 01a15286-1769-7246-9998-a059c0150a86 | SUCCESS | 0 | 5.869s | disposable | off | 0.05021318 |
| mutant-m02-0393fdabc8 | 01a15286-1731-7235-94da-76ec9229987e | SUCCESS | 0 | 5.916s | disposable | off | 0.05056698000000001 |
| mutant-m03-3b255390c8 | 01a15286-17e0-74fa-aea6-1dd87999305c | SUCCESS | 0 | 6.038s | disposable | off | 0.05082305000000001 |
| mutant-m05-5f41089758 | 01a15286-175e-7434-ba7d-798230c4620b | SUCCESS | 0 | 6.007s | disposable | off | 0.05071645 |
| mutant-m04-6bcc205e59 | 01a15286-1733-70a2-944d-33ff5443b752 | SUCCESS | 0 | 5.932s | disposable | off | 0.05075777000000001 |
| mutant-m06-6a29d7d579 | 01a15286-1780-73bf-8571-464510700edb | SUCCESS | 0 | 5.936s | disposable | off | 0.0504007 |
| mutant-m07-5d29cd421f | 01a15286-1765-760e-85b1-c13edb2b3be2 | SUCCESS | 0 | 5.823s | disposable | off | 0.04994209000000001 |
| mutant-m08-fb8df84d1d | 01a15286-17bd-73de-b6d0-25bfe81d98b3 | SUCCESS | 0 | 5.944s | disposable | off | 0.050570510000000006 |
| mutant-m09-00ddfb2aab | 01a15286-46a6-75a5-a620-32d9385d39bc | SUCCESS | 0 | 5.788s | disposable | off | 0.050710700000000004 |
| mutant-m10-7807bb5eae | 01a15286-484d-7319-a6dc-bc750799236d | SUCCESS | 0 | 5.999s | disposable | off | 0.05073724 |
| mutant-m11-22c1cb653a | 01a15286-4ae7-71ee-93c7-1e16cc0f25b3 | SUCCESS | 0 | 5.958s | disposable | off | 0.05070020000000001 |
| mutant-m12-befc7b61f3 | 01a15286-4b55-757a-abc7-fa7d672bd380 | SUCCESS | 0 | 5.94s | disposable | off | 0.050578080000000004 |
| breaker-tests | 01a15287-5b40-7475-8b12-c0b212469d9d | SUCCESS | 0 | 2.703s | disposable | off | 0.020591850000000002 |

Sandbox operations: 21, total guest duration 95.584s, retained images ['bc852347-45d3-492b-9b9f-3f875a576c4f'].

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
