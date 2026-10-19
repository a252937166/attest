# Repairs of the revision-5 follow-up review (revision 6, version 0.6.0, 19 October 2026)

The independent follow-up review of revision 5 (`reports/attest-revision5-review-2026-10-19/README.md`) left seven findings
open: two P1 (R5-01 accounting after a partial journal write, R5-03 an unsupported INFEASIBLE verdict) and five P2. This folder
records their repair: the mechanism, the acceptance tests (every counterexample next to a positive control), the re-run of the
review's own reproductions from documented copies, the complete offline suite, strict bundle checks and a small
development-gateway batch. The review folder, the earlier repair reports and every recorded run are unchanged; corrections to
earlier narratives are appended and dated (`reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/CORRECTIONS.md`, the
batch-2 row of `reports/attest-audit-repairs-2026-10-19/README.md`, one bracketed note in `FREEZE.md`).

No paid Nebius inference call was made. The development-gateway batch ran on the team's gateway with Token Factory Sandboxes
for execution, as every earlier development batch did; the proposed Nemotron work remains unapproved (`FREEZE.md`, revision-6
section).

## Finding by finding

| Finding | Repair | Acceptance (negative case and positive control) | Evidence | Remaining limitation |
| --- | --- | --- | --- | --- |
| R5-01 (P1) partial settlement corrupts the next reservation's framing | every journal append is written, flushed, fsynced and read back; a cut tail is terminated by a `journal_repair` record before anything is appended; a reservation that cannot be journaled and verified raises `LedgerError` and the provider halts paid dispatch; a failed settlement marks the ledger `journal_degraded` until a later reservation reads back intact; `read_journal` is binary-safe (`attest/ledger.py`, `attest/models/nebius_tokenfactory.py`) | `tests/test_audit_accounting.py::SettlementTailRecovery`: the review's exact sequence (partial write, next reservation, restart) recovers both reservations; the same through the real provider with a faked transport dispatches only a verified reservation; a cut inside a multi-byte character; a failing repair halts before dispatch; positive control: normal appends show no repair and read back byte-identical | `accounting/README.md`, `accounting/tests-output.txt`, the review's reproduction re-run from a byte-identical copy: `reproduced: false`, recovered $0.07 against $0.06 in memory (the review saw $0.02) | read-back verifies the OS's view of the bytes; a cut record is lost, not reconstructed (its reservation stays open at its bound, conservative) |
| R5-02 (P2) jointly omitted existing-suite evidence still passed | the checker derives the mandatory records from the protocol, the verdict, the frozen task and the execution mode; every recorded gate needs its stage record; held-out evidence exactly when the task declares it; evidence protocol 3 (`attest/core/check.py`, `attest/core/verdict.py`) | `tests/test_audit_core.py::R502MandatoryStagesDerivedFromTheTask`: six joint-omission shapes for the existing suite, three for the held-out suite, held-out evidence on a task without held-out tests, a gate without its stage record, a historical copy; positive controls: a bound run and a held-out run complete under protocol 3 | `core/README.md`, `core/review-repro/` (the review's reproduction re-run: the stripped copy now fails with `required_evidence` and `gates_match_stage_records`, the positive control passes), `bundle-checks-recorded-revision5-batches.txt` (the seven recorded revision-5 bundles still complete under the repaired checker) | completeness is about the records a verdict needs, not about their truth |
| R5-03 (P1) the kvparse witness did not prove task impossibility; the repair report misattributed the "every str input" quantifier | the auditor sees the task's own criteria (`TC` ids) apart from the derived ones (`AC` ids); INFEASIBLE needs a conflict whose requirements are all `TC` ids and whose witness is constrained (no definitions, no dynamic types, no `exec`/`eval`; literal inputs of the declared domain); a demonstrated conflict that is derived, mixed or unconstrained holds the run (`NEEDS HUMAN`, reason class `contract_conflict_held`); the checker re-derives grounding from the recorded witness file (`attest/core/prompts.py`, `attest/core/pipeline.py`, `attest/core/check.py`, `attest/core/exhibits.py`) | `tests/test_audit_core.py::R503GroundedInfeasibility`, `tests/test_verification.py`: derived, mixed and unconstrained demonstrations each hold with a complete bundle and a forged INFEASIBLE fails the check; the recorded kvparse witness classifies as unconstrained and the recorded rle-encode witness as constrained; positive control: a grounded conflict ends INFEASIBLE and checks complete, and forging derived ids onto it is caught | `core/README.md`; the corrected narrative in `reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/CORRECTIONS.md` (the quantifier is the task's own sentence; the witness disproved one implementation); the development batch below | grounding is by reference and execution: the semantic link between the witness's inputs and the named criteria stays the auditor's claim, so INFEASIBLE still reads "demonstrated by an executed witness"; whether the models name `TC` ids reliably is measured by batches |
| R5-04 (P2) diagnostics published through bundles, events and downloads | `attest/core/diagnostics.py`: a fixed public vocabulary with correlation references; every failure site of the pipeline, the drift and audit records, the schema-repair suffix, and the providers' call records (through `Ledger.public_error`) carry the public text; the raw text goes to a private sidecar outside the run directory, excluded from exports; the CLI points the operator at it | `tests/test_audit_core.py::R504DiagnosticsStayPrivate`, `::R504CallRecordsStayPublic`: a provider error carrying a private marker and a host path at the first call and in the drift stage leaves no marker in any run file, event, call record, journal line, console route or zip, while the sidecar carries it under the same reference; positive control: the bundle checks and the public reason names the HTTP status | `core/README.md`; `export-scan.txt` (the export's scan over the repaired tree) | raw supervisor results keep the sandbox operation's own status text (faithful execution records); historical bundles keep their recorded reasons, redacted on export with `REDACTION.json` |
| R5-05 (P2) the CLI smoke did not enforce the promised 22-call cap | `python -m attest run --max-calls` (22 by default for the Nebius provider), `ATTEST_PER_RUN_MAX_CALLS` on the console (22 by default), the provider refuses call 23 before dispatch and records the cap and its policy in the bundle (`attest/cli.py`, `attest/app/worker.py`, `attest/models/nebius_tokenfactory.py`) | `tests/test_audit_accounting.py::CallCap`: the provider serves exactly 22 and refuses the 23rd before any request with a fake transport; the CLI defaults to 22 for Nebius and none for the gateway; the CLI passes the cap to the provider it builds; the console worker builds the paid provider with the environment cap | `accounting/README.md`; `FREEZE.md` revision-6 section spells out the smoke command with `--max-calls 22` | no Nemotron bundle has recorded the cap yet (offline only) |
| R5-06 (P2) role and effort overrides escaped comparison validation | the harness registers the effective provider profile (resolved model id and effort per role, sampling, limits, thinking flags) with the schedule, refuses a resume under an environment override before any cell runs, does not run a cell whose profile differs, and invalidates a comparison whose rows ran another implementation model (`scripts/run_evaluation.py`, `scripts/render_evaluation.py`) | `tests/test_audit_accounting.py::ProviderProfileFreeze`: a role override and an effort override on resume are refused; a row with another implementation model invalidates the comparison; a cell whose provider differs is not run; positive control: a resume under the registered profile stays valid | `accounting/README.md`; the schedule of the development batch below records `provider_profile` | pre-revision schedules carry no profile (resuming them compares nothing and says so); earlier evaluation reports keep their recorded labels |
| R5-07 (P2) the download URL carried the master team token | the team token is read from the `X-Attest-Token` header only; a finished team run's downloads use short-lived (600 s), run-scoped, read-only tickets minted by `POST /api/runs/{id}/download-ticket`, honoured only by that run's artifact and zip routes; team downloads are `Cache-Control: no-store`; the vhost's access log drops the query string (`attest/app/server.py`, `attest/app/static/app.js`, `deploy/yungou/attest.axiqo.xyz.conf`) | `tests/test_audit_console.py::DownloadTickets`, `TeamVisibility`, `tests/test_console.py`, `tests/console_client_test.mjs`: a query token is ignored on every route; a ticket opens only its own run's downloads, never a listing, a detail or a POST; forged, malformed, other-process and expired tickets are refused; positive control: public runs download without any credential and the team token in the header still reveals the team run on every route | `console/README.md`, `console/unittest-console.txt`, `console/node-console-client.txt`, `console/review-repro/` (the review's reproduction now fails at the step that expected a query token to carry team privileges) | a ticket in a URL may sit in a browser history or referrer for up to ten minutes and grants that run's downloads; per-process secret (a restart invalidates tickets, the page mints new ones); no revocation before expiry |

The harness's confusion labels were also extended: a hold before any patch (`NEEDS HUMAN` with no changed path and an
implementer that never ran) is labelled by the ground truth (`true_reject` on an unsatisfiable task, `false_refusal` otherwise);
a hold with a patch keeps the held-out judge's label. Earlier evaluation reports keep their recorded labels.

