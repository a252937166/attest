# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-v2-20261015T161325Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T16:13:25.272664+00:00, finished 2026-10-15T16:17:29.789411+00:00.

Reasons: implementer did not finish within 14 turns; existing test suite failed on the candidate: no summary; child process nonzero exit: test_is_compatible_same_version exit 1, test_is_compatible_higher_patch_ignored exit 1, test_is_compatible_lower_patch_ignored exit 1, test_is_compatible_same_prerelease exit 1, test_is_compatible_major_zero_identical exit 1, test_is_compatible_major_zero_different_patch_false exit 1, test_is_compat; held-out tests failed: 0 of 0 (); resolve the failures or the contract disagreement before this patch can be verified; drift audit score 0.85 (off_target): The diff fails to implement the required method correctly; it corrupts the existing `isvalid` method and places `is_compatible` in the wrong scope. The test suite exits with error code 4, confirming t


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `a0cb7a06-f813-40ca-b8e0-b7f2c3920e2f`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the Version class in src/semver/version.py. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting with 'Expected a Version type but got ' followed by the type representation. Add a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging; keep the existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) can replace `self` (old version) per semantic versioning compatibility rules: majors equal; other.minor >= self.minor; p | TypeError: raised when `other` is not an instance of Version (or subclass); message must start with 'Expected a Version type but got ' followed by the type repr |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `420b5b80256d0556ebcae58fbbc20874af2894dc30b5512980ec8785cb944406`, 16 test methods, sealed at 2026-10-15T16:14:08.730502+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a14057-a0bd-76ee-ad35-e7445d6ddfc5`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_is_compatible_different_major_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_different_prerelease_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_docstring_has_two_doctest_examples | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_higher_patch_ignored | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_lower_minor_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_lower_patch_ignored | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_major_zero_different_patch_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_major_zero_identical | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_same_prerelease | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_same_version | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_self_has_prerelease_other_none_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_self_none_other_has_prerelease_false | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_subclass_accepted | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_dict_raises_typeerror | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_list_raises_typeerror | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_str_raises_typeerror | ERROR (1 ev) | ERROR (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 14 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -695,8 +695,61 @@
         try:
             cls.parse(version)
             return True
-        except ValueError:
-            return False
+        def is_compatible(self, other: 'Version') -> bool:
+            """Return True if `other` (new version) is compatible with `self` (old version).
+
+            Compatibility rules:
+            - Majors must be equal.
+            - For major version 0, only identical versions are compatible.
+            - For major version >= 1, the new minor must be >= old minor, and prerelease must be equal.
+            - Patch is ignored.
+
+            Examples:
+                >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+                True
+                >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+                True
+                >>> Version(1, 2, 4).is_compatible(Version(1, 2, 3))
+                True
+                >>> Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
+                True
+                >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+                True
+                >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+                False
+                >>> Version(1, 1, 0).is_compatible(Version(1, 0, 0))
+                False
+                >>> Version(2, 0, 0).is_compatible(Version(1, 5, 0))
+                False
+                >>> Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
+                False
+                >>> Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
+                False
+                >>> Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
+                False
+
+            :param other: The version to compare with.
+            :return: True if compatible, False otherwise.
+            :raises TypeError: If `other` is not a Version instance (or subclass).
+            """
+            if not isinstance(other, Version):
+                raise TypeError(f"Expected a Version type but got {type(other)}")
+
+            # Major version 0 is special: only identical versions are compatible.
+            if self.major == 0:
+                return (self.major, self.minor, self.patch, self.prerelease) == \
+                       (other.major, other.minor, other.patch, other.prerelease)
+
+            # For major >= 1:
+            if self.major != other.major:
+                return False
+            if other.minor < self.minor:
+                return False
+            # Prerelease must be equal (both None counts as equal)
+            if self.prerelease != other.prerelease:
+                return False
+            # Patch is ignored
+            return True
 
 
 #: Keep the VersionInfo name for compatibility
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: no summary (0 passed of 0). Sealed suite: FAILED (16 of 16 methods: ERROR 16). Operation `01a1405a-8a4b-73bd-9286-b8d00e91d000`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): no summary (0 passed of 0); operation `01a1405a-a841-7744-8bc9-56d69078a71a`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | FAIL | no summary |
| sealed_binding | FAIL | child process nonzero exit: test_is_compatible_same_version exit 1, test_is_compatible_higher_patch_ignored exit 1, test_is_compatible_lower_patch_ignored exit 1, test_is_compatible_same_prerelease exit 1, test_is_compatible_major_zero_identical exit 1, test_is_compatible_major_zero_different_patch_false exit 1, test_is_compat |
| heldout_suite | FAIL | no summary |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | FAIL | score 0.85 |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.850 (off_target; threshold 0.6). The diff fails to implement the required method correctly; it corrupts the existing `isvalid` method and places `is_compatible` in the wrong scope. The test suite exits with error code 4, confirming the breakage.

Scope narrowed: The existing `isvalid` classmethod is broken: its `except ValueError: return False` block was removed and replaced with the new method, so `isvalid` will now raise an unhandled exception on invalid versions.  
Scope widened: The `is_compatible` method was inserted inside the `isvalid` classmethod (at the same indentation level as the `try` block) instead of as a separate instance method of the Version class, altering the class structure in an unintended way.  
Unsupported claims: Action turn 10: 'Insert is_compatible method after isvalid classmethod' – the diff shows the method replaced the exception handler of `isvalid`, not inserted after it.

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1560 | 17408 | 0.025362 | 7.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20352 | 3219 | 0 | 0.009003 | 16.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2096 | 138 | 0 | 0.000753 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 7956 | 2067 | 0 | 0.004247 | 10.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2791 | 400 | 0 | 0.001197 | 3.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3788 | 1083 | 0 | 0.002111 | 6.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3566 | 3747 | 0 | 0.004442 | 16.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 4509 | 13668 | 0 | 0.013654 | 62.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4689 | 926 | 0 | 0.002240 | 6.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 5113 | 1512 | 0 | 0.002895 | 11.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 5293 | 2020 | 0 | 0.003406 | 10.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 5026 | 5584 | 0 | 0.006533 | 24.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 5720 | 96 | 0 | 0.001802 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 5303 | 433 | 0 | 0.001981 | 4.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 5709 | 1631 | 0 | 0.003181 | 9.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-14 | default | 5142 | 844 | 0 | 0.002302 | 5.9s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3484 | 1095 | 0 | 0.006769 | 4.9s | ok |

Model calls: 17 (0 failed, 0 malformed); tokens in/out/cached 111219/40023/17408; USD: 0.091878.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14057-2008-73bf-b0fa-d7309e2a8524 | SUCCESS | 0 | 3.321s | retained | on | 0.02212701 |
| red-1 | 01a14057-a0bd-76ee-ad35-e7445d6ddfc5 | SUCCESS | 0 | 3.876s | disposable | off | 0.031146730000000004 |
| impl-tests-11 | 01a1405a-27b7-7584-b92d-e86799946667 | SUCCESS | 0 | 1.127s | disposable | off | 0.00540802 |
| verify | 01a1405a-8a4b-73bd-9286-b8d00e91d000 | SUCCESS | 0 | 4.254s | disposable | off | 0.03485161 |
| heldout | 01a1405a-a841-7744-8bc9-56d69078a71a | SUCCESS | 0 | 1.048s | disposable | off | 0.005136000000000001 |

Sandbox operations: 5, total guest duration 13.626s, retained images ['a0cb7a06-f813-40ca-b8e0-b7f2c3920e2f'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
