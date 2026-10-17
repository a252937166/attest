# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-20261015T134125Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T13:41:25.128349+00:00, finished 2026-10-15T13:43:02.107255+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6191663e-795c-4813-82a6-f17870953de2`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other) -> bool` to the Version class in src/semver/version.py. The method determines if a new version can replace an old version per semantic versioning compatibility rules: majors must match; new.minor >= old.minor; prerelease parts must be identical (both None counts as equal); patch is ignored. Major 0 versions are special: they are only compatible with a version identical in major, minor, patch, and prerelease. Raise TypeError with message starting 'Expected a Version type' if other is not a Version instance (subclasses allowed). Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging files; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True if `other` (the candidate replacement version) is compatible with `self` (the version the code was written against). Compatibility rules: 1. If sel | Raise TypeError if `other` is not an instance of Version (including subclasses). The error message must start with 'Expected a Version type'. |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical version)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (prerelease differs)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease absent vs present)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease present vs absent)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting 'Expected a Version type'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting 'Expected a Version type'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting 'Expected a Version type'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. The method's docstring contains at least two doctest examples
17. The existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `77710087501d3e6d35f73f4142f7178677226a78d6a46a819b39cde18c76ab75`, 16 test methods, sealed at 2026-10-15T13:42:04.085224+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint: FAILED (16 of 16 methods failing): 16 of 16 methods failing, 0 passing, 0 subtest events; operation `01a13fcc-704b-7350-9b01-202a1d2eb838`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_docstring_has_two_doctest_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_positive_different_major_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_positive_lower_minor_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_exact_match_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_major_zero_exact_match_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_absent_vs_present_false_old_with_new_without | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_prerelease_absent_vs_present_false_old_without_new_with | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_major_minor_higher_patch_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_major_minor_lower_patch_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_major_minor_patch_different_prerelease_false | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_major_minor_patch_same_prerelease_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_same_version_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_subclass_accepted_true | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_dict_raises_typeerror | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_list_raises_typeerror | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIsCompatible.test_wrong_type_string_raises_typeerror | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -699,5 +699,43 @@
             return False
 
 
