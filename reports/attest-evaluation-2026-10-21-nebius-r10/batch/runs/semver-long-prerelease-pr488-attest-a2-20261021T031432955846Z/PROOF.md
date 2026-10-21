# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: ERROR**  
Run `semver-long-prerelease-pr488-attest-a2-20261021T031432955846Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:14:32.958182+00:00, finished 2026-10-21T03:18:30.021691+00:00.

**This run stopped for reconciliation.** At stage implement another run of its batch stopped (pipeline), so Attest sent nothing further, replayed nothing and certified nothing. The repository was not changed by this run.

Key evidence (E7): 0 operation(s) to reconcile: stopped for reconciliation at implement-8: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every ...



What to do: Reconcile the listed operations against the providers' records (each item names its read-only check) before this task is run again; nothing of this run is ever sent again.

Reasons: stopped for reconciliation at implement-8: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 3 of 8 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the pipeline at stage implement; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 3 of 8 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | pipeline failed at stage implement: stopped for reconciliation at implement-8: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further ... |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `4c1f95b0f1c13ddc44498ea7e4cb5191e1250819ffcae4d9877b065dbb344246`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `3ec1e42c-d6b6-4889-b7dc-25957b3b397d`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Fix the prerelease identifier comparison in `semver.version.Version._nat_cmp` to avoid converting long ASCII‑digit‑only identifiers to `int` (which raises `ValueError` for strings longer than 4300 digits in CPython), while preserving the exact existing ordering semantics: numeric identifiers (ASCII digits only) compare by decimal value after stripping leading zeros (all‑zero becomes "0"), using length‑then‑lexicographic comparison; numeric identifiers are less than any non‑numeric identifier; non‑numeric identifiers compare lexicographically; shorter identifier list is lower when all compared identifiers are equal. Legacy constructor behaviour must be preserved: identifiers with leading zeros or non‑ASCII decimal digits (where `str.isdigit()` is true) still compare by their `int()` value (so "١٢" == "12", "１２" < "13"); identifiers where `str.isdigit()` is true but `int()` fails (e.g. "²") must raise `ValueError` eagerly during `compare()` when core versions are equal, even if an earlier identifier would decide the order; core version comparison (major, minor, patch) still decides before prerelease is examined. Parsing, validation, build metadata handling, prerelease storage, and all other behaviour must remain unchanged, and the existing pytest suite must pass unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version._nat_cmp | @classmethod def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Compare two prerelease strings (or None) according to the semantic versioning prerelease ordering rules, but with the following refined numeric comparison for A | ValueError: raised when an identifier has `str.isdigit() == True` but `int(identifier)` raises ValueError (e.g. "²"), and the core versions are equal so the pre |
| semver.version.Version.compare | def compare(self, other: Comparable) -> int | Compare this Version with another Version (or string, dict, tuple, list). First compare major, minor, patch as integers. If they differ, return -1, 0, or 1 acco | TypeError: if `other` is not a Version, str, bytes, dict, tuple, or list.; ValueError: propagated from `_nat_cmp` when an identifier with `str.isdigit() == True |
| semver.version.Version.parse | @classmethod def parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Parse a version string according to the SemVer specification (with optional minor and patch). Must reject non‑canonical prerelease identifiers such as leading z | ValueError: if version string is not a valid SemVer string (including non‑canonical prerelease). |
| semver.version.Version.is_valid | @classmethod def is_valid(cls, version: str) -> bool | Return True if `Version.parse(version)` succeeds, False otherwise. Must remain unchanged. |  |
| semver.version.Version.__init__ | def __init__(self, major: int, minor: int, patch: int, prerelease: Optional[str] = None, build: Optional[str] = None) | Construct a Version instance storing the given parts exactly as provided. Prerelease and build are stored as given (including leading zeros, non‑ASCII digits, e | ValueError: if major, minor, or patch are negative. |

Acceptance criteria:
AC1. With v = "0.0.0-" + "1" * 5000: Version.is_valid(v) is True; Version.parse(v).compare(v) == 0; Version.parse(v).compare("0.0.0-2") == 1 and Version.parse("0.0.0-2").compare(v) == -1 (no ValueError).
AC2. Ordering of long numeric prereleases with Version.parse("0.0.0-" + x): "9" * 4999 < "1" + "0" * 4999; "1" + "0" * 4998 + "1" < "1" + "0" * 4998 + "2"; "1" * 5000 < "alpha"; "alpha." + "1" * 5000 < "alpha." + "1" * 5000 + ".1". For each pair low.compare(high) == -1, high.compare(low) == 1 and sorted([high, low]) == [low, high].
AC3. Build metadata is ignored and release order is preserved: with version = Version.parse("0.0.0-" + "1" * 5000), version == version.replace(build="other") and version < Version(0, 0, 0).
AC4. Constructor prereleases compare with legacy rules, as Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)): ("0001", "1") -> 0; ("000", "0") -> 0; ("02", "10") -> -1; ("01.2", "1.2") -> 0; ("2a", "10a") -> 1; ("01a", "1a") -> -1; ("-1", "0") -> 1; ("", None) -> 0; ("\u0661\u0662", "12") -> 0; ("\uff11\uff12", "13") -> -1; ("1\u0662", "12") -> 0; ("\u0660\u0660\u0661", "1") -> 0. The reverse comparison gives the negated result and both .prerelease attributes are stored as given.
AC5. Version.parse("0.0.0-" + p) raises ValueError for p in ("01", "01.2", "\u0661\u0662", "\uff11\uff12").
AC6. Version(0, 0, 0, prerelease=left).compare(Version(0, 0, 0, prerelease=right)) raises ValueError for (left, right) in (("\u00b2", "2"), ("a.\u00b2", "b.0"), ("a.0", "b.\u00b2")).
AC7. Version(0, 0, 0, prerelease="\u00b2") < Version(1, 0, 0, prerelease="\u00b2") is True (core comparison decides before prerelease is examined).
AC8. The existing pytest suite in tests/ passes unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is satisfiable. The key insight is that TC4 (authoritative) overrides the prose 'numeric < non-numeric' rule when both identifiers have str.isdigit()==True (legacy int() comparison), and TC6 requires a pre-scan of all identifiers in both prereleases for any identifier with isdigit()==True but failing int() (e.g., '²'), raising ValueError eagerly before any comparison logic runs. The resulting _nat_cmp algorithm: (1) split prereleases into identifiers (empty/None -> ['']); (2) for every identifier in both lists, if id.isdigit() and not all ASCII digits, try int(id) and raise ValueError on failure; (3) then compare pairwise with short-circuiting: both ASCII-digit-only -> numeric compare (strip leading zeros, length then lexicographic); both isdigit()==True -> int() compare; one ASCII-digit-only + other not isdigit() -> ASCII-digit-only smaller; else -> string compare; exhausted equal prefixes -> shorter list smaller. This satisfies all TC1-TC8. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `7499999d42143508d7e84ad4d9343f23e997b8943d6be4862f1a93eba04fcae7`, 8 test methods, sealed at 2026-10-21T03:15:55.678678+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 8 methods: ERROR 3): 3 of 8 methods failing, 5 passing; operation `01a15c75-584f-7705-9140-1e833dc01bc4`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestNatCmpAcceptance.test_ac1_long_numeric_is_valid_and_orders | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac2_ordering_long_numeric | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac3_build_metadata_ignored_and_release_order | ERROR (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac4_constructor_legacy_rules | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac5_parse_rejects_non_canonical | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac6_compare_raises_value_error_on_bad_digit | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac7_core_decides_before_prerelease_bad_digit | ok (1 ev) | - |
| test_sealed.TestNatCmpAcceptance.test_ac8_existing_pytest_suite_passes | ok (1 ev) | - |


## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 29607 | 3310 | 26112 | 0.039537 | 12.8s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 30877 | 9476 | 0 | 0.059305 | 35.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 28708 | 1628 | 0 | 0.010078 | 10.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 6120 | 116 | 0 | 0.001940 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 6265 | 112 | 0 | 0.001980 | 3.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 6711 | 1256 | 0 | 0.003144 | 11.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 6856 | 2137 | 0 | 0.003980 | 16.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 7305 | 7029 | 0 | 0.008518 | 68.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 7693 | 4078 | 0 | 0.005978 | 25.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 8061 | 3033 | 0 | 0.005148 | 26.3s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 138203/32175/26112; Inference USD: 0.139608.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a15c74-371f-74dc-86bb-6879fbc4f518 | SUCCESS | 0 | 0.678s | retained | off | 0.00117219 |
| checkpoint | 01a15c74-4b74-77db-a405-8d7d5b4224a6 | SUCCESS | 0 | 3.494s | retained | on | 0.02328492 |
| red-1 | 01a15c75-584f-7705-9140-1e833dc01bc4 | SUCCESS | 0 | 2.771s | disposable | off | 0.02062066 |

Sandbox operations: 3, total guest duration 6.943s, retained images ['3a88a48d-c747-4b5b-9d82-2a9b59ee50d5', '3ec1e42c-d6b6-4889-b7dc-25957b3b397d'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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

## 12. E7 Failure record
Component: pipeline; stage: implement; model calls 10 (0 failed); sandbox operations 3; committed inference USD 0.139608; uncertain unpriced calls 0; retried: no; outcome uncertain: no.

- stopped for reconciliation at implement-8: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operation to settle is listed under reconciliation with the read-only check that settles it

## 12b. Reconciliation (nothing of this run is sent again)
The run stopped at stage `-` (batch_stop) at 2026-10-21T03:18:28.611327+00:00: another run of this batch stopped for reconciliation; this run sent nothing further. Each item below is settled by a human with the read-only check it names.

No operation is left to settle on a provider's side; the stop concerns this run's own record.

Rule: once an operation's outcome is uncertain (a request that may have been executed and whose answer is unknown, an accepted operation whose outcome was not read, an answer that could not be priced) or a record of the run could not be made durable, the run sends nothing further: no model call, no sandbox operation, no poll; it ends ERROR with every such operation listed here with the read-only check that settles it, and none of them is ever sent again

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
