# Accounting repairs for the revision-5 follow-up review (19 October 2026): R5-01, R5-05, R5-06

Repairs to three findings of [`reports/attest-revision5-review-2026-10-19/README.md`](../../attest-revision5-review-2026-10-19/README.md)
and its [accounting review](../../attest-revision5-review-2026-10-19/accounting-review.md): the partial-settlement framing failure
(R5-01, reopened AC-03), the CLI and console entry points that built the paid provider without the promised 22-call cap (R5-05), and
the comparison validity that compared the provider name and limits but not the effective roles, effort and sampling (R5-06). The
harness's confusion labels were also extended so that a hold without a patch is a refusal judged by the ground truth. Nothing under
`reports/attest-revision5-review-2026-10-19/` was modified; the review's reproduction script was copied byte for byte into this folder
and run from the copy. Everything here was produced offline: fake transports, temporary directories, a socket tripwire in every test
and in the reproduction; no model call, no Nebius or Sandbox API, no credential read, no deployment, no git commit.

## Files in this folder

| File | Content |
| --- | --- |
| `README.md` | this map: finding, files, mechanism, acceptance tests, residual limitations |
| `tests-output.txt` | `python -m unittest tests.test_audit_accounting tests.test_budget tests.test_reliability.NebiusReasoningRunaway -v`: 49 tests, all passing (34 before this change set, 15 added) |
| `partial-settlement-repro-scratch-copy.py` | the review's `partial-settlement-repro.py`, byte-identical (sha256 `7e99b70186b8fc5bee9e807e6c621b49e5d92d70ff4581044158bf18534d22e3`, the same as the original's) |
| `run-partial-settlement-repro.py` | runs the scratch copy against the repaired tree; it only sets `__file__` to the depth the review's script expects for its project root and checks the copy's digest against the original's |
| `partial-settlement-repro-after-fix-results.json` | the scratch copy's output: `reproduced` is **false**; the journal recovers $0.07 (both reservations) against $0.06 in memory, where the review observed $0.02 against $0.06 |
| `partial-settlement-repro-after-fix.stderr.txt` | the two digests printed by the runner |

Re-run from the project root:

```bash
.venv/bin/python -m unittest tests.test_audit_accounting tests.test_budget tests.test_reliability.NebiusReasoningRunaway -v
.venv/bin/python -B reports/attest-revision5-repairs-2026-10-19/accounting/run-partial-settlement-repro.py
```

The complete offline suite was also run once after the change set (`python -m unittest discover -s tests -t .`): 349 tests, no failure.