+    def is_compatible(self, other: 'Version') -> bool:
+        """
+        Return True if ``other`` (a candidate replacement version) is compatible
+        with ``self`` (the version the code was written against) according to
+        semantic versioning compatibility rules.
+
+        Compatibility rules:
+        * If self.major == 0: only compatible if other is identical in major,
+          minor, patch, and prerelease.
+        * If self.major > 0: compatible if other.major == self.major,
+          other.minor >= self.minor, and other.prerelease == self.prerelease
+          (patch is ignored).
+        * Prerelease equality: both None counts as equal; otherwise string
+          equality.
+
+        Examples:
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+        True
+        >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type")
+        # self is old, other is new
+        if self.major == 0:
+            return (other.major == 0 and
+                    other.minor == self.minor and
+                    other.patch == self.patch and
+                    other.prerelease == self.prerelease)
+        else:
+            return (other.major == self.major and
+                    other.minor >= self.minor and
+                    other.prerelease == self.prerelease)
+
 #: Keep the VersionInfo name for compatibility
 VersionInfo = Version
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.64s (312 passed of 312). Sealed suite: OK (16 of 16 methods). Operation `01a13fcc-ffdc-7088-86e7-7fe060bec196`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.72s (325 passed of 328); operation `01a13fcd-1cc7-71ed-b1f4-a3917190fab7`. Reported only; not a gate.

## 6. Breaker pass (mutants of changed lines, each in its own branch)
12 mutants generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-815a2767ef | src/semver/version.py | 727 | remove `not` | killed | test_sealed.TestIsCompatible.test_major_positive_different_major_false, test_sealed.TestIsCompatible.test_major_positive | 01a13fcd-3bb4-71d9-927f-ea214be52123 |
| m02-6020942306 | src/semver/version.py | 728 | raise -> pass | killed | test_sealed.TestIsCompatible.test_wrong_type_dict_raises_typeerror, test_sealed.TestIsCompatible.test_wrong_type_list_ra | 01a13fcd-3d2a-7220-a752-9901217177e8 |
| m03-140ad47b88 | src/semver/version.py | 730 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_false, test_sealed.TestIsCompatible.test_same_major_minor_highe | 01a13fcd-3bf3-76b1-8ba4-e0774b5420ab |
| m04-de2d067482 | src/semver/version.py | 730 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_false, test_sealed.TestIsCompatible.test_same_major_minor_highe | 01a13fcd-3b93-72b1-90ef-d9af0ba36d7d |
| m05-cefb62c565 | src/semver/version.py | 731 | 0 -> 1 | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_true | 01a13fcd-3ba0-76fe-ae9f-642426384516 |
| m06-914d3c6b4f | src/semver/version.py | 731 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_true | 01a13fcd-3b8f-7771-be63-0a980e568677 |
| m07-eee86af438 | src/semver/version.py | 733 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_false, test_sealed.TestIsCompatible.test_major_zero_exact_match | 01a13fcd-3bb3-776d-a867-8d19e2038915 |
| m08-bbdd46ca5c | src/semver/version.py | 734 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_true | 01a13fcd-3b55-768e-a1cc-f1be1acb8c4a |
| m09-737d704a0c | src/semver/version.py | 731 | And -> Or | killed | test_sealed.TestIsCompatible.test_major_zero_exact_match_false | 01a13fcd-4df6-76ec-9e6a-ad827de71d28 |
| m10-75f8f6631d | src/semver/version.py | 736 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_major_positive_different_major_false, test_sealed.TestIsCompatible.test_same_major_min | 01a13fcd-5163-75ac-adcf-f93167d0eb9e |
| m11-a89cabfc65 | src/semver/version.py | 737 | GtE -> Gt | killed | test_sealed.TestIsCompatible.test_same_major_minor_higher_patch_true, test_sealed.TestIsCompatible.test_same_major_minor | 01a13fcd-50f2-7577-9dbd-27001db11e55 |
| m12-4bd0865f91 | src/semver/version.py | 738 | Eq -> NotEq | killed | test_sealed.TestIsCompatible.test_prerelease_absent_vs_present_false_old_with_new_without, test_sealed.TestIsCompatible. | 01a13fcd-518e-73bb-9ba5-4811fd843a15 |

## 7. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20549 | 1391 | 0 | 0.024722 | 6.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20301 | 4111 | 0 | 0.009790 | 19.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2121 | 117 | 0 | 0.000742 | 2.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 7980 | 2988 | 0 | 0.005083 | 15.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3134 | 308 | 0 | 0.001217 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4102 | 114 | 0 | 0.001333 | 2.7s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 58187/9029/0; USD: 0.042887.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13fcb-ee80-73c9-81f9-2a725b3d8c0e | SUCCESS | 0 | 3.362s | retained | on | 0.02221997 |
| red-1 | 01a13fcc-704b-7350-9b01-202a1d2eb838 | SUCCESS | 0 | 0.8s | disposable | off | 0.0031996299999999997 |
| impl-tests-3 | 01a13fcc-d7c1-761c-ba6e-30bb89cf5ff3 | SUCCESS | 0 | 1.75s | disposable | off | 0.0096372 |
| verify | 01a13fcc-ffdc-7088-86e7-7fe060bec196 | SUCCESS | 0 | 2.13s | disposable | off | 0.011609170000000002 |
| heldout | 01a13fcd-1cc7-71ed-b1f4-a3917190fab7 | SUCCESS | 0 | 1.826s | disposable | off | 0.01032133 |
| mutant-m01-815a2767ef | 01a13fcd-3bb4-71d9-927f-ea214be52123 | SUCCESS | 0 | 0.912s | disposable | off | 0.00308044 |
| mutant-m02-6020942306 | 01a13fcd-3d2a-7220-a752-9901217177e8 | SUCCESS | 0 | 0.918s | disposable | off | 0.0030884899999999997 |
| mutant-m03-140ad47b88 | 01a13fcd-3bf3-76b1-8ba4-e0774b5420ab | SUCCESS | 0 | 0.923s | disposable | off | 0.0030467199999999997 |
| mutant-m04-de2d067482 | 01a13fcd-3b93-72b1-90ef-d9af0ba36d7d | SUCCESS | 0 | 0.907s | disposable | off | 0.00316922 |
| mutant-m05-cefb62c565 | 01a13fcd-3ba0-76fe-ae9f-642426384516 | SUCCESS | 0 | 0.907s | disposable | off | 0.0030544300000000003 |
| mutant-m06-914d3c6b4f | 01a13fcd-3b8f-7771-be63-0a980e568677 | SUCCESS | 0 | 0.891s | disposable | off | 0.00306948 |
| mutant-m07-eee86af438 | 01a13fcd-3bb3-776d-a867-8d19e2038915 | SUCCESS | 0 | 0.918s | disposable | off | 0.00306136 |
| mutant-m08-bbdd46ca5c | 01a13fcd-3b55-768e-a1cc-f1be1acb8c4a | SUCCESS | 0 | 0.756s | disposable | off | 0.00313166 |
| mutant-m09-737d704a0c | 01a13fcd-4df6-76ec-9e6a-ad827de71d28 | SUCCESS | 0 | 0.825s | disposable | off | 0.00309415 |
| mutant-m10-75f8f6631d | 01a13fcd-5163-75ac-adcf-f93167d0eb9e | SUCCESS | 0 | 0.825s | disposable | off | 0.003074 |
| mutant-m11-a89cabfc65 | 01a13fcd-50f2-7577-9dbd-27001db11e55 | SUCCESS | 0 | 0.839s | disposable | off | 0.00307155 |
| mutant-m12-4bd0865f91 | 01a13fcd-518e-73bb-9ba5-4811fd843a15 | SUCCESS | 0 | 0.835s | disposable | off | 0.00310956 |

Sandbox operations: 17, total guest duration 20.324s, retained images ['6191663e-795c-4813-82a6-f17870953de2'].

## 8. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Breaker pass covers AST mutants of changed lines only; no model-written adversarial or property tests, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- The sealed suite runs in the same process as the code under test; in-process forgery is mitigated (nonce, digest, expected IDs, completion marker) but not impossible.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
