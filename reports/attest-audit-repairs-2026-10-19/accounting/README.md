# Accounting repairs for the 19 October 2026 audit: AC-01, AC-02, AC-03, AC-04, AC-07

Repairs to the findings of [`reports/attest-audit-2026-10-19/accounting-findings.md`](../../attest-audit-2026-10-19/accounting-findings.md)
that concern the ledger, the Nebius provider and the evaluation harness. AC-05 and AC-06 (console store and worker) are a separate
change set and are not covered here. Nothing under `reports/attest-audit-2026-10-19/` was modified. Everything in this folder was
produced offline: fake providers and transports, temporary directories, a socket tripwire in every test and reproduction; no model
call, no Nebius or Sandbox API, no credentials read.

## Files in this folder

| File | Content |
| --- | --- |
| `README.md` | this map: finding, files, mechanism, acceptance tests, residual limitations |
| `tests-output.txt` | `python -m unittest tests.test_budget tests.test_audit_accounting tests.test_revision4.LedgerJournal tests.test_revision4.HarnessLabels tests.test_reliability.NebiusReasoningRunaway -v`: 41 tests, all passing |
| `auditor-repro-after-fix.txt` | the auditor's `accounting-repro.py` run unchanged against the repaired tree: it stops in its AC-03 block with `LedgerError` (explained below) |
| `accounting-repro-after-fix.py` | the auditor's five observations of this change set re-expressed so that the repaired refusals are caught and reported |
| `accounting-repro-after-fix-results.json` | its output: every `reproduced` flag is `false`, `any_reproduced` is `false`, with the source digests of the repaired files |

Re-run from the project root:

```bash
.venv/bin/python -m unittest tests.test_budget tests.test_audit_accounting tests.test_revision4.LedgerJournal tests.test_revision4.HarnessLabels tests.test_reliability.NebiusReasoningRunaway -v
.venv/bin/python -B reports/attest-audit-repairs-2026-10-19/accounting/accounting-repro-after-fix.py
```

## Why the auditor's reproduction script no longer completes

`reports/attest-audit-2026-10-19/accounting-repro.py` asserts the faulty behaviour and has no tolerance for the repaired one. Its AC-03
block calls `Ledger.reserve` under an injected disk failure and expects a reservation id back; the repaired `reserve` raises
`LedgerError`, which the script does not catch, so it terminates there (`auditor-repro-after-fix.txt`, exit code 1) before printing
any flag. Had it passed that point, its AC-04 block would terminate as well: it sends three requests in a row and the repaired provider
refuses the second with `ModelError`. The script was left exactly as the auditor wrote it. `accounting-repro-after-fix.py` makes the
same observations with the same fixtures and reports the refusals as data: all five findings of this change set show `reproduced:
false`.

## Findings

### AC-01: a second resume dropped previously recovered interrupted spend

Files: `scripts/run_evaluation.py` (`interrupted_cells`, `run_batch`), `scripts/render_evaluation.py`.

