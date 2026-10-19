# Repairs of the 19 October 2026 audit (revision 5, version 0.5.0)

The independent audit of revision 4 (`reports/attest-audit-2026-10-19/README.md`) recorded 35 repair items (11 P1, 21 P2,
3 P3). This folder records their repair: one subfolder per area with the files changed, the mechanism, the acceptance tests
(every counterexample next to its positive control) and the remaining limitations, plus the full offline suite, the
development-gateway reliability batch and the strict bundle checks that followed. The auditor's folder was not modified;
where an auditor's reproduction script could not run against the repaired code (because it asserts the faulty behaviour or
indexes a record that the repair removes), an adapted copy lives next to its output in the area folder.

Order of work, as instructed: verification and arbitration first (CORE), then accounting (AC), console (API and the
publication contract), host boundaries (BOUND), release and deployment (REL, OPS), documentation (DOC). Arbitration
application was kept conditional on the structural validator: a correction clears a gate only on authentic, structurally
sound evidence, and anything unknown or untrusted preserves the hold.

| Area | Findings | Report | Acceptance tests |
| --- | --- | --- | --- |
| Core verification and offline evidence | CORE-01 to CORE-07, API-08 (atomic artifact writes), witness validation | [core/README.md](core/README.md) | `tests/test_audit_core.py` (29), `tests/test_verification.py` (42, two scenarios rewritten and nine added) |
| Budget and evaluation integrity | AC-01, AC-02, AC-03, AC-04, AC-07 | [accounting/README.md](accounting/README.md) | `tests/test_audit_accounting.py` (24), `tests/test_budget.py` |
| Console, API, storage, client | API-01 to API-11, AC-05, AC-06, publication contract, artifact containment | [console/README.md](console/README.md) | `tests/test_audit_console.py`, `tests/console_client_test.mjs`, `tests/test_console.py`, `tests/test_phase1.py` |
| Host execution, imports, output, release | BOUND-01 to BOUND-04, REL-01, REL-02 | [boundaries/README.md](boundaries/README.md) | `tests/test_audit_boundaries.py`, `tests/test_core.py`, `tests/test_external.py` |
| Deployment safeguards | OPS-01, OPS-02, OPS-03 | [ops/README.md](ops/README.md) | `tests/test_audit_ops.py` and the rehearsal logs in that folder |
| Documentation and claims | DOC-01 | this file, section "Documentation" | the console tests assert the public page names no gateway; `tests/test_budget.py::RegisterOnly` guards the registration path |

## Finding by finding

