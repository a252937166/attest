# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-20261015T172806Z` · profile `phase2-arbitration` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T17:28:06.735099+00:00, finished 2026-10-15T17:34:51.293290+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `812476c5-0619-40fd-b769-df0eeecc2529`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require matching majors and exactly equal prerelease values; for positive majors allow equal or higher candidate minors and ignore patches, while major zero requires equal minor and patch values too. Ignore build metadata in all cases, accept Version subclasses, reject all other argument types with the specified TypeError, and document the method with at least two executable doctest examples while preserving all existing public behavior.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Instance method accessible through semver.version.Version, semver.Version, and the existing VersionInfo alias, and inherited by subclasses. The receiver is the  | TypeError: if other is not an instance of Version, raise with the exact message 'Expected a Version type but got ' + str(type(other)), for every receiver major, |

Acceptance criteria:
1. 1. The new instance method is available from both documented Version import paths and the existing VersionInfo alias, accepts other positionally and by keyword, and returns True or False rather than an integer or NotImplemented.
2. 2. Version(1, 2, 3) is compatible with Version(1, 2, 3) and Version(1, 2, 4); Version(1, 2, 4) is compatible with Version(1, 2, 3).
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) is True, while the reverse call is False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False.
4. 4. Different majors are incompatible in both directions, including 1 versus 2 and 0 versus 1, regardless of minor, patch, or prerelease.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True. Equal prereleases also allow a higher candidate minor for positive majors.
6. 6. Different prereleases return False even with an increased candidate minor. Specifically, 'rc.1' versus 'rc.0', 'RC.0' versus 'rc.0', and absent prerelease versus 'rc1' are incompatible in both directions.
7. 7. Prerelease comparison uses stored values exactly: two absent prereleases match, two empty-string prereleases match, and None versus an empty string does not match, for both zero and positive majors.
8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True. Changing its candidate minor, patch, or prerelease makes the result False; patch increases and decreases are both incompatible for major zero. Version(0, 0, 0) is compatible with itself.
9. 9. Build differences alone never affect the result: otherwise matching versions with build=None, build='a', or build='b' are compatible for both major zero and positive majors. Build values cannot make otherwise incompatible versions compatible.
10. 10. For an ordinary subclass CustomVersion, equal versions are compatible for base/base, base/subclass, subclass/base, and subclass/subclass calls, including major zero. Instances of two different ordinary Version subclasses are also accepted.
11. 11. Passing 'wrongtype', a valid version string, bytes, {'a': 2}, [], a tuple, None, an integer, or an unrelated object raises TypeError. Each message equals 'Expected a Version type but got ' + str(type(other)); for 'wrongtype' it is exactly "Expected a Version type but got <class 'str'>". Verify rejection with both zero-major and positive-major receivers.
12. 12. Successful and unsuccessful compatibility checks leave all five fields of both operands unchanged; invalid-argument calls leave the receiver unchanged.
13. 13. The method has a docstring explaining replacement direction, the major-zero exception, prerelease equality, ignored build metadata, and invalid-argument behavior, and containing at least two executable doctest examples with correct expected outputs.
14. 14. The existing pytest suite in tests/ continues to pass. Existing comparison, parsing, formatting, hashing, immutability, subclass, deprecated-function, and CLI behavior remains unchanged.
15. 15. The implementation changes only src/semver/version.py and remains compatible with the repository's supported Python syntax, including Python 3.7.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `91d0954630d9c1461b5826e5660af26dc3ce4b29a5777677b1817dab41bfdb60`, 20 test methods, sealed at 2026-10-15T17:30:46.187675+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 20 methods: ERROR 16): 16 of 20 methods failing, 4 passing; operation `01a1409d-b640-76cf-b04c-fadc5132ccbf`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_absent_and_empty_prerelease_are_distinct_stored_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_base_and_unrelated_version_subclasses_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_build_metadata_is_ignored_without_rescuing_other_differences | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_calls_leave_both_operands_unchanged | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_different_majors_are_incompatible_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_different_prereleases_are_incompatible_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_docstring_explains_contract_and_contains_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_equal_prerelease_allows_patch_and_candidate_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_existing_comparison_behavior_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_existing_hash_behavior_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_existing_parse_and_format_behavior_remains_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_existing_public_fields_remain_read_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_invalid_arguments_raise_exact_type_error_for_major_zero | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_invalid_arguments_raise_exact_type_error_for_positive_major | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_keyword_argument_and_builtin_bool_result | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_requires_equal_minor_and_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_requires_equal_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_positive_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_positive_major_minor_is_directional | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_public_import_paths_and_alias_share_the_method | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -422,6 +422,31 @@
 
         return rccmp
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        Both versions must have the same major version and exactly equal
+        prerelease values. For a positive major, the candidate's minor must
+        be at least this version's minor; patch versions are ignored. For
+        major zero, minor and patch must both be equal. Build metadata is
+        ignored in all cases.
+
+        :param other: replacement candidate, which must be a Version instance
+        :raises TypeError: if ``other`` is not a Version instance
+
+        >>> Version(1, 2, 9).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type but got " + str(type(other)))
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

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.60s (312 passed of 312). Sealed suite: OK (20 of 20 methods, each in its own process). Operation `01a1409f-c53c-76b9-837d-bb7f5338fd5b`, networking disabled, disposable branch from the checkpoint.

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
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

