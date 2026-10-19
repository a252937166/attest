# Repairs after revision 7 (revision 8, versions 0.8.0 and 0.8.1, 19 October 2026)

This pass fixes the issues left after revision 7 before any video work: the memory limit on yungou, horizontal overflow on phones,
the development batches' transport failures, accidental spending, and the separation of the services' costs; it then verifies
the repairs from a clean checkout, deploys them with the transactional installer and checks the deployed console in a real browser.
Two problems found along the way are repaired too: the public export carried the development gateway's host in escaped
spellings, and the sealing stage sent the same prompt again after a call whose outcome was uncertain (an older defect; the run now
stops at the first uncertain call in every stage). yungou was unreachable twice during this pass, for reasons outside the project
(below). Every earlier record is unchanged; corrections are appended and dated.

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
execution. Every scheduled cell is reported; nothing was merged or selected; no uncertain request was sent again. The pinned package
(`ed41f4c95bd1…`) differs from the batches' package only by the stop fix of `5177cf4` (the run stops at the first uncertain call in
every stage); none of the batches' failures was in a stage that fix changes.

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

## Final-tree offline suite

Run after the batches, the reports and the export, on the exact trees that are pinned and deployed (`corpus/`, local paths masked):

| Run | Tree | Tests | Failures | Errors | Skips |
| --- | --- | --- | --- | --- | --- |
| 1 | clean checkout (`git worktree`) of the first pinned code commit `35248d0` | 397 | 0 | 0 | 0 |
| 2 | clean checkout of its pin record `6eca557` | 397 | 0 | 0 | 0 |
| 3 | private working tree, same code | 397 | 0 | 0 | 0 |
| 4 | clean checkout of `5177cf4` (the stop fix; the pinned code commit) | 402 | 0 | 0 | 0 |
| 5 | private working tree after the stop fix | 402 | 0 | 0 | 0 |
| 6 | clean checkout of `3be63fa`, the pin record the 0.8.0 release is built from | 402 | 0 | 0 | 0 |
| 7 | clean checkout of `d15046a` (0.8.1, the console repairs; the pinned code commit from then on) | 402 | 0 | 0 | 0 |

The count grew from 367 (revision 7) by the 28 tests of `tests/test_transport.py`, the five explicit-start tests and two
installer scenarios; the console's confirmation check and the escaped-host checks of the export were added inside existing tests. A high count is not evidence that the deployment, billing or external services are correct; those
are checked separately below and in the folders above. A last run on the commit that adds these records is in the commits table.

## Deployment and production verification

Revision 8 was installed on yungou on 19 Oct at 20:42 UTC from a clean checkout of the pin record `3be63fa` with the transactional
installer (`reports/attest-deployment-2026-10-19e/`): release `0.8.0-ed41f4c95bd1` active, `0.7.0-f836cfd0154f` kept as the
rollback target, the store backed up first (SQLite backup API and an archive of the data directory). Read back afterwards:

| What | Read back |
| --- | --- |
| Version and package | 0.8.0, `attest_revision()` `ed41f4c95bd1…` over 37 files through the deployed interpreter; all 3,862 `RELEASE.json` entries verified in place; `/`, `app.js` and `styles.css` served byte-identical to the commit's files |
| Memory limit in force | systemd `MemoryLimit=209715200`, kernel `memory.limit_in_bytes` and `memory.memsw.limit_in_bytes` 209,715,200, the main process in `/system.slice/attest.service`; an OOM drill of the deployed release in a temporary unit: killed by the memory-cgroup OOM killer at the memory-plus-swap limit, restarted by systemd, the run in flight settled as interrupted with its reservation committed and its accepted operation named (`memory/`) |
| Queue, reservations, budget | queue 0, idle, no run queued or running in the store (40 rows); 0 active reservations, $0.00 reserved; $0.0552 committed on this UTC day (the unapproved probe run of 19 Oct, recorded in `reports/attest-deployment-2026-10-19c/`), $1.9448 of the $2.00 daily cap remaining |
| Admission | `/api/openapi.json`: strict `RunRequest`, no provider default, the `X-Attest-Confirm` header documented; the 428 refusal itself is verified by the local tests only, since no POST was sent to production |
| Real browser, desktop and phone widths | 0.8.0 on the public URL in Chrome: no element or text wider than the viewport, no sideways-scrolling document and no page error at 320 to 1440 px (a visible window at 390 and 1440 px, 182 states; a headless sweep at eight widths, 726 states), with every disclosure of the evidence open, a missing run and every API call failing; 2,572 GET requests and no other request; the confirmation refused by the page in an automated browser. The checks found five defects outside the overflow measure (below), repaired in 0.8.1 |

