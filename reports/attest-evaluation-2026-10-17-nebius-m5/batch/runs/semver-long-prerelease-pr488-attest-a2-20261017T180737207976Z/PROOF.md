# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: NO CHANGE**  
Run `semver-long-prerelease-pr488-attest-a2-20261017T180737207976Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T18:07:37.208265+00:00, finished 2026-10-17T18:10:36.990750+00:00.

**The implementer changed nothing.** The implementer finished without modifying any file, so there is no candidate to verify. Nothing was certified.

Key evidence (trajectory): turn budget exhausted without changes



What to do: Read the implementer's action trail; then clarify the task or raise the turn budget and run again.

Reasons: turn budget exhausted without changes


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 3 of 7 sealed tests fail on the unmodified base; the candidate was never run against them (E1).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 3 of 7 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `4c1f95b0f1c13ddc44498ea7e4cb5191e1250819ffcae4d9877b065dbb344246`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `98dde650-ae03-43fd-8633-9e3af3a2509c`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Modify the private classmethod `Version._nat_cmp` in `src/semver/version.py` so that prerelease identifiers consisting solely of ASCII digits are compared by their decimal value without ever calling `int()` on the full string (to avoid CPython's 4300‑digit limit). All other identifiers keep their existing semantics: non‑ASCII digit identifiers (where `str.isdigit()` is true but not all characters are ASCII digits) are compared by their `int()` value and must raise `ValueError` eagerly if `int()` fails, but only when the core version parts (major, minor, patch) are equal. Non‑numeric identifiers compare as plain strings. Numeric identifiers (both ASCII and non‑ASCII) are considered lower than any non‑numeric identifier. The pairwise comparison rules (length then lexicographic for stripped ASCII numeric strings, integer value for non‑ASCII numeric, string order for non‑numeric, longer list wins when all compared identifiers are equal) must be preserved exactly. Parsing (`Version.parse`), the constructor (`Version.__init__`), build metadata handling, and all other public methods must remain unchanged. The existing pytest suite must continue to pass.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version._nat_cmp | @classmethod def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Compares two prerelease strings (or None/empty) according to the SemVer prerelease ordering rules with the following detailed algorithm: 1. Split each input on  | ValueError: raised eagerly when any non‑ASCII‑numeric identifier in either prerelease string fails `int()` conversion (e.g., identifier contains a superscript d |
| semver.version.Version.compare | def compare(self, other: Comparable) -> int | Unchanged except that it now relies on the fixed `_nat_cmp`. It first compares major, minor, patch; if they differ, returns that result. If they are equal, it c | TypeError: if `other` is not a Version, str, bytes, dict, tuple, or list.; ValueError: propagated from `_nat_cmp` when a non‑ASCII‑numeric identifier fails `int |

Acceptance criteria:
1. With v = "0.0.0-" + "1" * 5000: Version.is_valid(v) is True; Version.parse(v).compare(v) == 0; compare(v, "0.0.0-2") == 1 and compare("0.0.0-2", v) == -1 (no ValueError).
2. Ordering of long numeric prereleases with Version.parse("0.0.0-" + x): "9" * 4999 < "1" + "0" * 4999; "1" + "0" * 4998 + "1" < "1" + "0" * 4998 + "2"; "1" * 5000 < "alpha"; "alpha." + "1" * 5000 < "alpha." + "1" * 5000 + ".1". For each pair low.compare(high) == -1, high.compare(low) == 1 and sorted([high, low]) == [low, high].
3. Build metadata is ignored and release order is preserved: with version = Version.parse("0.0.0-" + "1" * 5000), version == version.replace(build="other") and version < Version(0, 0, 0).
4. Constructor prereleases compare with the legacy rules, as Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)): ("0001", "1") -> 0; ("000", "0") -> 0; ("02", "10") -> -1; ("01.2", "1.2") -> 0; ("2a", "10a") -> 1; ("01a", "1a") -> -1; ("-1", "0") -> 1; ("", None) -> 0; ("\u0661\u0662", "12") -> 0; ("\uff11\uff12", "13") -> -1; ("1\u0662", "12") -> 0; ("\u0660\u0660\u0661", "1") -> 0; the reverse comparison gives the negated result and both .prerelease attributes are stored as given.
5. Version.parse("0.0.0-" + p) raises ValueError for p in ("01", "01.2", "\u0661\u0662", "\uff11\uff12").
6. Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)) raises ValueError for (left, right) in (("\u00b2", "2"), ("a.\u00b2", "b.0"), ("a.0", "b.\u00b2")).
7. Version(0, 0, 0, prerelease="\u00b2") < Version(1, 0, 0, prerelease="\u00b2") is True (the core comparison decides before the prerelease is examined).
8. The existing pytest suite in tests/ passes unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `afc761de41c9ee731a386c0d485748b298e603ade49ad49947cb6ee981fefe52`, 7 test methods, sealed at 2026-10-17T18:08:44.034802+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 7 methods: ERROR 3): 3 of 7 methods failing, 4 passing; operation `01a14b0d-44fc-7395-800b-4edd66c5d6c0`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestNatCmpAcceptance.test_build_metadata_ignored_and_release_order | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_compare_raises_value_error_for_non_ascii_numeric_failing_int | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_constructor_prerelease_compare_legacy_rules | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_core_version_decides_before_prerelease_for_superscript | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_long_numeric_is_valid_and_orders | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ordering_long_numeric | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_parse_raises_value_error_for_non_ascii_numeric_with_leading_zero | ok (1 ev) | - |

## 4. Candidate patch
0 changed path(s); scope check passed; 12 implementer turn(s).

```diff
(no changes)
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
No grounding calls (no Tavily client configured).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 29607 | 9657 | 26112 | 0.058578 | 32.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 28454 | 1549 | 0 | 0.009930 | 10.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 4679 | 117 | 0 | 0.001509 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 10882 | 3651 | 0 | 0.006550 | 25.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 5644 | 132 | 0 | 0.001812 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 6665 | 121 | 0 | 0.002108 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 6976 | 196 | 0 | 0.002269 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 11861 | 650 | 0 | 0.004143 | 6.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 13293 | 4322 | 0 | 0.007878 | 25.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 8601 | 634 | 0 | 0.003151 | 5.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 12369 | 4095 | 0 | 0.007396 | 27.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 8654 | 469 | 0 | 0.003018 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 8923 | 202 | 0 | 0.002859 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 8972 | 120 | 0 | 0.002800 | 2.9s | ok |

Model calls: 14 (0 failed, 0 malformed); tokens in/out/cached 165580/25915/26112; USD: 0.114001.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a14b0c-651d-71a9-b674-a69e2c3aaea4 | SUCCESS | 0 | 0.652s | retained | off | 0.00117256 |
| checkpoint | 01a14b0c-7d01-77eb-9fba-06d2e70ddacf | SUCCESS | 0 | 3.879s | retained | on | 0.02320982 |
| red-1 | 01a14b0d-44fc-7395-800b-4edd66c5d6c0 | SUCCESS | 0 | 2.48s | disposable | off | 0.01867377 |

Sandbox operations: 3, total guest duration 7.011s, retained images ['70ca53c7-5b04-49e7-abe5-12b135b4c892', '98dde650-ae03-43fd-8633-9e3af3a2509c'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