## Verified baseline after the repairs

- Complete offline suite: **352 tests, no failure** (`offline-suite.log`; 314 after revision 5, 38 added).
- Strict bundle checks: the seven recorded revision-5 batch bundles still read `OK, EVIDENCE COMPLETE` under the repaired
  checker (`bundle-checks-recorded-revision5-batches.txt`); the new batch's bundles are checked in `bundle-checks.txt`.
- Public export: see `export-scan.txt` (allowlist, fail-closed secret scan, bundle verification of every exported run).

## Development-gateway batch (semantic outcomes, reported apart from bundle integrity)

Three cells, Attest only, one attempt each, provider the development gateway (`gpt-6-astra` low for spec, audit and arbitrate
at medium, `gpt-6-sol` medium for seal, implement and break, `gpt-6-luna` low for the summary; profile registered in
`evaluation-codex/schedule.json` as `provider_profile`), package `b11ec0658845…` (36 sources), harness `5af2b4989b2b…`, examples
`6db7a2e937d6…`; snapshot intact at the end; $0 committed (no paid call). Log: `evaluation-codex.log`; cells and labels:
`evaluation-codex/evaluation.json`, `evaluation-codex/RESULTS.md`.

**Semantic outcomes** (what the verdicts mean, judged by the independent held-out suite of each task):

