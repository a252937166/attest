# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: BASELINE**  
Run `semver-is-compatible-pr368-v2-20261015T180823Z` · profile `eval-baseline` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T18:08:23.430167+00:00, finished 2026-10-15T18:09:35.480723+00:00.

Reasons: all gates passed


## 1. Frozen task
Task `semver-is-compatible-pr368-v2`, spec digest `b812def0a4771ef1dc0619028ce84f5e5b0389a1e0eca147599b46a18eceb324`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `75a395b6-806c-47c2-bcb1-4e65521357a6`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking off).

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
@@ -545,6 +545,56 @@
     def __hash__(self) -> int:
         return hash(self.to_tuple()[:4])
 
+    def is_compatible(self, other: "Version") -> bool:
+        """
+        Return True if `other` can be used in place of `self`.
+
+        For a version with major number equal to 0, any change in version is considered
+        incompatible. For a version with major number >= 1, the version is compatible if
+        they have the same major version, the same prerelease version, and the minor
+        version of `other` is greater than or equal to the minor version of `self`.
+
+        The patch version is ignored.
+
+        Examples:
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3).is_compatible(Version(1, 2, 4))
+            True
+            >>> Version(1, 2, 4).is_compatible(Version(1, 2, 3))
+            True
+            >>> Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0'))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 0))
+            True
+            >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+            False
+            >>> Version(1, 1, 0).is_compatible(Version(1, 0, 0))
+            False
+            >>> Version(2, 0, 0).is_compatible(Version(1, 5, 0))
+            False
+            >>> Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0'))
+            False
+            >>> Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1'))
+            False
+            >>> Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0))
+            False
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        # For major 0, exact match required (including prerelease)
+        if self.major == 0:
+            return (self.major == other.major and
+                    self.minor == other.minor and
+                    self.patch == other.patch and
+                    self.prerelease == other.prerelease)
+
+        # For major >= 1
+        return (self.major == other.major and
+                self.prerelease == other.prerelease and
+                other.minor >= self.minor)
+
     def finalize_version(self) -> "Version":
         """
         Remove any prerelease and build metadata from the version.
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | default | 1977 | 113 | 0 | 0.000695 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | default | 7836 | 6016 | 0 | 0.007765 | 34.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | default | 3259 | 98 | 0 | 0.001066 | 7.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | default | 4231 | 213 | 0 | 0.001461 | 7.4s | ok |

Model calls: 4 (0 failed, 0 malformed); tokens in/out/cached 17303/6440/0; USD: 0.010987.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a140c0-5a75-7486-a274-a037fcd7473d | SUCCESS | 0 | 3.3s | retained | on | 0.02186555 |
| impl-tests-3 | 01a140c1-39db-775f-b2ef-1144d8354026 | SUCCESS | 0 | 1.717s | disposable | off | 0.00945097 |

Sandbox operations: 2, total guest duration 5.017s, retained images ['75a395b6-806c-47c2-bcb1-4e65521357a6'].

## 11. Limitations of this bundle
- Profile 'eval-baseline': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
