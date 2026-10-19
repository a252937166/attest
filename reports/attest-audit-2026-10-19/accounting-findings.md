# Revision 4 accounting audit — 19 October 2026

The new journal improves ordinary interruption recovery, but the current implementation does not yet keep the approved budget conservative on every recovery path. Five findings below can release committed USD incorrectly; two further findings concern UTC-day attribution and the registered evaluation profile. These are reproduced code defects or explicit policy gaps, not evidence that a real account was overcharged.

Scope: `attest/ledger.py`, the Nebius provider, console budget/recovery/import/retention, and evaluation scheduling/resume. No product source was edited, credentials read, network accessed, model or Sandbox called, or deployment changed. Reproductions use temporary files, temporary SQLite stores and fake provider responses. A socket tripwire rejects accidental networking.

## Evidence and repeatability

Run from the project root:

```bash
python3 -B reports/attest-audit-2026-10-19/accounting-repro.py
python3 -B -m unittest tests.test_revision4 tests.test_budget tests.test_phase1 -v
```

- [Standalone reproductions](accounting-repro.py) and [observed results with source SHA-256 fingerprints](accounting-repro-results.json): all seven findings reproduced on Python 3.12.0.
- [Existing targeted test output](accounting-targeted-tests.log): 37 tests passed in 3.670 seconds. They cover the normal recovery paths but do not detect these counterexamples.
- P1 means the configured spend ceiling can be understated under the described reachable condition. P2 means a narrower daily-budget or evaluation-integrity issue. None of these findings establishes an invoice amount.

## Findings

### AC-01 — P1: a second resume drops previously recovered interrupted spend

**Location:** `scripts/run_evaluation.py:337`, `491–495`.

**Trigger:** resume a batch that already has an `interrupted` entry from an earlier resume. `interrupted_cells()` marks an existing entry `counted_before=True`; however, `run_batch()` reconstructs `committed` from completed rows only, then excludes every `counted_before` interrupted entry. The earlier reservation is therefore absent from the new `Budget` even though the report still lists it.

**Observed reproduction:** a journal with an open $0.25 reservation contributes $0.25 on the first resume and $0.00 on the second. The second report entry still contains $0.25. Repeated stops can make the batch admit additional calls against an understated total.

**Fix:** rebuild the starting committed total from all distinct completed rows and all distinct interrupted runs on every process start. Deduplicate by stable run identity; do not use a prior-process flag to suppress a cost that has not entered the current process's total.

**Acceptance test:** perform at least three resumptions with one unchanged orphan and then a second new orphan. Every restart must count the original orphan once, the new orphan once, and each completed row once. Assert that the next per-run reservation is refused when their sum reaches the approved cap.

### AC-02 — P1: a finished bundle without a persisted evaluation row is excluded from recovery

**Location:** `scripts/run_evaluation.py:345–346`; completion/persistence window at `581–592`.

**Trigger:** the pipeline writes `proof_bundle.json`, then the process ends before its evaluation row is persisted. Recovery unconditionally skips every directory with that file, even when no completed row owns the directory. This also occurs naturally with concurrent workers: a later future may have finished while the main thread is still waiting on an earlier future in submission order.

**Observed reproduction:** an unowned directory has $0.25 committed in its journal. Without a bundle it is recovered; adding `proof_bundle.json` makes `interrupted_cells()` return no entry. The next run can repeat the cell without adding the earlier spend to the batch total.

**Fix:** skip a directory only after matching it to an actual persisted row by run ID or normalized path. Recover an unowned finished bundle's ledger totals, or its journal as a conservative fallback. Preserve its spend even if its scientific result cannot be reconstructed as a completed cell.

**Acceptance test:** interrupt after `Pipeline.finish()` but before row persistence, including an out-of-order future. Resume from disk and assert that the original run's committed total remains in the batch exactly once, whether the result is recovered or a fresh attempt is scheduled.

### AC-03 — P1: reservation journal failures are swallowed before a paid request

**Location:** `attest/ledger.py:112–119`, `129–138`; request dispatch at `attest/models/nebius_tokenfactory.py:150–163`; best-effort DB observer at `attest/app/worker.py:144–152`.

**Trigger:** the journal attaches successfully, but a later append fails, for example because the filesystem fills. `_append()` suppresses `OSError`; `reserve()` returns normally and the provider proceeds to the request. The console DB observer also suppresses its write failures, and the evaluation harness has no alternative live DB sink.

**Observed reproduction:** after a successful journal attachment, a fake disk-full error makes `reserve()` return `r1`. In-memory committed spend is $0.25, but reading the surviving journal restores $0.00. A process interruption after dispatch can erase that reservation from restart accounting. A truncated settlement after a successfully written reservation is already handled conservatively; an unwritten reservation is the uncovered case.

**Fix:** require successful persistence of a reservation before dispatch. If the journal cannot accept it and no authoritative durable alternate sink confirms it, refuse the request and stop further paid work. Preserve a durable open reservation if settlement persistence fails. Define and test whether durability includes host crashes; current append/close writes do not call `fsync`.

**Acceptance test:** inject failures on open, write, flush and close before reservation completion; the HTTP stub must receive zero calls. Separately fail settlement writes after a successful request, restart, and assert that the durable reservation remains committed. Verify the behavior of a partial journal tail and a failing DB observer.

### AC-04 — P1: a successful response without usage is settled as known zero

**Location:** `attest/models/nebius_tokenfactory.py:181–186`; `attest/models/base.py:49–65`.

**Trigger:** an HTTP 200 response contains valid generated JSON but missing or partial token usage. `extract_usage()` returns `None` for missing counters, and the price formula turns those values into zero. `add_call()` then labels the call `known` and closes its nonzero reservation. A usable generated answer does not establish that generation was free.

