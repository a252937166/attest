# Milestone M2: bundle provenance, artifact manifest, offline check and exhibits (17 Oct 2026)

> Terminology correction (17 Oct 2026, same day): this report originally called bundles with a manifest "signed" and
> bundles without one "unsigned". A SHA-256 manifest is an integrity and internal-consistency check, not a digital
> signature and not independent proof of execution. The wording below was corrected in place; the code and `attest check`
> now say "manifest verified" and "no manifest".

Scope: items 2.1 to 2.3 of the plan in `reports/attest-competitive-review-2026-10-16/README.md` section 5, implemented in
parallel with milestone M3 (console redesign, `reports/attest-m3-2026-10-17/README.md`). No inference was needed for the
implementation; the live evidence in section 5 used the team's Codex gateway and Nebius Token Factory Sandboxes only.
Nothing was published, submitted or redeployed; the live console is unchanged by this milestone.

## 1. What changed

| Item | Acceptance criterion | Implementation | Result |
| --- | --- | --- | --- |
| 2.1 Record Attest revision, runner and supervisor digests, sampling parameters, turn limit and thresholds, upstream URL and commit | Present in every new bundle; PROOF.md section 1 shows them | `attest/core/provenance.py`; `bundle["provenance"]` set at pipeline start; `TaskSpec.upstream` (`task.json` key `upstream`, included in the frozen record only when present); `Pipeline.limits()`; PROOF.md "1. Frozen task and provenance" | Every bundle produced by the offline suite and by the live runs in section 5 carries `provenance`; both python-semver tasks record `https://github.com/python-semver/python-semver` at commit `9b475f71ef91…` (parent of PR #368) with the merge commit of the held-out tests |
| 2.2 Artifact manifest with sha256 per file; `python -m attest check bundle.zip` | `check` recomputes digests, binding and gate-to-verdict derivation and exits non-zero on any mismatch; offline tests with a tampered zip | `attest/core/manifest.py` (`manifest.json` written last by `Pipeline.write_manifest`), `verify_raw.json` (raw supervisor results), `attest/core/check.py`, `attest/core/verdict.py`, CLI `attest check PATHS [--json]` | 80 offline tests pass; tampered directory, tampered zip, forged verdict with a regenerated manifest, edited sealed module, edited outcomes and edited ledger totals all exit 1 with the named finding (section 2); 68 recorded bundles swept (section 3) |
| 2.3 "What this bundle proves, and what it does not" citing exhibits E1 to E7 | Section present and generated from the gates, not hand-written | `attest/core/exhibits.py` (`exhibits`, `decision`, `gates_table`, `counterexamples`, `proves`, `summary`); PROOF.md section 0 and exhibit-labelled sections; the console API uses the same module (M3) | Generated for all 68 recorded bundles without error; the pre-M1 fail-open adversarial record renders as "not run", never as a pass |

Supporting changes made for the acceptance criteria:

- **Supervisor v5** (`attest-sealed-supervisor/5`): the per-test child keeps the unittest failure tracebacks as
  `failure_tail`, so a counterexample can show `AssertionError: 'a1111' != 'a1'` instead of an empty capture (every
  recorded failing test before M2 had an empty `captured_tail`, because only the test's own stdout/stderr was captured).
  The version string now comes from one constant; the fakes and the sandbox script use it.
- **Verdict derivation recorded**: `verdict.derivation` holds the rule, the derived verdict and what blocked VERIFIED. The
  pipeline fails closed with a recorded discrepancy if its reasons and the gate-derived verdict ever disagree.
- **Transport robustness**: `http.client.IncompleteRead` (a chunked body cut short while reading) is now a
  `TransportError`, so operation polls retry it and a POST after it stays uncertain. Found by the first v5 sandbox run,
  which crashed on a poll (`sandbox-adversarial-v5-attempt1-incompleteread.log`); the rerun is section 4.
- **Bound suites record test ids**: `verification.existing.modules[].ids` and `heldout.modules[].ids` so the checker can
  recompute `bind_modules` offline.

## 2. Offline tests

`python3 -m unittest discover -s tests -t .`: 94 tests pass (58 before this round, 22 added in `tests/test_m2.py`, 14 added by M3 in `tests/test_console.py`).

| Group | What it proves |
| --- | --- |
| `Provenance` | revision digest is stable and changes when a source changes; guest digests name supervisor v5; sampling recorded for both providers; `upstream` loaded, frozen only when present |
| `VerdictRule` | every gate must pass, skipped never counts, scope and turn budget block, arbitration changes the verdict only in apply mode; a VERIFIED without gates is inconsistent |
| `Exhibits` | fixed refs E1 to E7, honest statuses (no held-out suite is `none`, not a pass), decision copy per reason class (`verified`, `heldout_failed`, `integrity`, `sealed_failed`), proves/does-not-prove cite exhibits, assertion parsing keeps the argument order honest, legacy fail-open record is `not_run` |
| `ManifestAndCheck` | new bundles carry provenance, manifest, raw results and derivation; `check` passes on the directory and on a console-style zip with zero warnings; tampered PROOF.md fails the manifest; a forged VERIFIED with a regenerated manifest fails `verdict_derivation`, `verified_has_no_reasons` and `proof_md_matches`; edited sealed module, edited outcomes and edited totals are caught; an old unsigned bundle is reported unsigned, not tampered; CLI exit codes 0/1; zips with `..` paths are refused |
| `TransportRobustness` | a truncated chunked read raises `TransportError` |
| `RealSupervisorFailureText` | the real v5 supervisor and child run locally: a failing assertion and a `TypeError` appear in `failure_tail`, `summarize` carries it and the counterexample parser extracts both sides |

## 3. `attest check` over the 68 recorded bundles

Every `proof_bundle.json` under `reports/` was checked in place (none has a manifest or raw results, so all are
"no manifest" (integrity not checkable) and their bindings cannot be recomputed; digests inside the bundle, ledger totals, gate records and the verdict
rule are still checked). Historical artifacts were not modified.

| Finding | Bundles | Meaning |
| --- | --- | --- |
| `manifest_present` and `raw_results_present` warnings | 68 | all predate M2; reported as "no manifest" |
| `proof_md_matches` not comparable | 65 | rendered by an earlier Attest revision; digests still checked |
| `verdict_derivation` not applicable | 7 | first-slice bundles (15 Oct morning) have no `gates` record at all; 3 further bundles were decided before verification |
| `sealed_static_ids` not comparable | 2 | first-slice bundles record no `expected_ids` |
| `adversarial_gate_fail_open` warning | 3 | `console-run-durationkit-nebius` (the public judge run of 15 Oct), `p1-semver-codex`, `p1-semver-nebius`: the adversarial gate was recorded as passed although no adversarial test ran. This is the fail-open path removed in M1, now named by the checker; the VERIFIED verdicts of those runs rest on the other gates |
| `sealed_file_digest` and `adversarial_file_digest` errors | 2 | `attest-hardening-2026-10-16/semver-v2-codex-verified` and `smoke-run-durationkit-codex` are partial copies (4 to 5 files each); the sealed module and the adversarial module they reference are absent, so the checker correctly refuses to call them complete bundles |
| any other error | 0 | task digests, sealed and adversarial digests and static ids, candidate patch, ledger totals, gate records and verdict rule agree in every complete bundle |

Sample (no manifest, M1 run):

```
$ python3 -m attest check reports/attest-m1-2026-10-16/runs/balanced-brackets-20261016T192809Z
run balanced-brackets-20261016T192809Z verdict NEEDS HUMAN (no manifest: integrity not checkable)
  ok   task_spec_digest: recomputed b4b1ed357cf1c1bd vs recorded b4b1ed357cf1c1bd
  ok   sealed_file_digest: sealed/test_sealed.py sha256 a15d5e79001553e6 vs recorded a15d5e79001553e6
  ok   adversarial_file_digest: breaker_tests.py sha256 0dea373623eb7f35 vs recorded 0dea373623eb7f35
  ok   ledger_totals: totals recomputed from the individual records match
  ok   gates_match_stage_records: every gate agrees with the stage record it summarises
  ok   verdict_derivation: gates and verdict agree (blocking: adversarial_tests)
  warn proof_md_matches: PROOF.md differs from a fresh rendering; the bundle was produced by a different Attest revision ...
result: OK (0 error(s), 3 warning(s))
```

## 4. Real-sandbox adversarial scenarios against supervisor v5

`scripts/sandbox_adversarial_tests.py --workers 2` (Nebius Token Factory Sandboxes, no inference). Attempt 1 crashed on an
operation poll with `http.client.IncompleteRead` (log kept as `sandbox-adversarial-v5-attempt1-incompleteread.log`); the
HTTP client now treats that as a retryable transport error. Attempt 2 (`sandbox-adversarial-v5.json`, `.log`):
checkpoint operation `01a1487d-13e3-72a9-9171-d832090cbc2d`, 12 sandbox operations, all 11 scenarios correct.

| Scenario | Accepted | Canary | Failed checks | Operation |
| --- | --- | --- | --- | --- |
| honest | yes | ok | none | `01a1487d-2801-7338-a5b1-f32e0b382eff` |
| wrong | no | ok | `no_nonzero_exit`, `all_expected_pass` | `01a1487d-41cc-7285-a94e-92cf7b3d32cf` |
| tamper_sealed_file | no | flipped | digest changed, canary | `01a1487d-383b-712b-a59b-2270b5091913` |
| premature_exit | no | flipped | missing results | `01a1487d-5152-7288-9157-583007404b71` |
| forged_results_at_import | no | flipped | forged results, canary | `01a1487d-525d-703b-b065-f29ca0084796` |
| forged_stderr_text | no | ok | tests failed | `01a1487d-610f-770d-9be3-0a48e6dba861` |
| timeout | no | ok | `no_timeout` | `01a1487d-6d1e-7438-a497-7d502c5d562c` |
| crash_signal | no | ok | `no_signal` | `01a1487d-7052-7141-94c3-b96e83c22806` |
| forge_all_ok | no | flipped | `canary_must_fail_failed` | `01a1487d-8a0f-7443-9a21-8cc98addf17c` |
| plant_startup_hook | yes | ok | none (all writes denied, no hook afterwards) | `01a1487d-98fc-77d7-a535-a8efb4a3dc15` |
| legacy_order_plant_from_existing_step | no | flipped | `no_startup_hooks_on_import_path`, `canary_must_fail_failed` | `01a1487d-a7f2-7207-b8f6-512f92522415` |

Flags: `all_correct`, `privilege_separation_active`, `tamper_prevented_not_only_detected`, `forgery_caught_by_canary`,
`hook_planting_prevented`, `legacy_order_detected_as_tamper` all true. Codex allowance used: none. Nebius USD: none
(sandboxes are in free beta; raw cost diagnostics recorded in the ledger are not USD).

## 5. Live Codex evidence: the pre-registered 10-cell dry run (`m1-dryrun-3`)

The rerun pre-registered in `reports/attest-m1-2026-10-16/README.md` section 4.2 was started at 06:11 UTC on 17 Oct 2026
with the M2 code (`scripts/run_evaluation.py --provider codex --workers 2 --label m1-dryrun-3`, output
`reports/attest-m1-2026-10-16/evaluation-dryrun-codex-3/`, log `evaluation-dryrun-codex-3.log`). It is a dry run of the
harness on the development provider, not an evaluation result: Codex allowance only (61 model calls, no USD), one attempt
per cell, held-out suites stripped from both systems, every scheduled cell reported.

| Cell | Task | System | Verdict | Held-out judge | Reason class | Wall |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | BASELINE | correct (bound) | | 161 s |
| 1 | roman-to-numeral | attest | NEEDS HUMAN | correct (bound) | adversarial tests on `int` subclasses with overridden arithmetic and comparisons; arbiter: implementation bug | 680 s |
| 2 | rle-encode | baseline | BASELINE | correct (bound) | | 151 s |
| 3 | rle-encode | attest | INFEASIBLE | no candidate | specification stage: `encode('a1')` cannot round-trip through the unchanged `decode` | 50 s |
| 4 | balanced-brackets | baseline | BASELINE | correct (bound) | | 150 s |
| 5 | balanced-brackets | attest | NEEDS HUMAN | correct (bound) | one adversarial test timed out (exhaustive short streams); arbiter: test defect | 616 s |
| 6 | durationkit-units-001 | baseline | BASELINE | correct (bound) | | 206 s |
| 7 | durationkit-units-001 | attest | NEEDS HUMAN | correct (bound) | one adversarial test on mixed Unicode decimal scripts failed (`AssertionError: 45240.0 != 58440.0`); arbiter: test defect | 785 s |
| 8 | semver-is-compatible-pr368-v2 | baseline | BASELINE | correct (stdout) | | 414 s |
| 9 | semver-is-compatible-pr368-v2 | attest | ERROR | not judged | Codex gateway `HTTP 429 hourly limit reached for this key` at the specification call (1 failed call, nothing retried) | 20 s |

Harness summary: baseline 5 of 5 completed (5 accepted, all judged correct); Attest 5 of 5 completed (0 accepted,
3 held with a correct candidate, 1 infeasible, 1 infrastructure error); `complete: true`, `stopped: null`, committed
USD 0.0. The gateway's hourly key limit struck again at the end of the batch (after 57 successful calls in 27 minutes);
as in the earlier dry runs it is reported as an infrastructure error and nothing fell back to Nebius. For M5 the batch
has to be paced below the key's hourly budget (one worker, or a pause between tasks) or split across hours.

What the dry run shows for M2:

- **Every bundle carries a manifest and checks clean.** `attest check` on all 10 run directories: 0 errors, 0 warnings each
  (manifest digests, bindings recomputed from `verify_raw.json`, ledger totals, gate records, verdict rule and PROOF.md
  all agree). Every bundle carries `provenance` with supervisor `attest-sealed-supervisor/5`; the two python-semver cells
  record the upstream repository and commit.
- **Counterexamples now carry the assertion.** The durationkit and roman cells show `failure_tail` text
  (`AssertionError: 45240.0 != 58440.0 within 1e-09 delta`, `ValueError: n must be between 1 and 3999`), which no bundle
  before supervisor v5 had.
- **Revision digest.** The cells record five different `attest_revision` digests (`b0b50de7…` to `e8ac9354…`) and
  version `0.2.0`: the harness process kept the code it had imported at 06:11 UTC while the package sources on disk were
  still being edited (exhibits wording, checker tolerance, the version bump to 0.3.0), and the revision is hashed from
  disk at each pipeline start. The digests are truthful about the files present at each start; a deployed process does
  not edit its own sources, and a git commit id (once the repository is published) will make the record unambiguous.
- **Method observations carried to M5.** Three Attest holds on candidates the held-out judge accepts: the breaker asks
  questions the task contracts leave open (`int` subclass semantics, Unicode decimal digits, an exhaustive test that
  exceeds the per-test timeout). The arbiter classified two as test defects and one as an implementation bug; the holds
  stand because arbitration is advisory. The specification stage judged rle-encode infeasible again with the digit
  counterexample. These are task-contract questions for the M5 method freeze, not verifier defects.

## 6. Where we remain weaker

- The checker establishes integrity and internal consistency since the bundle was written; it cannot re-execute the
  sandbox runs or prove the recorded operation ids were real. Binding recomputation covers the sealed, adversarial,
  bound existing and bound held-out suites; stdout-parsed suites have no raw record to recompute from.
- Without a git repository the "revision" is a digest of the sources; it identifies the code exactly but is not a
  reviewable history. Publishing the repository (pending the owner's review) will add the commit id automatically.
- Counterexample parsing shows the two sides of a unittest assertion as "first" and "second" because the test's argument
  order decides which is the actual value; the console and PROOF.md say so instead of guessing.
- The sampling record for the Codex gateway is the requested reasoning effort per role; the gateway controls the
  temperature and does not report it.
