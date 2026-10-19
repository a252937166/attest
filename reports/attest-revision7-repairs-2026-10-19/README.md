# Repairs after revision 7 (revision 8, version 0.8.0, 19 October 2026)

This pass fixes the issues left after revision 7 before any video work: the memory limit on yungou, horizontal overflow on phones,
the development batches' transport failures, accidental spending, and the separation of the services' costs; it then verifies
the repairs from a clean checkout, deploys them with the transactional installer and checks the deployed console in a real browser.
Two problems found along the way are repaired too: the public export carried the development gateway's host in escaped
spellings, and yungou's network went down for about 17 minutes during the first development batch. Every earlier record is
unchanged; corrections are appended and dated.

No paid Nebius inference, smoke test, evaluation or demo run was started; the $10 proposal in `FREEZE.md` remains unapproved.

## What changed, and the evidence

| Issue | Repair | Evidence | Remaining limitation |
| --- | --- | --- | --- |
| Memory limit not in force (systemd 219 ignores `MemoryMax=`) | `MemoryLimit=` plus a memory-plus-swap limit of the same size written before the service starts; the installer reads the limit in force back after every restart and rolls back when it differs | `memory/` (the drill on the host: OOM kill at the limit and restart; the contrast run that swapped past a memory-only limit), `tests/test_audit_ops.py` scenarios 1, 9, 10; the readback after the deployment | a 200M limit is about four times the measured footprint; an OOM kill ends a run in flight (settled as interrupted, never replayed) |
| Horizontal overflow on phones | grid tracks that may shrink, wrapping of long identifiers and error texts, stacked decision buttons, wrapping tabs, a smaller logo row, the start form's price pill on its own line | `console/` (audits before and after at 320 to 1440 px with mobile emulation, every tab with every panel open, error states simulated in the browser) | tables and code blocks scroll inside their own boxes, by design |
| Gateway and Sandboxes transport failures | phase-aware transport: never-sent requests are sent again (bounded, recorded), reads are retried, uncertain requests never; accepted operation ids journaled before polling; a reconciliation list that stops a batch | `transport/` (each of the six revision-7 failures matched to the gateway's ingress log, the backend's audit records and the Sandboxes operation list; the revision-8 batches), `tests/test_transport.py` | a request whose body stalls after its first bytes left this machine is uncertain at the client; only the gateway's logs can settle it |
| Accidental paid runs | 428 without `X-Attest-Confirm: start-run`; the console's two-step confirmation; automated browsers refused on the public host; browser checks that block every non-GET request | `spending/`, `tests/test_audit_console.py` (`ExplicitStart`), `tests/console_client_test.mjs` | a confirmed request from a person is a paid run, by design |
| Costs presented as one figure | inference labelled as inference everywhere; development runs shown as team allowance; Sandboxes and Tavily stated separately; appended notes on earlier "$0" statements | `spending/`, the harness's `services` record | Sandboxes billing is not reconciled against an invoice |
| Private host in the public export | patterns from the exporter's private configuration, all spellings matched, rule labels in `REDACTION.json` | `export/`, `tests/test_external.py` | the review repository's earlier commits still contain the host: its history must not be published as it is |

## Development-gateway batches (semantic outcomes, reported apart from bundle integrity)

Three batches, Attest only, one attempt per cell, all on package `68e9de49df5b…` (37 sources), harness `9f9e4bc2ebfe…`, examples
`6db7a2e937d6…`, the development gateway for inference (the revision-7 profile: spec and audit `gpt-6-astra:low`, arbitrate
`gpt-6-astra:medium`, seal, implement and break `gpt-6-sol:medium`, summary `gpt-6-luna:low`) and Token Factory Sandboxes for
execution. Every scheduled cell is reported; nothing was merged or selected; no uncertain request was sent again.

| Batch | Task | Verdict | Label | What happened |
| --- | --- | --- | --- | --- |
| 1 (`evaluation-codex/`, 19:00 UTC, 2 workers) | `rle-encode` | ERROR | `infra_error` | the gateway's host lost its network during the specification call; the backend had executed the request (200), the answer never arrived (read timeout after 512 s); uncertain, not retried |
| 1 | `balanced-brackets` | ERROR | `infra_error` | the same outage: executed by the backend, answer lost (`RemoteDisconnected` after 202 s); its judge spawn timed out and created no operation |
| 1 | `durationkit-units-001`, `kvparse-refactor-001` | not run | `not_run` | the batch stopped for reconciliation (3 items) |
| 2 (`evaluation-codex-2/`, 19:25 UTC, 2 workers) | `rle-encode` (unsatisfiable) | NEEDS HUMAN | `true_reject` | the auditor demonstrated the conflict with a witness inside `attest-witness/1`, but named TC5 together with two derived criteria (AC8, AC13), so the run was held for a person rather than ended INFEASIBLE (a model's restatement cannot establish infeasibility); revision 7's batch had named TC5 alone and ended INFEASIBLE |
| 2 | `balanced-brackets` | ERROR | `infra_error` | the contract-audit request's body stalled in transit (nginx 408 after 62 s, never forwarded, absent from the backend's records); uncertain at the client, not retried |
| 2 | `durationkit-units-001` | VERIFIED | `true_accept` | held-out 13 of 13; mutation score 0.917; one generated adversarial test failed, arbitration classified it a test defect, the corrected test passes on the candidate and fails on the unmodified base, and the gate was re-run; warnings: the static tamper scan flagged two lines of the patch for review, the drift audit one unsupported claim; the task's first verdict since revision 6 |
| 2 | `kvparse-refactor-001` | not run | `not_run` | stop rule (the balanced-brackets cell) |
| 3 (`evaluation-codex-3/`, 19:37 UTC, 1 worker) | `kvparse-refactor-001` | NEEDS HUMAN | `false_reject` | the contract audit was consistent (no false refusal, unlike revision 5); a sealed test failed by assertion, the arbiter classified it a test defect and its correction was validated by execution, but a sealed test that fails by assertion is never overridden (the rule since revision 4), so the hold stands; the held-out judge accepts the patch |

Reading: nine cells scheduled; three judged outcomes are correct (`durationkit-units-001` verified, `rle-encode` held on the
unsatisfiable task) or a known cost of the rule that the sealed oracle is never weakened (`kvparse-refactor-001` held on a correct
patch); three ERRORs, all transport: two requests executed by the backend whose answers the host's network outage lost, and one
request whose body stalled in transit and was never executed; three cells were not run because a batch stopped for
reconciliation. No request was sent again after its outcome had become uncertain, and every reconciliation item is settled from the
server side (`transport/README.md`). These batches check the repaired mechanics on real model output; they are not an evaluation,
and the M5 results stand.

**Bundle integrity** (reported apart from the outcomes above): all six bundles check `OK, EVIDENCE COMPLETE` for their verdict under
protocol 4 with the manifest verified. Complete evidence establishes that each recorded verdict follows from its recorded evidence;
the held-out judge establishes the judged outcomes.

**Services, kept apart** (from each batch's `services` record and the reconciliations): inference on the development gateway, 29
call records in the three batches, 28 of them executed by the backend (all 200; the team's allowance, not USD) and one never
forwarded (the 408); none was a never-sent attempt; Token
Factory Sandboxes, 38 operations executed (3 + 27 + 8, every one matched to a ledger or judge record, all `SUCCESS`) and 1 uncertain
spawn that created none; Tavily, no call. The harness's peak resident memory was 53.2, 55.7 and 51.0 MiB.
