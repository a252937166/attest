# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261019T052252822448Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:22:52.823581+00:00, finished 2026-10-19T05:31:50.114389+00:00.

**Accept this patch.** All 29 sealed tests pass on the candidate in a fresh sandbox, and 23 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 29 of 29 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 29 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 23 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 6 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 23 of 29 failed on the unmodified base; 29 of 29 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `73102021-ca14-48af-b567-ff1376963aff`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require equal majors and exactly equal prerelease values; for positive majors allow equal or higher candidate minors and ignore patches, while major zero requires equal minor and patch values as well. Ignore build metadata in all cases. Accept Version subclasses, reject all other argument types with the specified TypeError, and document the method with at least two executable doctest examples while preserving existing behavior and leaving all other files unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Instance method available through semver.version.Version, semver.Version, and the existing VersionInfo aliases. The required other argument may be positional or | TypeError when other is not an instance of Version or a subclass, with the exact message formed by 'Expected a Version type but got ' followed by str(type(other |

Acceptance criteria:
AC1. 1. The method is callable through semver.Version and semver.version.Version, and through the existing VersionInfo aliases without changing their identity. Positional other and keyword other produce the same result.
AC2. 2. Version(1, 2, 3) is compatible with itself and Version(1, 2, 4); Version(1, 2, 4) is compatible with Version(1, 2, 3). Each result is True, demonstrating that positive-major patches are ignored in both directions.
AC3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) is True, while the reverse call is False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False.
AC4. 4. Different majors always return False, including 1 versus 2 and 0 versus 1, in both directions regardless of minor, patch, or prerelease.
AC5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True. Equal prereleases also permit increasing minor versions for positive majors.
AC6. 6. Prerelease differences return False even when all numeric conditions pass: 'rc.1' versus 'rc.0', 'RC.0' versus 'rc.0', and absent versus 'rc1' in either direction. Stored None and empty-string prereleases are distinct; two empty-string prereleases are equal.
AC7. 7. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True. Changing only the patch, minor, or prerelease returns False in both directions. Version(0, 0, 0) is compatible with itself, and equal major-zero versions carrying the same prerelease are compatible.
AC8. 8. Build-only differences do not affect compatibility for either positive-major or major-zero versions. Equal relevant fields with build=None versus build='build.1', or two different build strings, return True; build metadata cannot make otherwise incompatible versions compatible.
AC9. 9. For each of 'wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, and 1, the method raises TypeError with exactly 'Expected a Version type but got ' + str(type(other)). Verify rejection for both positive-major and major-zero receivers.
AC10. 10. For an ordinary subclass CustomVersion(Version), equal versions return True for subclass receiver/base candidate, base receiver/subclass candidate, and subclass receiver/subclass candidate, including major zero. Distinct ordinary subclasses are accepted and follow the same field rules.
AC11. 11. Successful and unsuccessful compatibility checks leave both operands' five version fields unchanged; invalid-argument calls leave the receiver unchanged.
AC12. 12. The method has a docstring describing directionality, compatibility rules, ignored build metadata, and TypeError behavior, with at least two executable compatibility-call doctest examples and correct expected outputs.
AC13. 13. Only src/semver/version.py is modified. The entire existing tests/ pytest suite continues to pass in the project's test environment, and existing parsing, comparison, equality, hashing, immutability, subclass, deprecated API, and CLI behavior is preserved.
AC14. 14. The addition remains compatible with the repository's Python 3.7 minimum and introduces no dependencies.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract can be satisfied by adding only the documented method in src/semver/version.py, using isinstance(other, Version) and direct field comparisons. Existing aliases expose the method automatically, and the constructor preserves the required distinction between None and empty-string prereleases without changing existing comparison behavior. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `c275f90f1957e14ad0c335498298eea8d7813ebf09532831ff6531ceb7ad9dc8`, 29 test methods, sealed at 2026-10-19T05:27:01.822079+00:00 by `gpt-6-sol`; attempts: 2.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (23 of 29 methods: ERROR 23): 23 of 29 methods failing, 6 passing; operation `01a152a0-8fb0-77aa-927d-d4728bd8b21d`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.CompatibilityAcceptanceTests.test_base_and_subclass_instances_interoperate | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_build_metadata_cannot_override_incompatibility | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_distinct_subclasses_follow_the_same_field_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_docstring_contains_two_compatibility_call_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_docstring_describes_contract | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_cli_compare_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_comparison_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_deprecated_compare_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_hash_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_parse_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_readonly_property_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_invalid_argument_preserves_receiver | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_accepts_equal_fields | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_ignores_build_metadata | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_requires_equal_minor_and_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_requires_equal_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_matching_prerelease_allows_patch_and_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_non_version_arguments_raise_exact_typeerror | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_none_and_empty_prerelease_are_distinct | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positional_and_keyword_other_agree | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_accepts_higher_minor | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_ignores_build_metadata | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_rejects_lower_minor | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_prerelease_values_must_match_exactly | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_public_aliases_keep_their_identity | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_python_argument_binding_rejects_missing_extra_and_unknown_arguments | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_successful_and_unsuccessful_checks_preserve_both_operands | ERROR (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -422,6 +422,29 @@
 
         return rccmp
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether *other* can replace this version.
+
+        Majors and prerelease values must match exactly. For a positive major,
+        the candidate's minor must be at least this version's minor; patches
+        are ignored. For major zero, minors and patches must also match.
+        Build metadata is ignored in all cases. A non-Version *other* raises
+        TypeError.
+
+        >>> Version(1, 2, 9).is_compatible(Version(1, 3, 0))
+        True
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
     def next_version(self, part: str, prerelease_token: str = "rc") -> "Version":
         """
         Determines next version, preserving natural order.
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (23 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (29 of 29 methods, each in its own process). Operation `01a152a2-c21e-773c-aa50-a162e5962983`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 312 passed in 0.64s (312 passed of 312); operation `01a152a2-f029-70b7-9b65-a4a096d834bd`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 312 passed in 0.64s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-6d0ea11345 | src/semver/version.py | 439 | remove `not` | killed | test_sealed.CompatibilityAcceptanceTests.test_public_aliases_keep_their_identity, test_sealed.CompatibilityAcceptanceTes | 01a152a3-0aaa-733d-b7a7-8efdb99a33be |
| m02-e3a556c1bd | src/semver/version.py | 440 | Add -> Sub | killed | test_sealed.CompatibilityAcceptanceTests.test_non_version_arguments_raise_exact_typeerror | 01a152a3-0acc-7140-82e1-07c6fb16686c |
| m03-41894bb791 | src/semver/version.py | 440 | raise -> pass | killed | test_sealed.CompatibilityAcceptanceTests.test_non_version_arguments_raise_exact_typeerror, test_sealed.CompatibilityAcce | 01a152a3-0b0a-74d5-805e-0fc413a3f894 |
| m04-fcd90efeab | src/semver/version.py | 442 | NotEq -> Eq | killed | test_sealed.CompatibilityAcceptanceTests.test_public_aliases_keep_their_identity, test_sealed.CompatibilityAcceptanceTes | 01a152a3-0a5b-7755-84d9-8c93d1990dec |
| m05-c8cdd8cb35 | src/semver/version.py | 442 | NotEq -> Eq | killed | test_sealed.CompatibilityAcceptanceTests.test_public_aliases_keep_their_identity, test_sealed.CompatibilityAcceptanceTes | 01a152a3-0a7b-7762-a232-dc66a7623c17 |
| m06-2abaf08eeb | src/semver/version.py | 442 | Or -> And | killed | test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible_in_both_directions, test_sealed.Compatib | 01a152a3-0ade-72f4-8efc-bc99f59f5fd6 |
| m07-2b5f2ad8af | src/semver/version.py | 443 | False -> True | killed | test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible_in_both_directions, test_sealed.Compatib | 01a152a3-0aa7-7642-b9e2-72296a46b0b7 |
| m08-82c0a39451 | src/semver/version.py | 444 | 0 -> 1 | killed | test_sealed.CompatibilityAcceptanceTests.test_positional_and_keyword_other_agree, test_sealed.CompatibilityAcceptanceTes | 01a152a3-0ada-7586-ab8b-7e6723437325 |
| m09-9d03230cf9 | src/semver/version.py | 444 | Eq -> NotEq | killed | test_sealed.CompatibilityAcceptanceTests.test_positional_and_keyword_other_agree, test_sealed.CompatibilityAcceptanceTes | 01a152a3-39cf-7176-918b-f1fb5d54eab1 |
| m10-d01c296f7c | src/semver/version.py | 445 | Eq -> NotEq | killed | test_sealed.CompatibilityAcceptanceTests.test_major_zero_accepts_equal_fields, test_sealed.CompatibilityAcceptanceTests. | 01a152a3-3a19-70f1-a4c0-9100b38b1073 |
| m11-8c4bc824fc | src/semver/version.py | 445 | Eq -> NotEq | killed | test_sealed.CompatibilityAcceptanceTests.test_major_zero_accepts_equal_fields, test_sealed.CompatibilityAcceptanceTests. | 01a152a3-3a7c-70ea-8119-e897613cf663 |
| m12-975c1af02b | src/semver/version.py | 445 | And -> Or | killed | test_sealed.CompatibilityAcceptanceTests.test_major_zero_requires_equal_minor_and_patch, test_sealed.CompatibilityAccept | 01a152a3-3c46-73ca-81e7-1690e68a6ee7 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `dced9753c7851940bb3e1eeaff41f7cd9022ebd2d0e14c55ceb327cf46f50cb4`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a152a4-a5af-7381-95a2-94df719706c3`. Notes: Targets large numeric boundaries, exact prerelease values, directional decisions with build changes, aliases and subclasses, additional invalid types, and operand preservation.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(other, Version)` accepts subclasses and enforces the exact TypeError message, the major/prerelease guard and minor/patch checks implement the directional rules, and build metadata is never compared. Only src/semver/version.py changes, the docstring includes two correct doctests, and the observed test output supports the claim that all 312 existing tests passed.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 28679 | 1269 | 7680 | - | 52.0s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 29267 | 111 | 7552 | - | 68.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | - | - | - | - | 10.9s | error |
| codex_gateway:gpt-6-sol | seal | seal-2 | medium | 28400 | 5437 | 7168 | - | 92.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11966 | 101 | 0 | - | 24.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12551 | 477 | 7168 | - | 34.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 12879 | 116 | 7168 | - | 36.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 13704 | 175 | 7168 | - | 30.8s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11152 | 2609 | 7040 | - | 80.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11657 | 139 | 0 | - | 25.7s | ok |

Model calls: 10 (1 failed, 0 malformed); tokens in/out/cached 160255/10434/50944; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1529c-f711-7621-86b4-57d355a09bf3 | SUCCESS | 0 | 4.157s | retained | on | 0.022168959999999998 |
| red-2 | 01a152a0-8fb0-77aa-927d-d4728bd8b21d | SUCCESS | 0 | 7.625s | disposable | off | 0.06772657000000001 |
| impl-tests-3 | 01a152a2-30ff-74dd-b5c3-eec2ec140bef | SUCCESS | 0 | 1.702s | disposable | off | 0.00971966 |
| verify | 01a152a2-c21e-773c-aa50-a162e5962983 | SUCCESS | 0 | 7.668s | disposable | off | 0.06735111 |
| existing | 01a152a2-f029-70b7-9b65-a4a096d834bd | SUCCESS | 0 | 1.773s | disposable | off | 0.00981828 |
| mutant-m02-e3a556c1bd | 01a152a3-0acc-7140-82e1-07c6fb16686c | SUCCESS | 0 | 7.29s | disposable | off | 0.06322165 |
| mutant-m01-6d0ea11345 | 01a152a3-0aaa-733d-b7a7-8efdb99a33be | SUCCESS | 0 | 7.413s | disposable | off | 0.06368446000000001 |
| mutant-m03-41894bb791 | 01a152a3-0b0a-74d5-805e-0fc413a3f894 | SUCCESS | 0 | 7.288s | disposable | off | 0.06288767 |
| mutant-m04-fcd90efeab | 01a152a3-0a5b-7755-84d9-8c93d1990dec | SUCCESS | 0 | 7.261s | disposable | off | 0.06323185 |
| mutant-m06-2abaf08eeb | 01a152a3-0ade-72f4-8efc-bc99f59f5fd6 | SUCCESS | 0 | 7.394s | disposable | off | 0.06361073 |
| mutant-m05-c8cdd8cb35 | 01a152a3-0a7b-7762-a232-dc66a7623c17 | SUCCESS | 0 | 7.288s | disposable | off | 0.06320997 |
| mutant-m07-2b5f2ad8af | 01a152a3-0aa7-7642-b9e2-72296a46b0b7 | SUCCESS | 0 | 7.262s | disposable | off | 0.06310377 |
| mutant-m08-82c0a39451 | 01a152a3-0ada-7586-ab8b-7e6723437325 | SUCCESS | 0 | 7.289s | disposable | off | 0.06327299 |
| mutant-m09-9d03230cf9 | 01a152a3-39cf-7176-918b-f1fb5d54eab1 | SUCCESS | 0 | 7.206s | disposable | off | 0.06323503000000001 |
| mutant-m10-d01c296f7c | 01a152a3-3a19-70f1-a4c0-9100b38b1073 | SUCCESS | 0 | 7.276s | disposable | off | 0.06314254 |
| mutant-m11-8c4bc824fc | 01a152a3-3a7c-70ea-8119-e897613cf663 | SUCCESS | 0 | 7.318s | disposable | off | 0.06360457 |
| mutant-m12-975c1af02b | 01a152a3-3c46-73ca-81e7-1690e68a6ee7 | SUCCESS | 0 | 7.316s | disposable | off | 0.06370406 |
| breaker-tests | 01a152a4-a5af-7381-95a2-94df719706c3 | SUCCESS | 0 | 2.882s | disposable | off | 0.022388929999999998 |

Sandbox operations: 18, total guest duration 113.408s, retained images ['73102021-ca14-48af-b567-ff1376963aff'].

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
