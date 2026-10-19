# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-20261015T182727Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:27:27.898580+00:00, finished 2026-10-15T18:30:35.714785+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `7f57ff5e-02b8-449a-9c13-c903a0b99c91`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: 'Version') -> bool` to the Version class in src/semver/version.py. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting with 'Expected a Version type but got ' followed by the type representation. Add a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging; keep the existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True when `other` (new version) is compatible with `self` (old version). Compatibility rules: 1) major versions must be equal. 2) If major == 0, version | TypeError: raised when `other` is not an instance of Version (or subclass). Message must start with 'Expected a Version type but got ' followed by the type repr |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (identical major-0 versions)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (new minor < old minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease differs: None vs 'rc1')
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease differs: 'rc1' vs None)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got '
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got '
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got '
15. Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `f40f4be1d0da06b7df0067caeacadd65030f49821bf8efc7610b78500305854e`, 16 test methods, sealed at 2026-10-15T18:28:09.623004+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a140d2-48cb-72c3-8cc4-1545a13f8eb1`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_docstring_has_at_least_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_equal_prerelease_returns_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_different_patch_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical_returns_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_new_minor_less_than_old_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_when_new_patch_higher | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_when_old_patch_higher | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_differs_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_none_vs_string_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_string_vs_none_returns_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_version_returns_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_dict_raises_typeerror | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_list_raises_typeerror | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_string_raises_typeerror | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,40 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """
+        Return True if `other` is compatible with `self`.
+
+        Compatibility rules:
+          - Major versions must be equal.
+          - If major == 0, then the versions must be identical in major, minor, patch, and prerelease.
+          - If major > 0, then other.minor must be >= self.minor and the prerelease must be the same (both None counts as equal).
+            The patch version is ignored.
+
+        Examples:
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+            False
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        if self.major != other.major:
+            return False
+
+        if self.major == 0:
+            return (self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+
+        # major > 0
+        return (other.minor >= self.minor and
+                self.prerelease == other.prerelease)
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.60s (312 passed of 312). Sealed suite: OK (16 of 16 methods, each in its own process). Operation `01a140d3-18a3-7526-881e-8c8cab4e48d4`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 328 passed in 0.63s (328 passed of 328); operation `01a140d3-40ac-708c-95a9-76aac57551b6`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.60s |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | 328 passed in 0.63s |
| mutation | pass | score 1.0 on 12 mutants |
| adversarial_tests | pass | OK (11 of 11 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-25a440c6c0 | src/semver/version.py | 722 | remove `not` | killed | test_sealed.TestIsCompatible.test_same_version_returns_true, test_sealed.TestIsCompatible.test_patch_ignored_when_new_pa | 01a140d3-6068-73c1-9d36-e0012e9095cb |
| m02-e626cf22f4 | src/semver/version.py | 723 | raise -> pass | killed | test_sealed.TestIsCompatible.test_wrong_type_string_raises_typeerror, test_sealed.TestIsCompatible.test_wrong_type_dict_ | 01a140d3-6b6c-7771-8f86-6b49a98524f9 |
| m03-1532c0c3a7 | src/semver/version.py | 725 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_same_version_returns_true, test_sealed.TestIsCompatible.test_patch_ignored_when_new_pa | 01a140d3-60f1-7463-9f94-b16fbb05d2fa |
| m04-62ac0e814c | src/semver/version.py | 726 | False -> True | killed | test_sealed.TestIsCompatible.test_different_major_returns_false | 01a140d3-7661-7594-8ad9-96a3a0c7a5ba |
| m05-d52ee6dd29 | src/semver/version.py | 728 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_patch_ignored_when_new_patch_higher, test_sealed.TestIsCompatible.test_patch_ignored_w | 01a140d3-60de-7782-9316-3b0ddd7bd3fa |
| m06-239132b412 | src/semver/version.py | 728 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_patch_ignored_when_new_patch_higher, test_sealed.TestIsCompatible.test_patch_ignored_w | 01a140d3-6114-70cf-ab16-9be0a5e30455 |
| m07-e8cba45bae | src/semver/version.py | 729 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_returns_true | 01a140d3-60ed-743e-9301-bc2aca389bc6 |
| m08-d064e7ecff | src/semver/version.py | 730 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_returns_true, test_sealed.TestIsCompatible.test_major_zero_differ | 01a140d3-600c-70b8-8a19-14b436fbfb74 |
| m09-9d0f5a990c | src/semver/version.py | 731 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_returns_true | 01a140d3-8cf6-7089-b92d-443118fda584 |
| m10-c589c206b3 | src/semver/version.py | 729 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_different_patch_returns_false | 01a140d3-c474-7104-aa95-5e4101eef871 |
| m11-2c3fe12ff6 | src/semver/version.py | 734 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_same_version_returns_true, test_sealed.TestIsCompatible.test_patch_ignored_when_new_pa | 01a140d3-8d74-7441-8794-4af51e9133ea |
| m12-34f93c215e | src/semver/version.py | 735 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_returns_true, test_sealed.TestIsCompatible.test_patch_ignored_when_new_pa | 01a140d3-8d6f-71d8-b8c1-56bbfba4684e |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `4021a7e9b1a58f9f7cc12b7f8907bb8024879a39a705cb4e0402c4d1677f998a`): OK (11 of 11 methods, each in its own process); binding ok; operation `01a140d4-5607-75b6-8e19-3e67f9dd6623`. Notes: Targeted edge cases: major zero minor/prerelease differences, positive major prerelease None handling, non‑container wrong types.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the Version.is_compatible method exactly as specified, including correct compatibility logic for major 0 and major > 0, proper TypeError with the required message format, and a docstring with four doctest examples. The existing test suite passes without modification, confirming no regression.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1663 | 17408 | 0.025671 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20387 | 3663 | 0 | 0.009413 | 15.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2219 | 112 | 0 | 0.000766 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 8079 | 5341 | 0 | 0.007231 | 27.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3175 | 152 | 0 | 0.001089 | 4.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4149 | 129 | 0 | 0.001361 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 2098 | 6211 | 0 | 0.006219 | 29.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2467 | 2437 | 0 | 0.009778 | 12.1s | ok |

Model calls: 8 (0 failed, 0 malformed); tokens in/out/cached 63256/19708/17408; USD: 0.061528.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140d1-d09b-7382-9c88-8c8ba0b31ac6 | SUCCESS | 0 | 3.485s | retained | on | 0.022501830000000004 |
| red-1 | 01a140d2-48cb-72c3-8cc4-1545a13f8eb1 | SUCCESS | 0 | 3.833s | disposable | off | 0.03149397 |
| impl-tests-3 | 01a140d2-f158-7006-9e66-64abe94e3604 | SUCCESS | 0 | 1.639s | disposable | off | 0.00939839 |
| verify | 01a140d3-18a3-7526-881e-8c8cab4e48d4 | SUCCESS | 0 | 4.934s | disposable | off | 0.03963888 |
| heldout | 01a140d3-40ac-708c-95a9-76aac57551b6 | SUCCESS | 0 | 1.709s | disposable | off | 0.00963235 |
| mutant-m01-25a440c6c0 | 01a140d3-6068-73c1-9d36-e0012e9095cb | SUCCESS | 0 | 3.808s | disposable | off | 0.0314195 |
| mutant-m02-e626cf22f4 | 01a140d3-6b6c-7771-8f86-6b49a98524f9 | SUCCESS | 0 | 3.877s | disposable | off | 0.03153799 |
| mutant-m03-1532c0c3a7 | 01a140d3-60f1-7463-9f94-b16fbb05d2fa | SUCCESS | 0 | 3.789s | disposable | off | 0.03099594 |
| mutant-m04-62ac0e814c | 01a140d3-7661-7594-8ad9-96a3a0c7a5ba | SUCCESS | 0 | 3.706s | disposable | off | 0.031148870000000002 |
| mutant-m06-239132b412 | 01a140d3-6114-70cf-ab16-9be0a5e30455 | SUCCESS | 0 | 3.868s | disposable | off | 0.03149736 |
| mutant-m08-d064e7ecff | 01a140d3-600c-70b8-8a19-14b436fbfb74 | SUCCESS | 0 | 3.778s | disposable | off | 0.031202250000000004 |
| mutant-m07-e8cba45bae | 01a140d3-60ed-743e-9301-bc2aca389bc6 | SUCCESS | 0 | 3.799s | disposable | off | 0.03129982 |
| mutant-m05-d52ee6dd29 | 01a140d3-60de-7782-9316-3b0ddd7bd3fa | SUCCESS | 0 | 3.778s | disposable | off | 0.031121350000000002 |
| mutant-m09-9d0f5a990c | 01a140d3-8cf6-7089-b92d-443118fda584 | SUCCESS | 0 | 3.803s | disposable | off | 0.031165370000000005 |
| mutant-m10-c589c206b3 | 01a140d3-c474-7104-aa95-5e4101eef871 | SUCCESS | 0 | 3.868s | disposable | off | 0.03114255 |
| mutant-m11-2c3fe12ff6 | 01a140d3-8d74-7441-8794-4af51e9133ea | SUCCESS | 0 | 3.829s | disposable | off | 0.031446310000000005 |
| mutant-m12-34f93c215e | 01a140d3-8d6f-71d8-b8c1-56bbfba4684e | SUCCESS | 0 | 3.824s | disposable | off | 0.03136183 |
| breaker-tests | 01a140d4-5607-75b6-8e19-3e67f9dd6623 | SUCCESS | 0 | 2.861s | disposable | off | 0.022087940000000004 |

Sandbox operations: 18, total guest duration 64.188s, retained images ['7f57ff5e-02b8-449a-9c13-c903a0b99c91'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
