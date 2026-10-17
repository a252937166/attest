# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: ERROR**  
Run `semver-is-compatible-pr368-v2-20261015T153041Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:30:41.132788+00:00, finished 2026-10-15T15:32:09.111131+00:00.

Reasons: model provider: model output violated the schema: no JSON output


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `b42b4c6b-441d-4b0e-99d9-e10edd271d4e`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other) -> bool` to the Version class in src/semver/version.py. The method implements semantic version compatibility checking: `old.is_compatible(new)` returns True when `new` can replace `old`. Compatibility requires equal major versions, new.minor >= old.minor, equal prerelease parts (both None counts as equal), and ignores patch. Major 0 versions are special: only compatible with an identical version (major, minor, patch, prerelease all equal). Raise TypeError with message 'Expected a Version type but got <type>' for non-Version arguments (subclasses allowed). Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging files; the existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool: | Returns True if `other` (the candidate replacement version) is compatible with `self` (the version the code was written against). Compatibility rules: 1. If `se | Raise TypeError if `other` is not an instance of Version (or a subclass). The error message must be exactly: 'Expected a Version type but got <class 'X'>' where |

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, symmetric for patch)
4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (major 0 identical)
6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical patch)
7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)
10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)
11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)
12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got'
13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got'
14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got'
15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
16. The method's docstring contains at least two doctest examples demonstrating usage
17. The existing pytest test suite (tests/) passes without modification

## 3. Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `0c52f7b45d67245cf7bfc2be833dc7a3da90b4d7ce05a6222cfec25c2cacc537`, 13 test methods, sealed at 2026-10-15T15:31:18.195570+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (13 of 13 methods: ERROR 13): 13 of 13 methods failing, 0 passing; operation `01a14030-672e-7366-a949-7b5d72458d52`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_different_major_returns_false | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_different_prerelease_returns_false | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_docstring_contains_at_least_two_doctest_examples | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_equal_prerelease_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_higher_patch_ignored_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_lower_minor_returns_false | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_lower_patch_ignored_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_major_zero_different_patch_returns_false | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_major_zero_identical_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_prerelease_vs_none_returns_false | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_same_version_returns_true | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_subclass_of_version_is_accepted | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_wrong_type_raises_typeerror_with_exact_message | ERROR (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

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



## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1569 | 0 | 0.025389 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 20363 | 1374 | 0 | 0.007345 | 8.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 2261 | 120 | 0 | 0.000786 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 8120 | 238 | 0 | 0.002650 | 3.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3235 | 844 | 0 | 0.001730 | 5.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 3808 | 8000 | 0 | 0.008342 | 39.6s | malformed |

Model calls: 6 (1 failed, 1 malformed); tokens in/out/cached 58469/12145/0; USD: 0.046242.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14030-02c4-737a-845c-27f4c3b644dd | SUCCESS | 0 | 3.646s | retained | on | 0.022427120000000002 |
| red-1 | 01a14030-672e-7366-a949-7b5d72458d52 | SUCCESS | 0 | 3.253s | disposable | off | 0.02591242 |

Sandbox operations: 2, total guest duration 6.899s, retained images ['b42b4c6b-441d-4b0e-99d9-e10edd271d4e'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