**Observed reproduction:** with a $0.02 per-run cap, three fake successful responses lacking `usage` are accepted. Each request reserved $0.014701, but committed cost stays $0.00 and all three settlements become `known`.

**Fix:** validate that the usage needed to price a successful generation is present and nonnegative. Otherwise keep the reservation as `unsettled`, mark the metering failure explicitly, and stop further paid calls pending reconciliation. Do not convert missing input or output counters to known zero.

**Acceptance test:** cover absent usage, empty usage, only one counter, malformed counters, and a valid explicitly zero-valued refusal. Unknown metering must retain its bound and affect both the per-run and batch/daily budgets; a second request must be refused when the remaining bound does not fit.

### AC-05 — P1: startup import discards conservative committed cost

**Location:** `attest/app/db.py:292–306`; daily calculation at `74–80`; startup import at `attest/app/server.py:46–58`.

**Trigger:** import a Nebius bundle containing a transport-uncertain call. The bundle stores both known USD and `cost_usd_committed`, but `import_run_dir()` inserts only the former. The daily-budget query falls back from the now-null committed field to known cost, or zero. This affects normal evidence imports and rebuilding a store from completed run directories.

**Observed reproduction:** a same-day ERROR bundle has `cost_usd=None` and `cost_usd_committed=$0.50`. After import the committed DB column is null; a $0.50 daily budget reports $0.50 remaining and says another run fits.

**Fix:** preserve `cost_usd_committed` during import, including conservative reservations. For legacy bundles without that total, recompute from their call records/journal when possible or keep an explicit conservative unknown bound. Do not discard it during import deduplication or recovery.

**Acceptance test:** import a same-day bundle with known cost plus an uncertain reservation, compare the DB value with the bundle, restart/import again, and assert no loss or duplication. Verify that a subsequent reservation is refused at the daily cap. Include rebuilding a fresh DB from run directories.

### AC-06 — P2: a queued-before-midnight run disappears from the new day's spend on completion

**Location:** `attest/app/db.py:74–84`; execution recheck at `attest/app/worker.py:131–135`.

**Trigger:** enqueue before UTC midnight, execute after midnight. Active reservations are counted without a day filter, but finished/error costs are selected using the run's `created_at`. Once the run finishes, its spend disappears from the new day's calculation even when all inference happened that day.

**Observed reproduction:** a run created at 23:59:59 starts at 00:01 and finishes at 00:05 with $0.50 committed. Under a $0.50 new-day cap, remaining budget changes from $0.00 while active to $0.50 on completion. The new day reports $0.00 committed.

**Fix:** define the intended daily-budget policy. For a UTC spending cap, account for per-call timestamps and carry active reservations over midnight; a conservative run-level alternative must include every day on which that run can spend. A creation-day allocation is a different policy and must be named as such, rather than advertised as a UTC spend limit.

**Acceptance test:** use a controlled clock with a run queued before midnight and started after it, plus a run whose calls straddle midnight. Finishing or erroring either run must not release USD that was spent or remains reserved on the current day.

### AC-07 — P2: resume can change the registered provider and limits without invalidating comparisons

**Location:** `scripts/run_evaluation.py:400–418`, `427–460`, `481–497`, `557–583`; validity check at `145–163`.

**Trigger:** resume an existing batch while omitting `--provider nebius` or changing runtime limit flags. The parser defaults to Codex, and resumed cells use the new CLI arguments rather than restoring or validating the registered schedule. The schedule still describes the old provider. Comparison validity checks source revision, not provider or limit consistency.

**Observed reproduction:** a fake batch registered as Nebius is resumed with the Codex default. Its resumed cell executes with `provider_name='codex'`, its new budget has no USD approval, its schedule still says Nebius, and `invalid_tasks` remains empty. All execution is stubbed in this reproduction; no credential or live provider is involved.

**Fix:** restore provider, per-run cap, call cap, turn cap, worker count and the approved batch total from the registered schedule on resume. Reject conflicting CLI overrides, or record an explicitly approved amendment/new evaluation and invalidate pooling with the old schedule. Do not silently change to the parser default.

**Acceptance test:** resume a Nebius registration with no provider flag and with conflicting provider/cap/call/turn flags. It must retain the registered configuration or refuse before runtime construction. A mixed provider or materially changed limit must never remain a valid same-profile comparison.

## Verified behavior and scope limits

- Normal reservation/settlement journal round trips, transport uncertainty, HTTP 422/429 refusal handling, and HTTP 502 reservation retention pass the targeted offline tests. This validates the configured handling, not an actual provider invoice.
- An intact reservation followed by a truncated call record stays committed at its bound. Console recovery uses the maximum of its DB total and readable journal total, and falls back to the per-run cap when the journal is absent.
- Ordinary exception paths retain paid fake-call totals in pipeline, harness and console records. The uncovered interruptions are the cases described above.
- Same-process console admission holds its lock across checking active reservations and inserting a queued row. Existing reservation tests pass.
- Retention removes artifacts while keeping accounting rows and spend. The standalone control prunes two fake runs: committed USD is $0.50 before and after. Historical costs should remain in the DB even after artifacts are pruned.
- No live billing reconciliation, deployment, grant balance, card charge, or Nebius price refresh was performed. This review does not claim that an observed zero or reserved figure equals a bank debit.

## Recommended repair order

First fix AC-01/02/03, then AC-04/05 before another paid batch or claiming interruption-safe caps. Resolve AC-06's day policy and enforce AC-07's frozen resume configuration before relying on a daily spend guarantee or pooling a resumed evaluation. Add the acceptance cases above to the product tests and re-run the offline reproductions; historical source snapshots and original run evidence should remain unchanged.
