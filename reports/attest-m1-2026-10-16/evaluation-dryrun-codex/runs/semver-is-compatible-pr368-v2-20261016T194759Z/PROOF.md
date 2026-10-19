# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: BASELINE**  
Run `semver-is-compatible-pr368-v2-20261016T194759Z` · profile `eval-baseline-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-16T19:47:59.839281+00:00, finished 2026-10-16T19:49:58.651865+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `eb98ac92304a58157f51e37e9cc837eaed332ed2a8d1ff89a80fff62eb580449`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `609a197b-9e12-4d41-9030-433c8e04c885`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking off).

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
1 changed path(s); scope check passed; 4 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -200,6 +200,27 @@
     def build(self, value):
         raise AttributeError("attribute 'build' is readonly")
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can be used in place of this version.
+
+        The major and prerelease parts must match. For stable major versions,
+        ``other`` may have a greater minor version; patch versions are ignored.
+        Major-zero versions require the same minor and patch as well.
+
+        >>> Version(1, 2, 3).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError("Expected a Version type but got {}".format(type(other)))
+
+        if self.major != other.major or self.prerelease != other.prerelease:
+            return False
+        if self.major == 0:
+            return self.minor == other.minor and self.patch == other.patch
+        return other.minor >= self.minor
+
     def to_tuple(self) -> VersionTuple:
         """
         Convert the Version object to a tuple.
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
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10564 | 101 | 7168 | - | 16.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 24674 | 497 | 19328 | - | 29.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11427 | 108 | 7168 | - | 30.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12251 | 161 | 7168 | - | 16.3s | ok |

Model calls: 4 (0 failed, 0 malformed); tokens in/out/cached 58916/867/40832; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14641-ece2-707d-968b-b8f8b7974441 | SUCCESS | 0 | 3.422s | retained | on | 0.02215785 |
| impl-tests-3 | 01a14643-4dba-7359-99b9-ad75a2537238 | SUCCESS | 0 | 1.669s | disposable | off | 0.00950298 |

Sandbox operations: 2, total guest duration 5.091s, retained images ['609a197b-9e12-4d41-9030-433c8e04c885'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
