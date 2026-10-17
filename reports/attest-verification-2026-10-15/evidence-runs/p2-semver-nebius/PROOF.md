# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-20261015T155824Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:58:24.669888+00:00, finished 2026-10-15T16:03:53.179677+00:00.

Reasons: held-out tests failed: 3 of 328 (tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype1], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrong); resolve the failures or the contract disagreement before this patch can be verified; model-written adversarial tests failed: 1 of 12 (test_breaker.TestVersionIsCompatible.test_docstring_doctests); each failure is a bug or a contract disagreement to resolve


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `3f565944-bbe7-45d4-aa18-98c3299c0c6b`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the Version class in src/semver/version.py. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting 'Expected a Version type'. Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging; keep the existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) can be used in place of `self` (old version). Compatibility rules: (1) self.major == other.major; (2) other.minor >= sel | TypeError: raised when `other` is not an instance of Version (or a subclass); message must start with 'Expected a Version type' |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting 'Expected a Version type'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting 'Expected a Version type'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting 'Expected a Version type'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `2d3a0098298e12662c1ae8bd4a9ee9fdd2e474c982f25219c78bb8d9ef1f0a33`, 15 test methods, sealed at 2026-10-15T15:59:46.241151+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 15 methods: ERROR 15): 15 of 15 methods failing, 0 passing; operation `01a1404a-7675-70cb-8f7f-aa90b5008301`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_docstring_has_doctests | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_equal_prerelease_allow_minor_increase | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical_false_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_higher | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_lower | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_vs_none_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_version_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_dict | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_string | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 9 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,45 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """
+        Return True if `other` (new version) can be used in place of `self` (old version).
+
+        Compatibility rules:
+            - Majors must be equal.
+            - The new minor must be greater than or equal to the old minor.
+            - Prerelease parts must be equal (both None counts as equal).
+            - Patch is ignored.
+            - For major version 0, only identical versions (major, minor, patch, prerelease) are compatible.
+
+        Examples:
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+            True
+            >>> Version(1, 2, 4).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+            False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type")
+
+        if self.major == 0:
+            return (self.major == other.major and
+                    self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+        else:
+            return (self.major == other.major and
+                    other.minor >= self.minor and
+                    self.prerelease == other.prerelease)
+
+
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.64s (312 passed of 312). Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a1404d-0674-7415-a6d8-5d16bca93f4e`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.65s (325 passed of 328); operation `01a1404d-366a-721b-ae65-740fc268fe7f`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.64s |
| sealed_binding | pass | all checks pass |
| heldout_suite | FAIL | 3 failed, 325 passed in 0.65s |
| mutation | pass | score 1.0 on 12 mutants |
| adversarial_tests | FAIL | FAILED (1 of 12 methods: ERROR 1) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-d8a47885c8 | src/semver/version.py | 727 | remove `not` | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed | 01a1404d-6676-76fe-a6f7-7a52b33526b2 |
| m02-5ee9552f74 | src/semver/version.py | 728 | raise -> pass | killed | test_sealed.TestIsCompatible.test_wrong_type_string, test_sealed.TestIsCompatible.test_wrong_type_dict, test_sealed.Test | 01a1404d-53a1-73b5-8c03-aee19b9c08b2 |
| m03-3ee418441c | src/semver/version.py | 730 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed.TestIsCompatible.test_patch_ignored_lower, test_seal | 01a1404d-53eb-77f8-a2da-45e502fe9f30 |
| m04-1567bd5e9f | src/semver/version.py | 730 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed.TestIsCompatible.test_patch_ignored_lower, test_seal | 01a1404d-539e-71a7-9376-d70f96c60c9c |
| m05-7ccfcabb55 | src/semver/version.py | 731 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a1404d-54bf-755c-9055-d0719e7030d5 |
| m06-4713c177c9 | src/semver/version.py | 732 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a1404d-5348-748a-97a0-166eef4bbc21 |
| m07-43c17d70cc | src/semver/version.py | 733 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true, test_sealed.TestIsCompatible.test_major_zero_identical_fals | 01a1404d-5ed8-7736-b948-3cd91e541f27 |
| m08-8c35dc7a99 | src/semver/version.py | 734 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical_true | 01a1404d-53de-7375-bda8-013011bbd9c2 |
| m09-1b6d2bc6f1 | src/semver/version.py | 731 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_identical_false_patch | 01a1404d-6fe8-760b-9c1c-7cf45a1c7e27 |
| m10-9fe76a7bce | src/semver/version.py | 736 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed | 01a1404d-7148-77e0-a78a-ef94f1cd0c7d |
| m11-efd8454df3 | src/semver/version.py | 737 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed | 01a1404d-72b0-779c-aabb-d774554db702 |
| m12-950ed72c7f | src/semver/version.py | 738 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_same_version_true, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed | 01a1404d-72a9-7722-8292-b8e70477c385 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `33babf9ee91cf2c3d54fd2be92e33949cfd71067fc2cdd131b62328915d80885`): FAILED (1 of 12 methods: ERROR 1); binding FAILED; operation `01a1404e-1811-7290-85d3-97577df17e56`. Notes: Targeted build metadata, prerelease empty string vs None, complex prerelease, wrong types, subclass reverse, doctest, and patch/lower boundary.

| Failing adversarial test | Outcome |
| --- | --- |
| test_docstring_doctests | ERROR |

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the Version.is_compatible method exactly as specified, with correct semantics for major/minor/prerelease/patch comparison, major-0 special case, TypeError for non-Version types, and a docstring with six doctest examples. The existing pytest suite passes (312 tests), and the implementer's verification script confirms all acceptance criteria.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
2 Tavily call(s) for 2 queries; 6 sources cited below.

| Query | Title | URL |
| --- | --- | --- |
| Semantic Versioning 2.0.0 specification (https://semver.org/spec/v2.0.0.html) for compatibility rules | Semantic Versioning 2.0.0 \| Semantic Versioning | https://semver.org |
| Semantic Versioning 2.0.0 specification (https://semver.org/spec/v2.0.0.html) for compatibility rules | Semantic Versioning 2.0.0 \| Ethereum Improvement Proposals | https://eips.ethereum.org/assets/eip-5139/semver |
| Semantic Versioning 2.0.0 specification (https://semver.org/spec/v2.0.0.html) for compatibility rules | Semantic Versioning 2.0.0-rc.1 \| Semantic Versioning | https://semver.org/spec/v2.0.0-rc.1.html |
| python-semver existing Version class API (src/semver/version.py) | Releases · python-semver/python-semver · GitHub | https://github.com/python-semver/python-semver/releases |
| python-semver existing Version class API (src/semver/version.py) | 8. API Reference — python-semver 3.0.4 documentation | https://python-semver.readthedocs.io/en/3.0.4/api.html |
| python-semver existing Version class API (src/semver/version.py) | Versioning and formatting your Python code - Jacob Tomlinson | https://jacobtomlinson.dev/posts/2020/versioning-and-formatting-your-python-code |

## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20617 | 1628 | 17408 | 0.025501 | 7.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 21256 | 2024 | 0 | 0.008198 | 17.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 3074 | 147 | 0 | 0.001054 | 8.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 3862 | 158 | 0 | 0.001301 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 4479 | 116 | 0 | 0.001448 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4956 | 435 | 0 | 0.001878 | 5.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 8096 | 4945 | 0 | 0.006879 | 26.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 5638 | 100 | 0 | 0.001781 | 11.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 6617 | 1042 | 0 | 0.002923 | 9.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 6499 | 16000 | 0 | 0.016350 | 64.2s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8-repair | default | 6589 | 1533 | 0 | 0.003356 | 14.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 7170 | 102 | 0 | 0.002243 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 3007 | 8029 | 0 | 0.008128 | 34.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2791 | 2785 | 0 | 0.011146 | 8.5s | ok |

Model calls: 14 (1 failed, 1 malformed); tokens in/out/cached 104651/39044/17408; USD: 0.092186.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14049-a973-7019-8a4b-989d987da244 | SUCCESS | 0 | 3.278s | retained | on | 0.02186729 |
| red-1 | 01a1404a-7675-70cb-8f7f-aa90b5008301 | SUCCESS | 0 | 3.592s | disposable | off | 0.029300670000000004 |
| impl-tests-6 | 01a1404b-770f-7387-93cb-ce94ebbd0d8b | SUCCESS | 0 | 1.706s | disposable | off | 0.00943141 |
| impl-python-8 | 01a1404c-e9b8-7153-ba50-4405517d25f9 | SUCCESS | 0 | 0.94s | disposable | off | 0.00233 |
| verify | 01a1404d-0674-7415-a6d8-5d16bca93f4e | SUCCESS | 0 | 4.899s | disposable | off | 0.03850237 |
| heldout | 01a1404d-366a-721b-ae65-740fc268fe7f | SUCCESS | 0 | 1.75s | disposable | off | 0.009919250000000001 |
| mutant-m01-d8a47885c8 | 01a1404d-6676-76fe-a6f7-7a52b33526b2 | SUCCESS | 0 | 3.577s | disposable | off | 0.029072650000000005 |
| mutant-m02-5ee9552f74 | 01a1404d-53a1-73b5-8c03-aee19b9c08b2 | SUCCESS | 0 | 3.719s | disposable | off | 0.029766690000000005 |
| mutant-m03-3ee418441c | 01a1404d-53eb-77f8-a2da-45e502fe9f30 | SUCCESS | 0 | 3.712s | disposable | off | 0.029689470000000003 |
| mutant-m04-1567bd5e9f | 01a1404d-539e-71a7-9376-d70f96c60c9c | SUCCESS | 0 | 3.696s | disposable | off | 0.029589070000000002 |
| mutant-m05-7ccfcabb55 | 01a1404d-54bf-755c-9055-d0719e7030d5 | SUCCESS | 0 | 3.769s | disposable | off | 0.030122770000000004 |
| mutant-m06-4713c177c9 | 01a1404d-5348-748a-97a0-166eef4bbc21 | SUCCESS | 0 | 3.729s | disposable | off | 0.02998687 |
| mutant-m07-43c17d70cc | 01a1404d-5ed8-7736-b948-3cd91e541f27 | SUCCESS | 0 | 3.698s | disposable | off | 0.029389720000000005 |
| mutant-m08-8c35dc7a99 | 01a1404d-53de-7375-bda8-013011bbd9c2 | SUCCESS | 0 | 3.739s | disposable | off | 0.02983712 |
| mutant-m09-1b6d2bc6f1 | 01a1404d-6fe8-760b-9c1c-7cf45a1c7e27 | SUCCESS | 0 | 3.622s | disposable | off | 0.029342420000000004 |
| mutant-m10-9fe76a7bce | 01a1404d-7148-77e0-a78a-ef94f1cd0c7d | SUCCESS | 0 | 3.559s | disposable | off | 0.029151840000000002 |
| mutant-m11-efd8454df3 | 01a1404d-72b0-779c-aabb-d774554db702 | SUCCESS | 0 | 3.55s | disposable | off | 0.02897496 |
| mutant-m12-950ed72c7f | 01a1404d-72a9-7722-8292-b8e70477c385 | SUCCESS | 0 | 3.546s | disposable | off | 0.029086260000000003 |
| breaker-tests | 01a1404e-1811-7290-85d3-97577df17e56 | SUCCESS | 0 | 3.351s | disposable | off | 0.02693078 |

Sandbox operations: 19, total guest duration 63.432s, retained images ['3f565944-bbe7-45d4-aa18-98c3299c0c6b'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
