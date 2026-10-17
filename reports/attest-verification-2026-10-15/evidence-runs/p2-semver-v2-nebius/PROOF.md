# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-v2-20261015T160353Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T16:03:53.364516+00:00, finished 2026-10-15T16:05:33.595700+00:00.

Reasons: child process nonzero exit: test_is_compatible_typeerror_str exit 1, test_is_compatible_typeerror_dict exit 1, test_is_compatible_typeerror_list exit 1


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `56faf72d-10a9-4de9-88ae-09d097ab56c5`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the `Version` class in `src/semver/version.py`. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both absent counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a `Version` instance (subclasses allowed), raise `TypeError` with message starting with 'Expected a Version type but got ' followed by the type. Include a docstring with at least two doctest examples. Do not modify tests, docs, packaging, or other public behavior; keep existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) is compatible with `self` (old version). Compatibility rules: 1) Major versions must be equal. 2) New minor >= old minor | TypeError: raised when `other` is not an instance of Version (or subclass). Message must start with 'Expected a Version type but got ' followed by the type repr |

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
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. Method docstring contains at least two doctest examples
17. Existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `071b735e3a1e49c8212c3df199d1dfa9b215401a626da0610086db8f725c01f5`, 15 test methods, sealed at 2026-10-15T16:04:26.924087+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (15 of 15 methods: ERROR 15): 15 of 15 methods failing, 0 passing; operation `01a1404e-c019-71cc-a4ba-419fda878446`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestVersionIsCompatible.test_docstring_contains_at_least_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_equal_prerelease_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_higher_patch_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_lower_patch_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_major0_different_patch_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_major0_identical_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_prerelease_vs_none_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_same_version_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_subclass_accepted_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_typeerror_dict | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_typeerror_list | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestVersionIsCompatible.test_is_compatible_typeerror_str | ERROR (1 ev) | ERROR (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,42 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """Return True if `other` is compatible with `self`.
+
+        Compatibility rules:
+        * Major versions must be equal.
+        * New minor >= old minor.
+        * Prerelease parts must be equal (both None counts as equal).
+        * Patch version is ignored.
+        * For major version 0, only identical versions are compatible.
+
+        Examples:
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+        True
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+        True
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f'Expected a Version type but got {type(other)}')
+
+        # Major versions must be equal
+        if self.major != other.major:
+            return False
+
+        # Major version 0 is special: only identical versions are compatible
+        if self.major == 0:
+            return (self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+
+        # For major > 0: new minor >= old minor and prerelease equal
+        if other.minor < self.minor:
+            return False
+        if self.prerelease != other.prerelease:
+            return False
+        # Patch is ignored
+        return True
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.56s (312 passed of 312). Sealed suite: FAILED (3 of 15 methods: ERROR 3). Operation `01a1404f-8ec8-708a-8b3b-bb863d04a8d2`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 328 passed in 0.66s (328 passed of 328); operation `01a1404f-b024-744c-bc0d-0f764a8c333e`. Gate: failures block VERIFIED.

## 6. Gates
| Gate | Result | Detail |
| --- | --- | --- |
| existing_suite | pass | 312 passed in 0.56s |
| sealed_binding | FAIL | child process nonzero exit: test_is_compatible_typeerror_str exit 1, test_is_compatible_typeerror_dict exit 1, test_is_compatible_typeerror_list exit 1 |
| heldout_suite | pass | 328 passed in 0.66s |
| mutation | FAIL | not run: verification did not pass |
| adversarial_tests | FAIL | not run: verification did not pass |
| drift_audit | pass | score 0.0 (aligned) |

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Score 0.000 (aligned; threshold 0.6). The diff adds the Version.is_compatible method exactly as specified, with correct compatibility logic for major>0 and major==0, proper TypeError messages, and a docstring containing two doctest examples. The existing pytest suite passes without modification, confirming no regression in public behavior.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1878 | 17408 | 0.026316 | 7.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20315 | 1527 | 0 | 0.007469 | 9.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2167 | 121 | 0 | 0.000759 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 8029 | 231 | 0 | 0.002617 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3145 | 301 | 0 | 0.001214 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3334 | 204 | 0 | 0.001184 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3517 | 1298 | 0 | 0.002223 | 7.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 3652 | 1810 | 0 | 0.002725 | 9.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4142 | 1287 | 0 | 0.002401 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 5115 | 112 | 0 | 0.001635 | 3.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2804 | 2286 | 0 | 0.009662 | 7.4s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 76902/11055/17408; USD: 0.058205.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1404e-5e8e-74fd-a69e-6b858ccd4e02 | SUCCESS | 0 | 3.329s | retained | on | 0.021951360000000003 |
| red-1 | 01a1404e-c019-71cc-a4ba-419fda878446 | SUCCESS | 0 | 3.601s | disposable | off | 0.029242560000000004 |
| impl-tests-7 | 01a1404f-6e2c-728d-a880-48704a217ca3 | SUCCESS | 0 | 1.758s | disposable | off | 0.00980192 |
| verify | 01a1404f-8ec8-708a-8b3b-bb863d04a8d2 | SUCCESS | 0 | 4.66s | disposable | off | 0.03745699 |
| heldout | 01a1404f-b024-744c-bc0d-0f764a8c333e | SUCCESS | 0 | 1.688s | disposable | off | 0.009814830000000002 |

Sandbox operations: 5, total guest duration 15.036s, retained images ['56faf72d-10a9-4de9-88ae-09d097ab56c5'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