Digests of the changed sources (sha256): `attest/ledger.py` `682b0420d48aa1a958b4090897a40686ffc2bcc6e29cc3bfadbedc4ce27e6ffd`,
`attest/models/nebius_tokenfactory.py` `95b423cb499df6191f016f75e4ef39634c6cf86f05f9adc6da82ce0805d33ed9` (both also recorded by the
reproduction's `source_sha256`), `attest/cli.py` `453df3bb9db3f45c8296549c2f75cf807adf6ca9a02fa24755190e35f6351ecb`, `attest/app/worker.py`
`1a58c7795a5ea414318961c88f37eef06b2f6c24ea2cfbfe98fabacb84122c1f`, `scripts/run_evaluation.py` `5af2b4989b2b93db7a9c37b4e1d654cb1e8b703bba47c8cfcf3a0e0c36bec5a3`,
`scripts/render_evaluation.py` `4713b781b4b49659012960ce7950cac2bedba6784ce1b74d4175ea3f4a26d4d3`. Other change sets edit other files
concurrently; these digests describe the files of this change set at the time this folder was written and will not match the next pin
if those files change again.

## Why the review's reproduction now reports `reproduced: false`

The script asserts the faulty behaviour: `reserve()` returns `r2` AND the in-memory committed total is $0.06 AND the journal read back
recovers only $0.02 with one unparsable line. Against the repaired tree `reserve()` still returns `r2` (the disk is healthy again, so the
reservation is taken), the in-memory total is still $0.06 (the known $0.01 of the first call plus the open $0.05), but the journal read
back recovers **$0.07**: the cut settlement line was terminated by a `journal_repair` record before `r2` was appended, so `r1` stays open
at its $0.02 bound (its settlement is lost) and `r2` is recovered in full. The recovered figure is never below the in-memory one. The
one unparsable line is the cut prefix, as before; `journal_failure_count` is 1, as before.

## Findings

### R5-01: a partial settlement corrupted the framing of the next reservation

Files: `attest/ledger.py` (tail recovery, verification, `journal_degraded`, binary-safe `read_journal`), `attest/models/nebius_tokenfactory.py`
(`describe()` reports the journal state; the existing LedgerError-to-halt conversion is kept).

Mechanism. Before every append the ledger reads the last byte of the journal (`_tail_state`). A non-empty file that does not end with a
newline is a line a failed append cut short; `_repair_tail` terminates it durably and appends a `journal_repair` record (`at_utc`, a
note that the cut record is lost and that any reservation it would have settled stays open at its bound, the cut line's length and its
head). Every append (`_write_verified`) is then written, flushed, fsynced, closed and read back from the offset where it started: the bytes
must equal what was written and the byte before the offset must be a newline (or the offset must be 0). A reservation whose repair,
write or verification fails raises `LedgerError`, records nothing in memory, and the Nebius provider turns it into a definite
`ModelError` and halts the instance (no further HTTP call). A settlement whose repair, write or verification fails is counted in
`journal_failures` and sets `journal_degraded = <reason>`; the next `reserve()` runs the same repair and verification and clears the
flag only once its own line read back intact. `attach_sink` goes through the same path (an existing cut tail is repaired before the
header). `read_journal` decodes with replacement, counts unparsable lines and `journal_repair` records (`journal_repairs`) and reports
whether the file ends with a newline (`tail_framed`); it never raises on a tail cut inside a multi-byte character. `Ledger.totals()` and
`to_dict()` carry `journal_repairs` and `journal_degraded` next to `journal_failures`; `NebiusTokenFactory.describe()` carries
`journal_degraded`, `journal_failures` and `journal_repairs`.

Acceptance tests (`tests/test_audit_accounting.py`, class `SettlementTailRecovery`):
`test_the_reviews_sequence_recovers_both_reservations` (the review's exact sequence at the ledger level: r1 intact, settlement writes
a prefix without newline and raises, disk healthy, `reserve()` returns r2, the journal recovers r2 in full and keeps r1 open, recovered
$0.07 against $0.06 in memory, one repair record between the terminated prefix and r2, `journal_degraded` cleared);
`test_the_sequence_through_the_provider_dispatches_only_a_verified_reservation` (the same through the real `NebiusTokenFactory` with
`request_json` mocked: the first request settles partially, the second request is dispatched because its reservation was written after
the repair and verified, the transport then "dies" before any settlement, and the journal recovers the second reservation with the
first still at its bound; `describe()` shows one failure, one repair and no degradation afterwards);
`test_a_tail_cut_inside_a_multibyte_character_is_repaired_and_read_back` (a tail cut inside a two-byte character is read without
exception before and after the repair; the repair terminates exactly at the cut and reports its length and head);
`test_normal_appends_show_no_repair_and_read_back_byte_identical` (positive control: five reservations, five settlements with non-ASCII
text and one sandbox operation; zero repairs, zero failures, the file is byte-identical to the concatenation of every append);
`test_a_failing_tail_repair_halts_the_provider_before_dispatch` (the disk stays unwritable after the cut settlement: the next
reservation's repair fails, the provider halts with a definite error, the stub is called exactly once and the third request is refused
without a call; r2 exists neither in memory nor on disk);
`test_a_line_that_reads_back_differently_is_refused_or_degrades` (a write whose bytes on disk differ from the bytes given: a
reservation is refused with nothing recorded, a settlement degrades the ledger, the next verified reservation clears it).
`CallCap.test_provider_serves_exactly_the_cap_and_refuses_the_next_call_before_dispatch` doubles as a 22-settlement positive control
(no repair, nothing unparsable, framed tail). The existing AC-03 tests (`ReservationDurability`) pass unchanged.

### R5-05: the CLI smoke and the console built the paid provider without the promised 22-call cap

Files: `attest/cli.py` (`--max-calls` on `run` and `preflight`, `NEBIUS_DEFAULT_MAX_CALLS = 22`, `effective_max_calls`, `build_parser`,
`parse_args`, `build_provider(..., max_calls)`), `attest/app/worker.py` (`PER_RUN_MAX_CALLS_ENV = "ATTEST_PER_RUN_MAX_CALLS"`,
`DEFAULT_PER_RUN_MAX_CALLS = 22`, `per_run_max_calls()`, the provider construction in `build_runtime`), `attest/models/nebius_tokenfactory.py`
(the refusal names the cap and states that the request was not sent; `describe()` adds `call_cap_policy`).

Mechanism. `attest run` and `attest preflight` take `--max-calls` (an integer of at least 1); when it is not given the parsed arguments
carry 22 for `--provider nebius` and `None` for codex, and `build_provider` applies the same default so a Nebius provider built by the CLI
is always capped. The console worker reads `ATTEST_PER_RUN_MAX_CALLS` when it builds a run's provider (default 22; a value that is not an
integer or is below 1 is logged and keeps the default, so a misconfiguration never removes the cap). The provider refuses the call that
would exceed the cap before dispatch with `ModelError("per-run call cap 22 reached (22 calls recorded in this run); the request was not
sent")`, a definite refusal (`uncertain=False`); the cap counts every call record of the run, failed calls and retries included, as before.
`describe()` reports `max_calls` (the effective cap) and `call_cap_policy`, and the pipeline records `describe()` as the bundle's
`profile.provider`, so every bundle shows the cap that governed its run.