| Task | Verdict | Held-out judge | Label | What happened |
| --- | --- | --- | --- | --- |
| `durationkit-units-001` (positive control) | VERIFIED | 13 of 13 held-out methods pass (bound) | `true_accept` | contract audit consistent (9 task criteria, 17 derived); sealed binding, existing suite 6/6, mutation 0.833 on 12 mutants (10 killed, 2 survived, 0 unknown), adversarial 11/11, drift aligned; 11 model calls, 679.6 s |
| `kvparse-refactor-001` (the recorded false refusal of revision 5) | VERIFIED | held-out suite passes (bound) | `true_accept` | contract audit consistent (8 task criteria, 18 derived): no conflict was claimed this time, the auditor accepted the `str` input domain; existing suite 4/4, mutation 1.0 on 12 mutants, adversarial 10/10, drift aligned; 11 model calls, 527.9 s. The task revision 5 refused as impossible was implemented and verified |
| `rle-encode` (the unsatisfiable task) | NEEDS HUMAN | no patch to judge | `true_reject` (a hold before any patch on a task marked unsatisfiable) | the auditor demonstrated a conflict with a constrained witness (exit code 3, marker line: `decode('a111')` returns 111 copies of `a`, not `a1`) but named mixed criteria `TC5, AC8, AC12`; AC8 restates the encoding format that the task's own TC1, TC3 and TC4 already fix, so the conflict could have been grounded in task criteria alone and was not; under the provenance rule the run is held (`contract_conflict_held`), no sealing, no implementation, 159.1 s |

Reading: the two satisfiable tasks were implemented and accepted by their held-out judges, including the task revision 5 had
wrongly refused. The unsatisfiable task was not shipped and not refused as impossible either: the deterministic rule held it
because the model mixed a derived criterion into a conflict it could have stated on the task's own criteria. That is the
designed trade of revision 6, a hold instead of an unsupported INFEASIBLE, and it shows the stated limitation (whether a model
names `TC` ids when it could is measured, not guaranteed). Three cells on one gateway are a reliability check of the repaired
mechanics, not an evaluation; the M5 results stand, and the Nemotron measurement remains the unapproved proposal.

**Bundle integrity** (`bundle-checks.txt`, reported apart from the outcomes above): all three bundles read `OK, EVIDENCE
COMPLETE` for their verdict under protocol 3 with the manifest verified, 0 errors, 0 warnings. Complete evidence establishes
that each recorded verdict follows from its recorded evidence; it does not establish that a verdict is correct. The held-out
judge above does that for the two VERIFIED cells; for the held cell there is nothing to judge.

## Frozen and deployed

REV6-DEPLOY-SECTION

## Remaining limitations (summary)

- Complete evidence establishes that the recorded verdict follows from the recorded evidence; it does not establish that the
  verdict is correct. The held-out judge of the evaluation harness measures correctness, and only on the tasks it has.
- A grounded INFEASIBLE verdict still rests on the auditor's claim that its literal inputs exercise the named criteria; the
  checker verifies ids, constraint, execution, marker and exit code, not meaning. Everything less is held for a person.
- The private diagnostics sidecar is best effort (an unwritable sidecar never fails a run; the public text is produced regardless).
- The journal's read-back verifies the operating system's view of the bytes; a record cut by a failed append is lost and its
  reservation stays open at its bound.
- The revision has been validated offline and on the development gateway only; its behaviour on Nemotron (grounded audit,
  recorded call cap, registered profile) is the unapproved paid proposal in `FREEZE.md`.
