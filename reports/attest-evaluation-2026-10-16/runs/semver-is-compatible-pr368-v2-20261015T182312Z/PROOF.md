# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: BASELINE**  
Run `semver-is-compatible-pr368-v2-20261015T182312Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:23:12.978023+00:00, finished 2026-10-15T18:27:21.717944+00:00.

Reasons: implementer did not finish


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `ff49beb1-4be2-4b40-a967-a873e4e358eb`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking off).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

(none)

Acceptance criteria:
1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True; Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True; Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch is ignored).
2. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases).
3. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True, but Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 only matches an identical version).
4. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor); Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major).
5. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False; Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False; Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (prerelease must be equal).
6. Version(1, 2, 3).is_compatible('wrongtype'), .is_compatible({'a': 2}) and .is_compatible([]) each raise TypeError whose message is 'Expected a Version type but got <class ...>' (starts with 'Expected a Version type but got').
7. A subclass instance is accepted: class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True.
8. The method's docstring contains doctest examples and the existing test suite (tests/) still passes.

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

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
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1977 | 113 | 0 | 0.000695 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 7836 | 157 | 0 | 0.002492 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 2551 | 202 | 0 | 0.000947 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4385 | 982 | 0 | 0.002199 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | default | 3575 | 333 | 0 | 0.001372 | 3.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | default | 4050 | 6789 | 0 | 0.007325 | 35.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | default | 4959 | 376 | 0 | 0.001826 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | default | 5199 | 454 | 0 | 0.001968 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | default | 5636 | 3380 | 0 | 0.004733 | 14.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | default | 6163 | 3262 | 0 | 0.004785 | 19.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | default | 7046 | 2717 | 0 | 0.004559 | 12.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | default | 7519 | 5504 | 0 | 0.007209 | 24.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13 | default | 7986 | 16000 | 0 | 0.016796 | 83.4s | malformed |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-13-repair | default | 8051 | 731 | 0 | 0.003073 | 6.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-14 | default | 7690 | 656 | 0 | 0.002897 | 5.1s | ok |

Model calls: 15 (1 failed, 1 malformed); tokens in/out/cached 84623/41656/0; USD: 0.062876.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140cd-fbff-7526-8f03-20dd095249d4 | SUCCESS | 0 | 3.45s | retained | on | 0.022774930000000002 |

Sandbox operations: 1, total guest duration 3.45s, retained images ['ff49beb1-4be2-4b40-a967-a873e4e358eb'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
