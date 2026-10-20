# Revision 9: stop for reconciliation (20 October 2026, version 0.9.0)

This pass repairs the six issues of the review of revision 8. Each one was reproduced on the code as deployed (version 0.8.3, commit
`a4a1f19` of the review repository) before it was changed, and the same reproduction then ran against the repaired code
(`repro/repro_revision9.py`, below). Video work was set aside for this pass.

No paid Nebius inference, smoke test or evaluation was started. Development stayed on the team's Codex gateway; Sandboxes and Tavily
usage is reported separately from inference below, and nothing was pushed or published.

## The issues, their causes and the repairs

### 1. Work went on after an uncertain operation

*Cause.* Revision 8 stopped a run at the first uncertain **model** call, but sandbox operations had no such rule. The breaker caught
the Sandboxes client's `SandboxError(uncertain=True)` and re-raised it as a plain `ModelError`, so `uncertain` was lost and the run went
on to the drift audit. Five more stage handlers (the contract-audit witness, the held-out suite, every mutant, the arbitration re-runs on
the candidate and on the base, the arbitration's mutant re-runs) caught any exception, recorded it and continued: after an uncertain
witness or mutant spawn a run could still end **VERIFIED**. The evaluation harness judged a cell after its run had stopped, decided
whether a cell was uncertain by searching its error text for the word "uncertain", and the console worker started the next queued run.
Two recorded development bundles of 17 Oct (`reports/attest-reliability-2026-10-17/evaluation-paced-codex/runs/balanced-brackets-attest-a1-20261017T121900586528Z`
and `.../semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z`) did exactly this: each ended VERIFIED with one mutant spawn of
unknown outcome excluded from its score.

*Repair.* The run's ledger, the one object its provider, executor and pipeline share, now carries the stop state. `Ledger.halt` records
why the run stopped (`uncertain_operation`, `journal_failure`, `metering_unknown`, `batch_stop`), and `Ledger.admit`, which every client
calls immediately before each request it sends (every attempt, every poll, every read), refuses with `RunHalted` from then on. Every
model call and sandbox operation of the pipeline goes through four guarded entry points (`ask`, `_branch`, `_create_checkpoint`,
`_resolve_image`), which refuse once the run has stopped and turn any error that stops a run into `ReconciliationRequired`; the stage
handlers let it pass. The run ends there: verdict ERROR, one reason naming the stage and the cause, and a `reconciliation` record in
the bundle that lists every operation whose outcome is unknown with the read-only check that settles it (evidence protocol 5). No reason,
decision header or console button suggests running the stage again: the console replaces "Start a new run" with "Held for reconciliation".
An uncertain Tavily search ends the run the same way. The harness skips the judge of a stopped run, halts every other cell in flight
(`batch_stop`) and takes uncertainty from the ledger's records. The console records the run as `reconciliation_required` and opens a
hold: no run starts and admission is refused (HTTP 503) until an operator clears the hold with a note (`python -m attest holds`).

### 2. Ambiguous HTTP answers were treated as definite

*Cause.* The Sandboxes client turned every HTTP error into a plain `SandboxError`, and its spawn handler only looked at transport errors:
a spawn answered 502 left the operation without a state, was not uncertain, and was missing from every reconciliation list. A poll
answered 5xx was not retried, raised a plain error, and left the accepted operation `ACCEPTED`, outside the reconciliation list; so did an
operation that never reached a terminal state. The development gateway's client treated every HTTP error but 429 as a definite failure,
although its proxy answers 502 or 504 when the backend is slow or drops the connection after the request was forwarded. The Token Factory
client kept a 5xx's reservation committed but raised a plain error. `read_journal` keyed operations by the service's id, so a spawn with no
id (uncertain, or in flight when the process died) was invisible after a restart.

*Repair.* `attest.http.post_outcome` is the one classification of a failed POST: `not_sent` (no byte left this machine: sent again,
bounded), `rejected` (HTTP 4xx: refused, nothing executed) or `uncertain` (HTTP 5xx or any other answer, or a failure after the request
was written: never sent again, the run stops). A spawn answered 4xx is REJECTED; 5xx, a 2xx without an operation id, or a lost answer is
UNCERTAIN. Polls and other reads are retried, bounded (four retries, 1/2/4/8 s or the server's Retry-After up to 30 s), on a transport
failure or an answer that asks for it (408, 429, 5xx, and 404 for a just-accepted id); an accepted operation whose outcome is still not
read, or that never ends, is ACCEPTED_UNREAD and listed. Both model clients record the HTTP status, the phase and the answer class of
every call, and a 5xx stops the run. Operations carry a client-side id (`op_id`) from their PENDING record on, so the journal names every
unresolved spawn after a restart.

### 3. Operation records were best effort

*Cause.* `add_op` and `update_op` appended to the journal best effort: when the append failed (disk full, an I/O error, a cut line) the
failure was counted and the client went on to send the spawn or to poll, although the module claimed that accepted ids survive an
interruption. A ledger without a journal dispatched without any record.

*Repair.* A sandbox operation is journaled as PENDING, fsynced and read back, before any byte of its spawn is sent; its accepted id the
same way before the first poll; and every later state the same way. When an append fails nothing further is dispatched or polled, the
run halts, and what is known (stage, image, accepted id) goes into the halt record and to the `attest.ledger` log as one `ATTEST-HALT`
line, which survives a journal on a full disk; a halt caused by the journal is not written to it again. A ledger without a journal
dispatches no sandbox operation. Every development-gateway call takes a zero-USD pending record the same way, so a call in flight when
the process stops is visible after a restart, as Nemotron calls already were through their USD reservations.

### 4. A cut HTTP error body escaped the transport wrapper

*Cause.* `request_json` read an error answer's body inside its `except HTTPError` handler. A chunked error body cut short raised a raw
`http.client.IncompleteRead` there, and a stalled one a raw timeout, past the sibling handler that wraps transport failures, losing the
status, the phase and the fact that the request had been sent. (A Content-Length body cut short was silently truncated.)

*Repair.* Both bodies, the error's and the success's, are read under their own guard. An error answer is always an `HttpError` that keeps
its status and records `request_sent`, the phase (`response`) and whether its body arrived complete (`body_complete`, `body_error`); a
success whose body is cut is a `TransportError` that keeps the status. The classification of an answer depends on its status, never on
its body.

### 5. The offline tests depended on private configuration and the network

*Cause.* Four reliability tests built the gateway client without a base URL, so they needed the developer's private configuration and
failed without it. One called `describe()` after its HTTP mock had ended: the policy refresh window compared the governor's (fake) clock
with the real one, so `describe()` sent a real `GET /status` (with four retries) to whatever gateway the configuration named, and the
test passed anyway, because the fallback policy text still contained the phrase it checked. Nothing in the suite blocked the network or
hid credentials.

*Repair.* The tests use an explicit synthetic gateway URL and journal, and the `describe()` call is inside the mock and asserts that it
sends nothing. The policy window uses the governor's clock. `tests/_isolation.py`, imported by `tests/__init__.py`, removes provider
credentials and private configuration from the test process, disables urllib's proxy discovery (`no_proxy=*`), and turns every connection
or name lookup outside the loopback interface into an assertion that no handler catches; `tests/test_zz_isolation.py`, the last module of a
discovery run, fails if any was recorded. The complete suite is then run from a clean checkout, with credentials absent and the network
blocked by the operating system (below).

### 6. The review repository's history is not publishable

*Cause.* The exported tree has been clean since revision 8, but the review repository's earlier commits keep 125 versions of
REDACTION.json and 16 versions of the export script that carry the development gateway's host (as a regular expression, plain and
JSON-escaped), and two early EXPORT.json files carry a local home directory (`scripts/scan_publication_history.py`, which scans every
object of a repository for the private hosts in every spelling, including base64 and compressed data).

*Repair.* `scripts/build_publication_history.py` replays the review history, commit by commit with the same authors, dates and messages,
into a separate repository. Only blobs that hold a private string change, through the export's own redaction, and the derived manifest of
each affected run copy gets that entry's digest and size recomputed. The review repository and its evidence stay untouched; the replay is
deterministic, so each review commit has exactly one publication commit, and `--verify` checks the result (records below).

## Reproduction

`repro/repro_revision9.py --code <checkout>` runs every scenario of the issues above against one checkout, offline: credentials removed,
HOME pointing to an empty directory, every connection and name lookup outside the loopback interface refused inside the process. It
reuses the checkout's own test fakes, so the same script runs against both versions.
