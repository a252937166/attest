# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-20261015T152816Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:28:16.409115+00:00, finished 2026-10-15T15:30:41.006549+00:00.

Reasons: held-out tests failed: 3 of 328 (tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrongtype1], tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_match[wrong); resolve the failures or the contract disagreement before this patch can be verified
Warnings: adversarial tests skipped: only 0 adversarial tests were written

## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d083356e-df4e-47a7-9f42-3dbd051687bd`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the `Version` class in `src/semver/version.py`. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both absent counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a `Version` instance (subclasses allowed), raise `TypeError` with a message starting with 'Expected a Version type'. Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging files; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) can be used in place of `self` (old version). Compatibility rules: (1) `self.major == other.major`; (2) `other.minor >=  | TypeError with message starting with 'Expected a Version type' if `other` is not an instance of `Version` (or a subclass thereof). |

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
16. The method's docstring contains at least two doctest examples
17. The existing pytest test suite (tests/) continues to pass without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `3d5f854eabf9aed3e824093534ea34c335eec2e488fd30af0fd86856cf18bb23`, 16 test methods, sealed at 2026-10-15T15:28:53.274610+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a1402e-2dbd-7679-b627-693f8c204ae3`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_docstring_has_at_least_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_equal_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_identical_versions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_different_patch_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_identical | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_none_vs_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_higher | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_patch_ignored_lower | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_vs_none_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_type_error_dict | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_type_error_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_type_error_string | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,32 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """
+        Return True if ``other`` (new version) can be used in place of ``self`` (old version).
+
+        Compatibility rules:
+        * Majors must be equal.
+        * New minor must be greater than or equal to old minor.
+        * Prerelease parts must be equal (both absent counts as equal).
+        * Patch is ignored.
+        * For major version 0, exact equality of major, minor, patch, and prerelease is required
+          (build is still ignored).
+
+        Examples::
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+            True
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type")
+        if self.major == 0:
+            return (self.major, self.minor, self.patch, self.prerelease) == \
+                   (other.major, other.minor, other.patch, other.prerelease)
+        return (self.major == other.major and
+                other.minor >= self.minor and
+                self.prerelease == other.prerelease)
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.64s (312 passed of 312). Sealed suite: OK (16 of 16 methods, each in its own process). Operation `01a1402e-fdc4-763e-9cdd-78cf934ea088`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.70s (325 passed of 328); operation `01a1402f-289f-761f-9e75-ba34aa13ef48`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.64s |
| sealed_binding | pass | all checks pass |
| heldout_suite | FAIL | 3 failed, 325 passed in 0.70s |
| mutation | pass | score 1.0 on 9 mutants |
| adversarial_tests | pass | only 0 adversarial tests were written |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 9 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f7bba2f6e5 | src/semver/version.py | 720 | remove `not` | killed | test_sealed.TestIsCompatible.test_identical_versions, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_seale | 01a1402f-4128-7247-907b-2a8de0f5f5e3 |
| m02-8d1d199e46 | src/semver/version.py | 721 | raise -> pass | killed | test_sealed.TestIsCompatible.test_type_error_string, test_sealed.TestIsCompatible.test_type_error_dict, test_sealed.Test | 01a1402f-4100-7079-b2d8-2d38dc886d75 |
| m03-9b3ddca7c1 | src/semver/version.py | 722 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed.TestIsCompatible.test_patch_ignored_lower, test_seal | 01a1402f-4122-76d9-b8d7-82af493d1e27 |
| m04-debbe0bcd9 | src/semver/version.py | 722 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_patch_ignored_higher, test_sealed.TestIsCompatible.test_patch_ignored_lower, test_seal | 01a1402f-3ff0-7742-9d90-e4dfacab8b11 |
| m05-35f90225a6 | src/semver/version.py | 723 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_identical, test_sealed.TestIsCompatible.test_major_zero_different_patch_fal | 01a1402f-4079-7395-8e8d-10b5f5d867f4 |
| m06-8ce94c3cb7 | src/semver/version.py | 725 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_identical_versions, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_seale | 01a1402f-4165-73d5-8b51-89fda48ff3fa |
| m07-f3d2d32480 | src/semver/version.py | 726 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_identical_versions, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_seale | 01a1402f-40f6-759e-91a2-80d3e2b972d7 |
| m08-9e35902929 | src/semver/version.py | 727 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_identical_versions, test_sealed.TestIsCompatible.test_patch_ignored_higher, test_seale | 01a1402f-409a-75ce-817a-449dc48b587a |
| m09-be45145908 | src/semver/version.py | 725 | And -> Or | killed | test_sealed.TestIsCompatible.test_lower_minor_false, test_sealed.TestIsCompatible.test_different_major_false, test_seale | 01a1402f-68c4-761d-8378-aae0ecf17a3c |

Model-written adversarial tests: skipped (only 0 adversarial tests were written)



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the Version.is_compatible method exactly as specified: it enforces major equality, requires new.minor >= old.minor, compares prerelease for equality (treating absent as equal), ignores patch for major > 0, and demands full equality for major 0. The TypeError message matches the required prefix, subclasses are accepted via isinstance, the docstring includes two doctest examples, and the existing 312-test suite passes without modification.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20617 | 1543 | 17408 | 0.025246 | 6.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20266 | 2163 | 0 | 0.008026 | 11.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2095 | 112 | 0 | 0.000729 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 7954 | 366 | 0 | 0.002716 | 4.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2726 | 220 | 0 | 0.001016 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 2958 | 1202 | 0 | 0.001969 | 7.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3178 | 1685 | 0 | 0.002470 | 10.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3419 | 1299 | 0 | 0.002195 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 3879 | 95 | 0 | 0.001249 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 4853 | 114 | 0 | 0.001558 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests | default | 1874 | 2125 | 0 | 0.002475 | 12.0s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2644 | 2762 | 0 | 0.010930 | 10.5s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 76463/13686/17408; USD: 0.060579.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1402d-c686-71c1-b543-b66135b25cf6 | SUCCESS | 0 | 3.63s | retained | on | 0.022351620000000003 |
| red-1 | 01a1402e-2dbd-7679-b627-693f8c204ae3 | SUCCESS | 0 | 3.827s | disposable | off | 0.03138703 |
| impl-tests-7 | 01a1402e-def8-73aa-9ddd-8edda338f72d | SUCCESS | 0 | 1.76s | disposable | off | 0.0096608 |
| verify | 01a1402e-fdc4-763e-9cdd-78cf934ea088 | SUCCESS | 0 | 5.021s | disposable | off | 0.03989466 |
| heldout | 01a1402f-289f-761f-9e75-ba34aa13ef48 | SUCCESS | 0 | 1.796s | disposable | off | 0.010144 |
| mutant-m01-f7bba2f6e5 | 01a1402f-4128-7247-907b-2a8de0f5f5e3 | SUCCESS | 0 | 3.894s | disposable | off | 0.03132224 |
| mutant-m02-8d1d199e46 | 01a1402f-4100-7079-b2d8-2d38dc886d75 | SUCCESS | 0 | 3.868s | disposable | off | 0.031081310000000004 |
| mutant-m03-9b3ddca7c1 | 01a1402f-4122-76d9-b8d7-82af493d1e27 | SUCCESS | 0 | 3.894s | disposable | off | 0.031200890000000002 |
| mutant-m05-35f90225a6 | 01a1402f-4079-7395-8e8d-10b5f5d867f4 | SUCCESS | 0 | 3.893s | disposable | off | 0.03125061 |
| mutant-m06-8ce94c3cb7 | 01a1402f-4165-73d5-8b51-89fda48ff3fa | SUCCESS | 0 | 3.907s | disposable | off | 0.031227360000000003 |
| mutant-m07-f3d2d32480 | 01a1402f-40f6-759e-91a2-80d3e2b972d7 | SUCCESS | 0 | 3.852s | disposable | off | 0.03093568 |
| mutant-m04-debbe0bcd9 | 01a1402f-3ff0-7742-9d90-e4dfacab8b11 | SUCCESS | 0 | 3.871s | disposable | off | 0.031012550000000003 |
| mutant-m08-9e35902929 | 01a1402f-409a-75ce-817a-449dc48b587a | SUCCESS | 0 | 3.882s | disposable | off | 0.03104815 |
| mutant-m09-be45145908 | 01a1402f-68c4-761d-8378-aae0ecf17a3c | SUCCESS | 0 | 3.832s | disposable | off | 0.031169640000000002 |

Sandbox operations: 14, total guest duration 50.927s, retained images ['d083356e-df4e-47a7-9f42-3dbd051687bd'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
