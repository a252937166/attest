# Console, API and accounting repairs, 19 October 2026

Repairs for the console/API slice of the 19 October 2026 audit (`reports/attest-audit-2026-10-19/`): findings API-01 to
API-11, the accounting findings AC-05 and AC-06 that live in the console store and worker, the publication contract for
team runs (product decision 1) and the containment of artifact downloads (product decision 2).

Offline work only: no model call, no Nebius or Sandbox API, no SSH, no live run, no deployment, no publication. Nothing under
`reports/attest-audit-2026-10-19/` was modified (the auditor's retained result files keep their checksums:
`api-repro-results.json` f33d969f..., `sqlite-concurrency-probe.json` d17fb5b7..., `console-repro-results.json` 638fed16...).

## Files changed

| File | Change |
|---|---|
| `attest/app/db.py` | lock-through-fetch helpers; atomic admission with `QuotaError`; new columns `visibility`, `error_code`, `error_ref`, `error_detail` with migration and back-fill; `record_failure`, `finalize_interrupted`; UTC-day budget policy; error retention; committed cost preserved on import and dedupe |
| `attest/app/worker.py` | supervised loop (`_run_one`, `ensure_alive`, `stop`/`start`, housekeeping on an idle timer and after every job), ordered queue mirror with `position()`, admission that requires a live worker and serialises capacity, row and queue slot |
| `attest/app/server.py` | trusted-proxy requester, team-token visibility on every read route, explicit public projection, contained artifact set and spooled ZIP with 413 caps, retryable `bundle_incomplete`, sanitized global exception handler |
| `attest/app/static/app.js` | token on reads and downloads once accepted, public field names (`has_artifacts`, `error_public`), authoritative `position`, bounded terminal retry with a Retry control, `res.ok` before the clipboard |
| `attest/app/static/index.html` | one sentence in "How to use it" (public runs are public, team runs are visible to the team only); asset stamps untouched |
| `tests/test_console.py` | the development-gateway fixture is read with the team token; new visibility and projection assertions; `/api/runs` and `/api/openapi.json` added to the no-gateway-name check |
| `tests/test_audit_console.py` (new) | acceptance tests, one class per finding (see below) |
| `tests/console_client_test.mjs` (new) | node checks of the extracted client functions, run from `tests/test_audit_console.py` |

Evidence in this folder: `test-output.txt` (the required test command, the `ConsoleInterruption` class, `node --check`, the
node test), `repro_api_offline.txt`, `repro_console_offline.txt`, `repro_sqlite_offline.txt` (the auditor's three
reproductions, unmodified, run after the repairs; each now stops at its first faulty-behaviour assertion or records zero
failures).

## Finding by finding

### API-01, caller-controlled forwarding address

- Files: `attest/app/server.py` (`TRUSTED_PROXIES`, `requester_from`, `_requester`).
- Mechanism: `ATTEST_TRUSTED_PROXIES` (comma-separated IPs or CIDRs, default `127.0.0.1,::1`). When the peer address is a
  trusted proxy, the identity is the LAST `X-Forwarded-For` item (the one the trusted proxy appended), validated as an IP
  literal; a malformed item attributes the request to the proxy itself. Any other peer is identified by its own address and
  the header is ignored. A caller cannot choose its identity.
- Tests: `TrustedProxyIdentity.test_requester_policy_is_explicit`,
  `TrustedProxyIdentity.test_forwarded_header_rotation_does_not_reset_the_quota_behind_the_proxy` (behind a 127.0.0.1 peer:
  429, then 429 with only the first item changed, then 200 for a different last item),
  `TrustedProxyIdentity.test_untrusted_peer_cannot_choose_its_identity` (three accepted, the fourth 429 whatever the header).
- Deployment: the vhost should overwrite the inbound header at the edge so the application always sees exactly one trusted
  item. In `deploy/yungou/attest.axiqo.xyz.conf`, both `location` blocks (lines 25 and 32):
  `proxy_set_header X-Forwarded-For $remote_addr;` instead of `$proxy_add_x_forwarded_for`. The default
  `ATTEST_TRUSTED_PROXIES` already covers the loopback proxy; set it explicitly in `/etc/attest/attest.env` if another hop is
  ever added.
- Residual: the test peer address is set by an ASGI shim because this starlette's TestClient has no `client=` parameter; the
  policy itself is a pure function (`requester_from`) and is tested directly as well.

### API-02, quota check and run creation not atomic

