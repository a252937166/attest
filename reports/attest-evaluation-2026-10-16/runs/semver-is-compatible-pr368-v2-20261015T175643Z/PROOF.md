# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-20261015T175643Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T17:56:43.560924+00:00, finished 2026-10-15T18:00:46.795766+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `74c1fae2-f687-49c4-8cec-63f20ea61a46`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the `Version` class in `src/semver/version.py`. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a `Version` instance (subclasses allowed), raise `TypeError` with message starting with "Expected a Version type but got " followed by the type representation (e.g., "<class 'str'>"). Add a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True if `other` (the new version) is compatible with `self` (the old version). Compatibility rules: (1) major versions must be equal; (2) other.minor >= | TypeError: raised when `other` is not an instance of Version (or a subclass). Message must start with 'Expected a Version type but got ' followed by the type re |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'
15. Subclass instance accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0f1b5485d6d23fc0ee6984336a495132b83b3cbe9c618c23563d70df9ff990a9`, 15 test methods, sealed at 2026-10-15T17:57:34.488927+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 15 methods: ERROR 15): 15 of 15 methods failing, 0 passing; operation `01a140b6-5252-7380-aa5f-9dc48aea327f`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_is_compatible_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_docstring_has_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_major_zero_different_patch_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_major_zero_identical | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_higher | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_lower | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_prerelease_vs_none_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_same_prerelease_different_patch | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_same_version | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_subclass_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_dict | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_list | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_str | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -681,6 +681,42 @@
             )
             raise TypeError(error)
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """
+        Return True if `other` (the new version) is compatible with `self` (the old version).
+
+        Compatibility rules:
+        1. Major versions must be equal.
+        2. other.minor >= self.minor (patch is ignored).
+        3. Prerelease parts must be equal (both None counts as equal).
+        4. For major version 0, exact equality of major, minor, patch, and prerelease is required.
+
+        Examples:
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+        True
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        # Major version 0 requires exact equality
+        if self.major == 0:
+            return (self.major == other.major and
+                    self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+
+        # For major >= 1
+        if self.major != other.major:
+            return False
+        if self.prerelease != other.prerelease:
+            return False
+        # Patch is ignored, only minor must be >=
+        return other.minor >= self.minor
+
     @classmethod
     def isvalid(cls, version: str) -> bool:
         """
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.60s (312 passed of 312). Sealed suite: OK (15 of 15 methods, each in its own process). Operation `01a140b7-bef7-7636-9a97-5016bbcefb5d`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 328 passed in 0.62s (328 passed of 328); operation `01a140b7-e4ba-777d-8c53-bc59d437a45b`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.60s |
| sealed_binding | pass | all checks pass |
| heldout_suite | pass | 328 passed in 0.62s |
| mutation | pass | score 1.0 on 12 mutants |
| adversarial_tests | pass | OK (12 of 12 methods, each in its own process) |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-ad0a1c7e16 | src/semver/version.py | 702 | remove `not` | killed | test_sealed.TestIsCompatible.test_is_compatible_same_version, test_sealed.TestIsCompatible.test_is_compatible_patch_igno | 01a140b7-fd7b-7267-99a7-970a05363b14 |
| m02-bb0be44a9d | src/semver/version.py | 703 | raise -> pass | killed | test_sealed.TestIsCompatible.test_is_compatible_wrong_type_str, test_sealed.TestIsCompatible.test_is_compatible_wrong_ty | 01a140b7-fdc9-707c-9bd9-13b2526a6c45 |
| m03-5d7f06f094 | src/semver/version.py | 706 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_higher, test_sealed.TestIsCompatible.test_is_compatible_pa | 01a140b7-fe08-7608-aa24-e38ddc1cb0c4 |
| m04-e724966237 | src/semver/version.py | 706 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_higher, test_sealed.TestIsCompatible.test_is_compatible_pa | 01a140b7-fde5-709a-bf2e-71940e94f671 |
| m05-1222a9ccd4 | src/semver/version.py | 707 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_is_compatible_major_zero_identical | 01a140b7-fd86-7783-9535-1a6feb5152c0 |
| m06-a6514f3beb | src/semver/version.py | 708 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_is_compatible_major_zero_identical | 01a140b7-fdff-7646-88e1-233a0d7cf662 |
| m07-ce70f4e924 | src/semver/version.py | 710 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_is_compatible_major_zero_identical | 01a140b7-fda0-728e-91b7-97a7bbc3b6c2 |
| m08-826b2b2097 | src/semver/version.py | 707 | And -> Or | killed | test_sealed.TestIsCompatible.test_is_compatible_major_zero_different_patch_false | 01a140b7-fe54-714d-8568-5ec8c3fdd897 |
| m09-45786a3942 | src/semver/version.py | 713 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_is_compatible_same_version, test_sealed.TestIsCompatible.test_is_compatible_patch_igno | 01a140b8-19d6-713e-8283-680d45896c26 |
| m10-793d26afe7 | src/semver/version.py | 714 | False -> True | killed | test_sealed.TestIsCompatible.test_is_compatible_different_major_false | 01a140b8-221a-7574-913c-7f6fd9707d1f |
| m11-22a15dca4d | src/semver/version.py | 715 | NotEq -> Eq | killed | test_sealed.TestIsCompatible.test_is_compatible_same_version, test_sealed.TestIsCompatible.test_is_compatible_patch_igno | 01a140b8-234a-76a6-b14e-8c0ca8308b24 |
| m12-8f5969dfbd | src/semver/version.py | 716 | False -> True | killed | test_sealed.TestIsCompatible.test_is_compatible_different_prerelease_false, test_sealed.TestIsCompatible.test_is_compati | 01a140b8-25cb-7139-a96e-f0e170a1fb56 |

Model-written adversarial tests (`breaker_tests.py`, by `nvidia/nemotron-3-super-120b-a12b`, sha256 `5134b76dd4665b78cf8cbdbca05e721c7d89396a88a2eefe34a5628392899695`): OK (12 of 12 methods, each in its own process); binding ok; operation `01a140b8-fe90-708b-a180-7567e063f1d7`. Notes: Targeted edge cases: zero-major prerelease/build differences, subclass with extra attributes, overridden __eq__, large patch numbers, and varied TypeError inputs.

(none)

## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fully implements the required Version.is_compatible method with correct semantics for major version equality, minor version comparison, prerelease equality, patch ignorance, and the major-0 special case. The TypeError message format matches the specification exactly, the docstring includes three doctest examples (exceeding the minimum of two), and the existing pytest suite passes without modification. No required behavior was omitted and no extraneous changes were made.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1634 | 17408 | 0.025584 | 10.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20407 | 2988 | 0 | 0.008811 | 18.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2248 | 123 | 0 | 0.000785 | 7.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 8109 | 2388 | 0 | 0.004582 | 16.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2941 | 391 | 0 | 0.001234 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3272 | 411 | 0 | 0.001352 | 4.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3703 | 4187 | 0 | 0.004879 | 24.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 9566 | 2421 | 0 | 0.005049 | 15.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4678 | 615 | 0 | 0.001957 | 5.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 5650 | 112 | 0 | 0.001796 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | default | 2119 | 9053 | 0 | 0.008783 | 45.5s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2817 | 2452 | 0 | 0.010173 | 13.4s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 86192/26775/17408; USD: 0.074985.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140b5-ac91-77d5-940f-d871896154f2 | SUCCESS | 0 | 3.525s | retained | on | 0.0220425 |
| red-1 | 01a140b6-5252-7380-aa5f-9dc48aea327f | SUCCESS | 0 | 3.684s | disposable | off | 0.029846090000000002 |
| impl-tests-7 | 01a140b7-9d27-7347-9dcf-f1d2b8157814 | SUCCESS | 0 | 1.672s | disposable | off | 0.00946691 |
| verify | 01a140b7-bef7-7636-9a97-5016bbcefb5d | SUCCESS | 0 | 4.716s | disposable | off | 0.03792657 |
| heldout | 01a140b7-e4ba-777d-8c53-bc59d437a45b | SUCCESS | 0 | 1.672s | disposable | off | 0.00963189 |
| mutant-m01-ad0a1c7e16 | 01a140b7-fd7b-7267-99a7-970a05363b14 | SUCCESS | 0 | 3.67s | disposable | off | 0.029333860000000003 |
| mutant-m02-bb0be44a9d | 01a140b7-fdc9-707c-9bd9-13b2526a6c45 | SUCCESS | 0 | 3.665s | disposable | off | 0.029325600000000004 |
| mutant-m03-5d7f06f094 | 01a140b7-fe08-7608-aa24-e38ddc1cb0c4 | SUCCESS | 0 | 3.665s | disposable | off | 0.029587550000000004 |
| mutant-m04-e724966237 | 01a140b7-fde5-709a-bf2e-71940e94f671 | SUCCESS | 0 | 3.669s | disposable | off | 0.0295706 |
| mutant-m05-1222a9ccd4 | 01a140b7-fd86-7783-9535-1a6feb5152c0 | SUCCESS | 0 | 3.624s | disposable | off | 0.0291805 |
| mutant-m06-a6514f3beb | 01a140b7-fdff-7646-88e1-233a0d7cf662 | SUCCESS | 0 | 3.667s | disposable | off | 0.02964907 |
| mutant-m07-ce70f4e924 | 01a140b7-fda0-728e-91b7-97a7bbc3b6c2 | SUCCESS | 0 | 3.67s | disposable | off | 0.02956466 |
| mutant-m08-826b2b2097 | 01a140b7-fe54-714d-8568-5ec8c3fdd897 | SUCCESS | 0 | 3.683s | disposable | off | 0.02938968 |
| mutant-m09-45786a3942 | 01a140b8-19d6-713e-8283-680d45896c26 | SUCCESS | 0 | 3.538s | disposable | off | 0.029325160000000003 |
| mutant-m10-793d26afe7 | 01a140b8-221a-7574-913c-7f6fd9707d1f | SUCCESS | 0 | 3.694s | disposable | off | 0.02933668 |
| mutant-m11-22a15dca4d | 01a140b8-234a-76a6-b14e-8c0ca8308b24 | SUCCESS | 0 | 3.742s | disposable | off | 0.029396380000000003 |
| mutant-m12-8f5969dfbd | 01a140b8-25cb-7139-a96e-f0e170a1fb56 | SUCCESS | 0 | 3.669s | disposable | off | 0.0294181 |
| breaker-tests | 01a140b8-fe90-708b-a180-7567e063f1d7 | SUCCESS | 0 | 3.047s | disposable | off | 0.02390109 |

Sandbox operations: 18, total guest duration 62.272s, retained images ['74c1fae2-f687-49c4-8cec-63f20ea61a46'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
