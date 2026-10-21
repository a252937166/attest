# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: NO CHANGE**  
Run `semver-is-compatible-pr368-v2-20261021T070345824312Z` · profile `judge-demo` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T07:03:45.917434+00:00, finished 2026-10-21T07:09:35.024388+00:00.

**The implementer did not produce a patch.** The implementer used its whole turn budget (12 turn(s)) without finishing and without changing a file. This is an unfinished task, not a judgement that no change was needed and not a repair: there is no candidate, so nothing was verified and nothing was certified.

Key evidence (trajectory): unfinished: the turn budget (12 turns) was exhausted without a patch; the implementer neither finished nor changed a file



What to do: Read the implementer's action trail (the Activity tab) to see where the turns went. Run again with a larger turn budget or a narrower task; a task the model cannot navigate in the budget stays unfinished.

Reasons: unfinished: the turn budget (12 turns) was exhausted without a patch; the implementer neither finished nor changed a file


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 16 of 17 sealed tests fail on the unmodified base; the candidate was never run against them (E1).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 16 of 17 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | not run | - | configured but not reached |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `8ad94176d183307774d0c06f5c58bf164f132a8eadde1b945f6169fbb5c4ab70`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `174e4080-005e-4040-9932-710fb93fa653`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.10.3 revision `c002ef609d9c4de8` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.15 on Linux-5.13.5-1.el7.elrepo.x86_64-x86_64-with-glibc2.17; package executed from `/opt/attest/releases/0.10.3-c002ef609d9c/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add an instance method `Version.is_compatible(other: Version) -> bool` to the Version class in src/semver/version.py. The method returns True when `other` (the new version) can be used in place of `self` (the old version). Compatibility rules: majors must be equal; new.minor >= old.minor; prerelease parts must be equal (both None counts as equal); patch is ignored. Major version 0 is special: only identical versions (major, minor, patch, prerelease all equal) are compatible. If `other` is not a Version instance (subclasses allowed), raise TypeError with message starting with 'Expected a Version type but got ' followed by the type representation. Include a docstring with at least two doctest examples. Do not modify any other public behavior, tests, docs, or packaging; keep the existing pytest suite passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version.is_compatible | def is_compatible(self, other: 'Version') -> bool | Returns True when `other` (new version) is compatible with `self` (old version). Compatibility rules: 1) major versions must be equal. 2) If major == 0: version | TypeError: raised when `other` is not an instance of Version (or subclass). Message must start with 'Expected a Version type but got ' followed by the type repr |

Acceptance criteria:
AC1. Version(1, 2, 3).is_compatible(Version(1, 2, 3)) is True
AC2. Version(1, 2, 3).is_compatible(Version(1, 2, 4)) is True (patch ignored)
AC3. Version(1, 2, 4).is_compatible(Version(1, 2, 3)) is True (patch ignored, minor equal)
AC4. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) is True (equal prereleases)
AC5. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) is True (identical major-0 versions)
AC6. Version(0, 1, 0).is_compatible(Version(0, 1, 1)) is False (major 0 requires identical version)
AC7. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) is False (lower minor)
AC8. Version(2, 0, 0).is_compatible(Version(1, 5, 0)) is False (different major)
AC9. Version(1, 2, 3, 'rc.1').is_compatible(Version(1, 2, 3, 'rc.0')) is False (different prerelease)
AC10. Version(1, 0, 0).is_compatible(Version(1, 0, 0, 'rc1')) is False (prerelease vs none)
AC11. Version(1, 0, 0, 'rc1').is_compatible(Version(1, 0, 0)) is False (none vs prerelease)
AC12. Version(1, 2, 3).is_compatible('wrongtype') raises TypeError with message starting with 'Expected a Version type but got <class 'str'>'
AC13. Version(1, 2, 3).is_compatible({'a': 2}) raises TypeError with message starting with 'Expected a Version type but got <class 'dict'>'
AC14. Version(1, 2, 3).is_compatible([]) raises TypeError with message starting with 'Expected a Version type but got <class 'list'>'
AC15. class CustomVersion(Version): pass; CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) is True (subclass accepted)
AC16. The method's docstring contains at least two doctest examples
AC17. The existing pytest test suite (tests/) continues to pass without modifications

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The authoritative task criteria (TC1-TC8) are internally consistent: they describe a coherent compatibility semantics with a clear major-0 special case, prerelease equality, minor monotonicity, patch ignorance, subclass acceptance, and a precise TypeError message format. No two criteria demand different outputs for the same concrete input. The new method can be added to src/semver/version.py without touching any other public API, tests, docs, or packaging, and the existing pytest suite will continue to pass. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `18f3c7cae3e0d0c4958e1f17645f3572bbfbb3365cfbc60250acbd8a36ecaa05`, 17 test methods, sealed at 2026-10-21T07:04:52.463205+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 3.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (16 of 17 methods: ERROR 16): 16 of 17 methods failing, 1 passing; operation `01a15d46-d63d-75b8-9085-9fecbf8e75cc`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIsCompatible.test_ac1 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac10 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac11 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac12 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac13 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac14 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac15 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac16 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac17 | ok (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac2 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac3 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac4 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac5 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac6 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac7 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac8 | ERROR (1 ev) | - |
| test_sealed.TestIsCompatible.test_ac9 | ERROR (1 ev) | - |


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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 20682 | 1603 | 17408 | 0.025491 | 7.0s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 22317 | 4945 | 0 | 0.037152 | 16.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 20608 | 1474 | 0 | 0.007509 | 6.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-2 | low | 20664 | 1464 | 0 | 0.007517 | 8.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-3 | low | 20662 | 1475 | 0 | 0.007526 | 8.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 3431 | 247 | 0 | 0.001252 | 3.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 3527 | 238 | 0 | 0.001272 | 6.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 9105 | 318 | 0 | 0.003018 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 4375 | 194 | 0 | 0.001487 | 2.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 4495 | 419 | 0 | 0.001726 | 3.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4614 | 144 | 0 | 0.001514 | 11.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 5069 | 7658 | 0 | 0.008413 | 49.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 5184 | 13019 | 0 | 0.013272 | 78.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 5741 | 4406 | 0 | 0.005688 | 21.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 6438 | 10891 | 0 | 0.011733 | 57.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 6784 | 835 | 0 | 0.002787 | 4.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 6716 | 4790 | 0 | 0.006326 | 28.3s | ok |

Model calls: 17 (0 failed, 0 malformed); tokens in/out/cached 170412/54120/17408; Inference USD: 0.143683.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15d45-f1fe-72e5-84b5-efda3789c0d4 | SUCCESS | 0 | 3.444s | retained | on | 0.022350560000000002 |
| red-2 | 01a15d46-9eec-73cf-ab4e-d29dc53b10e6 | SUCCESS | 0 | 4.367s | disposable | off | 0.03502683 |
| red-3 | 01a15d46-d63d-75b8-9085-9fecbf8e75cc | SUCCESS | 0 | 4.496s | disposable | off | 0.036864919999999995 |
| impl-python-8 | 01a15d49-6944-7535-9b26-b9ecd602e9b0 | SUCCESS | 0 | 0.632s | disposable | off | 0.0016652200000000002 |
| impl-python-9 | 01a15d49-c4dc-718b-8297-90589851500f | SUCCESS | 0 | 0.828s | disposable | off | 0.0016632 |
| impl-python-10 | 01a15d4a-b486-766a-ad82-7b79f522ef00 | SUCCESS | 0 | 0.606s | disposable | off | 0.00170862 |

Sandbox operations: 6, total guest duration 14.373s, retained images ['174e4080-005e-4040-9932-710fb93fa653'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'judge-demo': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