- Files: `attest/app/db.py` (`create_run_reserving(..., quota=(requester, since_hour, limit))`, `QuotaError`),
  `attest/app/worker.py` (`enqueue(..., quota=)` under `_admit_lock`), `attest/app/server.py` (`start_run`: 429 on `QuotaError`).
- Mechanism: the per-visitor hourly count, the daily budget check and the insert run under the store lock in one method;
  a refused request raises before anything is written. The worker additionally serialises admissions (capacity check, row,
  queue slot) so the queue cannot overfill between check and put.
- Tests: `AtomicAdmission.test_simultaneous_requests_from_one_visitor_admit_at_most_the_quota` (four simultaneous requests
  behind a barrier: `[200, 200, 200, 429]`, three rows, three reservations, three queue items).

### API-03, live cursors fetched outside the lock

- Files: `attest/app/db.py` (`_rows`, `_row_one`, `_write`; `_exec` removed).
- Mechanism: every read materialises its rows while the lock is held; the budget helpers that run inside a caller's lock
  fetch inside it too; no cursor leaves the lock.
- Tests: `MaterialisedReads.test_concurrent_reads_and_writes_on_the_shared_connection_never_fail` (four readers x 120
  iterations of count/list/detail/events/budget plus a concurrent writer: zero exceptions, correct values).
- Runtime: locally Python 3.12.0 / SQLite 3.42.0 (the auditor's probe now records 0/120 failures in both arms, three runs,
  `repro_sqlite_offline.txt`). The deployed interpreter is a Python 3.12 standalone build whose exact Python and sqlite3
  versions could not be read offline; the server readback is pending for the orchestrator.

### API-04, public responses disclose requester addresses and paths

- Files: `attest/app/server.py` (`PUBLIC_RUN_FIELDS`, `public_run`, `public_error`, `tasks`, `health`), `attest/app/static/app.js`.
- Mechanism: every run row leaves the API through an explicit allowlist projection. `requester`, `out_dir`, `error`,
  `error_detail` and `error_ref` never leave the server; `has_artifacts` replaces the directory, `error_code`/`error_public`
  replace the stored message. `/api/tasks` drops `path`. `/api/health` drops `data_dir` and the raw reconciliation records
  (`startup: {reconciled, deduplicated}` counts remain). The client reads `has_artifacts` and `error_public`.
- Tests: `PublicProjection.test_public_responses_carry_no_identity_paths_or_diagnostics` (seeded IP, absolute path and
  marker appear in no response; keys are a subset of the allowlist), `PublicProjection.test_console_page_still_renders_from_the_public_fields`,
  `tests/test_console.py: test_public_rows_carry_no_requester_or_host_paths`.
- Default task estimates now also carry `recorded_runs` and `estimate_provider`, so the estimate shape is the same with or
  without recorded runs.

### API-05, ZIP silently omits manifested files; artifact publication boundary

- Files: `attest/app/server.py` (`contained_file`, `artifact_set`, `ArtifactSetError`, `ZIP_MAX_FILE_BYTES` = 32 MiB,
  `ZIP_MAX_TOTAL_BYTES` = 128 MiB, `bundle_zip`, `artifact`).
- Mechanism: the archive is built from an explicit artifact set. With `manifest.json`: exactly the files it lists plus the
  manifest; a listed file that is missing, a symlink or outside the run directory is an explicit 409 `manifest_mismatch`,
  never a silent omission. Without a manifest (runs recorded before M2): the regular files matching `ARTIFACT_PATTERN`.
  Caps are checked before any byte is written and answered with 413 `export_too_large` naming the limit. The archive is
  written to a `tempfile.TemporaryFile` spool and streamed with a `Content-Length`. Containment (`contained_file`): no
  absolute or dotted segments, no symlink at or below the run directory (a symlinked run directory is refused as a whole),
  resolved path inside the resolved run directory; applied to both the single-artifact route (404) and the ZIP.
- Tests: `ZipExportAndContainment.test_manifested_large_artifact_is_included_and_verifies_or_is_refused_explicitly`
  (a 5,000,000-byte manifested `verify_raw.json` is included and the download verifies against the manifest; with the
  per-file cap at 1,000,000 bytes or the aggregate cap at 4,000,000 bytes the answer is 413 naming the limit),
  `test_zip_never_silently_omits_a_manifested_file` (409), `test_symlinks_and_non_allowlisted_files_are_unavailable_through_both_routes`
  (symlinked `ledger.json` to an outside sentinel, a symlinked `sealed/` directory and `private-notes.env` are in neither
  route; a manifest that lists the link is a 409, never the outside bytes), `test_a_symlinked_run_directory_is_not_served`,
  `test_traversal_shaped_names_stay_closed`.
