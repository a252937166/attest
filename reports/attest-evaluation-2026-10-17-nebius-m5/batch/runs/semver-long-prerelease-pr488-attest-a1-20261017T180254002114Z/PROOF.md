# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: NO CHANGE**  
Run `semver-long-prerelease-pr488-attest-a1-20261017T180254002114Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T18:02:54.002312+00:00, finished 2026-10-17T18:07:26.723046+00:00.

**The implementer changed nothing.** The implementer finished without modifying any file, so there is no candidate to verify. Nothing was certified.

Key evidence (trajectory): turn budget exhausted without changes



What to do: Read the implementer's action trail; then clarify the task or raise the turn budget and run again.

Reasons: turn budget exhausted without changes


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 4 of 9 sealed tests fail on the unmodified base; the candidate was never run against them (E1).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 4 of 9 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `4c1f95b0f1c13ddc44498ea7e4cb5191e1250819ffcae4d9877b065dbb344246`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `1c90725f-cc47-44be-b160-d6022776be10`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Replace the prerelease identifier comparison in Version._nat_cmp so that ASCII-only digit identifiers of arbitrary length are compared by their decimal value without calling int() (strip leading zeros, then compare length, then lexicographically), while preserving legacy behavior for non-ASCII digit identifiers (compare via int(), raising ValueError eagerly on failure) and for non-numeric identifiers (plain string comparison). Core version comparison (major, minor, patch) must still decide before prerelease is examined. All other Version behavior (parsing, constructor storage, build metadata handling, release ordering) remains unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version._nat_cmp | _nat_cmp(cls: Type[Version], a: Optional[str], b: Optional[str]) -> int | Compare two prerelease strings (dot-separated identifiers) according to SemVer ordering with the following rules: (1) Split each string by '.'; empty or None be | ValueError: raised eagerly when a non-ASCII-numeric identifier (str.isdigit() true but not all ASCII) fails int() conversion, but only when core versions are eq |
| semver.version.Version.compare | compare(self: Version, other: Comparable) -> int | Compare self with other version. Convert other to Version via parse (str), constructor (dict/tuple/list), or direct instance. First compare core version tuple ( | TypeError: if other is not str, bytes, dict, tuple, list, or Version instance.; ValueError: propagated from Version.parse (invalid version string) or from _nat_ |
| semver.version.Version.__lt__ | __lt__(self: Version, other: Comparable) -> bool | Return self.compare(other) < 0. | TypeError, ValueError: propagated from compare(). |
| semver.version.Version.__le__ | __le__(self: Version, other: Comparable) -> bool | Return self.compare(other) <= 0. | TypeError, ValueError: propagated from compare(). |
| semver.version.Version.__gt__ | __gt__(self: Version, other: Comparable) -> bool | Return self.compare(other) > 0. | TypeError, ValueError: propagated from compare(). |
| semver.version.Version.__ge__ | __ge__(self: Version, other: Comparable) -> bool | Return self.compare(other) >= 0. | TypeError, ValueError: propagated from compare(). |
| semver.version.Version.__eq__ | __eq__(self: Version, other: Comparable) -> bool | Return self.compare(other) == 0. | TypeError, ValueError: propagated from compare(). |
| semver.version.Version.__ne__ | __ne__(self: Version, other: Comparable) -> bool | Return self.compare(other) != 0. | TypeError, ValueError: propagated from compare(). |

Acceptance criteria:
1. Version.is_valid('0.0.0-' + '1'*5000) returns True.
2. Version.parse('0.0.0-' + '1'*5000).compare('0.0.0-' + '1'*5000) returns 0 (no ValueError).
3. Version.parse('0.0.0-' + '1'*5000).compare('0.0.0-2') returns 1 and Version.parse('0.0.0-2').compare('0.0.0-' + '1'*5000) returns -1 (no ValueError).
4. Ordering of long numeric prereleases via Version.parse: '9'*4999 < '1'+'0'*4999; '1'+'0'*4998+'1' < '1'+'0'*4998+'2'; '1'*5000 < 'alpha'; 'alpha.'+'1'*5000 < 'alpha.'+'1'*5000+'.1'. For each pair low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
5. Build metadata ignored: Version.parse('0.0.0-' + '1'*5000) == Version.parse('0.0.0-' + '1'*5000).replace(build='other') and Version.parse('0.0.0-' + '1'*5000) < Version(0,0,0).
6. Constructor prerelease legacy comparison (Version(0,0,0, prerelease=left).compare(Version(0,0,0, prerelease=right))): ('0001','1')->0; ('000','0')->0; ('02','10')->-1; ('01.2','1.2')->0; ('2a','10a')->1; ('01a','1a')->-1; ('-1','0')->1; ('',None)->0; ('\u0661\u0662','12')->0; ('\uff11\uff12','13')->-1; ('1\u0662','12')->0; ('\u0660\u0660\u0661','1')->0. Reverse comparisons give negated results. Both .prerelease attributes stored as given.
7. Version.parse('0.0.0-' + p) raises ValueError for p in ('01', '01.2', '\u0661\u0662', '\uff11\uff12').
8. Version(0,0,0, prerelease=left).compare(Version(0,0,0, prerelease=right)) raises ValueError for (left,right) in (('\u00b2','2'), ('a.\u00b2','b.0'), ('a.0','b.\u00b2')).
9. Version(0,0,0, prerelease='\u00b2') < Version(1,0,0, prerelease='\u00b2') is True (core comparison decides before prerelease examination).
10. Existing pytest suite in tests/ passes unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `a12b2b5879a489ce0e0297ef88ccdccae4e58d71d0ffc6ca44f6650489f6e87e`, 9 test methods, sealed at 2026-10-17T18:03:56.596428+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (4 of 9 methods: ERROR 4): 4 of 9 methods failing, 5 passing; operation `01a14b08-db21-7450-ad7a-60e93f01a26b`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestNatCmpAcceptance.test_build_metadata_ignored | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_constructor_legacy_comparison | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_constructor_raises_on_non_ascii_digit | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_core_decides_before_prerelease | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_long_numeric_is_valid | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_long_numeric_parse_equal | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_long_vs_short_numeric | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ordering_long_numeric | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_parse_raises_on_non_ascii_digit | ok (1 ev) | - |

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 29607 | 7743 | 0 | 0.052836 | 23.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 28345 | 1460 | 0 | 0.009817 | 11.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 4685 | 1551 | 0 | 0.002801 | 8.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 10882 | 3652 | 0 | 0.006551 | 19.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 5235 | 191 | 0 | 0.001742 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 5671 | 213 | 0 | 0.001893 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 6546 | 173 | 0 | 0.002119 | 2.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 8886 | 181 | 0 | 0.002829 | 18.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 10184 | 4186 | 0 | 0.006823 | 26.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 7720 | 432 | 0 | 0.002705 | 5.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 8726 | 128 | 0 | 0.002733 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 9705 | 290 | 0 | 0.003172 | 54.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 9998 | 471 | 0 | 0.003423 | 61.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 8831 | 274 | 0 | 0.002896 | 3.6s | ok |

Model calls: 14 (0 failed, 0 malformed); tokens in/out/cached 155021/20945/0; USD: 0.10234.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a14b08-129d-7273-be8b-cf2822ae4f90 | SUCCESS | 0 | 0.665s | retained | off | 0.0011854900000000002 |
| checkpoint | 01a14b08-2d05-7046-a3dd-c27d4ae65336 | SUCCESS | 0 | 3.708s | retained | on | 0.02421161 |
| red-1 | 01a14b08-db21-7450-ad7a-60e93f01a26b | SUCCESS | 0 | 2.893s | disposable | off | 0.022389549999999998 |

Sandbox operations: 3, total guest duration 7.266s, retained images ['3df3018d-3511-4e0c-89c8-0beeab706fa8', '1c90725f-cc47-44be-b160-d6022776be10'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
