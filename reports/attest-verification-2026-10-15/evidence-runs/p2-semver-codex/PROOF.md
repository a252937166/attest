# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: ERROR**  
Run `semver-is-compatible-pr368-20261015T155255Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T15:52:55.654406+00:00, finished 2026-10-15T15:58:24.480925+00:00.

Reasons: SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `1ad48318-aead-45de-9fdd-54690240e066`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require matching majors and exactly equal prerelease values; for positive majors require other.minor >= self.minor and ignore patches, while major zero requires matching minor and patch as well. Ignore build metadata in all cases. Accept Version instances and subclasses, reject other types with the specified TypeError prefix, document the method with at least two executable doctest examples, and preserve existing behavior and the existing test suite without modifying other files.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Public instance method also available through semver.Version and the existing VersionInfo alias. The required other argument may be supplied positionally or by  | TypeError: other is not an instance of Version or a subclass; str(exception) must start with 'Expected a Version type'. This applies for every receiver major an |

Acceptance criteria:
1. 1. The method is defined on Version in src/semver/version.py, has the specified signature, and is callable through semver.Version, semver.version.Version, and the existing VersionInfo alias, including with other supplied by keyword.
2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) returns True; the reversed call returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
4. 4. Different majors return False in both directions, including 1 versus 2 and 0 versus 1, regardless of minor, patch, or prerelease.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) returns True. Equal prereleases also permit a higher candidate minor, but never permit a lower candidate minor.
6. 6. Unequal prereleases return False even if the candidate minor is higher. Cover 'rc.1' versus 'rc.0', case differences, and absent versus 'rc1' in both directions. Stored None and an empty prerelease string are unequal; two empty prerelease strings are equal.
7. 7. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) returns True. Changes to either minor or patch return False in both directions, including Version(0, 1, 1) and Version(0, 2, 0) as candidates.
8. 8. Major-zero versions with identical major, minor, patch, and prerelease return True, including matching nonempty prereleases; any prerelease difference returns False. Version(0, 0, 0) is compatible with itself.
9. 9. Build differences do not affect compatibility for positive or zero majors. In particular, Version(0, 1, 0, build='a').is_compatible(Version(0, 1, 0, build='b')) returns True; absent versus present build metadata also has no effect.
10. 10. For both zero-major and positive-major receivers, non-Version arguments raise TypeError with a message starting 'Expected a Version type'. Cover at least 'wrongtype', a valid version string, bytes, {'a': 2}, a version-shaped dictionary, [], a version-shaped tuple, None, an integer, and an unrelated object.
11. 11. With an otherwise unmodified CustomVersion subclass, CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) and the reverse each return True. Base/subclass and distinct subclass combinations also obey the major-zero rule without TypeError.
12. 12. Every successful call returns exactly True or False, and both operands retain all five original version components after compatible, incompatible, and invalid-argument calls.
13. 13. The method docstring explains replacement direction, positive-major and major-zero rules, prerelease equality, ignored build metadata, and the invalid-type error. It includes at least two executable compatibility doctest examples with expected results, and those examples pass.
14. 14. Only src/semver/version.py is modified. Existing tests, documentation files, packaging files, metadata, and exports remain unchanged; the full existing pytest suite in tests/ passes.
15. 15. Existing public behavior, including construction, parsing, comparison and ordering, hashing, formatting, immutability, subclass support, deprecated APIs, and CLI behavior, remains unchanged. The change retains the repository's Python 3.7 compatibility.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `cfb0a5dbfb02cf8a32f9bb2df898d8720a550f62e65ffe6ce628e346b3601369`, 27 test methods, sealed at 2026-10-15T15:55:49.291709+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (24 of 27 methods: ERROR 24): 24 of 27 methods failing, 3 passing; operation `01a14046-cc52-76e3-8c8e-5ac6ae2fb690`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.CompatibilityAcceptanceTests.test_absent_and_present_prereleases_differ_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_base_and_subclass_mix_for_positive_major | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_distinct_subclasses_follow_zero_major_rule | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_docstring_contains_two_passing_compatibility_doctests | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_docstring_explains_the_contract | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_empty_prerelease_is_distinct_from_none | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_equal_prerelease_allows_patch_and_higher_minor | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_comparison_and_hash_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_parse_and_format_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_existing_readonly_properties_remain_readonly | ok (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_invalid_call_preserves_receiver_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_method_signature | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_other_can_be_passed_by_keyword | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_ignores_build_metadata | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_minor_is_directional | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_positive_major_rejects_every_non_version_type | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_prerelease_requires_exact_stored_value | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_public_aliases_expose_the_method | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_successful_calls_preserve_all_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_identical_versions_are_compatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_ignores_build_metadata | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_minor_must_match_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_patch_must_match_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_prerelease_must_match | ERROR (1 ev) | ok (1 ev) |
| test_sealed.CompatibilityAcceptanceTests.test_zero_major_rejects_every_non_version_type | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -240,6 +240,28 @@
             )
         )
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        Both versions must have the same major version and exactly equal
+        prerelease values. For a positive major, ``other`` may have the same
+        or a higher minor version; patch versions are ignored. For major zero,
+        minor and patch versions must both match. Build metadata is ignored
+        in all cases. A non-Version ``other`` raises :class:`TypeError`.
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
     def __iter__(self) -> VersionIterator:
         """Return iter(self)."""
         yield from self.to_tuple()
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: 312 passed in 0.59s (312 passed of 312). Sealed suite: OK (27 of 27 methods, each in its own process). Operation `01a14048-967f-7553-8966-9b753c7b9fa5`, networking disabled, disposable branch from the checkpoint.

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

Held-out suite (tests/test_heldout_pr368.py): 3 failed, 325 passed in 0.66s (325 passed of 328); operation `01a14048-c310-71c3-8cfe-491063f1afe0`. Gate: failures block VERIFIED.

## 6. Gates
(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28595 | 1404 | 0 | - | 63.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28242 | 4044 | 7040 | - | 71.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10954 | 167 | 7168 | - | 15.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 27137 | 582 | 20480 | - | 25.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11828 | 91 | 7168 | - | 15.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12646 | 680 | 7168 | - | 23.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 13038 | 171 | 7168 | - | 16.3s | ok |

Model calls: 7 (0 failed, 0 malformed); tokens in/out/cached 132440/7139/56192; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14044-8d76-71de-a6f3-2bca4daf8373 | SUCCESS | 0 | 3.35s | retained | on | 0.02189289 |
| red-1 | 01a14046-cc52-76e3-8c8e-5ac6ae2fb690 | SUCCESS | 0 | 7.207s | disposable | off | 0.059399030000000005 |
| impl-tests-3 | 01a14047-d2cb-7386-867a-4ce86a663ea4 | SUCCESS | 0 | 1.727s | disposable | off | 0.00952712 |
| impl-python-4 | 01a14048-40da-747c-8544-76bbe58aea24 | SUCCESS | 0 | 0.802s | disposable | off | 0.00304359 |
| verify | 01a14048-967f-7553-8966-9b753c7b9fa5 | SUCCESS | 0 | 7.849s | disposable | off | 0.06691238000000001 |
| heldout | 01a14048-c310-71c3-8cfe-491063f1afe0 | SUCCESS | 0 | 1.741s | disposable | off | 0.010013280000000001 |
| mutant-m01-1acbc236ff | 01a14048-dcf0-779a-b9b7-05256dbe46b3 | SUCCESS | 0 | 6.84s | disposable | off | 0.059301809999999996 |
| mutant-m02-5f552724de | 01a14048-d71d-70c4-9778-c3d4a1b93165 | SUCCESS | 0 | 6.752s | disposable | off | 0.05853535 |
| mutant-m03-22bf8f49f6 | 01a14048-d75b-743d-afaf-a982daea85e0 | SUCCESS | 0 | 6.752s | disposable | off | 0.05833588 |
| mutant-m04-530165f573 | 01a14048-d7e2-70b6-811e-005214639230 | SUCCESS | 0 | 6.755s | disposable | off | 0.05879335000000001 |
| mutant-m05-13ea230cc5 | 01a14048-ef23-7111-8c3b-f3031ae2e524 | SUCCESS | 0 | 6.816s | disposable | off | 0.05882481 |
| mutant-m06-23646fc6ed | 01a14048-d77b-73c9-917e-57ff53038edd | SUCCESS | 0 | 6.752s | disposable | off | 0.05829472 |
| mutant-m07-3a5fda88eb | 01a14048-d77d-7450-ad14-0055aec14553 | SUCCESS | 0 | 6.794s | disposable | off | 0.05916669 |
| mutant-m08-792cc71ab7 | 01a14048-d743-73ab-b12d-86e096f6a9e0 | SUCCESS | 0 | 6.75s | disposable | off | 0.058397920000000006 |
| mutant-m09-2c97a4ba81 | 01a14049-0039-72d1-8a5b-058917627c78 | SUCCESS | 0 | 6.736s | disposable | off | 0.058733999999999995 |
| mutant-m10-a2d66cfb02 | 01a14049-0918-7113-aaf2-3285e05d4723 | SUCCESS | 0 | 6.76s | disposable | off | 0.058571200000000004 |
| mutant-m11-b24364b5d4 | None | UNCERTAIN | None | - | disposable | off | None |
| mutant-m12-745ffb8b2e | 01a14049-1dde-7320-be2c-7230494783b8 | SUCCESS | 0 | 6.617s | disposable | off | 0.058139090000000004 |

Sandbox operations: 18, total guest duration 97.0s, retained images ['1ad48318-aead-45de-9fdd-54690240e066'].

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
