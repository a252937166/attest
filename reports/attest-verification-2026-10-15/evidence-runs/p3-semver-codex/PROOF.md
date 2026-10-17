# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-20261015T160749Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T16:07:49.347824+00:00, finished 2026-10-15T16:13:25.087665+00:00.

Reasons: child process nonzero exit: test_method_docstring_describes_rules_and_contains_two_examples exit 1; held-out tests failed: 3 of 328 (tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype1], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrong); resolve the failures or the contract disagreement before this patch can be verified


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `010e9a6e-d799-4e3a-a772-f1ca2bb7fadc`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether a candidate version can replace the receiver. For nonzero majors, require equal majors, a candidate minor at least as large as the receiver's, and equal prerelease values; ignore patch and build. For major zero, require equal major, minor, patch and prerelease, still ignoring build. Accept Version subclasses, reject all other argument types with the specified TypeError prefix, and document the method with at least two working doctest examples. Preserve existing public behavior and keep the existing pytest suite passing without changing tests, documentation files or packaging.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Public instance method, also accessible through semver.Version and the existing VersionInfo alias. Supports positional or keyword argument other. The receiver i | TypeError when other is not an instance of Version or a Version subclass; str(exception) must start with 'Expected a Version type'. This applies for all receive |

Acceptance criteria:
1. 1. The method exists on semver.version.Version, semver.Version and the existing VersionInfo alias, has one required argument named other, and declares a bool return annotation. Positional and keyword calls produce the same result.
2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) returns True; the reverse call returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
4. 4. Different majors always return False, in both directions, including comparisons between major zero and a nonzero major. In particular, Version(2, 0, 0).is_compatible(Version(1, 5, 0)) returns False.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) returns True. Equal prereleases also permit a higher candidate minor for equal nonzero majors.
6. 6. Different prerelease values return False even when the major and minor conditions hold. This includes 'rc.1' versus 'rc.0', case differences, and absent versus present prerelease in either direction. Exact stored equality applies: None differs from '', while two empty strings match.
7. 7. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) returns True. Changing only its candidate patch, minor, major or prerelease returns False. A lower patch or minor also returns False. Matching major-zero prereleases return True only when major, minor and patch also match.
8. 8. Changing only build metadata never changes the result. Version(1, 2, 3, build='a') and Version(1, 2, 3, build='b') are compatible in both directions, as are Version(0, 1, 0, build='a') and Version(0, 1, 0, build='b'). Absent versus present build is also ignored.
9. 9. For receivers with major zero and nonzero major, each non-Version argument raises TypeError with a message starting 'Expected a Version type'. Cover 'wrongtype', a valid version string, bytes, {'a': 2}, a version-shaped dictionary, [], a version-shaped tuple, None, a number, and an unrelated object. No parsing or conversion is attempted.
10. 10. For a plain subclass CustomVersion(Version), compatible base/subclass, subclass/base and subclass/subclass pairs return True, including CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)). The same acceptance applies for major-zero instances and distinct plain Version subclasses.
11. 11. Every successful call returns exactly True or False, and neither operand's major, minor, patch, prerelease or build changes.
12. 12. The method docstring explains call direction, compatibility conditions, the major-zero exception, ignored build metadata and invalid-type errors. It includes at least two executable doctest calls with expected results, and those examples pass when executed with their documented imports or the repository doctest namespace.
13. 13. The implementation modifies only src/semver/version.py. Existing tests, documentation, packaging, metadata and exports remain unchanged.
14. 14. The complete existing pytest suite in tests/ passes. Existing construction, parsing, comparison, equality, hashing, matching, version manipulation, subclass behavior, aliases, deprecated APIs and CLI behavior remain unchanged.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `dbfc337a1b6033ce7b008619c2520a07a288212996448c1dee1477c6aa878526`, 18 test methods, sealed at 2026-10-15T16:10:29.120838+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (18 of 18 methods: ERROR 18): 18 of 18 methods failing, 0 passing; operation `01a14054-3a45-7497-816c-197729aefd73`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.CompatibilityAcceptanceTests.test_absent_and_present_build_metadata_are_equivalent | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_base_and_subclass_operands_are_accepted_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_build_metadata_is_ignored_in_both_major_regimes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_different_prerelease_values_are_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_distinct_version_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_empty_prerelease_is_distinct_from_absent_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_equal_versions_and_patch_changes_are_compatible_for_nonzero_major | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_accepts_base_and_subclass_operands | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_requires_exact_core_version | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_requires_exact_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_matching_prerelease_allows_patch_or_minor_change | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_method_docstring_describes_rules_and_contains_two_examples | ERROR (1 ev) | FAIL (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_non_version_arguments_raise_typeerror_for_both_major_regimes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_nonzero_major_minor_may_increase_but_not_decrease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_public_access_and_signature | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_python_argument_binding_errors | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_results_are_builtin_bool_and_operands_are_unchanged | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -200,6 +200,38 @@
     def build(self, value):
         raise AttributeError("attribute 'build' is readonly")
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        For a nonzero major version, the candidate must have the same major,
+        an equal or higher minor, and an exactly equal prerelease. Patch and
+        build metadata are ignored. For major zero, major, minor, patch, and
+        prerelease must all match; build metadata is still ignored.
+        A non-Version candidate raises ``TypeError``.
+
+        >>> import semver
+        >>> semver.Version(1, 2, 9).is_compatible(semver.Version(1, 3, 0))
+        True
+        >>> semver.Version(0, 1, 0).is_compatible(semver.Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type")
+
+        if self.major == 0:
+            return (
+                other.major == self.major
+                and other.minor == self.minor
+                and other.patch == self.patch
+                and other.prerelease == self.prerelease
+            )
+
+        return (
+            other.major == self.major
+            and other.minor >= self.minor
+            and other.prerelease == self.prerelease
+        )
+
     def to_tuple(self) -> VersionTuple:
         """
         Convert the Version object to a tuple.
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.61s (312 passed of 312). Sealed suite: FAILED (1 of 18 methods: FAIL 1). Operation `01a14056-60df-70dd-8428-96277d6e5c72`, networking disabled, disposable branch from the checkpoint.

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
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.68s (325 passed of 328); operation `01a14056-9dd5-7210-b5d9-f189f3c3d554`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.61s |
| sealed_binding | FAIL | child process nonzero exit: test_method_docstring_describes_rules_and_contains_two_examples exit 1 |
| heldout_suite | FAIL | 3 failed, 325 passed in 0.68s |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(other, Version)` accepts subclasses and rejects other types with the required prefix, while `if self.major == 0` enforces exact major/minor/patch/prerelease equality; the nonzero branch requires equal majors, `other.minor >= self.minor`, and equal prereleases, ignoring build. Only src/semver/version.py changes, the docstring includes two executable examples, and observed outputs support the reported 312 passing tests and successful targeted checks.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28595 | 1408 | 0 | - | 69.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28302 | 3903 | 0 | - | 66.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10957 | 121 | 7168 | - | 22.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12981 | 510 | 7168 | - | 23.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11880 | 220 | 7168 | - | 18.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12065 | 82 | 0 | - | 18.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12885 | 565 | 0 | - | 21.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 13136 | 134 | 7168 | - | 15.8s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11876 | 161 | 0 | - | 19.4s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 142677/7104/28672; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14051-f8ed-75ea-a87d-d11be6fdb407 | SUCCESS | 0 | 3.326s | retained | on | 0.02187208 |
| red-1 | 01a14054-3a45-7497-816c-197729aefd73 | SUCCESS | 0 | 4.449s | disposable | off | 0.03551387 |
| impl-tests-4 | 01a14055-a293-77d4-acde-40769695a06f | SUCCESS | 0 | 1.805s | disposable | off | 0.00963836 |
| impl-python-5 | 01a14056-1196-711f-924a-5049f301757c | SUCCESS | 0 | 0.828s | disposable | off | 0.00306279 |
| verify | 01a14056-60df-70dd-8428-96277d6e5c72 | SUCCESS | 0 | 5.315s | disposable | off | 0.0434601 |
| heldout | 01a14056-9dd5-7210-b5d9-f189f3c3d554 | SUCCESS | 0 | 1.781s | disposable | off | 0.010001640000000001 |

Sandbox operations: 6, total guest duration 17.504s, retained images ['010e9a6e-d799-4e3a-a772-f1ca2bb7fadc'].

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