## Found on the deployed console, repaired in 0.8.1

The production checks of 0.8.0 found what the local audits had not (`reports/attest-deployment-2026-10-19e/`): at 1024 px the
Guide, which opened by itself on windows wider than 900 px, covered the case file's Activity and Files tabs (two tab presses
failed); the decision card's text was squeezed to about 80 px between its seal and its buttons, and the overview's evidence table
into a sideways scroll; with every API call failing, the start form said that no sample tasks were configured; on phones the
collapsed workspace rail stretched into an empty band on short pages. Version 0.8.1 (`d15046a`) repairs the five: the Guide opens
by itself only from 1320 px, the decision's buttons take their own row below 1320 px (the compact bar keeps one row), the overview
stacks below 1180 px, a task list that failed to load says so, and the rail no longer stretches. The `attest/` Python sources differ
from 0.8.0 only in the version string (package `3c0cbfcaa9d6…`); the pipeline, the providers and the harness are unchanged.

0.8.1 was installed at 22:18 UTC from a clean checkout of the pin record `ab8c445` (`reports/attest-deployment-2026-10-19f/`) and
checked the same way: version 0.8.1 and package `3c0cbfcaa9d6…` read back through the deployed interpreter; systemd and the kernel
enforce 209,715,200 bytes for memory and for memory plus swap on the new main process; queue 0, no reservation, $0.0552 committed;
the static files served byte-identical to the commit's. In Chrome on the public URL (a headless sweep at eight widths from 320 to
1440 px and a visible window at 390 and 1440 px, 910 states): no offender, no clipped control, no page error, every tab press went
through, the Guide opened by itself only at 1440 px, and 2,563 GET requests left the browser and no other request. Rollback target:
`0.8.0-ed41f4c95bd1`.

## yungou's availability during this pass

The host was unreachable twice before the deployment (details in the deployment record, from `/var/log/messages` and the nginx
access logs): from 19:02 to 19:18 UTC its network failed while it kept running (its outbound connections got `No route to host`;
no inbound request reached nginx); this cut the first development batch's two answers (`transport/`). At 19:56:29 UTC the QEMU
guest agent received a shutdown request from the hypervisor side (the provider or its control panel) and the host powered off; it
booted again at 20:35:01 UTC and every service came back by itself. The cause of the first outage is not established; the host's
hourly subscription refresh, which finished 104 s before it, changes no route and runs no proxy, and no link to it was found. While
the host is down the console is unreachable; nothing in Attest can change that.

## Usage in this pass, per service (never added into one figure)

| Service | Use | Billing |
| --- | --- | --- |
| Nebius Token Factory inference | **none**: no paid call, smoke test, evaluation or demo run. The Nemotron provider was constructed once offline, with a placeholder key and blocked sockets, to compute the effective profile | none incurred |
| Production console | no POST, PUT or DELETE request. Production was read with GET requests, with a browser that blocked every other request before it was sent, and with read-only SSH commands; the deployment changed the host through the installer only | none |
| Development gateway (team allowance) | 29 model-call records in the three batches, 28 executed by the backend (all 200), one never forwarded (408); plus the batches' status and catalog reads | the team's ChatGPT allowance, recorded in tokens; not USD |
| Token Factory Sandboxes | 38 operations executed in the three batches (3, 27 and 8; every one matched to a ledger or judge record; all `SUCCESS`; 154.4 s of guest time: 4.4, 106.0 and 43.9 s) and one uncertain spawn that created none; 7 read-only `GET /operations` listings for reconciliation (the revision-7 windows and the three revision-8 batches) | a beta service; Nebius's console says beta runs are free; not reconciled against an invoice, so no record here claims a zero cost |
| Tavily | no call: the harness runs without it, and no console run was started | none incurred |

