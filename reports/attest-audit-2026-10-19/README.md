# Attest revision 4 comprehensive review — 19 October 2026

**Disposition: the implemented MVP is live, but revision 4 should not yet be treated as fully hardened or ready for a new paid evaluation.** This audit records 35 repair items: 11 P1, 21 P2 and 3 P3. These include reproduced logic faults, conditional release/runtime boundary failures, and confirmed deployment/documentation mismatches; they are not 35 observed production incidents. Separate documented limitations and publication decisions are not counted as defects.

The highest-priority work is to prevent arbitration/mutation evidence from clearing a gate without trusted execution results, preserve committed spend across every failure/restart path, and correct the misleading rollback command. Use Codex and offline fakes for remediation. The proposed $10 Nebius evaluation is still awaiting explicit authorization; this audit does not approve it.

## Scope and boundaries

Reviewed pipeline/specification/audit/sealing/correction/mutation/verdict code, supervision and process cleanup, the offline checker/manifest, providers/ledger/evaluation resume, the FastAPI console/worker/SQLite store, client refresh/copy/queue behavior, repository import/workspace bounds, public export, deployment scripts and documented release state.

No product code or product tests were edited, no production write, SSH deployment, service restart, paid model call or Sandbox API operation was performed. Offline probes used temporary stores/files, fake responses/executors and audit-only sentinels. The runtime-boundary regex was contained in a child with a one-second parent deadline. A temporary deployment archive was built locally, inspected and removed. Live checks were low-frequency unauthenticated GETs and read-only browser navigation; no live run button was used.

This is a bounded source and behavioral audit, not a proof that every possible defect has been found. It did not reconcile official billing/credit expiry, verify the server's exact Python/SQLite race susceptibility, load-test production, repeat every earlier browser/mobile state, verify external pilot adoption, or publish/submit anything. Legal/licensing claims and new dependency CVEs were not assessed. GraphQL, WebSocket and JWT flows do not exist in this application's reviewed API and were not invented as audit requirements.

## Verified baseline

| Check | Observed result | Evidence |
|---|---|---|
| Existing complete offline suite | 179 tests; zero failures, errors or skips | [Result](offline-suite-results.json), [log](offline-suite.log) |
| Public exported directory bundles | 157/157 accepted by the existing checker; 282 total historical warnings | [Results](bundle-check-results.json) |
| Latest development-gateway batch bundles | 8/8 accepted; zero checker warnings | [Results](bundle-check-results.json) |
| Static scan | Semgrep 1.175.0, 151 Python rules, 53 targets, zero findings | [Raw result](semgrep.json) |
| API reproduction scenarios | Twelve scenarios reproduce/control current behavior | [Results](api-repro-results.json) |
| Client-function reproduction scenarios | Three unchanged original functions reproduce faulty behavior | [Results](console-repro-results.json) |
| Accounting reproductions | Seven current-behavior assertions pass | [Results](accounting-repro-results.json) |
| Import/workspace/export/runner probes | Six bounded reproductions confirmed | [Results](boundaries-repro-results.json) |
| Live service, around 06:45 UTC | HTTP 200, 0.4.0, worker alive, empty queue, no current run/reservation, 39 Nebius rows | [Read-only snapshot](live-readonly-results.json) |
| Live static assets | Home HTML, JS and CSS exactly match the audited local files | [Read-only snapshot](live-readonly-results.json) |
| Live browser | Home and one recorded VERIFIED case load; no captured browser warning/error for that case | [Case binding readback](browser-recorded-case.json) |
| Disk headroom | 1,327 MB / 9.61% free; guard accepts runs | [Read-only snapshot](live-readonly-results.json) |
| Local release Git | Clean `dist/public`, records HEAD `85a5212`, no configured remote | Local Git readback; code `4437b29`, pin `ac2dc04` |
| Package fingerprint | 35 Python sources, `b27a1c070a852ae2f0f2776c59cebe09cea87307a014ca80a1c37f7e66e68b49` | [Results](bundle-check-results.json) |
| Existing final video strict decode | Exit 183, invalid H.264 NAL records | [Results](video-decode-results.json) |