Mechanism. The starting committed total of a batch is rebuilt from disk on every process start, fresh or resumed: every completed row
once, plus every run directory under `runs/` that no persisted row owns once. Ownership is decided by stable run identity (the row's
`run_id` equals the directory name, or the row's `out_dir` resolves to the same path). The list an earlier resumption wrote into
`evaluation.json` only supplies the time an entry was first seen (`first_listed_at_utc`, `listed_by_earlier_resumption`); it is never a
reason to leave a cost out. The report keeps its `interrupted` section with honest semantics: one entry per distinct directory, with
`kind` (`interrupted` or `finished_unreported`), `source` (which record was read), `cost_usd_committed` and
`included_in_batch_total`. The report also carries `starting_total` (rows USD, unowned directories USD, the sum, the time it was
rebuilt). The old `counted_before` field is retained for readers of earlier reports and is always `false`, because the condition it
described (left out of this process's total because an earlier process counted it) no longer exists. The Markdown renderer shows the
starting total and the new columns.

Acceptance tests (`tests/test_audit_accounting.py`):
`UnownedRunDirectories.test_every_process_start_counts_each_orphan_once_and_new_orphans_too` (four process starts over one unchanged
orphan and a second new one, each counted once every time);
`BatchResumeAccounting.test_three_resumptions_count_each_orphan_and_row_once_and_the_cap_binds_on_the_sum` (a four-cell batch through
one fresh start and three resumptions with a mid-run orphan, a finished-but-unreported orphan and a lost row; the fourth process's
reservation is refused because rows plus orphans reach the approved cap: `$0.6500 committed + $0.20 for this run` against `$0.80`);
`BatchResumeAccounting.test_a_fresh_start_also_counts_directories_nobody_owns`;
`RenderUnownedDirectories.test_report_shows_the_starting_total_and_each_unowned_directory_once`. Updated:
`tests/test_revision4.py::HarnessLabels.test_interrupted_run_directories_are_read_back_from_their_journals`.

### AC-02: a finished bundle without a persisted row was excluded from recovery

Files: `scripts/run_evaluation.py` (`recover_spend`, `interrupted_cells`, `run_identity`).

Mechanism. A directory is skipped only when a persisted row owns it by run id or by normalised path. An unowned directory that holds
`proof_bundle.json` is `finished_unreported`: its spend is read from `ledger.json` totals (written by `Pipeline.finish`), with the journal
`ledger.jsonl` as the fallback and the bundle's own ledger totals as the last resort; when both totals and journal are readable the higher
committed figure is kept, so a disagreement can only raise the bound. The spend enters the batch total exactly once and the cell runs
again as a fresh attempt (its scientific result is not reconstructed as a row). A finished bundle with no readable record at all counts at
the per-run cap when the harness runs (the console's policy for an unreadable run) and is listed as not included when no cap is known.

Acceptance tests: `FinishedButUnreportedRun.test_the_finished_run_is_counted_exactly_once_and_the_cell_runs_again` (the harness's real
`one_system` over the offline pipeline fakes; the process dies after `Pipeline.finish` wrote the bundle, `ledger.json` and the manifest
but before the row is persisted; on resume the original run's committed total is in the batch exactly once, the cell runs again, and a
third process start lists and counts it exactly once again); `UnownedRunDirectories.test_an_unowned_finished_bundle_is_recovered_from_its_records`
(ledger.json, journal-only as in the auditor's reproduction, bundle-only, unreadable with and without a cap, journal higher than totals);
`UnownedRunDirectories.test_owned_directories_are_skipped_by_run_id_or_by_path_spelling`. Updated:
`tests/test_budget.py::InterruptedBatch.test_resume_runs_only_the_missing_cell_and_keeps_costs`, whose fixture (a row dropped from the
report while its finished directory stays) is precisely this case; it now asserts the recovered directory and the honest total.

### AC-03: reservation journal failures were swallowed before a paid request

Files: `attest/ledger.py`, `attest/models/nebius_tokenfactory.py`.

Mechanism. `attest/ledger.py` gains `class LedgerError(RuntimeError)`. Every journal append goes through one durable write path
(`_open_journal` via `Path.open`, write, flush, `os.fsync`, close). `Ledger.reserve` appends with `must_persist=True`: with no sink
attached, or with a failure at any of the five steps, it raises `LedgerError` and records nothing in memory either (no request will be
sent, so nothing is owed). `attach_sink` raises `LedgerError` when the journal cannot be created. Settlement appends (`add_call`,
`add_op`) stay best-effort: a failure is counted in `journal_failures` (in `totals()` and `to_dict()`), the in-memory record is kept,
and the journal still holds the open reservation, which `read_journal` counts at its bound. The Nebius provider converts `LedgerError`
into a definite `ModelError` (`uncertain=False`) whose message says the reservation could not be journaled and the request was not
sent, and sets `halted` on the instance so every further request of that run is refused before any reservation or dispatch. The
pipeline's constructor attaches the journal before any call, so the CLI, the console worker and the harness all meet this path.

Acceptance tests: `ReservationDurability.test_reservation_failure_at_every_step_sends_nothing` (open, write, flush, fsync and close
injected before reservation completion: the HTTP stub receives zero calls, nothing is recorded, the instance refuses the next request
even with the disk healthy); `ReservationDurability.test_reserve_without_a_sink_is_refused_and_records_nothing`;
`ReservationDurability.test_the_auditors_injection_point_is_refused` (the auditor's `Path.open` injection);
`ReservationDurability.test_reservation_is_in_the_journal_and_fsynced_before_the_request_leaves`;
`ReservationDurability.test_failed_settlement_write_keeps_the_durable_reservation` (the settlement append fails, the journal is re-read,
the reservation remains committed at its bound; also through the provider with the answer still returned). Updated so that provider
instances get a journal: `tests/test_revision4.py::LedgerJournal.test_provider_refusals_are_free_but_server_failures_stay_reserved`,
`tests/test_reliability.py::NebiusReasoningRunaway` (setUp/tearDown and `_client`).

### AC-04: a successful response without usage was settled as known zero

Files: `attest/models/base.py` (`token_count`, `extract_usage`, `usage_problem`), `attest/models/nebius_tokenfactory.py`.

Mechanism. A token counter is a non-negative integer (an integral float is accepted); booleans, negatives, NaN or infinity, text and
nulls are not counters and yield `None`. After an HTTP 200, `usage_problem` names why the generation cannot be priced (usage absent,
not an object, empty, or without a usable input or output counter). In that case the call keeps `cost_usd = None`,
`settlement = "unsettled"`, a `cost_note` that names the metering failure and the retained reservation, the generated answer is still
returned and validated like any other, and the instance is `halted`: every later request is refused with a `ModelError` saying metering
failed and paid calls stop pending reconciliation (the low-effort retry of a reasoning runaway is skipped too). `spent_usd` already
counted an unsettled call at its reservation, so the per-run cap binds on it. Explicit zero-valued counters are valid and settle as
known 0. `describe()` records the reservation and metering policies and the `halted` reason.

Acceptance tests: `MeteringFailures.test_three_answers_without_usage_are_not_all_accepted` (the auditor's scenario: a $0.02 cap,
three fake 200 answers without usage; one request reaches the stub, the second is refused, committed USD equals the first reservation,
settlements are `["unsettled"]`); `MeteringFailures.test_each_metering_defect_keeps_the_reservation_unsettled` (absent, empty, one
counter only, malformed counters, negative, boolean, not an object, non-integral float);
`MeteringFailures.test_explicit_zero_counters_settle_as_known_zero_and_do_not_halt`; `MeteringFailures.test_valid_usage_prices_the_call_from_the_table`;
`MeteringFailures.test_metering_failure_on_a_reasoning_runaway_blocks_the_low_effort_retry`; `MeteringFailures.test_token_counters_reject_malformed_values`.

### AC-07: resume could change the registered provider and limits without invalidating comparisons

Files: `scripts/run_evaluation.py` (`parse_args`, `restore_registered`, `apply_defaults`, `registered_argv`, `strip_flags`, `launch`,
`run_batch`, `main`, `run_cell`, `comparison_validity`).

Mechanism. The parser leaves provider, per-run USD cap, approved total, call cap, turn cap, workers, attempts and systems unset so that
"not given" is distinguishable from "given". On resume, `main()` (launcher) and `run_batch()` (snapshot process, or a direct caller) read
`schedule.json`, fill every unset value from it and refuse with exit code 2, before any runtime construction, when the command line gives
a different value. The harness's defaults are applied only afterwards (`apply_defaults`); the Nebius default call cap is 22 and is
recorded as `max_calls_per_run`. The launcher forwards the registered configuration as explicit flags to the snapshot process, so a
frozen harness copy that predates this logic still runs the registered provider and limits instead of its parser defaults. Every row
records `executed_provider`, `usd_cap`, `max_calls` and `max_turns`; `comparison_validity` marks a task invalid when a completed cell's
value differs from the schedule (rows written before this revision carry no profile and are not judged on it). The schedule records a
`resume_policy` and each resumption notes that the configuration was restored.

Acceptance tests: `ResumeConfiguration.test_resume_without_flags_keeps_the_registered_nebius_profile`;
`ResumeConfiguration.test_conflicting_flags_are_refused_before_any_runtime_construction` (`--provider`, `--usd-cap`, `--max-calls`,
`--max-turns`, `--workers`, `--approve-usd`, and the auditor's exact Codex-default scenario; the provenance probe, the provider
builder, the Codex governor and `one_system` are patched to fail if touched; the report and schedule are unchanged);
`ResumeConfiguration.test_launcher_forwards_the_registered_configuration_or_refuses` (a real snapshot, `subprocess.call` captured: the
forwarded invocation carries the registered values once; eight conflicting invocations never reach the snapshot process);
`ResumeConfiguration.test_restore_fills_unset_values_and_names_conflicts`;
`ResumeConfiguration.test_defaults_apply_after_restoration_and_give_nebius_a_22_call_cap`;
`ResumeConfiguration.test_comparison_validity_marks_provider_and_limit_drift`. `tests/test_budget.py` now registers with the 22 default
and checks the rows' profile.

### Default per-run call cap

The harness default for `--max-calls` on the Nebius profile is 22 (`NEBIUS_DEFAULT_MAX_CALLS`), applied by `apply_defaults` and recorded
in `schedule.json` as `max_calls_per_run`. An explicit `--max-calls` is kept as given. The documented commands that still spell
`--max-calls 20` (`FREEZE.md`, `README.md`) are outside this change set.

## Residual limitations

- Batches registered before this repair resume under their frozen harness copy by design (the launcher verifies the snapshot digests).
  The launcher now forwards the registered configuration explicitly, which closes AC-07 for them, but the recovery logic inside the
  frozen copy is the old one (AC-01 and AC-02 as audited). Such batches should be registered anew rather than resumed; the only
  pre-repair Nebius batch with an interrupted history (M5, 17 Oct) is complete and will not be resumed.
- Rows written before this revision carry no `executed_provider` or limits; `comparison_validity` does not judge them on it.
  `comparison_validity` compares the harness-level provider name and limits; a change of the model roles inside the provider (for
  example through `ATTEST_NEBIUS_ROLES`) is recorded in each bundle's provenance but not flagged as an invalid comparison.
- Durability means the journal line was written, flushed and fsynced before dispatch. A host crash is covered as far as the device
  honours fsync. When the line reached the file and a later step (flush, fsync or close) failed, a restart counts a reservation for a
  request that was never sent: a conservative overstatement, visible as an open reservation next to the run's ERROR verdict.
- A failed settlement append does not halt the provider; the next reservation fails and halts if the disk stays unwritable.
  `journal_failures` in the totals shows that a journal is incomplete.
- The metering halt is per provider instance, that is per run. The run's committed total (which includes the unsettled reservation) is
  what the harness batch total and the console's daily budget see; reconciliation against the provider's billing remains manual.
- A finished bundle with no readable record counts at the per-run cap, a bound rather than the spend.
- `counted_before` is kept in every `interrupted` entry as an always-false compatibility field.
- The acceptance tests stub the provider construction and the provenance probe where a batch is exercised; the harness's scheduling,
  budget, persistence, resume and validity logic run unmodified. No live provider, sandbox or billing figure was involved.
