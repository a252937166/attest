# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: ERROR**  
Run `semver-is-compatible-pr368-v2-20261016T195003Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:50:03.939741+00:00, finished 2026-10-16T19:52:35.341015+00:00.

Reasons: model provider: HTTP 429 from https://development-gateway.invalid/run: hourly limit reached for this key


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `eb98ac92304a58157f51e37e9cc837eaed332ed2a8d1ff89a80fff62eb580449`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `177d2962-08e1-427e-a895-581484603b8b`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether other can replace the receiver. Require Version instances, including subclasses. For nonzero majors, compatibility requires equal majors, a replacement minor at least as large as the receiver's minor, and equal prerelease values; ignore patch. For major zero, require equal major, minor, patch and prerelease values. Ignore build metadata in all cases. Include at least two executable doctest examples in the method docstring, preserve all existing public behavior, and modify only src/semver/version.py.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | An instance method also available through semver.Version and the existing VersionInfo alias. Accept other positionally or by keyword. First require isinstance(o | TypeError: other is not a Version instance or subclass instance. The exact message is 'Expected a Version type but got ' followed by str(type(other)), with no a |

Acceptance criteria:
1. 1. The method is available on semver.version.Version, semver.Version and the existing VersionInfo alias; both old.is_compatible(new) and old.is_compatible(other=new) work and return actual bool values.
2. 2. Version(1, 2, 3) is compatible with itself and Version(1, 2, 4); Version(1, 2, 4) is compatible with Version(1, 2, 3).
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) is True; the reverse call is False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False.
4. 4. Different majors are incompatible in both directions, including 1 versus 2 and 0 versus 1. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True. Equal prereleases also permit an increased minor for equal nonzero majors.
6. 6. Different prereleases are incompatible regardless of patch or minor increases. In particular, 'rc.1' versus 'rc.0', 'RC.0' versus 'rc.0', and absent prerelease versus 'rc1' return False in both directions.
7. 7. Prerelease equality uses stored property values: two None values match, two empty strings match, and None versus an empty string does not match.
8. 8. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True. Changing its minor, patch or prerelease independently produces False in either direction; this includes increasing the minor and retaining the same prerelease.
9. 9. Build metadata is ignored for every major: otherwise compatible versions remain compatible when builds differ or only one has a build, including Version(0, 1, 0, build='a') versus Version(0, 1, 0, build='b'). Build equality cannot make otherwise incompatible versions compatible.
10. 10. For receivers with major 0 and major 1, passing 'wrongtype', a valid version string, bytes, {'a': 2}, [], a tuple, None, an integer, or a plain object raises TypeError with exactly 'Expected a Version type but got ' + str(type(other)).
11. 11. For an ordinary subclass CustomVersion(Version), base-to-subclass, subclass-to-base and subclass-to-subclass calls are accepted and follow the same compatibility rules for both zero and nonzero majors. In particular, CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True.
12. 12. Successful and unsuccessful compatibility checks leave all five version properties of both operands unchanged; invalid-type calls also leave the receiver unchanged.
13. 13. The method docstring explains replacement direction, nonzero-major rules, the major-zero exception, ignored build metadata and TypeError behavior, and contains at least two executable compatibility examples with correct expected outputs.
14. 14. Only src/semver/version.py is modified. Existing tests remain unchanged and the complete existing tests/ pytest suite passes. Existing parsing, comparison, equality, ordering, hashing, construction, aliases and other public behavior remain unchanged.

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `1e24ec039f2f1fca6798f38d8993c4994e210fbfe0e67ab2db4e20127b20e416`, 18 test methods, sealed at 2026-10-16T19:52:32.294267+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 18 methods: ERROR 16): 16 of 18 methods failing, 2 passing; operation `01a14645-ebf8-7327-af2e-972e79392cdd`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.CompatibilityAcceptanceTests.test_build_metadata_is_ignored_for_both_major_rules | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_different_majors_are_incompatible | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_different_prereleases_are_incompatible_both_ways | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_equal_build_cannot_rescue_incompatible_versions | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_equal_prerelease_allows_patch_and_minor_increases | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_existing_comparison_equality_ordering_and_hash_behavior | ok (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_existing_parse_and_construction_behavior | ok (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_invalid_type_call_does_not_mutate_receiver | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_invalid_types_raise_exact_typeerror_for_both_major_rules | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_identical_parts_are_compatible | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_major_zero_rejects_each_changed_part_in_both_directions | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_method_docstring_describes_contract_and_has_two_doctest_examples | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_nonzero_major_ignores_patch_in_both_directions | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_nonzero_major_minor_is_directional | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_prerelease_compares_stored_none_and_empty_string | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_public_aliases_and_keyword_call_return_bool | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_subclasses_are_accepted_across_both_receiver_types | ERROR (1 ev) | - |
| test_sealed.CompatibilityAcceptanceTests.test_successful_and_unsuccessful_calls_do_not_mutate_operands | ERROR (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```




## 5. Fresh-branch verification (bound to the sealed suite)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

Held-out suite: none configured.

## 6. Gates
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 8b. Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28681 | 1300 | 7680 | - | 58.8s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28218 | 3789 | 0 | - | 64.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | - | - | - | - | 3.0s | error |

Model calls: 3 (1 failed, 0 malformed); tokens in/out/cached 56899/5089/7680; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14643-d303-74e7-bb7d-dbaa2fd5a798 | SUCCESS | 0 | 3.48s | retained | on | 0.021963120000000003 |
| red-1 | 01a14645-ebf8-7327-af2e-972e79392cdd | SUCCESS | 0 | 5.155s | disposable | off | 0.044374040000000003 |

Sandbox operations: 2, total guest duration 8.635s, retained images ['177d2962-08e1-427e-a895-581484603b8b'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