Passing the existing tests/checker or a pattern scan does not negate the counterexamples below. In particular, the current checker also accepts deliberately incomplete synthetic evidence; its current success status is not the acceptance criterion for the repaired protocol. Historical warnings must remain visibly distinguished from complete current evidence.

## Complete repair inventory

### Verification and offline evidence — [detailed core review](core-findings.md)

| ID | Priority | Problem | Required repair |
|---|---|---|---|
| CORE-01 | P1 | Missing base results, forged corrected mutants or original adversarial tampering can be arbitrated into a passing gate | Share strict structural validation for all positive/negative evidence; preserve raw base/mutant records; never treat unknown as red |
| CORE-02 | P1 | A real bad candidate can throw in correct test code and have the test weakened as a supposed test defect | Keep executed sealed oracle failures held unless an independent test defect is established; do not infer cause from exception frame/type |
| CORE-03 | P1 | Incomplete/zero-test/non-isolated mutant execution can score as a kill | Validate execution/discovery before scoring; unknown must not increase mutation score |
| CORE-04 | P1 | Killing only the test child followed by unbounded pipe collection defeats its timeout | Isolate process groups, kill/reap descendants and bound all draining/cleanup |
| CORE-05 | P2 | Correction scope ignores import/class changes and does not exactly cover failing classification IDs | Compare the whole AST except approved method bodies; preserve bindings/class metadata; match IDs exactly |
| CORE-06 | P2 | Incomplete modern VERIFIED/witnessless INFEASIBLE evidence and unscoped legacy clear flags pass offline checking | Introduce versioned required evidence; strict modern schema; explicit historical/partial mode; isolation must be present and true |
| CORE-07 | P2 | An empty/incomplete manifest can still receive the verified-integrity badge | Require exact complete listings, supported schema, correct totals/counts, unique contained paths; missing required files are errors |

CORE-04's timeout probe executes the exact function AST with a fake process/clock. It demonstrates an unbounded call, not a measured real multi-hour delay. CORE-06's incomplete/legacy bundles are clearly synthetic and do not prove current live pipeline invocation of the legacy route.

### Budget and evaluation integrity — [detailed accounting review](accounting-findings.md)

| ID | Priority | Problem | Required repair |
|---|---|---|---|
| AC-01 | P1 | Second resume drops an already recovered interrupted reservation | Reconstruct every distinct completed/interrupted run's committed USD on every start |
| AC-02 | P1 | A completed bundle written before its evaluation row is persisted is ignored in recovery | Reconcile ownership by run ID/path; recover its ledger/journal even if its result cannot be restored |
| AC-03 | P1 | Failed reservation journal append is swallowed before HTTP dispatch | Persist reservation successfully before dispatch; fail closed if no durable sink; retain uncertainty after failed settlement |
| AC-04 | P1 | Valid HTTP 200 output without complete usage is settled as known $0 | Validate usage counters; retain the conservative reservation until usage/cost is established |
| AC-05 | P1 | Imported uncertain-cost bundle loses `cost_usd_committed` in the DB | Preserve conservative committed USD and recover it before accepting new runs |
| AC-06 | P2 | Run creation before UTC midnight causes next-day completed spend to disappear from that day's cap | Account by call time with reservation carryover, or define a conservative explicitly named allocation policy |
| AC-07 | P2 | Resume can silently switch the registered provider/limits without invalidating comparison | Restore and enforce the registered schedule; refuse conflicting overrides or create an explicit amended evaluation |

Illustrative reproduced values: a $0.25 interrupted reservation becomes $0 on the second resume; three fake successful calls fit a $0.02 cap when each nonzero reservation is settled at zero. These are local fault injections, not measured real charges. They show why a newly approved total alone is insufficient until recovery and settlement are repaired.

### Console, API, storage and UI behavior — [detailed API review](api-findings.md)