| ID | Priority | Repair in one sentence | Where |
| --- | --- | --- | --- |
| CORE-01 | P1 | Lost, forged, mismatched, incomplete or non-isolated execution results are never red: discrimination of a correction counts only authentic failures under a structurally sound base or mutant run, untrusted original failures are never arbitrated, and the raw base and mutant evidence is kept and recomputed by `attest check`. | core |
| CORE-02 | P1 | A sealed test that failed by assertion or by any exception is never overridden; only a test the supervisor killed at its timeout may be corrected. | core |
| CORE-03 | P1 | A mutant is killed only by an authentic test failure under a sound supervisor run; incomplete, zero-test, non-isolated, forged, crashed or timed-out runs are unknown and excluded from the score; `attest check` reclassifies every mutant. | core |
| CORE-04 | P1 | Supervisor v7: one session and process group per test child, group kill at the timeout, bounded pipe draining and cleanup, escaped descendants swept through `/proc`, cleanup recorded and bound. | core |
| CORE-05 | P2 | A correction may change only the failing tests' bodies (additive, non-colliding imports allowed); class metadata, signatures, helpers and module code must be identical; the arbiter must classify exactly the failing tests. | core |
| CORE-06 | P2 | Every bundle declares an evidence protocol; a current bundle must carry the complete evidence for its verdict; historical bundles are never fully verified; the former apply mode is confined to dated historical bundles. | core |
| CORE-07 | P2 | Manifest v2: complete listing, unique contained paths, correct counts, no symbolic links; the integrity badge needs digests and completeness. | core |
| AC-01 | P1 | Every process start rebuilds the batch total from all distinct completed rows and all distinct unowned run directories; nothing suppresses a recovered cost. | accounting |
| AC-02 | P1 | A finished bundle without a persisted row is recovered from its ledger (journal fallback) and counted once; its cell runs again as a fresh attempt. | accounting |
| AC-03 | P1 | A USD reservation is journaled, flushed and fsynced before dispatch; a journal failure refuses the request and halts the provider; a failed settlement write leaves the durable reservation at its bound. | accounting |
| AC-04 | P1 | A 200 answer without complete usage keeps its reservation unsettled, is recorded as a metering failure and halts further paid calls; explicit zero counters settle as known zero. | accounting |
| AC-05 | P1 | Imports preserve `cost_usd_committed` (recomputed from call records or the journal for legacy bundles); deduplication carries it. | console |
| AC-06 | P2 | UTC-day policy: a run counts against every day on which it was queued, started, ran or finished; active reservations count regardless of day; the policy is named in health. | console |
| AC-07 | P2 | Resume restores the registered provider and limits from the schedule, refuses conflicting flags before any runtime construction, records executed provider and limits per row and invalidates drifted comparisons; the Nebius call cap defaults to 22. | accounting |
| API-01 | P2 | Explicit trusted-proxy policy; the vhost overwrites the forwarded address with the real peer. | console, `deploy/yungou/attest.axiqo.xyz.conf` |
| API-02 | P2 | Visitor quota and run creation under one store lock. | console |
| API-03 | P2 | Every query materialised under the lock; no live cursor leaves it. | console |
| API-04 | P2 | Explicit public response models: no requester address, host path or raw error. | console |
| API-05 | P2 | Zip downloads built from the manifest with containment checks; caps refuse with 413 instead of omitting files. | console |
| API-06 | P2 | Bounded retention of failed runs with independent housekeeping. | console |
| API-07 | P2 | 503 before any row or reservation when the worker is not alive; the worker loop is supervised and restarted. | console |
| API-08 | P2 | Client retries the terminal detail with a visible state; the server answers 503 `bundle_incomplete` for a half-written bundle; all artifacts are written atomically. | console, core |
| API-09 | P3 | Sanitized public errors with correlation ids; diagnostics stored server-side. | console |
| API-10 | P3 | Copy patch only on a successful response. | console |
| API-11 | P3 | Authoritative per-run queue position from the worker's ordered queue. | console |
| Publication | decision | Team runs carry `visibility: team` and are hidden from every read route without the team token; the page says so. | console |
| Containment | decision | Symlinks and resolved paths outside the run directory are unavailable through both download routes. | console |
| BOUND-01 | P2 | Literal search by default; `re:` runs a regular expression in a child process under a 2 s deadline with bounded input and output. | boundaries |
| BOUND-02 | P2 | Snapshots never follow links or read special files (`O_NOFOLLOW`, fd-relative walks, bounded reads); skipped entries are recorded. | boundaries |
| BOUND-03 | P2 | Archives are streamed; declared sizes, totals, member and link counts are bounded before any read; reads are capped. | boundaries |
| BOUND-04 | P2 | Guest runner v3 drains both streams into bounded buffers while the step runs, kills the step's process group on timeout or output exhaustion and records the cleanup. | boundaries |
| REL-01 | P1 | Strict release exclusions at every depth (credential files, archives, databases, binaries), every staged file scanned whatever its name, fail-closed scan on the staged tree. | boundaries |
| REL-02 | P2 | Export destinations overlapping the source tree are refused before any deletion; the export is staged in a sibling directory and swapped in only after verification. | boundaries |
| OPS-01 | P1 | A real scoped version rollback; the old behaviour is a clearly named decommission command that requires `--yes`. | ops |
| OPS-02 | P2 | Transactional installer: staged release and dependencies, validation and nginx test before the switch, strict health assertions, automatic restoration of the previous release on failure. | ops |
| OPS-03 | P2 | Required-file manifest in the archive (`RELEASE.json`), readback of every entry after extraction. | ops |
| DOC-01 | P2 | See "Documentation" below. | this file |

## Documentation (DOC-01)

- The console page no longer calls the two external-task outcomes correct refusals; the frozen-results note says they were
  unfinished tasks and labels the table as the historical M5 figures of the pinned 17 Oct version, distinct from the
  revision the console runs now.
- The capability text says that deterministic code derives the verdict from the recorded gates, several of which rest on
  model-generated evidence, instead of "no model opinion enters".
- One call cap: 22 calls per run for the Nebius provider (harness default, schedule, the revision-5 command and the proposal
  in `FREEZE.md`); the M5 pin keeps its historical 20 and the revision-4 section records its own 20-versus-22 inconsistency.