Acceptance tests (`tests/test_audit_accounting.py`, class `CallCap`):
`test_provider_serves_exactly_the_cap_and_refuses_the_next_call_before_dispatch` (22 `structured` calls with valid priced answers, the
23rd and 24th refused with zero further stub calls, the message names the cap, `describe()["max_calls"] == 22`, the provider is not
halted); `test_cli_defaults_the_cap_to_22_for_nebius_and_none_for_codex` (parser default 22 for nebius, None for codex and for the
default provider, explicit values kept, 0 refused, `build_provider` default and explicit); `test_cli_run_passes_the_cap_to_the_provider_it_builds`
(`attest run --provider nebius` with and without `--max-calls 5`, the pipeline replaced by a recorder: the provider handed to the
pipeline carries 22 or 5 and reports it in `describe()`); `test_console_worker_builds_the_paid_provider_with_the_environment_cap`
(`Worker.build_runtime` with `load_secret` and `project_id` patched: `ATTEST_PER_RUN_MAX_CALLS=9` gives 9, an unset variable gives 22,
an unusable value gives 22 with a warning).

### R5-06: role and effort overrides escaped the comparison validity

Files: `scripts/run_evaluation.py` (`PROFILE_KEYS`, `PROFILE_ENVIRONMENT`, `provider_profile`, `profile_differences`, `profile_refusal`,
`registered_profile_conflicts`; `comparison_validity`, `one_system`, `run_cell`, `run_batch`), `scripts/render_evaluation.py`
(`profile_summary`, the provenance line).

Mechanism. `provider_profile(describe_dict)` selects the stable keys of a provider description: for `nebius_tokenfactory` the provider,
roles, reasoning_effort, temperature, max_tokens, usd_cap, max_calls, thinking_roles and send_thinking_flag; for `codex_gateway` the
provider, the roles spelled `model:effort` per role and `base_url_sha256`; any other provider contributes its name only. The profile is
recorded in `schedule.json` as `provider_profile` at registration (next to the full `provider_detail`), and the registration log names
any of `ATTEST_NEBIUS_ROLES`, `ATTEST_NEBIUS_REASONING_EFFORT`, `ATTEST_NEBIUS_THINKING_FLAG`, `ATTEST_CODEX_ROLES` present in the
environment. Every completed row carries `provider_profile` taken from its bundle's `profile.provider` (the ERROR path too); the
`not_run` row of a drifted cell carries the profile actually built. `comparison_validity` marks a task invalid when a row's profile
differs from the registered one and names the differing keys, per role (`roles.implement 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B'
differs from the registered 'nvidia/nemotron-3-super-120b-a12b'`); rows without a profile (written before this revision) and schedules
without one are not judged on it, like the earlier execution-profile fields. On resume `run_batch` builds the provider for the restored
configuration in this process, computes its profile and refuses with exit code 2, naming the differences and the environment variables,
before `runtime_provenance`, the governor or any cell exists; the schedule's `resumptions` entry records that the check passed. At the
start of every cell `one_system` compares the profile of the provider it actually built with the registered one and returns a `not_run`
row with the reason when they differ, before the executor, the run directory or any paid call exists. `render_evaluation.py` appends the
registered profile to the provenance line (`provider profile: provider=...; roles implement=... seal=...; reasoning_effort ...;
temperature=0.2; max_tokens=16000; usd_cap=0.5; max_calls=22; ...`).

Acceptance tests (`tests/test_audit_accounting.py`, class `ProviderProfileFreeze`):
`test_profile_selects_the_effective_configuration_and_names_role_drift` (the profile of a real offline `NebiusTokenFactory`, its
stable keys, the exclusion of state and policy prose, the JSON round trip, `ATTEST_NEBIUS_ROLES=implement=<Nano>` and
`ATTEST_NEBIUS_REASONING_EFFORT=high` named per role, the codex spelling, unknown providers);
`test_a_row_with_another_implement_model_invalidates_the_comparison` (a row whose bundle profile shows the Nano implementer invalidates
its task and names `roles.implement`; equal and round-tripped rows and rows without a profile stay valid; the rendered report shows the
profile and the invalid task);
`test_resume_under_a_role_override_is_refused_before_any_cell` (negative: a registered Nebius schedule, built with the real provider
class offline, resumed with `ATTEST_NEBIUS_ROLES=implement=nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` and separately with
`ATTEST_NEBIUS_REASONING_EFFORT=high` in the environment is refused with exit code 2, the refusal names the differing role or effort and
the environment variables, nothing is constructed, the report and schedule are untouched; positive: the unchanged environment resumes,
runs the missing cell, stays a valid comparison and records the profile check in `resumptions`);
`test_a_cell_whose_provider_differs_from_the_registration_is_not_run` (per-cell: a drifted effort gives a `not_run` row naming the
difference, no executor, no run directory, no request, nothing committed; positive control: a provider carrying the registered profile
runs the cell and its row records that profile). `FinishedButUnreportedRun.test_the_finished_run_is_counted_exactly_once_and_the_cell_runs_again`
now also asserts that the schedule registers the profile and every row of a real `one_system` run carries it.

