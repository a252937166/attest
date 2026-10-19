# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NO CHANGE**  
Run `semver-is-compatible-pr368-v2-20261015T180949Z` · profile `eval-attest` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:09:49.393780+00:00, finished 2026-10-15T18:13:28.407297+00:00.

Reasons: turn budget exhausted without changes


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ec179e31-6645-401f-bef3-12b31c95645d`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the Version class in src/semver/version.py. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting with 'Expected a Version type but got ' followed by the type representation. Include a docstring with at least two doctest examples. Do not modify tests, docs, packaging, or other public behavior; keep existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) is compatible with `self` (old version). Compatibility rules: 1) self.major == other.major. 2) If self.major == 0: retur | TypeError: raised when `other` is not an instance of Version (or subclass). Message must start with 'Expected a Version type but got ' followed by the type repr |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (identical major-0)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical version)
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
`sealed/test_sealed.py` sha256 `73849b287736f7e7edd83d300f9b2e7a8775f16105f8cde40e36ee9886a604cd`, 16 test methods, sealed at 2026-10-15T18:10:46.665470+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 16 methods: ERROR 16): 16 of 16 methods failing, 0 passing; operation `01a140c2-5ee2-73e9-aa10-bc377499112e`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_docstring_has_two_doctest_examples | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_different_major | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_different_prerelease | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_equal_prerelease | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_lower_minor | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_major0_identical | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_major0_not_identical | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_none_vs_prerelease | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_higher | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_patch_ignored_lower | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_prerelease_vs_none | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_same_version | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_subclass_accepted | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_dict | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_list | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_is_compatible_wrong_type_str | ERROR (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check passed; 14 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Gates
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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1691 | 17408 | 0.025755 | 7.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20421 | 4359 | 0 | 0.010049 | 20.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2277 | 203 | 0 | 0.000866 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 8137 | 9572 | 0 | 0.011056 | 43.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3525 | 155 | 0 | 0.001197 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4316 | 127 | 0 | 0.001409 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 4905 | 155 | 0 | 0.001611 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 5452 | 104 | 0 | 0.001729 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 5977 | 93 | 0 | 0.001877 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 6477 | 108 | 0 | 0.002040 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 6950 | 233 | 0 | 0.002295 | 3.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 6343 | 488 | 0 | 0.002342 | 5.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 6017 | 5405 | 0 | 0.006670 | 28.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 5740 | 4030 | 0 | 0.005349 | 20.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 5566 | 7658 | 0 | 0.008562 | 35.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-14 | default | 5206 | 601 | 0 | 0.002103 | 4.8s | ok |

Model calls: 16 (0 failed, 0 malformed); tokens in/out/cached 117991/34982/17408; USD: 0.08491.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140c1-b46b-7193-839e-523fa3968844 | SUCCESS | 0 | 4.495s | retained | on | 0.0220926 |
| red-1 | 01a140c2-5ee2-73e9-aa10-bc377499112e | SUCCESS | 0 | 4.023s | disposable | off | 0.0316689 |

Sandbox operations: 2, total guest duration 8.518s, retained images ['ec179e31-6645-401f-bef3-12b31c95645d'].

## 11. Limitations of this bundle
- Profile 'eval-attest': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