| ID | Priority | Problem | Required repair |
|---|---|---|---|
| API-01 | P2 | Caller-controlled forwarding header rotates the visitor quota identity | Define trusted proxies, overwrite/normalize the edge address and use only the validated client identity |
| API-02 | P2 | Quota count and enqueue race admits four requests under a limit of three | Check quota and create/reserve the row atomically |
| API-03 | P2 | Shared SQLite cursor fetches outside the lock fail under concurrent local reads | Materialize results inside synchronization or isolate connections; verify actual deployed runtime |
| API-04 | P2 | Public list/detail/tasks/health expose visitor IPs and absolute operational paths | Explicit public response models; keep identity/internal diagnostics out of public evidence |
| API-05 | P2 | ZIP silently drops manifested files at/above 5 MB and keeps their original manifest | Stream the advertised complete bundle or explicitly refuse/label a derivative export |
| API-06 | P2 | Error-run artifacts escape retention indefinitely | Bound terminal-error retention and clean up independently of successful completion |
| API-07 | P2 | API accepts work despite a dead consumer | Enforce worker readiness before row/reservation creation; supervise worker recovery |
| API-08 | P2 | One failed final-detail fetch permanently stops selected-run updates; half-written JSON can return 500 | Retry final detail visibly; atomically publish JSON and deliberately handle incomplete artifact state |
| API-09 | P3 | Raw exception/traceback text is public | Stable sanitized errors with server-side diagnostics and correlation IDs |
| API-10 | P3 | Failed patch response is copied with a false success message | Require a successful response before changing clipboard or status |
| API-11 | P3 | Claimed position counts jobs behind the selected run | Expose authoritative per-run position or label only total waiting work |

The two hourly quota bypasses do **not** prove bypass of the independent daily USD admission guard. The SQLite fault is reproduced on local Python 3.12.0/SQLite 3.42.0 (retained probe 3/120 faults versus 0/120 with lock-through-fetch); production runtime behavior was not tested.

### Host/import/export/recovery/documentation — [detailed boundaries review](boundaries-findings.md)

| ID | Priority | Problem | Required repair |
|---|---|---|---|
| BOUND-01 | P2 | A tiny pathological regex can occupy the host worker without a deadline | Literal/linear search or a separately bounded search process |
| BOUND-02 | P2 | Direct local snapshot follows file symlinks outside the chosen repository | No-follow/containment checks with explicit internal-link policy |
| BOUND-03 | P2 | Archive file/total limits are checked after whole-file reads | Streaming enumeration, pre-read sizes/counts and bounded reads |
| BOUND-04 | P2 | Guest output cap clips text only after full output capture | Concurrent bounded stream draining and output/process-group limits |
| REL-01 | P1 before publication | Export copies `.env`/archives that its scanner never examines | Strict file allowlist, credential exclusions and bounded archive-aware final scanning |
| REL-02 | P2 | `export_public.py --force --out .` can erase the source tree | Refuse source/ancestor overlap before deletion; staged validated replacement |
| OPS-01 | P1 recovery | Claimed version rollback actually disables service and removes its vhost | Implement/test a real scoped version rollback; separate decommissioning and correct runbooks |
| OPS-02 | P2 | Installer switches active code before dependencies/health/config validation and can report success after failed nginx validation | Versioned staged app/venv, strict health/config failure handling and scoped automatic rollback |
| OPS-03 | P2 | Archive omits promised `FREEZE.md` and `TESTING.md` | Shared required-file manifest and archive/installed-file readback |
| DOC-01 | P2 | Stale “correct refusal” prose, excessive deterministic claims, 20-vs-22 call cap and unclear current/historical pin | One corrected data/limit source; exact approved command; explicit revision/evidence scope |

REL-01 uses fake sentinels and establishes a scanner gap, **not an actual leaked key**. BOUND-02 and the API's analogous download symlink observation require a local/imported directory precondition, **not a demonstrated remote arbitrary-file-read chain**. OPS-01/02 are source/runbook observations; no installer or rollback was run on any server.

## Product decisions and remaining claim limits

