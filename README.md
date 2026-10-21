# Attest

An evidence-gated coding agent for the Nebius x NVIDIA Global AI Hackathon (Coding and Agentic Engineering track).
Every task is a claim that must be proven: an independent model instance seals acceptance tests before any code exists,
the tests are shown failing on an unmodified checkpoint, the implementer works through validated JSON actions,
a fresh sandbox branch verifies the candidate against the pristine sealed copy, and a Proof Bundle records the evidence
and the usage ledger.

Watch the [2 min 50 s demonstration](https://youtu.be/EwW-yEKCk1A): a real Nemotron run ends NO CHANGE, followed by separately
labelled VERIFIED and refusal cases from the recorded evaluation, and an offline check of the downloaded evidence.

At a glance (21 Oct 2026). Live console: https://attest.axiqo.xyz (recorded runs first; a live Nemotron run starts only after an
explicit confirmation, within a daily cap). The latest evaluation on NVIDIA Nemotron, 32 cells on one suite: the plain agent shipped 2
broken patches and Attest none; Attest refused the task that cannot be satisfied both times, and it accepted 2 correct patches to the
plain agent's 8; other runs required review, stopped on infrastructure uncertainty, or ended without a patch
(`reports/attest-evaluation-2026-10-21-nebius-r10/README.md`). Judges: start at
[For judges](#for-judges). The dated paragraphs below record the project's history.

Status (16 Oct 2026): end-to-end pipeline with a hardened, privilege-separated verifier, a web console/API, and a live
deployment, plus a controlled evaluation against a plain agent. Start with the dated reports:
`reports/attest-hardening-2026-10-16/README.md` (verifier privilege separation, budget, disk, arbitration, implementer
efficiency), `reports/attest-evaluation-2026-10-16/README.md` (plain agent vs Attest, independent held-out judge),
`reports/attest-deployment-2026-10-16/README.md` (hardened build live at https://attest.axiqo.xyz). See
`attest-first-slice.md` for the earlier slices, `attest-console.md` for the console, and `attest-product-design.md` for
the full design. Competitive review, audit and plan (16 Oct 2026): `reports/attest-competitive-review-2026-10-16/README.md`;
console redesign (approved 16 Oct 2026, implemented in M3, second pass with a home page, brand, guide and motion on
18 Oct 2026: `reports/attest-ui-2026-10-18/README.md`, deployed the same day: `reports/attest-deployment-2026-10-18/README.md`). Milestone M1
(16 Oct 2026, `reports/attest-m1-2026-10-16/README.md`): the sealed supervisor is the first step of its own branch and the
repository's own suite runs in a separate branch (closes the root-before-supervisor bypass); verifier canaries and a
start-up-hook check catch blanket result forgery; unittest repository and held-out suites are bound through the same
supervisor and every gate carries an evidence class; the evaluation harness pre-registers every attempt, strips the
held-out suite from the system under test, defaults to Codex and refuses an unapproved Nebius batch. Corrections to the
earlier evaluation: `reports/attest-evaluation-2026-10-16/CORRECTIONS.md`. Milestone M2 (17 Oct 2026,
`reports/attest-m2-2026-10-17/README.md`): provenance in every bundle, an artifact manifest, the offline `attest check`,
one recorded verdict rule and exhibits E1 to E7 in PROOF.md. Milestone M3 (17 Oct 2026,
`reports/attest-m3-2026-10-17/README.md`): the console redesign approved on 16 Oct, implemented in `attest/app/` and
verified in a real browser. Reliability round and milestone M4 (17 Oct 2026, `reports/attest-reliability-2026-10-17/README.md`,
`reports/attest-m4-2026-10-17/README.md`): the three dry-run holds resolved (one verifier defect in the supervisor's result
pipe, one wrong expected value in a generated test, one contract gap), supervisor v6, Codex pacing that adopts the
gateway's declared policy, batches run from an immutable snapshot with provenance checks, the bounded external-repository
import with a real python-semver task, the pilot kit (`PILOT.md`) and the frozen M5 method (`METHOD.md`). Milestone M5
(17 Oct 2026, `reports/attest-evaluation-2026-10-17-nebius-m5/README.md`, results in `RESULTS.md` of that folder): the
frozen evaluation ran on Nemotron from the pinned commit `6b786a2e…`, 8 tasks x 2 systems x 2 attempts, all 32 cells
reported, $1.09 committed. Attest accepted 4 correct patches, shipped 2 broken ones (both on the unsatisfiable rle-encode
task, the same two the plain agent shipped), held 5 correct patches for a human, and produced no patch on the external semver
task twice (unfinished tasks, as corrected in that report's `CORRECTIONS.md`), and hit 3 transport-uncertain infrastructure errors;
the plain agent accepted 10 correct patches, shipped
2 broken ones, did not finish once and hit 3 errors. On this suite Attest did not ship fewer broken patches than the plain
agent; every one of its holds was on a patch the held-out judge accepted. License: MIT.

Revision 4 (19 Oct 2026, `reports/attest-revision-2026-10-19/README.md`, version 0.4.0): INFEASIBLE now requires a witness
program, written by a contract auditor and executed on the unmodified repository, that demonstrates the contradiction (a
bare claim of infeasibility is a hold); the sealer returns a coverage map that is checked for completeness; a failing
generated test corrected by the arbiter counts only after mechanical validation (same test methods, only the failing ones
changed, passes on the candidate, still fails on the base or is caught by a mutant) and then re-runs its gate, while a
sealed test that failed by assertion is never overridden; breaker syntax errors escalate to the arbiter's model; the
implementer has `search`, a def/class outline and a navigation warning, and an exhausted turn budget is reported as an
unfinished task (`NO CHANGE`, harness label `no_patch`), never as a correct refusal (`reports/attest-evaluation-2026-10-17-nebius-m5/CORRECTIONS.md`);
every run keeps an append-only ledger journal with reservations written before each request, the console reconciles an
interrupted run from it, and an idle service no longer reports a phantom reservation. The frozen M5 results are unchanged.
Revision 4 was deployed at https://attest.axiqo.xyz on 19 Oct 05:42 UTC (`reports/attest-deployment-2026-10-19/README.md`).

Revision 5 (19 Oct 2026, version 0.5.0, `reports/attest-audit-repairs-2026-10-19/README.md`) repairs the 35 findings of the
same day's audit (`reports/attest-audit-2026-10-19/README.md`) before any further paid work. Evidence: every bundle declares an
evidence protocol (version 2) and `attest check` requires the complete evidence for its verdict (every gate with its raw
supervisor result, every evaluated mutant's raw result, the base and mutant evidence of any correction, the executed witness
of an INFEASIBLE verdict, isolation recorded as active, a complete manifest); bundles without the field are historical and
are never reported as fully verified. Verification: a mutant is killed only by an authentic child failure under a structurally
sound supervisor run (lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown); a correction discriminates
only through authentic results on the base or a validly killed mutant, lost or forged evidence never does, and untrusted
original failures are never arbitrated; a sealed test that failed by assertion or by any exception is never overridden (only a
test the supervisor killed at its timeout may be corrected); a correction may change only the failing tests' bodies and must be
classified for exactly the failing tests; the supervisor (v7) kills a timed-out test's whole process group, bounds its cleanup
and records it. Accounting: a paid request is dispatched only after its reservation is durably journaled, a successful answer
without usage keeps its reservation and stops further paid calls, resumed batches restore their registered configuration and
recover every interrupted or unreported run's spend once, the console preserves committed cost on import and counts a run
against every UTC day it touched. Console: trusted-proxy visitor identity, atomic quota admission, materialised store reads,
public response models without requester addresses or paths, complete or explicitly refused bundle downloads with containment
checks, bounded retention of failed runs, admission refused without a live worker, sanitized errors with correlation ids,
authoritative queue positions, and team runs visible to the team only. Host: literal search with a bounded regular-expression
mode, snapshots that never follow links, streaming archive limits, bounded guest output. Release: a strict export allowlist
with a fail-closed scan, refusal of overlapping export destinations, a real version rollback, a transactional installer and a
release manifest. The repaired revision is validated offline and on the development gateway; its validation on Nemotron
remains a proposal awaiting the owner's approval (FREEZE.md).

Revision 6 (19 Oct 2026, version 0.6.0, `reports/attest-revision5-repairs-2026-10-19/README.md`) closes the seven findings of
the independent follow-up review of revision 5 (`reports/attest-revision5-review-2026-10-19/README.md`). Infeasibility: a run
ends INFEASIBLE only on a conflict grounded in the requester's own acceptance criteria (the task's `TC` ids, never only the
specification's derived `AC` ids) and demonstrated by a constrained witness (a program that defines no function or class,
creates no dynamic type and calls no `exec`/`eval`, inside the declared input domain); a demonstrated conflict that is derived,
mixed or unconstrained is held for a person (`NEEDS HUMAN`, reason class `contract_conflict_held`), and the recorded kvparse
refusal is re-read under that rule (`reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/CORRECTIONS.md`: the "every str
input" quantifier is the task's own sentence, and the witness disproved one implementation, not every allowed one). Evidence
protocol 3: `attest check` derives the mandatory stage records from the frozen task and the execution mode (an existing-suite
record with its raw result and binding in bound mode, held-out evidence exactly when the task declares held-out tests, a
grounded conflict behind every INFEASIBLE verdict), so jointly deleting a stage record with its raw result or its gate is a
named completeness error. Diagnostics: raw exception text never enters a bundle, a stage record, a progress event, a call
record, PROOF.md or a download; every failure is recorded in a private sidecar outside the run directory and published as a
fixed public sentence with a correlation reference. Accounting: a journal append that fails leaves the journal's framing
repaired or halts paid dispatch, and a partial write followed by another request and a restart recovers every reservation;
the CLI enforces and records the 22-call cap of the paid proposal, call 23 being refused before dispatch; the harness
freezes the effective provider configuration (resolved model ids per role, reasoning effort, sampling, limits) and an
environment override no longer silently preserves a valid comparison. Console: the team token travels in a header only, and
team downloads use short-lived, run-scoped, read-only tickets that can authorise no POST. The M5 results are unchanged.

Revision 7 (19 Oct 2026, version 0.7.0, `reports/attest-revision6-repairs-2026-10-19/README.md`) closes the three items of
the independent review of revision 6 (`reports/attest-revision6-review-2026-10-19/README.md`). Witness constraints: the
revision-6 rule was a list of forbidden spellings and an import alias of `type` passed it; a witness can now establish
INFEASIBLE only when it conforms to the constrained witness language `attest-witness/1` (`attest/core/witness.py`), a positive
grammar whose every import, call and attribute has an origin resolved statically against the frozen repository (allowed
built-ins, a short list of standard-library functions, functions and classes the repository itself defines, methods of
built-in values); anything outside the language holds the run for a person, and `attest check` repeats the analysis from the
witness file and copies of the repository files the resolution read (evidence protocol 4). This is mechanical enforcement of
how a witness builds inputs and what it may call; whether its inputs demonstrate that the criteria cannot all hold remains the
auditor model's reasoning. Admission: `POST /api/runs` refuses unknown fields and requires an explicit, supported provider (no
default), so a malformed request is answered 422 before any row, queue entry, reservation or provider exists; the 19 Oct
verification request that started an unapproved Nemotron run (16 model calls, $0.055226 journal-accounted) would now be refused.
Tests: the recorded evidence is classified explicitly (a frozen historical corpus, a modern corpus by declared protocol, and an
inventory that fails on any unclassified run directory), replacing a glob that counted new protocol-3 bundles as historical.
Running the complete suite on a clean checkout of the review repository, rather than on the private working tree, exposed two
export defects present since that repository was created: scripts were exported without their executable bit, and the
exported `.gitignore` ignored every `reports/**/runs/` directory, so the repository held 25 of the 175 exported bundles. Both
are fixed, the export now fails when git would ignore an exported file, its derived manifests are deterministic, and a clean
checkout of the pinned commit passes all 367 tests.

Revision 8 (19 Oct 2026, version 0.8.0, `reports/attest-revision7-repairs-2026-10-19/README.md`) repairs the issues left after
revision 7. Memory: yungou runs systemd 219 on cgroup v1, which ignored the unit's `MemoryMax=` from the first deployment on; the
unit now sets `MemoryLimit=` and, before the service process exists, a memory-plus-swap limit of the same size, and the installer
reads the limit in force back from systemd and the kernel after every restart and rolls back when it differs. A drill on the host
showed the memory-cgroup OOM killer ending a process at the limit and systemd starting it again, and showed that the memory limit
alone lets the same process swap past it. Transport: every request records how far it got. A request whose connection, proxy
tunnel or TLS handshake failed before any byte of it was written cannot have reached the server, so it is sent again (bounded,
every attempt recorded, a paid reservation closed at a known $0); reads are retried; a request whose bytes were written is
uncertain and is never sent again: the run stops at the first uncertain call in any stage (the sealing stage used to send its
next attempt with the same prompt), a batch stops with a list of what to reconcile, and an accepted Sandboxes operation id is
journaled before polling starts. Of the six revision-7 transport failures, four failed during connection setup
and two after the request body stalled in transit; the gateway's ingress log and the Sandboxes operation list show that none of
them was executed. Spending: a run starts only on explicit confirmation. The console's Run button opens a confirmation that states
the inference cap and names Sandboxes and Tavily as separately metered services, the page refuses to start a run from an
automated browser on the public host, and `POST /api/runs` answers 428 before anything exists unless it carries
`X-Attest-Confirm: start-run`. Inference money is labelled as inference throughout, and a development run is shown as team
allowance, never as $0. Mobile: nothing on the page is wider than a 320 px viewport (long identifiers and error texts wrap, tabs
wrap, grid columns shrink), checked in Chrome with mobile emulation on every tab with every panel expanded; the right-edge clipping
in the revision-7 390 px screenshot came from the screenshot method, not the page. Export: the public tree no longer contains the
development gateway's host in any spelling (the exporter's own redaction patterns had carried it), and
`scripts/check_export_provenance.py` checks every exported bundle against its source and its batch's registration.
Revision 8 was deployed at https://attest.axiqo.xyz on 19 Oct 20:42 UTC (`reports/attest-deployment-2026-10-19e/README.md`): on
the running service systemd and the kernel report 200M for memory and for memory plus swap, and a drill of the deployed release in
a temporary unit showed the OOM kill at the limit, the restart, and the run in flight settled as interrupted with its committed
cost and its unread Sandboxes operation on record.
The browser checks of the deployed console then found five console defects outside the overflow measure (at 1024 px the Guide
covered two of the case file's tabs, the decision card's text was squeezed to about 80 px and the overview's evidence table into a
sideways scroll; two error states were wrong); version 0.8.1 repairs them in the console's static files, with the pipeline
unchanged, and was deployed at 22:18 UTC (`reports/attest-deployment-2026-10-19f/README.md`). Versions 0.8.2 and 0.8.3 correct
the home page's replay, which claimed "offline check 24 of 24 OK" for a 17 Oct bundle that the current checker passes as a
historical bundle with two warnings; 0.8.3, deployed at 23:55 UTC (`reports/attest-deployment-2026-10-19h/README.md`), is the
version the console runs.

Revision 9 (20 Oct 2026, version 0.9.0, `reports/attest-revision9-repairs-2026-10-20/README.md`) makes the stop rule hold for every
operation, not only for model calls. A run now stops where an operation's outcome becomes uncertain, whatever the stage: a sandbox spawn
whose answer was lost or came back HTTP 5xx, an accepted operation whose outcome could not be read, a model call answered 5xx after it was
sent, a Tavily search whose answer was lost, or a journal that could not take a record. Nothing is sent afterwards (every client asks the
run's ledger to admit each request, and a stopped run refuses), the bundle ends ERROR with a `reconciliation` record that lists every
operation to settle and the read-only check that settles it (evidence protocol 5, recomputed by `attest check`), and nothing suggests
running the stage again. Revision 8 had stopped only uncertain model calls: an uncertain sandbox operation in the breaker became a plain
model error and the run went on to the drift audit, and after an uncertain witness or mutant spawn a run could still end VERIFIED, as two
recorded development runs of 17 Oct did. A sandbox operation is journaled durably as PENDING before its spawn is sent and its accepted id
before the first poll; when the journal cannot take either, nothing further is dispatched. HTTP answers are classified once: 4xx is a
refusal, 5xx is uncertain, reads are retried with bounded backoff, and a cut error body keeps its status. The console holds new runs while a
stopped run awaits reconciliation, the evaluation harness halts every cell in flight and never judges a stopped one, and the offline
suite runs without credentials, private configuration or network (it fails if any test reaches outside the loopback interface). The
review repository stays the private record; `scripts/build_publication_history.py` replays its history into a separate, publishable
repository with the private gateway host removed from every historical file, keeping every recorded digest (`FREEZE.md`).
Revision 9 was deployed at https://attest.axiqo.xyz on 20 Oct 08:22 UTC (`reports/attest-deployment-2026-10-20/README.md`); the console
runs 0.9.0, with the memory limit in force as before (200M for memory and for memory plus swap) and no reconciliation hold open.

Revision 10 (20 Oct 2026, version 0.10.0, `reports/attest-revision10-repairs-2026-10-20/README.md`) closes four ways around that stop
rule. After a restart the console reads a run's proof bundle and its journal before it settles the row, so a run that stopped for
reconciliation keeps its hold even when the process died right after writing the bundle (0.9.0 settled such a run as finished). The
held state and the hold are written in one transaction; when that fails the console fails closed (it admits nothing and starts nothing
until the record is written or the restart recovers it), start-up repairs a missing hold, and a hold an operator cleared is never
reopened. A resumed evaluation batch reads every row, bundle and run or judge journal it has and starts nothing while any item is
unresolved; `--resume` alone approves nothing, and an acknowledgement must name the item ids (`--reconciled NOTE --items ID,...`) and is
kept in the report directory for later restarts. Every upstream answer is checked before use (UTF-8, standard JSON, the documented
shape, well-formed identifiers): an unreadable spawn answer leaves the spawn UNCERTAIN, an unreadable poll leaves the accepted operation
ACCEPTED_UNREAD with its id, an unreadable model answer is an uncertain call, and the run halts at once with nothing sent afterwards
(0.9.0 let raw `AttributeError`, `TypeError` and `UnicodeDecodeError` escape, polled on, or sent a repair request). The two development
runs of 17 Oct that went on after an uncertain mutant spawn were reconciled read-only against the Sandboxes account and the gateway's
ingress log: both spawns did execute (late, one after its run had ended), both mutants were killed, and both verdicts stand.
Revision 10 was deployed at https://attest.axiqo.xyz on 20 Oct 16:02 UTC (`reports/attest-deployment-2026-10-20b/README.md`); the console
runs 0.10.0, with the memory limit in force as before and no reconciliation hold open, and the host's free disk went from 7.4 % to 9.2 %
by removing obsolete Attest builds and uploads.

Paid validation of revision 10 on Nemotron (21 Oct 2026, approved by the owner; `reports/attest-validation-2026-10-21-nebius-r10/README.md`,
`reports/attest-evaluation-2026-10-21-nebius-r10/README.md`): from a clean checkout of the pin, the two-run smoke test ($0.116, both NEEDS
HUMAN with complete evidence; every real Token Factory answer passed revision 10's strict decoding) and the frozen 32-cell evaluation of
0.10.0 ($1.387 of the approved $9.00). Plain agent against Attest, 16 cells each: correct patches accepted 8 against 2, broken patches
shipped 2 against 0 (both on the task that cannot be satisfied, which Attest refused twice, once as INFEASIBLE with an executed witness),
correct patches held 1 against 2, holds without a patch or unfinished 1 against 4 (three of Attest's from a test writer that could not seal
a valid suite), infrastructure errors 4 against 6. The infrastructure errors are six Sandboxes spawns answered HTTP 500 after they were
sent; each stopped the batch, read-only checks found that none had run, and each item was acknowledged by id before the batch resumed;
nothing was replayed. An Attest run cost 5.8 cents of inference on average. One batch of 32 cells on one suite, not a benchmark.

Console release 0.10.1 (deployed 21 Oct 2026, 03:56 UTC; `reports/attest-deployment-2026-10-21/README.md`): the console reports that
evaluation and serves its 32 runs and the 2 smoke-test runs; no server code changed. Read-only checks afterwards: the page and its assets
byte-identical to the release, 74 runs, 0 holds, and 515 page states at five widths in a real browser with no overflow and no request
other than GET. The console's daily cap counts the imported runs on the day they ran, so until 00:00 UTC on 22 Oct the public console
runs one job at a time. A read-only sweep one hour after the last uncertain spawn confirmed that none of the six had executed. The public
repository (https://github.com/a252937166/attest) replays the review history with the owner's identity on every commit and the session
scratch paths rewritten; `FREEZE.md` maps every pin to its published commit.

Console release 0.10.2 (deployed 21 Oct 2026, 04:57 UTC; `reports/attest-deployment-2026-10-21b/README.md`) corrects the page in three
places. It no longer names Nemotron 3.5 Lightning, which no recorded run called. The architecture names the revision each evaluation
recorded. The home counts cover every run: the page had counted only the newest 50 of 74. The same read-only checks as for 0.10.1 all
pass, and the demonstration film's console footage was recorded on this release.

Console release 0.10.3 (deployed 21 Oct 2026, 07:01 UTC; `reports/attest-deployment-2026-10-21c/README.md`) replaces the task menu
with a picker. It names each task briefly; shows its repository, issue, runner and held-out tests, and its latest Attest verdict; and
browsing a task now opens that verdict rather than an infrastructure error. The demonstration film's live run was started on this
release: owner-approved, NO CHANGE, $0.144 (`reports/attest-demo-run-2026-10-21/README.md`).

Gateway operations update (17 Oct 2026): the self-hosted Codex API's hourly request cap has been removed and the
Aliyun backend deployed and verified. Authentication, daily caps, one active request/eight waiting slots, priorities,
deadlines and ingress protection remain. See [deployment and regression evidence](reports/codex-gateway-hourly-limit-removal-2026-10-17/README.md).
The Attest application was not redeployed and the recorded evaluation was not rerun by this operation.

## For judges

Start with `TESTING.md` (offline tests in 15 seconds, `attest check` on a recorded bundle, the live console, your own
repository), `METHOD.md` (the frozen evaluation method) and `FREEZE.md` (the pinned commit, digests, models, limits and
the exact evaluation command; its published-history tables map the evaluation and release pins from the review repository to
the commits available in the public repository). Every dated report under `reports/` keeps its failed and inconclusive runs; rehearsals by
the project's own agents are labelled as rehearsals, not as user testing.

## Deployment targets

The console, API, orchestration and application data are deployed without Docker on the owner's existing `yungou` server.
The latest recorded console release is 0.10.3, deployed on 21 Oct 2026; see the
[deployment record](reports/attest-deployment-2026-10-21c/README.md). Nebius Token Factory Sandboxes executes the isolated task
branches. The host policy reserves components that require Docker for the existing Aliyun host; the deployed Attest path does
not require a cross-host Docker worker.

## Layout

```
attest/
  secrets.py              private credential loading (env, then the private vault notes; never written to artifacts)
  http.py                 TLS-verified JSON client; records how far each request got: a request that was never sent may be
                          sent again (bounded), an uncertain POST is never replayed; one classification of a failed POST
                          (not sent, rejected by a 4xx, uncertain) and of a retryable read; cut error bodies keep their status
  ledger.py               model-call and sandbox-operation ledgers and their journal; the run's stop state (halt, admit) and
                          the list of everything left to reconcile
  models/codex_gateway.py        development provider: self-hosted Codex gateway, POST /v1/run with output_schema
  models/nebius_tokenfactory.py  submission provider: NVIDIA Nemotron on Token Factory, json_schema response format, USD cap
  sandbox/tf_sandboxes.py        Token Factory Sandboxes REST adapter: checkpoint + disposable networking-off branches
  core/task.py            task.json loading and freezing (content digests, pinned install, runner, held-out tests)
  core/workspace.py       implementer workspace with a write-scope policy and unified diff
  core/prompts.py         stage prompts and strict JSON schemas (spec, seal, action)
  core/testparse.py       unittest (subtest-aware) and pytest output parsers for the repository's own suite
  core/sealed.py          sealed-suite supervisor (v7: one process group per test child, bounded cleanup) and child (nonce, digests,
                          uid 65534 children, canaries, start-up-hook check), static discovery of repository suites, the host-side
                          binding and the evidence classes (structural problems, authentic green/red/timeout/untrusted records)
  core/tamper.py          static tamper scan of the candidate's added lines (warnings, never a gate)
  core/mutate.py          AST mutants of the candidate's changed lines for the breaker pass
  core/pipeline.py        freeze -> checkpoint -> spec -> ground -> seal -> red -> implement -> verify (bound, privilege-separated) -> held-out -> break -> drift -> arbitrate -> attest
  core/verdict.py         the one gate-to-verdict rule (used by the pipeline and re-derived by `attest check`)
  core/exhibits.py        exhibits E1 to E7, decision copy per verdict and reason class, counterexamples, "what this bundle proves"
  core/provenance.py      Attest revision digest, supervisor/child/canary/runner digests, sampling parameters, limits, upstream
  core/manifest.py        manifest.json (v2): sha256, size and purpose of every artifact, complete listing required, no links (written last)
  core/check.py           `attest check`: offline recomputation of digests, bindings, mutants, corrections, ledger totals, verdict rule and
                          PROOF.md; strict for current bundles (evidence protocol 2 to 5, mandatory records derived from the
                          frozen task and the execution mode; under 5 the reconciliation record), historical mode for older ones
  core/witness.py         the constrained witness language attest-witness/1: positive grammar, static call-origin resolution
                          against the frozen repository, shared by the pipeline and `attest check`
  core/diagnostics.py     public error vocabulary with correlation references; the raw text of every failure goes to a private
                          sidecar outside the run directory, never into a bundle, an event, a call record or a download
  core/proof.py           Proof Bundle (proof_bundle.json + PROOF.md, exhibits and provenance sections)
  app/                    FastAPI console + API, single worker, SQLite store, static UI (decision header, exhibits E1 to E7,
                          counterexamples, keyed updates, recorded evidence first; development profile only after a team token)
  cli.py                  `python -m attest preflight|run|check|import` (run: --max-calls, 22 by default for the Nebius provider and
                          enforced before dispatch; --arbitration-advisory, --no-arbitration, ...)
examples/eval/            frozen evaluation suite (SUITE.json) with independent held-out tests
scripts/run_evaluation.py plain agent vs Attest harness: pre-registered attempts, held-out stripped from the system under test,
                          Codex by default, Nebius only with --approve-usd and --max-calls
scripts/usage_report.py   deduplicated usage by provider and day (keyed by bundle run_id; optional console store)
scripts/sandbox_adversarial_tests.py  real-sandbox adversarial scenarios for the supervisor (forgery, hook planting, legacy order)
scripts/check_export_provenance.py   every exported bundle: attest check, identity with its source, its batch's registration
scripts/console_layout_audit.py      the console in Chrome at 320 to 1440 px: anything wider than the viewport, every non-GET blocked
scripts/scan_publication_history.py  every object of a git repository: the private hosts in any spelling, secret-like tokens
scripts/build_publication_history.py the review history replayed into a separate publishable repository, private strings removed
examples/durationkit-task/     sample repository (unittest) and task.json
examples/semver-is-compatible/ python-semver at the parent of PR #368, pinned pytest, upstream held-out tests
tests/                    offline harness tests: adversarial verification scenarios, verification order, canaries, bound
                          suites, the real supervisor run locally, store hygiene, manifest and tampered-bundle checks
reports/                  dated evidence (preflight, probes, Proof Bundles)
runs/                     run outputs (git-ignored)
```

## Running

Credentials are loaded from the process environment first (`NEBIUS_API_KEY`, `CODEX_API_KEY`, `TAVILY_API_KEY`), then,
only on a developer machine that configures it, from a private credential note mapped in `~/.config/attest/notes.json`.
`NEBIUS_PROJECT_ID` / `NEBIUS_AI_PROJECT` hold the project ID, never the key. The development gateway's URL comes from
`ATTEST_CODEX_BASE_URL`. Nothing secret is written to `runs/` or `reports/`.

```bash
python3 -m unittest discover -s tests -t . -v                       # offline harness tests
python3 -m attest preflight --provider codex --adapter-smoke          # queue, catalog, sandbox limits, one disposable op
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider codex
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider nebius --usd-cap 0.5
python3 -m attest run --task examples/semver-is-compatible/task.json --out runs --provider codex --max-mutants 12
python3 scripts/run_evaluation.py --provider codex --attempts 1 --label dryrun        # exploratory evaluation (allowance)
python3 scripts/run_evaluation.py --provider nebius --attempts 2 --approve-usd 9 --max-calls 22 --label final  # after approval only
python3 scripts/usage_report.py --store data/attest.db                               # unique runs and committed USD
python3 -m attest check runs/<run-id>            # offline: manifest digests, bindings, ledger totals, verdict rule, PROOF.md
python3 -m attest check downloaded-bundle.zip --json
python3 -m attest import --github https://github.com/<owner>/<repo> --commit <40-char sha> --id my-task --out tasks \
    --runner pytest --write-glob 'src/<pkg>/**' --python-path src --pin pytest==8.3.3 --pin pluggy==1.5.0 \
    --pin iniconfig==2.0.0 --pin packaging==24.1 --statement-file statement.txt --criteria-file criteria.txt   # bounded external import (M4)
python3 scripts/replay_holds.py --run <run-dir> --task <task.json> --module original=<tests.py> --out replay.json [--sandbox]  # re-run breaker tests on candidate and base
python3 scripts/run_evaluation.py --resume reports/<batch-dir>     # continue an interrupted batch from its own snapshot and registered configuration (cells never executed only; conflicting flags are refused; unresolved items are listed and nothing starts)
python3 scripts/run_evaluation.py --resume reports/<batch-dir> --reconciled "what the read-only checks found" --items u-...,u-...   # acknowledge those items (kept for later restarts)
python3 scripts/export_public.py --out dist/public                 # allowlisted, redacted copy for the public repository, with a secret scan
python3 scripts/build_publication_history.py --review dist/public --out dist/publication --map map.json --verify verify.json   # publishable history
python3 scripts/scan_publication_history.py --repo dist/publication   # every object, every spelling; exit 1 on any hit
python3 -m attest reconcile runs/<run-id>                          # what a stopped or interrupted run left to reconcile (offline)
python3 -m attest holds --db data/attest.db [--clear HOLD_ID --note TEXT]   # the console's reconciliation holds
python3 -m attest run --task examples/eval/rle-encode/task.json --out runs --provider codex --arbitration-advisory   # record corrections, never re-run a gate on them
```

External repositories (M4, `attest/core/external.py`, `PILOT.md`): a public GitHub repository at a pinned commit, or a local
directory, becomes a task under documented bounds that are enforced before any sandbox operation and named in every refusal:
at most 2,000 files and 25 MB, 200 KB per file by default (hard cap 1 MB), Python with unittest or pytest, pinned
dependencies installed once at checkpoint time, an explicit write scope, protected tests and packaging files, test
timeout at most 300 s, at most 12 implementer turns. The sandbox job is gzip-compressed and a checkpoint larger than one
request (about 400 KB compressed) is built as a chain of retained images.

Codex pacing (`attest/models/pacing.py`): every request of the development profile takes a slot from one process-wide
governor per key (all roles, all workers; shared with other processes on the machine through a small state file). The
governor adopts the gateway's declared policy from `GET /v1/status` (hourly counting is not enforced since 17 Oct 2026),
keeps at most two requests in flight, and treats an HTTP 429 as a definite rejection: the attempt is recorded as a failed
call, the key is blocked for the declared or inferred interval, and the same request is retried after a bounded wait.
When the bound is exceeded the call fails visibly (`ERROR` verdict, infrastructure error in the harness). Nothing ever
falls back to paid Nebius inference. Without a readable policy the governor assumes the limit observed on 16 and 17 Oct
(60 requests per rolling hour, 90% of it planned).

Evaluation provenance (`scripts/run_evaluation.py`): a batch copies the package, the harness and the task files into
`<report>/snapshot/` and re-executes itself from that copy in a fresh process; the schedule records the application
revision, the harness digest, the examples digest and the guest-program digests actually executed, every row records its
bundle's revision, and a task whose cells did not all run the registered revision (or whose snapshot changed) is marked an
invalid comparison. The frozen M5 method is `METHOD.md`; the suite is `examples/eval/SUITE-M5.json`.

Options: `--max-turns` (implementer actions), `--max-mutants` and `--mutant-workers` (breaker pass, parallel branches),
`--mutation-threshold` (warning below this score), `--usd-cap` (hard per-run cap for the Nebius profile, enforced by a
conservative pre-request reservation).

Model roles can be overridden per provider: `ATTEST_CODEX_ROLES="spec=gpt-6-astra:low,implement=gpt-6-sol:medium"`,
`ATTEST_NEBIUS_ROLES="spec=nvidia/Nemotron-3-Ultra-550b-a55b,implement=nvidia/nemotron-3-super-120b-a12b"`.

## Execution model

One retained checkpoint per task (repository unpacked, baseline suite run), then every later execution is a disposable
branch of that image with networking disabled: the sealed-test red check, each implementer `run_tests` / `run_python`
action, and the final verification. Inputs travel as a base64 JSON job on stdin to a small stdlib guest runner that
writes files, runs steps and returns a JSON report. Repositories with dependencies install a pinned set at checkpoint
time (the only operation with networking on). Sealed tests are injected only into red-check, verification and mutant
branches; the implementer never receives them. A root supervisor that never imports candidate code runs one child
process per test as uid 65534, hands each child the per-run nonce only after the test module is imported, hashes every
test module before and after, makes every import-path root root-owned, checks for interpreter start-up hooks, and runs
two verifier canaries (one must pass, one must fail) after the suite. The verdict is bound to the test IDs proven red,
the digests, the nonce and the canaries, so edited tests, forged console output, hidden tests, early exits and blanket
result forgery are recorded as failures (see `tests/test_verification.py`, `tests/test_m1.py`).

Contract audit (revision 4): after the specification, the `audit` role looks for requirements that no implementation confined
to the write scope can satisfy and must back each claim with a witness program; Attest runs every witness in a disposable
branch of the unmodified checkpoint and records the program, its digest, exit code, output and operation id. A conflict is
demonstrated only by exit code 3 and a `CONTRADICTION` line. Since revision 6 the auditor sees the task's own criteria
(`TC` ids) apart from the specification's derived ones (`AC` ids) and every conflict records its provenance (`task`,
`derived`, `mixed`); INFEASIBLE needs a conflict whose requirements are all the task's own and, since revision 7, whose
witness conforms to the constrained witness language `attest-witness/1`: imports, assignments, control flow and
comprehensions only, no function, class or lambda definitions; imports limited to `sys`, `itertools`, `math`, `string`, `json`
and the repository's own modules, every repository name resolving through the repository's source to a function or class it
defines; calls only to allowed built-ins, allowed standard-library functions, resolved repository code and methods of
built-in values, never through a value held in a variable; no attribute starting with an underscore. The analysis is
recorded per conflict with the resolved origins, and the repository files it read are copied into the bundle. A demonstrated
conflict that fails either condition holds the run for a person instead (`contract_conflict_held`); a witness that
disproves one implementation never establishes that the task is impossible.
The sealer's coverage map (which test checks which criterion) is checked for completeness and its gaps are recorded.

Arbitration (revisions 4 and 5): a corrected generated-test module counts only when it keeps every test method, changes only
the bodies of the failing ones (new imports may be added, nothing existing may be rebound), is classified for exactly the
failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results
(every corrected sealed test fails on the unmodified base with an exit-1 FAIL or ERROR report bound to the nonce; a corrected
adversarial module fails on the base or is caught by a validly killed mutant). A lost, forged or crashed result is never
"red", and an original failure whose own evidence is untrusted is never arbitrated. The affected gate is then re-run and the
verdict re-derived; `verdict.before_corrections` keeps the first derivation, and the raw results of the base and mutant re-runs
are kept for `attest check`. A sealed test that failed by assertion or by any exception, whatever its origin, is never
overridden: only a test the supervisor killed at its timeout may be corrected. The third breaker attempt, after two modules
that do not compile, escalates to the arbiter's model.

Mutation evidence (revision 5): every mutant run is bound like a verification run; a mutant counts as killed only when at
least one sealed test failed with an authentic child result under a structurally sound run, as survived only when every test
passed authentically, and otherwise as unknown (excluded from the score). The policy is recorded in the bundle and `attest
check` reclassifies every mutant from its raw result.

Evidence protocol (revisions 5 to 9): every bundle declares `evidence_protocol.version` (2 for revision 5, 3 for revision 6,
4 for revisions 7 and 8, 5 since revision 9, whose bundles carry the reconciliation record that `attest check` recomputes from the
ledger: a bundle that lists an operation of unknown outcome, or whose run halted, must be ERROR). `attest check` requires the complete evidence for a current bundle's verdict and reports `EVIDENCE COMPLETE` only when
the digests, the complete manifest and that evidence all check; a bundle without the field is historical (internal
consistency only, never fully verified), and the former explicit apply mode (`cleared_by_arbitration`) is honoured only for
historical bundles started before 19 Oct 2026. Under version 3 the mandatory records are derived from the frozen task and
the execution mode rather than from what survived in the bundle: the existing-suite stage record, its raw supervisor result
and its binding in bound mode, held-out evidence exactly when the task declares held-out tests, a stage record behind every
recorded gate, and a grounded conflict with a constrained witness behind an INFEASIBLE verdict. Under version 4 the
checker repeats the witness-language analysis from the witness file and the repository copies kept in the bundle (a copy
counts only when its digest equals the frozen task's) and never trusts a recorded `grounded` or `witness_constrained` flag;
a protocol-3 INFEASIBLE bundle keeps no copies, so its grounding cannot be re-established when its witness imports
repository code (no such bundle has been recorded). Complete evidence
establishes that the recorded verdict follows from the recorded evidence; it does not establish that the verdict is correct
(the held-out judge of the evaluation harness measures that).

Ledger journal (revision 4): `ledger.jsonl` in every run directory records a reservation before each Nebius request and the
call record as soon as it is known; `attest.ledger.read_journal` sums known costs and open reservations, which the console's
restart reconciliation and the harness's resume use for interrupted runs. Transport-uncertain calls stay `unsettled` at
their reservation; nothing uncertain is ever replayed. Since revision 6 every append is written, flushed, fsynced and read back;
a line that an earlier failed append cut short is terminated by a `journal_repair` record before anything else is appended
(the cut record is lost, its reservation stays open at its bound), a reservation that cannot be journaled and verified halts
paid dispatch, and a failed settlement marks the ledger `journal_degraded` until a later reservation reads back intact. Since
revision 9 sandbox operations are journaled the same way, as PENDING before the spawn and with their accepted id before the first
poll, development-gateway calls take a zero-USD pending record, and any of these failures halts the run.

Order rule: the sealed supervisor is the only step of the verification branch; nothing that imports candidate code runs
before it in the same sandbox operation. The repository's own suite and the held-out suite run afterwards in their own
disposable branches. For unittest repositories whose tests are statically discoverable they run through the same
supervisor and are bound to the frozen digests (`evidence_class: bound`); otherwise they are parsed from console output
and labelled `stdout`. Every gate in the Proof Bundle carries its evidence class (`bound`, `stdout`, `model`).

Proof Bundle integrity (M2): every run records its provenance (Attest revision digest, supervisor and runner digests,
sampling parameters, limits, upstream commit), the raw supervisor results (`verify_raw.json`) and, written last, a
manifest with the sha256 of every artifact. `python -m attest check` recomputes the digests, the bindings, the ledger
totals and the gate-to-verdict rule offline and re-renders PROOF.md; any mismatch exits 1. The manifest is an integrity and
internal-consistency check, not a digital signature and not independent proof that the sandbox operations happened (that
evidence is the operation ids and the nonce-bound per-test records). PROOF.md opens with the
decision, the key exhibit and "What this bundle proves, and what it does not", generated from the gates and citing the
exhibits E1 to E7 (sealed tests, mutation check, tests written after the patch, held-out tests, drift audit, arbitration,
failure record).

## Profiles

| Profile | Inference | Execution | Label |
| --- | --- | --- | --- |
| development | Codex gateway (`gpt-6-astra` spec, `gpt-6-sol` seal and implement) | Token Factory Sandboxes | `provider=codex_gateway` |
| submission | NVIDIA Nemotron on Nebius Token Factory (Ultra spec, Super seal and implement) | Token Factory Sandboxes | `provider=nebius_tokenfactory` |

Development results and submission results are never pooled.

## Console

```bash
python3 -m venv .venv && .venv/bin/pip install "fastapi==0.115.5" "uvicorn[standard]==0.32.1" jsonschema certifi
ATTEST_DATA_DIR=./data ATTEST_IMPORT_DIRS=./runs ATTEST_ADMIN_TOKEN=change-me \
  .venv/bin/python -m uvicorn attest.app.server:app --host 127.0.0.1 --port 4070
```

Open http://127.0.0.1:4070. The home page says what problem Attest solves, how a run earns its verdict, who provides the
core capabilities (NVIDIA Nemotron on Nebius Token Factory, Token Factory Sandboxes, Attest's own supervisor) and how
to use the console, lists the recorded evidence, and holds the one entry point: pick a task, browse its recorded Proof
Bundle (no inference) or "Run live on Nemotron", an explicit action that shows the cost and duration range of recorded
runs of the same task and the remaining daily budget. Judges run the Nemotron profile (rate-limited, budget-capped);
the development profile appears only after the team token is validated by the server, and the public page source
names no gateway. A run reads as a case file: the verdict seal, one decision sentence, the key exhibit, then tabs for
the request, the patch, the exhibits E1 to E7 with counterexamples, the activity and the artifacts with their digests;
a guide that follows the state of the run explains what each part means and spotlights it. `scripts/console_replay.py`
replays a recorded run as a labelled synthetic fixture for development. See `attest-console.md` for the API and the
verified behaviour, and `deploy/yungou/` for the production deployment without Docker (the 18 Oct 2026 console is live;
`reports/attest-deployment-2026-10-18/README.md`).
