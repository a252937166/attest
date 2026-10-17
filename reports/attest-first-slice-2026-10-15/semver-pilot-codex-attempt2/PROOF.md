# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NO CHANGE**  
Run `semver-is-compatible-pr368-20261015T132238Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T13:22:38.655535+00:00, finished 2026-10-15T13:33:49.896284+00:00.

Reasons: turn budget exhausted without changes


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ab8519b7-721f-4697-8088-ff16cae0a5f0`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiving version. Require equal majors and prereleases; for nonzero majors allow an equal or higher minor and ignore patch, while major zero requires equal minor and patch as well. Ignore build metadata in all cases. Accept Version instances and subclasses, reject other types with the specified TypeError prefix, and document the method with at least two passing doctest examples. Preserve all existing public behavior and keep the existing pytest suite passing without modifying tests, documentation files, or packaging.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible (also accessible through semver.Version) | def is_compatible(self, other: "Version") -> bool | Instance method with one required positional-or-keyword argument, other. Accept any instance of Version, including subclasses, independently of the receiver's s | TypeError: other is not an instance of Version or a Version subclass; the exception message must start with 'Expected a Version type'. The remainder of the mess |

Acceptance criteria:
1. 1. The method is available through both semver.Version and semver.version.Version, accepts other positionally or by keyword, and returns True or False rather than another truthy or falsy value for valid inputs.
2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) returns True; the reverse returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
4. 4. Different majors return False in both directions, including between majors zero and one and between Version(2, 0, 0) and Version(1, 5, 0), regardless of other fields.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) and Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 3, 0, 'rc.0')) return True.
6. 6. Unequal prereleases return False even when the proposed minor is higher. In particular, 'rc.1' versus 'rc.0', 'RC.0' versus 'rc.0', and an absent prerelease versus 'rc1' are incompatible in both directions.
7. 7. Prerelease equality uses the values stored by Version: two None values match, two empty strings match, and an empty string versus None does not match, for both major zero and nonzero majors.
8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) returns True. Changing only patch or only minor makes the result False in both directions. Equal major-zero versions with equal prereleases return True; changing or removing the prerelease returns False.
9. 9. Build metadata is ignored for every major. Versions differing only in build metadata, including absent versus present metadata, are compatible in both directions for major zero and nonzero majors. Build differences do not override any otherwise incompatible field.
10. 10. For receivers Version(1, 2, 3) and Version(0, 1, 0), each of 'wrongtype', '1.2.3', b'1.2.3', {'a': 2}, {'major': 1}, [], (1, 2, 3), 1, None, and object() raises TypeError with a message starting 'Expected a Version type'.
11. 11. For a plain subclass CustomVersion(Version), compatible base/subclass, subclass/base, and subclass/subclass operands are accepted and return True. Incompatible subclass operands return False according to the same field rules.
12. 12. Calling the method leaves all five component values of both operands unchanged, whether returning True, returning False, or rejecting an invalid other.
13. 13. The method docstring contains at least two compatibility-call doctest examples with expected boolean output, and those examples pass when executed with the required imports or the repository's doctest namespace.
14. 14. Only src/semver/version.py is modified. Existing public behavior, including construction, parsing, comparisons, hashing, formatting, immutability, subclass support, deprecated functions, and CLI behavior, remains unchanged, and the complete existing pytest suite passes.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `045cca9160f98c23f53b0e45f3fb86911a79f9bc4704ce0c81d51a3cff341e33`, 27 test methods, sealed at 2026-10-15T13:25:29.202622+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint: FAILED (24 of 27 methods failing): 24 of 27 methods failing, 3 passing, 35 subtest events; operation `01a13fbd-4192-710b-bfd9-6e334b635ef7`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.CompatibilityTests.test_base_and_subclass_operands_work_in_every_combination | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_build_metadata_does_not_override_incompatible_fields | ERROR (3 ev) | - |
| test_sealed.CompatibilityTests.test_build_metadata_is_ignored_for_both_major_categories | ERROR (2 ev) | - |
| test_sealed.CompatibilityTests.test_different_majors_are_incompatible_in_both_directions | ERROR (3 ev) | - |
| test_sealed.CompatibilityTests.test_docstring_explains_the_contract | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_docstring_has_two_executable_compatibility_doctests | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_empty_prerelease_matches_only_empty_prerelease | ERROR (2 ev) | - |
| test_sealed.CompatibilityTests.test_higher_minor_can_replace_lower_minor_only | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_identical_versions_return_actual_bool | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_invalid_call_leaves_receiver_components_unchanged | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_invalid_other_raises_typeerror_for_major_zero | ERROR (10 ev) | - |
| test_sealed.CompatibilityTests.test_invalid_other_raises_typeerror_for_nonzero_major | ERROR (10 ev) | - |
| test_sealed.CompatibilityTests.test_lower_minor_cannot_replace_nonzero_major | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_major_zero_identical_components_are_compatible | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_major_zero_requires_equal_minor_and_patch_in_both_directions | ERROR (2 ev) | - |
| test_sealed.CompatibilityTests.test_major_zero_requires_exact_prerelease | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_matching_prereleases_allow_nonzero_minor_increase | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_matching_prereleases_allow_nonzero_patch_change | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_method_is_available_through_both_public_imports | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_patch_is_ignored_for_nonzero_major_in_both_directions | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_signature_requires_one_positional_or_keyword_other | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_subclass_operands_follow_the_same_incompatibility_rules | ERROR (1 ev) | - |
| test_sealed.CompatibilityTests.test_unequal_prereleases_are_incompatible_even_with_higher_minor | ERROR (3 ev) | - |
| test_sealed.CompatibilityTests.test_valid_calls_leave_all_components_of_both_operands_unchanged | ERROR (1 ev) | - |
| test_sealed.ExistingBehaviorTests.test_existing_comparison_and_hash_behavior_remain_available | ok (1 ev) | - |
| test_sealed.ExistingBehaviorTests.test_existing_read_only_properties_remain_read_only | ok (1 ev) | - |
| test_sealed.ExistingBehaviorTests.test_parsing_and_formatting_still_preserve_components | ok (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check passed; 14 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Breaker pass (mutants of changed lines, each in its own branch)
Not run (verification did not pass).

(none)

## 7. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 34479 | 1375 | 0 | - | 70.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 34130 | 4174 | 0 | - | 82.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10784 | 99 | 0 | - | 17.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 15818 | 547 | 7168 | - | 31.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 16376 | 849 | 0 | - | 30.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 16892 | 69 | 0 | - | 21.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 35502 | 562 | 24704 | - | 30.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 18072 | 280 | 0 | - | 28.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 37033 | 654 | 25344 | - | 38.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 18919 | 677 | 0 | - | 28.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-9 | medium | 83709 | 2666 | 68224 | - | 66.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-10 | medium | 15067 | 844 | 0 | - | 38.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-11 | medium | 14730 | 320 | 0 | - | 23.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-12 | medium | 14377 | 171 | 0 | - | 19.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-13 | medium | 18625 | 860 | 7168 | - | 34.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-14 | medium | 58389 | 2038 | 37888 | - | 49.0s | ok |

Model calls: 16 (0 failed, 0 malformed); tokens in/out/cached 442902/16185/170496; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13fba-bebc-766f-b2a8-381492f4f7c7 | SUCCESS | 0 | 3.846s | retained | on | 0.02223848 |
| red-1 | 01a13fbd-4192-710b-bfd9-6e334b635ef7 | SUCCESS | 0 | 0.88s | disposable | off | 0.00383264 |
| impl-python-2 | 01a13fbe-0e95-708a-869b-1c5215a88039 | SUCCESS | 0 | 0.549s | disposable | off | 0.0017886100000000002 |
| impl-python-3 | 01a13fbe-937f-70ce-bb50-60033fb488e6 | SUCCESS | 0 | 0.625s | disposable | off | 0.00181086 |
| impl-tests-4 | 01a13fbe-f2a6-74bd-adce-14a4328ad06d | SUCCESS | 0 | 1.718s | disposable | off | 0.009659000000000001 |
| impl-python-5 | 01a13fbf-8029-7266-98bd-dc4f0d5a3c68 | SUCCESS | 0 | 0.776s | disposable | off | 0.00328994 |
| impl-python-6 | 01a13fbf-fc6c-75a8-9a6a-38bca82fdc7f | SUCCESS | 0 | 0.654s | disposable | off | 0.00256774 |
| impl-python-7 | 01a13fc0-a06a-7633-8ef5-f5e622f46f36 | SUCCESS | 0 | 0.553s | disposable | off | 0.00178512 |
| impl-python-8 | 01a13fc1-23aa-70ac-a2df-b7b66592a70a | SUCCESS | 0 | 0.608s | disposable | off | 0.00178292 |
| impl-python-9 | 01a13fc2-3188-73f5-a2ba-93c04ee0d1c4 | SUCCESS | 0 | 0.633s | disposable | off | 0.00178753 |
| impl-python-10 | 01a13fc2-d54d-770c-85e6-ee85f42c74ea | SUCCESS | 0 | 0.593s | disposable | off | 0.0018312199999999997 |
| impl-python-11 | 01a13fc3-3cb4-74d9-a4ed-8dda6a3d985c | SUCCESS | 0 | 0.617s | disposable | off | 0.00179189 |
| impl-python-13 | 01a13fc4-1b69-7194-a1fc-6a389a2f9ef1 | SUCCESS | 0 | 0.576s | disposable | off | 0.001833 |
| impl-python-14 | 01a13fc4-e6d0-71e2-9a25-fd307bc2350f | SUCCESS | 0 | 0.8s | disposable | off | 0.0033180300000000005 |

Sandbox operations: 14, total guest duration 13.428s, retained images ['ab8519b7-721f-4697-8088-ff16cae0a5f0'].

## 8. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Breaker pass covers AST mutants of changed lines only; no model-written adversarial or property tests, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- The sealed suite runs in the same process as the code under test; in-process forgery is mitigated (nonce, digest, expected IDs, completion marker) but not impossible.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
