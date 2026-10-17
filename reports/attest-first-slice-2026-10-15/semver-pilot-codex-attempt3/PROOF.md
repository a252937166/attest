# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-20261015T133555Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T13:35:55.323114+00:00, finished 2026-10-15T13:40:44.814934+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `518b19f1-d9ab-4e47-8444-e4fa17498219`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require matching majors and exactly equal prerelease values; for positive majors require other's minor to be at least the receiver's minor while ignoring patch, and for major zero require matching minor and patch as well. Ignore build metadata in all cases. Accept Version subclasses, reject other types with the specified TypeError prefix, and document the method with at least two working doctest examples. Preserve existing public behavior and the existing pytest suite, changing only src/semver/version.py.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Instance method also accessible through semver.Version and the existing VersionInfo alias. Accept other positionally or by keyword. Return a bool indicating whe | TypeError: other is not an instance of semver.version.Version or a subclass; str(exception) must start with 'Expected a Version type'. The remainder is unspecif |

Acceptance criteria:
1. 1. The method is callable through semver.Version, semver.version.Version and the existing VersionInfo alias, accepts other as a positional or keyword argument, and returns literal True or False for valid operands.
2. 2. Version(1, 2, 3) is compatible with Version(1, 2, 3) and Version(1, 2, 4); Version(1, 2, 4) is compatible with Version(1, 2, 3).
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) is True, whereas the reverse call is False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False.
4. 4. Different majors are incompatible in both directions, including 1 versus 2 and 0 versus 1, regardless of minor, patch or prerelease.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True. Equal prereleases also allow a higher candidate minor for positive majors.
6. 6. Different prereleases are incompatible: 'rc.1' versus 'rc.0', and None versus 'rc1' in either direction, return False even when the candidate minor is higher.
7. 7. Prerelease values are compared exactly: 'RC.1' differs from 'rc.1', and a constructor-supplied empty string differs from None. These rules also apply to major zero.
8. 8. Version(0, 1, 0) is compatible with Version(0, 1, 0), but incompatible with Version(0, 1, 1) and Version(0, 2, 0) in either direction. Version(0, 0, 0) is compatible with itself.
9. 9. Major-zero operands with identical major, minor, patch and prerelease are compatible; changing only the prerelease makes them incompatible.
10. 10. Build metadata is ignored for both zero and positive majors: otherwise compatible operands remain compatible when builds differ or only one operand has a build. Build equality cannot make otherwise incompatible operands compatible.
11. 11. Passing 'wrongtype', '1.2.3', b'1.2.3', {'a': 2}, [], (1, 2, 3), None, an integer or a version-like non-Version object raises TypeError with a message starting 'Expected a Version type', for both zero-major and positive-major receivers.
12. 12. For a subclass CustomVersion inheriting the method, CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) and the reverse return True. Equivalent major-zero operands and operands from distinct Version subclasses are accepted and follow the same compatibility rules.
13. 13. Neither operand's major, minor, patch, prerelease or build changes after compatibility evaluation.
14. 14. The method's docstring describes directionality, minor and prerelease requirements, the major-zero exception, ignored build metadata, return value and TypeError. It contains at least two executable compatibility-call doctest examples with correct expected results.
15. 15. The complete existing pytest suite in tests/ passes without modifications. Existing construction, parsing, comparison, equality, hashing, exports, aliases, deprecated functions and CLI behavior remain unchanged.
16. 16. The implementation diff changes only src/semver/version.py and remains compatible with the project's Python 3.7-and-later support.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0e754948def1ff4a1eca510855724cfc95551ed58c95140091ff0d834707d677`, 24 test methods, sealed at 2026-10-15T13:38:25.843863+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint: FAILED (24 of 24 methods failing): 24 of 24 methods failing, 0 passing, 36 subtest events; operation `01a13fc9-1a4d-76c5-bd12-89c6f461d943`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_build_is_ignored_for_compatible_versions | ERROR (4 ev) | ok (5 ev) |
| test_sealed.TestVersionCompatibility.test_different_positive_majors_in_both_directions | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_different_prerelease_identifiers_are_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_distinct_subclasses_follow_same_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_docstring_describes_contract | ERROR (1 ev) | ok (7 ev) |
| test_sealed.TestVersionCompatibility.test_docstring_has_two_working_compatibility_doctests | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_empty_prerelease_differs_from_none | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_equal_prerelease_allows_patch_and_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_higher_candidate_minor_is_compatible_despite_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_keyword_argument_and_literal_bool | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_lower_candidate_minor_is_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_matching_build_cannot_override_incompatibility | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_non_version_operands_raise_typeerror_for_each_major | ERROR (18 ev) | ok (19 ev) |
| test_sealed.TestVersionCompatibility.test_operands_are_not_mutated | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_positive_major_ignores_patch_in_both_directions | ERROR (3 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_prerelease_comparison_is_case_sensitive | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_public_exports_and_alias | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_release_and_prerelease_are_incompatible_in_both_directions | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_zero_and_positive_majors_in_both_directions | ERROR (2 ev) | ok (3 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_exact_match | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_requires_matching_minor_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_requires_matching_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionCompatibility.test_zero_major_requires_matching_prerelease | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -200,6 +200,31 @@
     def build(self, value):
         raise AttributeError("attribute 'build' is readonly")
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        Majors and prerelease values must match exactly. For positive majors,
+        ``other`` must have at least this version's minor; patches are ignored.
+        For major zero, minor and patch must both match. Build metadata is
+        ignored in every case.
+
+        :param other: the candidate replacement version
+        :return: ``True`` if ``other`` can replace this version, else ``False``
+        :raises TypeError: if ``other`` is not a Version instance
+
+        >>> Version(1, 2, 9).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
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
Existing suite: 312 passed in 0.66s (312 passed of 312). Sealed suite: OK (24 of 24 methods). Operation `01a13fca-de96-7419-9587-58234b7c9685`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| completed | pass |
| nonce_matches | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| no_import_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| ran_count_matches | pass |
| all_expected_pass | pass |

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.70s (325 passed of 328); operation `01a13fca-fed5-74f2-9bd0-bf96c2050ab4`. Reported only; not a gate.

## 6. Breaker pass (mutants of changed lines, each in its own branch)
12 mutants generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-e69fe38efa | src/semver/version.py | 220 | remove `not` | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-1488-774b-aa18-42ef3257fbe2 |
| m02-a97140961f | src/semver/version.py | 221 | raise -> pass | killed | test_sealed.TestVersionCompatibility.test_non_version_operands_raise_typeerror_for_each_major | 01a13fcb-1458-7541-b90e-5bba6722bd35 |
| m03-3c46ba4bf1 | src/semver/version.py | 222 | NotEq -> Eq | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-1442-7653-bd18-541529f5273b |
| m04-4925ef2263 | src/semver/version.py | 222 | NotEq -> Eq | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-14aa-710c-9465-f0d6692f0fa5 |
| m05-7ad410be51 | src/semver/version.py | 222 | Or -> And | killed | test_sealed.TestVersionCompatibility.test_different_positive_majors_in_both_directions, test_sealed.TestVersionCompatibi | 01a13fcb-14a7-7091-9d26-56bdbb256497 |
| m06-8681d8e19e | src/semver/version.py | 223 | False -> True | killed | test_sealed.TestVersionCompatibility.test_different_positive_majors_in_both_directions, test_sealed.TestVersionCompatibi | 01a13fcb-14c8-746a-a8c8-af72eb09f669 |
| m07-598d4377dc | src/semver/version.py | 224 | 0 -> 1 | killed | test_sealed.TestVersionCompatibility.test_build_is_ignored_for_compatible_versions, test_sealed.TestVersionCompatibility | 01a13fcb-14b1-705d-8684-45211f5e3010 |
| m08-26edf17ec6 | src/semver/version.py | 224 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_build_is_ignored_for_compatible_versions, test_sealed.TestVersionCompatibility | 01a13fcb-1476-738a-a276-944f8c173982 |
| m09-b93e40b4a1 | src/semver/version.py | 225 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-3057-734e-bc82-b7fa8de52ed3 |
| m10-bde0fe8b42 | src/semver/version.py | 225 | Eq -> NotEq | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-337f-774f-82a9-e3126e8e8701 |
| m11-1bd105bd6f | src/semver/version.py | 225 | And -> Or | killed | test_sealed.TestVersionCompatibility.test_distinct_subclasses_follow_same_rules, test_sealed.TestVersionCompatibility.te | 01a13fcb-33cc-76e8-86b9-8353f9da7bb5 |
| m12-65b28875f7 | src/semver/version.py | 226 | GtE -> Gt | killed | test_sealed.TestVersionCompatibility.test_base_and_subclass_operands_in_both_directions, test_sealed.TestVersionCompatib | 01a13fcb-345a-705d-9583-7f10b01a70d7 |

## 7. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28533 | 1300 | 0 | - | 64.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28116 | 3470 | 0 | - | 68.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10856 | 130 | 0 | - | 23.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12742 | 605 | 0 | - | 23.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11757 | 86 | 0 | - | 15.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12578 | 522 | 0 | - | 21.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12825 | 138 | 0 | - | 16.0s | ok |

Model calls: 7 (0 failed, 0 malformed); tokens in/out/cached 117407/6251/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13fc6-e7b4-733f-bd0f-d0b0b71018e7 | SUCCESS | 0 | 3.425s | retained | on | 0.02223999 |
| red-1 | 01a13fc9-1a4d-76c5-bd12-89c6f461d943 | SUCCESS | 0 | 0.857s | disposable | off | 0.0037693699999999998 |
| impl-tests-3 | 01a13fca-1d36-74f2-889a-695466570de6 | SUCCESS | 0 | 1.743s | disposable | off | 0.009674869999999999 |
| impl-python-4 | 01a13fca-8ec1-7433-9b80-73e1da5e2d9d | SUCCESS | 0 | 0.788s | disposable | off | 0.0031136099999999997 |
| verify | 01a13fca-de96-7419-9587-58234b7c9685 | SUCCESS | 0 | 2.027s | disposable | off | 0.012082679999999998 |
| heldout | 01a13fca-fed5-74f2-9bd0-bf96c2050ab4 | SUCCESS | 0 | 1.797s | disposable | off | 0.01011396 |
| mutant-m01-e69fe38efa | 01a13fcb-1488-774b-aa18-42ef3257fbe2 | SUCCESS | 0 | 0.952s | disposable | off | 0.00347131 |
| mutant-m02-a97140961f | 01a13fcb-1458-7541-b90e-5bba6722bd35 | SUCCESS | 0 | 0.952s | disposable | off | 0.00339014 |
| mutant-m04-4925ef2263 | 01a13fcb-14aa-710c-9465-f0d6692f0fa5 | SUCCESS | 0 | 0.955s | disposable | off | 0.00338058 |
| mutant-m03-3c46ba4bf1 | 01a13fcb-1442-7653-bd18-541529f5273b | SUCCESS | 0 | 0.857s | disposable | off | 0.0033891200000000002 |
| mutant-m05-7ad410be51 | 01a13fcb-14a7-7091-9d26-56bdbb256497 | SUCCESS | 0 | 0.948s | disposable | off | 0.00338387 |
| mutant-m06-8681d8e19e | 01a13fcb-14c8-746a-a8c8-af72eb09f669 | SUCCESS | 0 | 0.925s | disposable | off | 0.0035228699999999996 |
| mutant-m07-598d4377dc | 01a13fcb-14b1-705d-8684-45211f5e3010 | SUCCESS | 0 | 0.947s | disposable | off | 0.0034217200000000005 |
| mutant-m08-26edf17ec6 | 01a13fcb-1476-738a-a276-944f8c173982 | SUCCESS | 0 | 0.946s | disposable | off | 0.00339185 |
| mutant-m09-b93e40b4a1 | 01a13fcb-3057-734e-bc82-b7fa8de52ed3 | SUCCESS | 0 | 0.84s | disposable | off | 0.00338535 |
| mutant-m10-bde0fe8b42 | 01a13fcb-337f-774f-82a9-e3126e8e8701 | SUCCESS | 0 | 0.849s | disposable | off | 0.00341448 |
| mutant-m11-1bd105bd6f | 01a13fcb-33cc-76e8-86b9-8353f9da7bb5 | SUCCESS | 0 | 0.751s | disposable | off | 0.00336424 |
| mutant-m12-65b28875f7 | 01a13fcb-345a-705d-9583-7f10b01a70d7 | SUCCESS | 0 | 0.837s | disposable | off | 0.00340434 |

Sandbox operations: 18, total guest duration 21.396s, retained images ['518b19f1-d9ab-4e47-8444-e4fa17498219'].

## 8. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Breaker pass covers AST mutants of changed lines only; no model-written adversarial or property tests, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- The sealed suite runs in the same process as the code under test; in-process forgery is mitigated (nonce, digest, expected IDs, completion marker) but not impossible.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