Held-out suite (tests/test_heldout_pr368.py): 328 passed in 0.61s (328 passed of 328); operation `01a1409f-eece-7264-8881-c3a895d8b64b`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.60s |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | 328 passed in 0.61s |
| mutation | pass | score 1.0 on 12 mutants |
| adversarial_tests | pass | OK (8 of 8 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ada25f6f60 | src/semver/version.py | 442 | remove `not` | killed | test_sealed.TestIsCompatible.test_public_import_paths_and_alias_share_the_method, test_sealed.TestIsCompatible.test_keyw | 01a140a0-02e4-771e-a54b-d1010ea73b4f |
| m02-297e8672f1 | src/semver/version.py | 443 | Add -> Sub | killed | test_sealed.TestIsCompatible.test_invalid_arguments_raise_exact_type_error_for_positive_major, test_sealed.TestIsCompati | 01a140a0-0397-72b0-ad0a-1cd80cb4e855 |
| m03-8fc1b5a85a | src/semver/version.py | 443 | raise -> pass | killed | test_sealed.TestIsCompatible.test_invalid_arguments_raise_exact_type_error_for_positive_major, test_sealed.TestIsCompati | 01a140a0-0432-7647-b8df-5597743397c7 |
| m04-843b97c297 | src/semver/version.py | 444 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_public_import_paths_and_alias_share_the_method, test_sealed.TestIsCompatible.test_keyw | 01a140a0-16aa-70c0-8c05-03b17c1841ec |
| m05-ddabf44e6d | src/semver/version.py | 444 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_public_import_paths_and_alias_share_the_method, test_sealed.TestIsCompatible.test_keyw | 01a140a0-0482-70cb-ae99-63f4bdcf10a1 |
| m06-7327d6d2d5 | src/semver/version.py | 444 | Or -> And | killed | test_sealed.TestIsCompatible.test_different_majors_are_incompatible_in_both_directions, test_sealed.TestIsCompatible.tes | 01a140a0-0909-7428-a12c-a02ebb1841f2 |
| m07-a3fce98723 | src/semver/version.py | 445 | False -> True | killed | test_sealed.TestIsCompatible.test_different_majors_are_incompatible_in_both_directions, test_sealed.TestIsCompatible.tes | 01a140a0-03ab-750d-97ac-037a3a0fe715 |
| m08-072cc04269 | src/semver/version.py | 446 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_keyword_argument_and_builtin_bool_result, test_sealed.TestIsCompatible.test_positive_m | 01a140a0-0384-76bf-bfbe-da34cada84dc |
| m09-57c234ea01 | src/semver/version.py | 446 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_keyword_argument_and_builtin_bool_result, test_sealed.TestIsCompatible.test_positive_m | 01a140a0-2387-7706-8698-6a1ae8f7885b |
| m10-ebbd917cbe | src/semver/version.py | 447 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_absent_and_empty_prerelease_are_distinct_stored_values, test_sealed.TestIsCompatible.t | 01a140a0-2b41-71c2-a036-85fefb640932 |
| m11-f44639c649 | src/semver/version.py | 447 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_absent_and_empty_prerelease_are_distinct_stored_values, test_sealed.TestIsCompatible.t | 01a140a0-2c35-7416-873b-07659f9e510a |
| m12-1f691f40df | src/semver/version.py | 447 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_requires_equal_minor_and_patch, test_sealed.TestIsCompatible.test_build_met | 01a140a0-2fa2-74b2-9484-69c40892d3cf |

Model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `934b98433bff2069c3737927f2e444f55cc8e7a83783c4f5876e33c9e05695f9`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a140a1-19d4-77f5-bea1-72d2f7556b8d`. Notes: Targets duck typing, subclass comparison overrides, large numeric boundaries, prerelease ordering traps, and subclass keyword calls.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff satisfies the task: `isinstance(other, Version)` accepts subclasses and enforces the exact TypeError message, major and prerelease comparisons reject mismatches, and the remaining branches implement major-zero equality and directional minor compatibility while ignoring builds. Only src/semver/version.py changes, the docstring contains two correct doctests, and observed tool outputs support the reported 312 passing tests and targeted checks.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28658 | 1281 | 0 | - | 58.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28187 | 4606 | 7040 | - | 73.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10931 | 136 | 0 | - | 16.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 25992 | 139 | 12800 | - | 19.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 13194 | 555 | 0 | - | 21.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12324 | 109 | 0 | - | 16.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 13147 | 436 | 0 | - | 17.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 13280 | 148 | 0 | - | 14.6s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 10901 | 2457 | 7040 | - | 49.7s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11813 | 125 | 0 | - | 25.9s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 168427/9992/26880; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1409b-7b09-763d-8860-ab0c7a50afc0 | SUCCESS | 0 | 3.508s | retained | on | 0.022126650000000005 |
| red-1 | 01a1409d-b640-76cf-b04c-fadc5132ccbf | SUCCESS | 0 | 5.168s | disposable | off | 0.044335530000000005 |
| impl-tests-4 | 01a1409e-fdd5-7284-9af8-aa71fcccfcda | SUCCESS | 0 | 1.665s | disposable | off | 0.009471690000000001 |
| impl-python-5 | 01a1409f-5c29-734a-92da-7205d054f202 | SUCCESS | 0 | 0.761s | disposable | off | 0.0030513800000000002 |
| verify | 01a1409f-c53c-76b9-837d-bb7f5338fd5b | SUCCESS | 0 | 6.205s | disposable | off | 0.05216826000000001 |
| heldout | 01a1409f-eece-7264-8881-c3a895d8b64b | SUCCESS | 0 | 1.656s | disposable | off | 0.0095948 |
| mutant-m01-ada25f6f60 | 01a140a0-02e4-771e-a54b-d1010ea73b4f | SUCCESS | 0 | 5.191s | disposable | off | 0.04433963 |
| mutant-m02-297e8672f1 | 01a140a0-0397-72b0-ad0a-1cd80cb4e855 | SUCCESS | 0 | 5.26s | disposable | off | 0.044379550000000004 |
| mutant-m03-8fc1b5a85a | 01a140a0-0432-7647-b8df-5597743397c7 | SUCCESS | 0 | 5.136s | disposable | off | 0.04420607 |
| mutant-m04-843b97c297 | 01a140a0-16aa-70c0-8c05-03b17c1841ec | SUCCESS | 0 | 5.099s | disposable | off | 0.04393925 |
| mutant-m05-ddabf44e6d | 01a140a0-0482-70cb-ae99-63f4bdcf10a1 | SUCCESS | 0 | 5.06s | disposable | off | 0.0439562 |
| mutant-m06-7327d6d2d5 | 01a140a0-0909-7428-a12c-a02ebb1841f2 | SUCCESS | 0 | 5.229s | disposable | off | 0.044537150000000005 |
| mutant-m07-a3fce98723 | 01a140a0-03ab-750d-97ac-037a3a0fe715 | SUCCESS | 0 | 5.138s | disposable | off | 0.04373405 |
| mutant-m08-072cc04269 | 01a140a0-0384-76bf-bfbe-da34cada84dc | SUCCESS | 0 | 5.26s | disposable | off | 0.044236580000000005 |
| mutant-m09-57c234ea01 | 01a140a0-2387-7706-8698-6a1ae8f7885b | SUCCESS | 0 | 5.121s | disposable | off | 0.04387564 |
| mutant-m10-ebbd917cbe | 01a140a0-2b41-71c2-a036-85fefb640932 | SUCCESS | 0 | 5.096s | disposable | off | 0.04408629 |
| mutant-m11-f44639c649 | 01a140a0-2c35-7416-873b-07659f9e510a | SUCCESS | 0 | 5.25s | disposable | off | 0.04457755 |
| mutant-m12-1f691f40df | 01a140a0-2fa2-74b2-9484-69c40892d3cf | SUCCESS | 0 | 5.242s | disposable | off | 0.044474360000000004 |
| breaker-tests | 01a140a1-19d4-77f5-bea1-72d2f7556b8d | SUCCESS | 0 | 2.291s | disposable | off | 0.01676109 |

Sandbox operations: 19, total guest duration 83.336s, retained images ['812476c5-0619-40fd-b769-df0eeecc2529'].

## 11. Limitations of this bundle
- Profile 'phase2-arbitration': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