- `FREEZE.md` separates the historical M5 pin (the results quoted in the Devpost draft), the superseded revision-4 pin and
  the current revision-5 pin; `submission/DEVPOST.md` names both the M5 commit and the current release.
- README, TESTING, PILOT, the console notes and the Devpost draft describe the repaired rules (sealed oracle never weakened,
  authentic evidence only, evidence protocol, historical versus fully verified bundles, team runs private).
- Retained limitations, stated where the claims are made: an executed contradiction witness is a model claim with a recorded
  execution, not a formal proof of impossibility; the sealer's coverage map is its own claim and not proof of behavioural
  completeness; the in-interpreter outcome report of a test child can still be forged by a candidate that spares the
  canaries, so no absolute anti-forgery claim is made (mutation and held-out gates remain the detectors).

## Verified baseline after the repairs

| Check | Result | Evidence |
| --- | --- | --- |
| Complete offline suite | 314 tests, no failure (179 before the audit; 135 added or rewritten, every audit finding with at least one counterexample and one positive control) | `offline-suite.log` |
| Auditor's reproductions against the repaired code | none reproduces; where a script asserts the faulty behaviour it now stops at that assertion (recorded) | `core/core-repro-after-fix.json`, `accounting/auditor-repro-after-fix.txt`, `console/repro_*.txt`, `boundaries/boundaries-repro-after-fix.txt` |
| Recorded bundle corpus (165 bundles under `reports/`, outside the three known defective sets) | every bundle still passes `attest check` as a historical bundle; none is reported as complete evidence, by design | `tests/test_audit_core.py::RecordedCorpusHistorical` |
| Development-gateway reliability batch 1 (`evaluation-codex/`, 5 Attest cells, package `722cd6dd…`) | `durationkit-units-001` VERIFIED (judge correct), `semver-long-prerelease-pr488` VERIFIED (held-out 450 passed), `rle-encode` INFEASIBLE on an executed witness (true reject), `balanced-brackets` and `kvparse-refactor-001` ERROR: HTTP 502 "model at capacity" from the development gateway on the sealing call, recorded as infrastructure errors, nothing replayed | `evaluation-codex/RESULTS.md`, `evaluation-codex.log` |
| Development-gateway reliability batch 2 (`evaluation-codex-2/`, the two cells above, pinned package `1e12d462…`) | `balanced-brackets` VERIFIED (judge correct); `kvparse-refactor-001` INFEASIBLE on an executed witness: a wrong refusal of a satisfiable task, caused by a contradiction inside the specification model's own restatement; the batch recorded it as `true_reject` under the harness of the time, corrected to `false_refusal` in `evaluation-codex-2/CORRECTIONS.md` and in the harness | `evaluation-codex-2/RESULTS.md`, `evaluation-codex-2/CORRECTIONS.md` |
| Strict current-protocol checks of the seven new bundles | every bundle: evidence protocol 2, complete evidence for its verdict, manifest verified (`OK, EVIDENCE COMPLETE`) | `attest check` on each run directory (`bundle-checks.txt`) |
| Mutation evidence in the three VERIFIED runs | 9/0/0, 10/2/0 and 8/1/0 killed/survived/unknown under the authentic-kill policy; no unknown mutant | the bundles' `breaker.json` |
| Public export of the repaired tree | passes the staged export, the fail-closed scan and `attest check` on every exported bundle (figures in `EXPORT.json` of the review tree) | `dist/public/EXPORT.json` |

What the batches did not exercise: no run needed an arbitration correction, so the validated-correction path (CORE-01, CORE-05)
rests on the offline acceptance tests and the earlier revision-4 batches; no sealed hold occurred (`kvparse-refactor-001`,
which held in M5, now ends INFEASIBLE before sealing, see above).

## Remaining limitations (summary)

See each area's README for the complete list. The ones that bound the claims most: the supervisor's trust boundary is
unchanged (a candidate can forge its own child report while sparing the canaries; mutation and held-out tests detect it);
without `/proc` an escaped descendant cannot be found and the result is refused rather than trusted; a sealed timeout
correction reduces the workload the oracle demanded; batches registered before this revision resume under their frozen
harness copy; the deployment scripts were rehearsed under shims that model systemd and nginx, not against the production
daemons; the Nemotron validation of this revision has not run and the proposal in `FREEZE.md` remains unapproved.
