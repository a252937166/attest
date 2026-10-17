# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284)

**Verdict: NEEDS HUMAN**  
Run `semver-is-compatible-pr368-20261015T132135Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-15T13:21:35.581370+00:00, finished 2026-10-15T13:21:45.288925+00:00.

Reasons: existing tests do not pass on the unmodified repository: no summary


## 1. Frozen task
Task `semver-is-compatible-pr368`, spec digest `11bd0819f03dcf1a4d8e3e0bf60593cbc7aa9c35004eaede2637221bf4e21bb5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `f6224df7-392f-4448-aa4c-76093ead6046`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with a message starting 'Expected a Version type'. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: None. (specification stage did not complete)

(none)

Acceptance criteria:
(none)

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint: n/a: 0 of 0 methods failing, 0 passing, 0 subtest events; operation `None`.

(none)

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

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
(none)

Model calls: 0 (0 failed, 0 malformed); tokens in/out/cached 0/0/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13fb9-c7af-7228-b584-94f750b8316b | SUCCESS | 0 | 3.673s | retained | on | 0.02242805 |

Sandbox operations: 1, total guest duration 3.673s, retained images ['f6224df7-392f-4448-aa4c-76093ead6046'].

## 8. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Breaker pass covers AST mutants of changed lines only; no model-written adversarial or property tests, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- The sealed suite runs in the same process as the code under test; in-process forgery is mitigated (nonce, digest, expected IDs, completion marker) but not impossible.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