The memory drills on yungou (two before the deployment, one of the deployed release after it) used temporary units with no
credentials and made no external request.

## Remaining limitations and open decisions

- **The review repository's history** still contains the development gateway's host in every commit before revision 8 (escaped
  spellings in the exporter's patterns and in 125 redaction records). The revision-8 tree is clean; the history must not be
  published as it is. Publishing a fresh repository from the final tree, or rewriting the history, is the owner's decision.
- **Uncertain requests on this machine's path.** A request whose body stalls after its first bytes leave this machine (through the
  local proxy) is uncertain at the client, stops its run and its batch, and can be settled only from the gateway's ingress log and
  the backend's records. Making such requests safe to repeat would need the gateway to accept an idempotency key, or batches run
  from a host with a stable path to the gateway; both are changes to the team's infrastructure and were not made.
- **The resend of never-sent requests** is covered by the loopback and adapter tests; no real connection-setup failure occurred in
  this pass's batches, so live traffic has not yet exercised it.
- **yungou's availability.** The host lost its network for 16 minutes and was later powered off from the hypervisor side (above);
  the first cause is not established and neither is under this project's control. `auditd` and `kdump` fail at every boot of this
  host (no `/var/log/audit` directory, no crash-kernel memory), as on 7 Oct; they are unrelated to Attest and were left alone.
- **The memory drill of the running service** was done on a copy of the deployed release (0.8.0) in a temporary unit, not by
  running `attest.service` itself out of memory, which would have interrupted the public console; for 0.8.1 (the same unit, the
  same Python code apart from the version string) the limits were read back, and the drill was not repeated.
- **The sealed-oracle rule** holds a correct patch when a sealed test fails by assertion, even after the arbiter classified the test
  a defect and the correction was validated (kvparse in the third batch). This is deliberate (revision 4); its cost is false rejects.
- **Sandboxes billing** is not reconciled against an invoice; the operation counts and guest times are recorded, no amount.
- **The paid Nemotron validation of revision 8** has not run; the $10 proposal in `FREEZE.md` remains unapproved. The M5 figures are
  historical results of the version pinned on 17 Oct 2026, not an evaluation of revision 8.

## Commits (review repository, local only, not pushed)

| Commit | Content |
| --- | --- |
| `d5498e6` | memory limit in force on systemd 219, installer readback, rehearsal shims, ops scenarios 9 and 10 |
| `be503dd` | transport phases, bounded resends of never-sent requests, accepted-operation journaling, reconciliation and services records, checker counters, `tests/test_transport.py` |
| `2183c03` | console: explicit start (428 without the confirmation header, the confirmation step, automated browsers refused), cost labels by service, the phone layout, the layout audit script |
| `21d5310` | export privacy (private hosts from private configuration, every spelling, rule labels in `REDACTION.json`), the provenance check |
| `35248d0` | documentation, this folder's evidence, dated corrections of earlier records, version 0.8.0 (the first pinned code commit, package `68e9de49…`) |
| `6eca557` | the first revision-8 pin record (superseded before any deployment) |
| `5177cf4` | the run stops at the first uncertain model call in every stage (sealing no longer sends the same prompt again); the pinned code commit, package `ed41f4c9…` |
| `3be63fa` | the revision-8 pin record re-pinned to `5177cf4` before any deployment; the release was built from a clean checkout of this commit |
| `d15046a` | 0.8.1: the console repairs found on the deployed 0.8.0 (the Guide, the decision card and the overview at narrow desktop widths, two error states); the layout audit's new checks; the pinned code commit, package `3c0cbfca…` |
| `ab8c445` | the pin record re-pinned to `d15046a` before 0.8.1 was deployed, and the records of the 0.8.0 deployment; the 0.8.1 release was built from a clean checkout of this commit |