1. **Team runs:** the live page explicitly declares all console content public. The token currently gates only use of the team inference profile. Anonymous reads of a team row therefore are not labelled unauthorized private access here. Decide whether to retain this all-public contract with deliberate safe publication or implement persistent visibility across every read/export/current-run reference. Startup import filtering is not read authorization.
2. **Artifact publication boundary:** the ZIP includes non-allowlisted regular files and follows run-directory file symlinks. The individual endpoint also follows allowlisted-name symlinks. The auditor created only temporary sentinels; no remote creation route or actual secret exposure was found. If directories are not fully trusted public inputs, enforce containment/no-links plus an explicit artifact set and aggregate export limits.
3. **Contradiction witnesses:** marker+exit-code execution is an executed model claim, not formal proof of unsatisfiability. Validate criterion IDs and structured observations; retain witness source/output; state the semantic limitation. This audit did not invalidate the recorded RLE witness.
4. **Coverage:** the sealer self-reports mapping, and retry-exhausted coverage gaps do not currently block verdicts. If full criterion mapping is promised, make it a strict gate; do not equate a populated map with behavioral completeness.
5. **In-interpreter outcome reports:** the supervisor module already documents targeted child-result forgery as a trust limitation. This audit did not execute that attack. Nonces/canaries/isolation do not prove all possible candidate behavior is authenticated; narrow the claims or move trusted observation outside the candidate interpreter.
6. **Measured effectiveness:** revision 4 has workflow evidence on Codex, not a revised formal Nemotron outcome table. M5 remains historical evidence and did not demonstrate fewer broken patches. The new audit counterexamples also mean a passing development dry run is insufficient to claim the newly repaired guarantees.

## Repair and release order

1. Make correction application advisory again until CORE-01/02/05 are fixed; unknown/untrusted results must hold. Repair structural mutation handling and exact current-protocol offline checking/manifest completeness.
2. Close all five P1 accounting holes, define daily attribution and enforce registered resume configuration. Require a durable reservation before any paid dispatch. Prove repeated restart behavior with fake providers.
3. Bound host search, archive reads, guest streams and process cleanup. Repair quota/proxy/SQLite/admission/retention and public response/export boundaries. Run a small Codex-only fault/reliability batch with these acceptance cases.
4. Correct/rehearse rollback and transactional deployment outside production; repair release-file manifests and verify the new release's code/pin/assets/docs. Main app stays on **yungou**; any necessary Docker component stays on **Aliyun**, with no disruption to existing services.
5. Freeze a new reviewed revision, exact schedule/provider/models/sampling/caps and the acceptance results. Preserve old bundles and publish corrections/derived evidence rather than rewriting history. Only then propose or execute a separately approved, bounded Nebius smoke/evaluation plan; $10 remains a proposal here. Reconcile official usage/remaining credit separately.
6. Before publication/video/submission, close remaining delivery gates below. A small known-bad counterexample suite must fail correctly, and known-good cases must continue to complete. The 179 existing tests alone are not the release gate.

## Outstanding delivery gates

- Review the exact public tree **and Git history**, then publish a repository and replace placeholders. No remote is currently configured in the reviewed local repository; this does not disprove a separate owner-created remote.
- Rebuild the damaged final MP4 from valid captures matching the final UI; require strict full decode, visual/audio review and resolved voice provenance before upload. The video was intentionally untouched in this audit.
- Refresh Devpost text/screenshots/testing links to the final code and measured evaluation, then verify actual submission separately from a local draft.
- Obtain a real consented external pilot if presenting adoption/impact. The current feedback form is blank; no external developer trial was verified.
- Confirm official Token Factory credit balance, expiry/beta constraints and provider usage. The local journal is not an invoice and the last reported balance is not a current readback. No actual debit/remaining credit was established here.
- Keep judging access viable with measured disk/retention, an explicit daily spend policy and verified renewal coverage. Current 1.3 GB disk headroom is limited, but a live low-disk failure was not induced or observed.

## Handoff acceptance

Each detailed finding includes a concrete acceptance test. The repairing agent should return: issue IDs fixed; code revision; targeted counterexample and positive-control results; full offline suite; complete/strict modern bundle checks; Codex fault/reliability evidence; a new freeze; exact deployment digest/readback and a tested scoped rollback; and a separately approved paid proposal, without inferring authorization from this review.

Final [audit-integrity readback](audit-integrity-results.json): all report links resolve; 19 audited-source fingerprint checks match; the reviewed public Git tree remains clean with no remote; inventory counts are 11 P1, 21 P2 and 3 P3. This readback verifies audit consistency, not that the reported product defects have been repaired.
