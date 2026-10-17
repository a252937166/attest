# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-20261015T152115Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T15:21:15.701230+00:00, finished 2026-10-15T15:28:16.299115+00:00.

Reasons: held-out tests failed: 3 of 328 (tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype1], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrong); resolve the failures or the contract disagreement before this patch can be verified
Warnings: adversarial tests skipped: only 0 adversarial tests were written

## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `91d283b5-68dd-4217-9b29-efa95f8104ed`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether another Version can replace the receiver. For nonzero majors, require equal majors, an equal or higher replacement minor, and equal prerelease values, ignoring patch and build. For major zero, require equal major, minor, patch and prerelease values, still ignoring build. Accept Version subclasses, reject other argument types with the specified TypeError prefix, and document the method with at least two executable doctest examples while preserving all existing public behavior and leaving other files unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Instance method also accessible through semver.Version and the existing VersionInfo alias. The receiver is the old version and other is the proposed replacement | TypeError: other is not an instance of Version or a Version subclass; str(exception) must start with 'Expected a Version type'. This applies even to valid versi |

Acceptance criteria:
1. 1. The method exists on semver.version.Version, semver.Version and the existing VersionInfo alias, accepts the keyword other, and returns True or False rather than another truthy or falsy value.
2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) returns True; the reverse call returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
4. 4. Different majors return False in both directions, including the pairs 2.0.0 versus 1.5.0 and 0.1.0 versus 1.1.0.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) returns True. Equal prereleases also allow an increased minor for a nonzero major.
6. 6. Different prereleases return False even when the replacement minor is higher. In particular, 'rc.1' versus 'rc.0', 'RC.1' versus 'rc.1', and None versus 'rc1' are incompatible in both directions.
7. 7. Prerelease equality uses stored values without normalization: two empty-string prereleases match, but an empty-string prerelease and None do not match, for both zero and nonzero majors.
8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) and Version(0, 0, 0).is_compatible(Version(0, 0, 0)) return True. For major zero, changing either minor, patch or prerelease returns False in either direction; identical nonempty prereleases match.
9. 9. Build differences alone never alter the result. Version(1, 2, 3, build='a') is compatible with Version(1, 2, 3, build='b'), and Version(0, 1, 0, build='a') is compatible with Version(0, 1, 0, build='b'). Absent versus present build metadata likewise has no effect.
10. 10. Passing 'wrongtype', '1.2.3', b'1.2.3', {'a': 2}, {'major': 1}, [], (1, 2, 3), None, an integer, or an unrelated object raises TypeError with a message starting 'Expected a Version type', for both major-zero and nonzero receivers.
11. 11. For an otherwise unmodified CustomVersion subclass, base-to-subclass, subclass-to-base, and subclass-to-subclass calls follow the same compatibility rules without type rejection. This includes CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) returning True and equivalent major-zero cases.
12. 12. Successful and unsuccessful compatibility checks leave all five version properties of both operands unchanged; invalid argument checks leave the receiver unchanged.
13. 13. The method docstring describes replacement direction, compatibility rules, ignored build metadata and invalid argument behavior, and contains at least two executable doctest examples with correct expected results.
14. 14. Only src/semver/version.py is modified. The entire existing pytest suite under tests/ continues to pass unchanged, and existing construction, parsing, comparison, hashing, formatting, aliases, and other public behavior remain unchanged.
15. 15. The addition remains compatible with the repository's supported Python syntax, including Python 3.7.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `778b2e84357782ebfd011faa7c531e206b1e8923d3fa6a5083872757ee10f76b`, 16 test methods, sealed at 2026-10-15T15:24:07.468578+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a14029-bd55-714a-8282-feafe234f508`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.VersionCompatibilityTests.test_build_metadata_is_ignored_for_both_major_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_compatibility_checks_do_not_mutate_either_operand | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_different_majors_are_incompatible_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_different_prereleases_are_incompatible_even_with_higher_minor | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_docstring_explains_contract_and_has_two_passing_doctests | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_empty_prerelease_matches_itself_but_not_none | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_invalid_arguments_raise_typeerror_with_required_prefix | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_major_zero_identical_versions_are_compatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_major_zero_requires_equal_minor_and_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_major_zero_requires_equal_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_matching_prerelease_allows_patch_and_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_nonzero_major_allows_only_equal_or_higher_minor | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_nonzero_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_prerelease_comparison_is_case_sensitive | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument | ERROR (1 ev) | ok (1 ev) |
| test_sealed.VersionCompatibilityTests.test_subclasses_are_accepted_independently_of_receiver_class | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -200,6 +200,29 @@
     def build(self, value):
         raise AttributeError("attribute 'build' is readonly")
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether *other* can replace this version.
+
+        Majors must match. For a nonzero major, the replacement minor must
+        be at least this version's minor and prerelease values must match;
+        patch values are ignored. For major zero, minor, patch, and
+        prerelease values must all match. Build metadata is always ignored.
+        *other* must be a Version instance (or subclass), otherwise a
+        TypeError is raised.
+
+        >>> Version(1, 2, 3).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(0, 2, 3).is_compatible(Version(0, 2, 4))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type")
+        if self.major != other.major or self.prerelease != other.prerelease:
+            return False
+        if self.major == 0:
+            return self.minor == other.minor and self.patch == other.patch
+        return other.minor >= self.minor
+
     def to_tuple(self) -> VersionTuple:
         """
         Convert the Version object to a tuple.
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.65s (312 passed of 312). Sealed suite: OK (16 of 16 methods, each in its own process). Operation `01a1402b-ba73-75c4-8438-f3b13e4cbb10`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| static_ids_match_red | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.71s (325 passed of 328); operation `01a1402b-e631-73bb-9cdb-573fb6149a4c`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.65s |
| sealed_binding | pass | all checks pass |
| heldout_suite | FAIL | 3 failed, 325 passed in 0.71s |
| mutation | pass | score 1.0 on 12 mutants |
| adversarial_tests | pass | only 0 adversarial tests were written |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-7446d24d82 | src/semver/version.py | 218 | remove `not` | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-0ae9-719f-ad15-c46cce730ff3 |
| m02-a2ee30ca61 | src/semver/version.py | 219 | raise -> pass | killed | test_sealed.VersionCompatibilityTests.test_invalid_arguments_raise_typeerror_with_required_prefix | 01a1402c-0ab1-77b6-a2cf-715239d95cb9 |
| m03-1b83f93f7f | src/semver/version.py | 220 | NotEq -> Eq | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-0ae9-753c-a613-1e33fca4a8a7 |
| m04-91a3a90f64 | src/semver/version.py | 220 | NotEq -> Eq | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-0a32-77ef-b2e0-d7c41dbf7f9d |
| m05-2121c6ef4b | src/semver/version.py | 220 | Or -> And | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-0b47-730d-a0c9-f371eccf8c23 |
| m06-64aed6e3c8 | src/semver/version.py | 221 | False -> True | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-0b48-73ca-8b84-fe9b0f640eda |
| m07-42e3379280 | src/semver/version.py | 222 | 0 -> 1 | killed | test_sealed.VersionCompatibilityTests.test_nonzero_major_ignores_patch_in_both_directions, test_sealed.VersionCompatibil | 01a1402c-0acd-738a-aea4-340a0cc1e043 |
| m08-89b98f4463 | src/semver/version.py | 222 | Eq -> NotEq | killed | test_sealed.VersionCompatibilityTests.test_nonzero_major_ignores_patch_in_both_directions, test_sealed.VersionCompatibil | 01a1402c-0abf-746c-b49a-9e0dfb0f094c |
| m09-c87ed552a7 | src/semver/version.py | 223 | Eq -> NotEq | killed | test_sealed.VersionCompatibilityTests.test_empty_prerelease_matches_itself_but_not_none, test_sealed.VersionCompatibilit | 01a1402c-3195-7735-aeaf-9945b4a4d7d4 |
| m10-32a035b0a9 | src/semver/version.py | 223 | Eq -> NotEq | killed | test_sealed.VersionCompatibilityTests.test_empty_prerelease_matches_itself_but_not_none, test_sealed.VersionCompatibilit | 01a1402c-353d-7478-9f74-7b4fd3b85af2 |
| m11-52022b84ba | src/semver/version.py | 223 | And -> Or | killed | test_sealed.VersionCompatibilityTests.test_major_zero_requires_equal_minor_and_patch, test_sealed.VersionCompatibilityTe | 01a1402c-3884-7355-b0f5-785da1c2029e |
| m12-4bcbe2517e | src/semver/version.py | 224 | GtE -> Gt | killed | test_sealed.VersionCompatibilityTests.test_public_names_and_keyword_argument, test_sealed.VersionCompatibilityTests.test | 01a1402c-3a82-72a0-b7ae-f7080958f817 |

Model-written adversarial tests: skipped (only 0 adversarial tests were written)



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(other, Version)` accepts subclasses and enforces the required TypeError prefix, direct prerelease comparison preserves stored values, and the minor/patch branches implement replacement direction and major-zero rules while ignoring build metadata. Only src/semver/version.py changes, the docstring includes two correct doctests, and observed tool output supports the reported 312 passing existing tests and successful targeted checks.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28591 | 1360 | 0 | - | 72.9s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28176 | 3264 | 0 | - | 69.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10910 | 88 | 0 | - | 21.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12934 | 536 | 0 | - | 27.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11800 | 104 | 7168 | - | 16.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12622 | 540 | 0 | - | 25.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12870 | 132 | 0 | - | 16.5s | ok |
| codex_gateway:gpt-6-sol | break | break-tests | medium | 34876 | 2379 | 21504 | - | 67.1s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11725 | 128 | 0 | - | 23.2s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 164504/8531/28672; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14027-5997-7649-908a-28d16f710194 | SUCCESS | 0 | 3.494s | retained | on | 0.022475890000000002 |
| red-1 | 01a14029-bd55-714a-8282-feafe234f508 | SUCCESS | 0 | 7.401s | disposable | off | 0.036145680000000006 |
| impl-tests-3 | 01a1402a-f018-7742-805a-4dc3150ca381 | SUCCESS | 0 | 1.728s | disposable | off | 0.00962614 |
| impl-python-4 | 01a1402b-66f4-750e-80ec-1f0bcaea2a45 | SUCCESS | 0 | 0.742s | disposable | off | 0.0030987700000000003 |
| verify | 01a1402b-ba73-75c4-8438-f3b13e4cbb10 | SUCCESS | 0 | 5.428s | disposable | off | 0.044288570000000006 |
| heldout | 01a1402b-e631-73bb-9cdb-573fb6149a4c | SUCCESS | 0 | 1.789s | disposable | off | 0.01013264 |
| mutant-m01-7446d24d82 | 01a1402c-0ae9-719f-ad15-c46cce730ff3 | SUCCESS | 0 | 4.376s | disposable | off | 0.03599629 |
| mutant-m02-a2ee30ca61 | 01a1402c-0ab1-77b6-a2cf-715239d95cb9 | SUCCESS | 0 | 4.354s | disposable | off | 0.03583122 |
| mutant-m03-1b83f93f7f | 01a1402c-0ae9-753c-a613-1e33fca4a8a7 | SUCCESS | 0 | 4.371s | disposable | off | 0.03558232 |
| mutant-m04-91a3a90f64 | 01a1402c-0a32-77ef-b2e0-d7c41dbf7f9d | SUCCESS | 0 | 4.393s | disposable | off | 0.036091950000000005 |
| mutant-m05-2121c6ef4b | 01a1402c-0b47-730d-a0c9-f371eccf8c23 | SUCCESS | 0 | 4.37s | disposable | off | 0.0358104 |
| mutant-m06-64aed6e3c8 | 01a1402c-0b48-73ca-8b84-fe9b0f640eda | SUCCESS | 0 | 4.356s | disposable | off | 0.035689389999999994 |
| mutant-m07-42e3379280 | 01a1402c-0acd-738a-aea4-340a0cc1e043 | SUCCESS | 0 | 4.355s | disposable | off | 0.035545810000000004 |
| mutant-m08-89b98f4463 | 01a1402c-0abf-746c-b49a-9e0dfb0f094c | SUCCESS | 0 | 4.391s | disposable | off | 0.03586554 |
| mutant-m09-c87ed552a7 | 01a1402c-3195-7735-aeaf-9945b4a4d7d4 | SUCCESS | 0 | 4.283s | disposable | off | 0.035672709999999996 |
| mutant-m10-32a035b0a9 | 01a1402c-353d-7478-9f74-7b4fd3b85af2 | SUCCESS | 0 | 4.317s | disposable | off | 0.03607146000000001 |
| mutant-m11-52022b84ba | 01a1402c-3884-7355-b0f5-785da1c2029e | SUCCESS | 0 | 4.309s | disposable | off | 0.035729920000000005 |
| mutant-m12-4bcbe2517e | 01a1402c-3a82-72a0-b7ae-f7080958f817 | SUCCESS | 0 | 4.368s | disposable | off | 0.0358184 |

Sandbox operations: 18, total guest duration 72.825s, retained images ['91d283b5-68dd-4217-9b29-efa95f8104ed'].

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