- Residual: for a manifested run the manifest is authoritative for the ZIP (the run's own declared evidence, which
  `attest check` requires to be complete); the closed `ARTIFACT_PATTERN` allowlist applies to the single-artifact route and
  to runs without a manifest. The caps are constants; the UI shows no partial-export mode because none exists.

### API-06, error-run directories never pruned

- Files: `attest/app/db.py` (`prune_runs(..., keep_errors=10)`), `attest/app/worker.py` (`housekeeping`, called after every
  job in `_run_one` and from the idle timer in `_loop`, `retention_keep_errors`, `housekeeping_s` = 300 s),
  `attest/app/server.py` (`ATTEST_RETENTION_KEEP_ERRORS`, default 10).
- Mechanism: finished rows keep the newest `keep`, errored rows the newest `keep_errors`; only directories inside the
  console's run directory are touched (the run root itself never is); queued/running rows and protected verdicts are left
  alone; rows and accounting stay. Housekeeping runs after every job, successful or not, and whenever the queue has been
  idle for `housekeeping_s`, so an all-failure period still reclaims disk.
- Tests: `ErrorRetention.test_old_error_directories_beyond_the_budget_are_reclaimed_and_protected_items_remain`,
  `ErrorRetention.test_the_run_root_itself_is_never_removed`,
  `ErrorRetention.test_the_failure_path_and_idle_housekeeping_prune_without_a_successful_run`;
  `tests/test_phase1.py: test_prune_keeps_recent_protects_verified_and_imported_evidence` still passes.
- Deployment: `ATTEST_RETENTION_KEEP_ERRORS=10` can be set in `/etc/attest/attest.env` (optional; the default applies).

### API-07, admission without a live worker

- Files: `attest/app/worker.py` (`ensure_alive`, `stop`, `start`, `alive`, `_run_one`, `_settle`, `WorkerUnavailable`),
  `attest/app/server.py` (`start_run` returns 503 before any row or reservation; `health` reports `worker_alive`, `ready`,
  `worker_restarts` and calls `ensure_alive`).
- Mechanism: the loop survives any failure of a run (any `BaseException` other than `SystemExit`/`KeyboardInterrupt` is
  recorded on the row and the loop continues); a `SystemExit` settles the running row (journal-based committed cost or the
  per-run cap) before the thread goes. `ensure_alive()` restarts a thread that died unexpectedly, at most once per 5 s, and
  reports a thread that dies on start as dead; a deliberate `stop()` is respected until `start()`. Admission (`enqueue` and
  `start_run`) refuses with 503 when no live thread exists.
- Tests: `WorkerReadiness.test_admission_requires_a_live_worker_and_resumes_after_recovery` (stopped worker: health
  `worker_alive`/`ready` false, public and team submissions 503, no row, no reservation, no queue item; after `start()`
  admission resumes), `WorkerSupervision.test_ensure_alive_restarts_a_thread_that_died_unexpectedly`,
  `WorkerSupervision.test_the_loop_survives_any_exception_and_records_the_failure`,
  `WorkerSupervision.test_a_dying_thread_settles_the_running_row_before_it_goes`,
  `WorkerSupervision.test_a_row_that_execute_already_finalized_is_left_alone`.

### API-08, one failed final-detail fetch leaves the page stale; half-written bundle is a 500

- Files: `attest/app/static/app.js` (`finishLive`, `finishingState`, `finishFailed`, `pollLive`, `api` error metadata,
  `[data-retry-final]`), `attest/app/server.py` (`run_detail`, `_bundle_incomplete`).
