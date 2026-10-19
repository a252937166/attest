# Revision 5 accounting closure review — 19 October 2026

The original AC-01–07 examples have repairs and targeted acceptance tests. The current accounting and console suites pass **60 tests in 2.646 seconds**. However, the interruption-safe accounting claim still needs one further P1 repair: a partially written settlement can consume the framing of the next successfully returned reservation.

Read-only review of product source, tests and existing evidence. Only files in this new review folder were added; the original audit and repair reports were not changed. No credentials were read, no network or provider request was made, and no Sandbox or deployment was touched.

## Closure of the original findings

| Finding | Verified mechanism | Current source |
| --- | --- | --- |
| AC-01/02 | Starting USD is rebuilt from every completed row and every unowned run directory; finished-but-unreported bundles are included. Repeated-resume and post-finish interruption tests pass. | `scripts/run_evaluation.py:405–448`, `746–752` |
| AC-03 | Reservation writes now flush, fsync and close before returning; failure at open/write/flush/fsync/close refuses dispatch. A later partial settlement remains the new counterexample below. | `attest/ledger.py:42–52`, `150–185`; `attest/models/nebius_tokenfactory.py:164–172` |
| AC-04 | Missing/partial/malformed usage retains the reservation and halts further paid requests; explicit zero counters remain valid. | `attest/models/nebius_tokenfactory.py:205–220` |
| AC-05 | Imports preserve committed USD, including legacy reconstruction; deduplication tests preserve it. | `attest/app/db.py:463–475` |
| AC-06 | Active reservations cross midnight; completed cost is included when creation, start or finish reaches the current UTC day. This is the documented conservative overlapping-day policy. | `attest/app/db.py:184–196` |
| AC-07 | Resume restores the registered harness provider and limits, rejects conflicting flags and checks executed fields. Model-role and sampling overrides remain outside that comparison. | `scripts/run_evaluation.py:159–191`, `535–552` |

Test command run in this review:

```bash
.venv/bin/python -B -m unittest tests.test_audit_accounting tests.test_audit_console -v
```

## P1: a partial settlement can hide the next durable reservation

**Location:** `attest/ledger.py:42–52` appends without checking or repairing the tail; `150–164` suppresses settlement write errors; `187–195` keeps the in-memory call and permits work to continue. `read_journal()` at `276–280` skips malformed lines. The provider's `164–185` path proceeds from a successful `reserve()` to dispatch and does not treat a prior settlement failure as a halt.

**Trigger:** the first reservation is intact. Its settlement append writes a JSON prefix without a newline, then raises `OSError`. That failure is best-effort. The filesystem becomes writable again; the next reservation append writes and fsyncs its full record directly after the unfinished prefix. `reserve()` returns successfully, but both records now occupy one invalid JSONL line. An interruption before that second call's settlement leaves its reservation absent from restart accounting.

**Observed bounded reproduction:** [script](partial-settlement-repro.py), [results](partial-settlement-results.json). The first call is known to cost $0.01 after reserving $0.02; the next open reservation is $0.05. In-memory committed USD is **$0.06**. Restart readback is **$0.02**, with one unparsable line. The second reserve returns `r2` even though its record cannot be read back.

No HTTP stub was invoked in this reproduction. It proves that the reservation API returns permission to proceed while losing the bound on readback; it does not claim that a real request was dispatched or a real account lost money.

The current injected write failure in `tests/test_audit_accounting.py:80–83` raises before writing any prefix. Its passing settlement-failure test therefore does not cover this framing failure.

**Required repair:** either halt all further paid dispatch after a settlement journal failure until the journal is reconciled, or repair/frame an incomplete tail safely and durably before admitting another reservation. Do not discard a known durable reservation while repairing the tail. Fsync alone cannot make a concatenated invalid JSONL record recoverable.

**Acceptance:** inject an actual partial settlement prefix followed by a write failure; restore disk health; attempt another paid request; interrupt before its result. Either the later request must be refused before dispatch, or restart accounting must preserve its whole reservation together with the earlier committed/bounded amount. Include the same sequence through the real provider with fake HTTP and a process-like interruption, plus a non-ASCII truncated tail.

## Frozen-profile qualifications before paid validation

1. **Model-role drift is still permitted.** `attest/models/nebius_tokenfactory.py:38–43` reads `ATTEST_NEBIUS_ROLES`; the reasoning settings at `71–78` are also environment-controlled. The restored schedule does not enforce these fields. A purely in-memory check changing only implementer Super to Nano still returns `comparison_validity(...)["t"]["valid"] == True`. The repair report discloses this at `accounting/README.md:165–167`; it is not an undisclosed repair claim. Before a paid same-model comparison, freeze and compare the effective role and sampling maps, including on resume, or refuse environment overrides for that evaluation.

2. **The proposed CLI smoke has no enforced 22-call cap.** `FREEZE.md:178` promises at most 22 calls per smoke run through the CLI. `attest/cli.py:24` constructs the provider without `max_calls`, whose default is `None` at `attest/models/nebius_tokenfactory.py:52`; `attest/app/worker.py:254` does the same. The harness enforces 22 via `scripts/run_evaluation.py:502`, `566–567` and passes it to the provider, but that does not cover a CLI smoke or a console run. Add the cap to those entry points or run the proposed smoke through an entry point that actually supplies it. The USD cap still applies; this is a mismatch with the promised request-count limit.

The current package digest `1e12d46217fb6b8a27a08b4463f42f361e7309257b211103c08777c91cb10ce5`, harness digest `2aa28413a1ccfe425c400a085a18e3e3625aa11f7170b3f655de7bab53e8816c`, and working-tree examples digest `6db7a2e937d6e5d4aa4d2074d969782e0c76095f1dd661e773c03edd8f479ba4` match the revision-5 section of `FREEZE.md`. That pin's revised evaluation command uses 22 calls. The repair folder contains only the two Codex validation schedules (five and two cells); no new paid Nebius evaluation was verified in this review.

## Next action

Keep paid validation pending. Repair the partial-settlement case, make the proposed smoke's 22-call limit concrete, and freeze the effective provider roles/sampling for a comparable rerun. Then re-run the targeted tests, pin the changed source and register a fresh evaluation rather than resuming a pre-repair harness snapshot. This review does not assess the other audit areas or confirm live deployment state.