### Confusion labels: a hold without a patch is a refusal

Files: `scripts/run_evaluation.py` (`classify`, the schedule's `definitions`), `scripts/render_evaluation.py` (summary header, footer text).

Mechanism. `classify` labels `INFEASIBLE` as before and additionally `NEEDS HUMAN` with `changed_paths == 0` and an unfinished implementer
as a refusal of the task: `true_reject` when the task's ground truth is `unsatisfiable`, `false_refusal` otherwise. A NEEDS HUMAN with a
patch keeps the accepted/correct logic; NO CHANGE stays `no_patch`; a row without `changed_paths` keeps the existing logic. The schedule's
definitions of `true_reject`, `false_refusal`, `not_run` and `comparison_invalid` were updated and `provider_profile` added; the renderer's
summary column reads "False refusal (hold without a patch on a satisfiable task)" and its footer states the rule.

Acceptance test: `HoldLabels.test_a_hold_without_a_patch_is_a_refusal_judged_by_the_ground_truth` (both ground truths, the judge's
view of the unmodified repository ignored, a NEEDS HUMAN with a patch judged on the patch, a finished implementer that changed nothing
kept under the existing logic, INFEASIBLE and NO CHANGE unchanged, a legacy row, the summary counts and the rendered header and footer).
`tests/test_revision4.py::HarnessLabels` was not edited and passes.

## Changes needed outside this change set

- `FREEZE.md`, proposed paid work, "Smoke test" row: the entry point and its flag should be spelled out so that command, schedule, proposal
  and runtime description agree, for example
  `python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider nebius --usd-cap 0.5 --max-calls 22` and the
  same with `--task examples/eval/rle-encode/task.json`. The CLI now defaults to 22 for nebius; the explicit flag makes the promise visible
  in the command itself. `README.md` line 145 (`python3 -m attest run ... --provider nebius --usd-cap 0.5`) should carry `--max-calls 22`
  for the same reason, and the CLI section (line 120) can list `--max-calls`.
- The console deployment should set `ATTEST_PER_RUN_MAX_CALLS=22` explicitly in the service environment (the default applies without it)
  and `attest/app/server.py` could surface `per_run_max_calls()` next to the USD caps in its health or configuration output so the console
  states the cap it enforces; neither is required for enforcement.
- Bundles now carry `profile.provider.max_calls`, `call_cap_policy`, `journal_degraded`, `journal_failures` and `journal_repairs`, and the
  ledger carries `journal_repairs`/`journal_degraded`; the console's run detail could show `journal_degraded` and `journal_repairs` for a
  run, and any documentation of the journal format should mention the `journal_repair` event.
- A new pin is needed (the package and harness digests changed); the frozen record is not modified in place.
- Earlier evaluation reports keep the `confusion` labels they recorded; applying the extended hold rule to the M5 result needs a
  re-labelling pass over its rows, which this change set does not perform.

## Residual limitations

- Read-back verification proves that the operating system holds the bytes that were written; the fsync before it asks the device to
  store them, which is covered as far as the device honours fsync. A device that acknowledges and later loses the write is not detected.
- A cut record is lost, not reconstructed. A lost settlement leaves its reservation open at its bound (an overstatement, reconciled against
  the provider's billing, visible as an open reservation and a `journal_repair` record); a cut reservation line whose request was never
  sent is not counted and costs nothing. The repair record carries the cut line's length (at most 65,536 bytes are examined) and its head.
- `journal_degraded` is per ledger, that is per run, and is cleared only by a verified reservation; a run that settles without reserving
  again keeps the flag in its totals, which is the honest reading (its last settlement is not in the journal).
- The call cap counts call records (failed calls and retries included), as the harness has always done; a run with provider failures
  reaches it with fewer successful calls.
- Schedules registered before this revision carry no `provider_profile`; resuming them logs that nothing is compared, and such batches
  run their frozen harness copy in any case. They should be registered anew rather than resumed.
- The codex profile compares the roles with their effort and the gateway URL digest; the gateway's pacing policy and its catalog are
  operational state recorded in provenance, not part of the comparison.
- The acceptance tests build the real `NebiusTokenFactory` offline (no request leaves at construction) and run the real pipeline with the
  offline fake provider; no Nemotron bundle was produced, so a real bundle's recorded profile has not been observed under this revision.
