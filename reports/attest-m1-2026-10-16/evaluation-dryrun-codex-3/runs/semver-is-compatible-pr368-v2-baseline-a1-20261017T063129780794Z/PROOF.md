# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: BASELINE**  
Run `semver-is-compatible-pr368-v2-baseline-a1-20261017T063129780794Z` · profile `eval-baseline-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T06:31:29.781199+00:00, finished 2026-10-17T06:38:23.574405+00:00.

**Baseline run: no verification.** This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, and the candidate was judged only by the harness. It certifies nothing.

Key evidence (trajectory): candidate produced for the independent judge; no gates recorded



What to do: Compare with the Attest run of the same task in the evaluation report.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- nothing: no gate was reached

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `bf2d8e08-8152-4bce-aeaf-6395085b58f8`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking off).

Attest 0.2.0 revision `f2f93c051afe14b4` (33 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/5` sha256 `8511520ba75a7690`, per-test child `fb466d37f748f9ef`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

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

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -422,6 +422,34 @@
 
         return rccmp
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can be used in place of this version.
+
+        Patch differences are ignored for major versions above zero. For major
+        version zero, major, minor, patch, and prerelease must all match.
+
+        >>> Version(1, 2, 3).is_compatible(Version(1, 3, 0))
+        True
+        >>> Version(0, 1, 0).is_compatible(Version(0, 1, 1))
+        False
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        if self._major == 0:
+            return (
+                self._major == other._major
+                and self._minor == other._minor
+                and self._patch == other._patch
+                and self._prerelease == other._prerelease
+            )
+
+        return (
+            self._major == other._major
+            and other._minor >= self._minor
+            and self._prerelease == other._prerelease
+        )
+
     def next_version(self, part: str, prerelease_token: str = "rc") -> "Version":
         """
         Determines next version, preserving natural order.
```




## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10564 | 131 | 7168 | - | 59.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 12447 | 144 | 7168 | - | 57.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 13205 | 469 | 7168 | - | 79.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11878 | 113 | 7168 | - | 39.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12699 | 623 | 7168 | - | 76.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12977 | 135 | 7168 | - | 74.4s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 73770/1615/43008; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1488f-0f70-74a7-bfcf-9a41a1037199 | SUCCESS | 0 | 3.695s | retained | on | 0.02188536 |
| impl-tests-4 | 01a14892-d95b-70c9-b8fd-a5fe0a32c88e | SUCCESS | 0 | 2.115s | disposable | off | 0.00951214 |
| impl-python-5 | 01a14894-23c6-742d-87f6-bd59c83e782d | SUCCESS | 0 | 0.687s | disposable | off | 0.002334 |

Sandbox operations: 3, total guest duration 6.497s, retained images ['bf2d8e08-8152-4bce-aeaf-6395085b58f8'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
