# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: BASELINE**  
Run `semver-long-prerelease-pr488-baseline-a1-20261021T031014472935Z` · profile `eval-baseline-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:10:14.477091+00:00, finished 2026-10-21T03:13:06.010679+00:00.

**Baseline run: no verification.** This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, and the candidate was judged only by the harness. It certifies nothing.

Key evidence (trajectory): candidate produced for the independent judge; no gates recorded



What to do: Compare with the Attest run of the same task in the evaluation report.

Reasons: implementer did not finish


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
Task `semver-long-prerelease-pr488`, spec digest `4c1f95b0f1c13ddc44498ea7e4cb5191e1250819ffcae4d9877b065dbb344246`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `1885356e-e86a-4780-875b-1877e9a75081`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

(none)

Acceptance criteria:
AC1. With v = "0.0.0-" + "1" * 5000: Version.is_valid(v) is True; Version.parse(v).compare(v) == 0; compare(v, "0.0.0-2") == 1 and compare("0.0.0-2", v) == -1 (no ValueError).
AC2. Ordering of long numeric prereleases with Version.parse("0.0.0-" + x): "9" * 4999 < "1" + "0" * 4999; "1" + "0" * 4998 + "1" < "1" + "0" * 4998 + "2"; "1" * 5000 < "alpha"; "alpha." + "1" * 5000 < "alpha." + "1" * 5000 + ".1". For each pair low.compare(high) == -1, high.compare(low) == 1 and sorted([high, low]) == [low, high].
AC3. Build metadata is ignored and release order is preserved: with version = Version.parse("0.0.0-" + "1" * 5000), version == version.replace(build="other") and version < Version(0, 0, 0).
AC4. Constructor prereleases compare with the legacy rules, as Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)): ("0001", "1") -> 0; ("000", "0") -> 0; ("02", "10") -> -1; ("01.2", "1.2") -> 0; ("2a", "10a") -> 1; ("01a", "1a") -> -1; ("-1", "0") -> 1; ("", None) -> 0; ("١٢", "12") -> 0; ("１２", "13") -> -1; ("1٢", "12") -> 0; ("٠٠١", "1") -> 0; the reverse comparison gives the negated result and both .prerelease attributes are stored as given.
AC5. Version.parse("0.0.0-" + p) raises ValueError for p in ("01", "01.2", "١٢", "１２").
AC6. Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)) raises ValueError for (left, right) in (("²", "2"), ("a.²", "b.0"), ("a.0", "b.²")).
AC7. Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True (the core comparison decides before the prerelease is examined).
AC8. The existing pytest suite in tests/ passes unchanged.

## 2b. Contract audit (executed witnesses)
Not run (bundle predates the contract audit, or the run ended before the specification).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


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
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 5213 | 117 | 0 | 0.001669 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 5390 | 144 | 0 | 0.001747 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 5786 | 1283 | 0 | 0.002890 | 9.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 6137 | 6637 | 0 | 0.007814 | 45.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 6501 | 1394 | 0 | 0.003205 | 10.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 6618 | 676 | 0 | 0.002594 | 8.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 6789 | 4060 | 0 | 0.005691 | 33.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 6906 | 456 | 0 | 0.002482 | 4.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 7052 | 913 | 0 | 0.002937 | 8.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 7195 | 486 | 0 | 0.002596 | 4.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 7469 | 892 | 0 | 0.003044 | 6.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 7265 | 3303 | 0 | 0.005152 | 19.3s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 78321/20361/0; Inference USD: 0.041821.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a15c70-4516-762d-aada-45ab869f3c0a | SUCCESS | 0 | 0.93s | retained | off | 0.00117173 |
| checkpoint | 01a15c70-5b39-7777-ae9f-daa3903e589f | SUCCESS | 0 | 3.814s | retained | on | 0.02332793 |

Sandbox operations: 2, total guest duration 4.744s, retained images ['c0752537-cb39-4050-b801-bbc9e4c06c62', '1885356e-e86a-4780-875b-1877e9a75081'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
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
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