- Mechanism: on a terminal event the final detail fetch is retried up to 5 times with backoff (bounded by the server's
  `retry_after_s`), the header shows "Finishing: loading the record, attempt N of 5", and updates stop only once the terminal
  view rendered or an explicit error with a Retry control is on screen. The server answers an unreadable, partial or
  non-object `proof_bundle.json` with 503 `{"error": "bundle_incomplete", "retry_after_s": 2}` and `Retry-After: 2`.
  (The atomic bundle write in `attest/core/proof.py` is the orchestrator's.)
- Tests: `BundleIncomplete.test_a_partial_bundle_is_a_retryable_503_not_a_500`; node: `terminal_detail_retried` in
  `tests/console_client_test.mjs` (first detail fetch fails, second succeeds: the terminal verdict renders without a reload;
  five persistent failures show the Retry control; Retry renders), run by `ConsoleClient.test_client_functions_behave_as_repaired`.

### API-09, raw errors public

- Files: `attest/app/server.py` (`unhandled`, `public_error`), `attest/app/db.py` (`record_failure`, `ERROR_TEXT`, columns
  `error_code`, `error_ref`, `error_detail`), `attest/app/worker.py` (every failure path uses `record_failure`).
- Mechanism: the global handler returns `{"error": "internal_error", "correlation_id": <uuid hex>}` (also as
  `X-Correlation-ID`) and logs the traceback under that id with logger `attest.app`. Worker failures keep the operator's
  message in `error` and the full traceback in `error_detail` (never published) with a 12-hex `error_ref`; the public form is
  `error_code` plus a neutral sentence, for example `the run failed before completion; reference 1a2b3c4d5e6f`. Rows recorded
  before error codes existed (imported, replayed, legacy) are projected to `run_failed` with the run id as the reference.
- Tests: `SanitizedErrors.test_unhandled_exception_returns_a_correlation_id_and_logs_the_traceback`,
  `SanitizedErrors.test_worker_failure_detail_stays_server_side`,
  `SanitizedErrors.test_legacy_imported_and_replayed_error_rows_are_projected_too`.
- Note: `tests/test_budget.py: ConsoleBudgetAccounting` (read-only) still reads the exception text from the row's `error`
  column through the Store, which is server-side; it passes unchanged.

### API-10, failed patch response copied as success

- Files: `attest/app/static/app.js` (`copyPatch(btn, runId, url)`).
- Mechanism: the clipboard changes only after `res.ok`; a failed response shows `Copy failed (status)` and leaves the
  clipboard untouched; a clipboard failure after a 200 falls back to opening the patch URL.
- Tests: node `copy_patch_requires_ok` (404 and 503 leave the clipboard untouched; 200 copies the exact text and shows
  `Copied`), run by `ConsoleClient.test_client_functions_behave_as_repaired`.

### API-11, queue position counts runs behind the selected run

- Files: `attest/app/worker.py` (`_queued` mirror under `_state_lock`, `position`, `_begin`), `attest/app/server.py`
  (`position` in the events endpoint and in the enqueue response), `attest/app/static/app.js` (`applyLiveUpdate`,
  `liveHeaderText`).
- Mechanism: `position` is 0 while the run executes and N when N runs precede it (the executing run plus the queued runs
  before it), from the worker's ordered mirror; the client never infers a position from the queue size.
- Tests: `QueuePosition.test_position_counts_only_the_runs_ahead` (A running, B and C queued: B 1, C 2; D appended: B still
  1, D 3), node `queue_position_is_authoritative`.

### AC-05, imported bundle loses `cost_usd_committed`

- Files: `attest/app/db.py` (`import_run_dir`, `committed_from_ledger`, `dedupe_imports`, `finalize_interrupted`).
- Mechanism: the bundle's `totals.cost_usd_committed` is stored; a legacy bundle without it has the figure recomputed from
  its call records (known cost, or the reservation when the cost is unknown, plus open reservations, never below the known
  cost), else from the ledger journal in the directory; dedupe carries the committed (and known) cost of a removed duplicate
  to the kept row; finalisation from a bundle uses the same recomputation.
- Tests: `ImportedCommittedCost.test_import_preserves_the_committed_cost_and_the_daily_cap_binds` (same-day bundle with
  `cost_usd` None and `cost_usd_committed` 0.50: the row carries 0.50, a 0.50 cap refuses another run, re-import is a no-op,
  a fresh database rebuilt from the directory reproduces the figure),
  `ImportedCommittedCost.test_legacy_bundles_recompute_the_figure_from_call_records_or_the_journal`,
  `ImportedCommittedCost.test_dedupe_carries_the_committed_cost_to_the_kept_row`,
  `ImportedBudgetAtStartup.test_the_imported_committed_cost_counts_against_today_and_refuses_another_run` (through the
  server's startup import and `/api/health`).

### AC-06, UTC-day accounting

- Files: `attest/app/db.py` (`_nebius_committed`, `BUDGET_POLICY`, module and `Store` docstrings), `attest/app/server.py`
  (`budget.policy` in `/api/health`).
- Policy: a conservative UTC-day cap. A run counts against every UTC day on which it was queued, started, ran or finished
  (its `created_at`, `started_at` or `finished_at` falls on or after the day's start); a queued or running run reserves the
  per-run cap whatever the day. A run that straddles midnight is charged to both days; the cap never undercounts a day.
- Tests: `DayBoundaryAccounting.test_a_run_straddling_midnight_counts_against_the_new_day_before_and_after_it_finishes`
  (created 23:59:59, started 00:01, finished 00:05 with $0.50: the new day's remaining budget is $0.00 before and after it
  finishes; the policy text is in the Store docstring and in the health payload).

### Publication contract, team runs

- Files: `attest/app/db.py` (`visibility` column, `TEAM_PROVIDERS`, `visibility_for`, back-fill at open, `list_runs` and
  `task_estimates` filters), `attest/app/server.py` (`_team_caller`, `_visible_run`, `_current_ref`, token via
  `X-Attest-Token` or `?token=`), `attest/app/static/app.js` (token on reads once accepted, `?token=` on download links,
  history reloaded on sign-in), `attest/app/static/index.html` (the sentence).
- Mechanism: runs of the development gateway (provider `codex`: the team profile, and imported bundles whose provider is the
  gateway) are `team` rows; older rows are back-filled whenever the store opens. Every read route (list, detail, events,
  artifacts, ZIP, the `current` reference in `/api/runs`, `/api/health` and events, task estimates) hides them unless the
  caller presents the team token. `busy` tells the public that a run is executing without naming it; `queue` stays a count.
- Tests: `TeamVisibility.test_anonymous_reads_never_see_the_team_run` (after a team enqueue and a synthetic bundle every
  anonymous route is 404 or omits the run, and no response contains the gateway name or the run id),
  `TeamVisibility.test_the_team_token_reveals_the_team_run_on_every_route`,
  `TeamVisibility.test_imported_development_bundles_become_team_rows_and_old_rows_are_backfilled`;
  `tests/test_console.py: test_team_rows_are_hidden_from_anonymous_readers_and_shown_with_the_token`,
  `test_public_page_and_unauthenticated_responses_name_no_gateway` (now including `/api/runs` and `/api/openapi.json`).
- Residual: a download link carries the token as a query parameter (the browser's history and the nginx access log see it);
  the token lives in page memory only and is never stored. The anonymous `queue` count includes team runs (a number, not a
  reference).

## Schema changes and migration

`runs` gains `visibility TEXT NOT NULL DEFAULT 'public'`, `error_code TEXT`, `error_ref TEXT`, `error_detail TEXT` (the earlier
`cost_committed_usd` and `model_calls` migrations are kept). An existing database is migrated with `ALTER TABLE ... ADD COLUMN`
when the store opens, then `UPDATE runs SET visibility = 'team' WHERE provider IN ('codex')` back-fills existing rows; both
steps are idempotent and run at every start. No row is deleted or rewritten otherwise. The `error` column keeps its meaning
(operator message, server-side); `error_detail` holds tracebacks and is never published.

## Verification

- `.venv/bin/python -m unittest tests.test_console tests.test_phase1 tests.test_audit_console -v`: 59 tests, OK;
  `tests.test_revision4.ConsoleInterruption`: 3 tests, OK; `node --check attest/app/static/app.js`: OK;
  `node tests/console_client_test.mjs`: 3 checks OK (`test-output.txt`). Read-only `tests.test_budget.ConsoleBudgetAccounting`
  also passes against the new worker and store.
- Auditor's reproductions after the repairs: `repro_api_offline.py` stops at its first faulty-behaviour assertion
  (`assert created.status_code == 200` for admission with a dead worker; the server now answers 503 and creates nothing);
  `repro_console_offline.mjs` stops at its first assertion (`copyPatch` now shows `Copy failed (404)` and leaves the clipboard
  untouched); `repro_sqlite_offline.py` records 0 failures in both arms in three runs.

## Residual limitations

- The deployed interpreter's Python and sqlite3 versions were not read (offline); the lock-through-fetch repair does not
  depend on them, but the readback remains to be recorded by the orchestrator.
- The nginx edge still has to be changed to overwrite `X-Forwarded-For` (one line in each `location`, above); until then the
  application's trusted-proxy policy already ignores caller-controlled items because it reads only the last one.
- The restart supervision covers a worker thread that dies; it does not replace process-level supervision (`Restart=on-failure`).
- `ERROR` log lines from `attest.app` go to stderr through Python's last-resort handler (journald in production); no logging
  configuration was added.
- `index.html` asset stamps (`?v=20261019a`) were deliberately left for the orchestrator to bump, since `app.js` changed.
