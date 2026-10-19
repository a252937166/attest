# Runtime boundaries and release repairs — BOUND-01..04, REL-01, REL-02 (19 October 2026)

Repairs for six findings of [the boundaries audit](../../attest-audit-2026-10-19/boundaries-findings.md). Everything here ran
offline: synthetic files and child processes of the project interpreter only; no model call, Sandbox API operation, network,
deployment, publication or Git commit. The auditor's folder `reports/attest-audit-2026-10-19/` was not modified (its results
file was hashed before and after the exact reproduction command; identical). The review tree `dist/public` was not rewritten.

| File | What it is |
|---|---|
| `test-output.txt` | `python -m unittest tests.test_core tests.test_external tests.test_audit_boundaries -v`: 48 tests, OK |
| `test-output-implementer-navigation.txt` | `tests.test_revision4.ImplementerNavigation`: 4 tests, OK (its search test adapted to the `re:` contract) |
| `boundaries-repro-after-fix.txt` | the auditor's unmodified `boundaries-repro.py` after the repairs: it stops at its first check with `KeyError: 'linked.txt'`, because the outside link is no longer in the snapshot (the script indexes the key directly; it asserted the faulty behaviour) |
| `repro_checks_after_fix.py`, `repro-checks-after-fix.txt`, `repro-checks-after-fix.json` | the auditor's six expressions evaluated after the repairs, reading the link entry with `.get` so the other five checks run too |
| `export-rules-comparison.txt` | old export rules (the pre-fix script preserved in `dist/public/scripts/`) versus the new rules on the same current tree |
| `export-dryrun-output.txt` | `scripts/export_public.py --out <scratchpad>/export-dryrun` on the full working tree (fail-closed outcome; see REL-01) |

Auditor's six `confirmed` flags after the repairs: `snapshot_reads_outside_symlink` false, `host_regex_exceeds_deadline` false,
`tar_file_limit_after_read` false, `public_export_unscanned_env_and_zip` false, `export_force_can_target_source_root` false,
`guest_stream_cap_applied_after_capture` **true by construction** (explained under BOUND-04).

## BOUND-01 — model-controlled regex on the worker thread

Files: `attest/core/workspace.py` (`Workspace.search`, `_regex_search`, `REGEX_WORKER`, `REGEX_PREFIX`, `SEARCH_TIMEOUT_S`,
`SEARCH_INPUT_BYTES`); `tests/test_revision4.py` class `ImplementerNavigation` (search test only).

Mechanism: `search(pattern, path=None, limit=60)` is a literal, case-sensitive substring search (linear, `pattern in line`),
with the unchanged `path:line: text` output. A pattern starting with `re:` is a regular expression; the expression and the
candidate files (binary files skipped, at most 25,000,000 bytes of text, the rest reported as not searched) are sent as JSON on
stdin to `sys.executable -I -c REGEX_WORKER`, a stdlib-only child that compiles and runs the expression and prints at most
`limit` hits (200 chars each) plus the total count. `subprocess.run(..., timeout=2.0)` kills the child at the deadline and the
action returns `search aborted: the regular expression exceeded 2 s; use a literal search`; the worker thread continues at once.
An invalid expression returns `INVALID ACTION: invalid regular expression: ...` instead of a silent literal search; `re:` alone is
rejected. No regular expression from the model is ever compiled or executed in the orchestrator process.

Acceptance tests (`tests/test_audit_boundaries.py`, class `Bound01SearchIsLiteralByDefaultAndRegexIsBounded`):
`test_literal_search_is_the_default_so_the_pathological_text_returns_at_once`, `test_regex_prefix_runs_in_a_child_and_is_cut_at_the_deadline`
(`(a+)+$` on a 29-byte line returns the abort text in about 2.0 s), `test_long_lines_and_a_large_tree_return_promptly` (2 MB single
line, 400-file tree, quadratic `re:x+y`).

Residual limits: the 2 s deadline is fixed; on a workspace near the 25 MB input bound a benign expression may hit it and the
message tells the model to narrow with `path` or search literally. The literal search has no deadline because its cost is linear
in the workspace, which the import limits bound. The child inherits the process environment (Python's `-I` ignores `PYTHON*`).

## BOUND-02 — snapshots followed symlinks out of the repository

Files: `attest/core/workspace.py` (`snapshot_repo`), `attest/core/external.py` (`import_local` now walks with `snapshot_repo`).

Mechanism: the walk uses `os.scandir` on directory descriptors and identifies every entry with lstat semantics
(`is_symlink()`, `is_dir(follow_symlinks=False)`, `is_file(follow_symlinks=False)`). Directories are opened relative to their
parent descriptor with `O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, files with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK`
(`dir_fd=`), so a link swapped in after the listing is refused by the kernel (`ELOOP`) and a FIFO cannot block; `fstat` must
report a regular file before any read; reads are capped at `max_file_bytes + 1`. Symbolic links, special files and unopenable
entries are skipped and, when the caller passes `skipped=[]`, recorded as `{"path", "reason"}`; `SKIP_DIRS` entries stay silent.
Optional `max_files` and `max_total_bytes` raise `ValueError` naming the limit; `import_local` passes the import limits and
converts them to `ImportRefused`, so import and direct run see exactly the same regular files. The root directory itself may be a
link (the caller chose it); on platforms without descriptor-relative opens a path-based walk with a realpath containment check is
used. Signature kept: `snapshot_repo(repo_dir, max_file_bytes=MAX_FILE_BYTES, skipped=None, max_files=None, max_total_bytes=None)`.
The python-semver example's two dangling `tests/*.py -> ../docs/advanced/...` links are skipped and recorded (they were already
absent from the snapshot, so no frozen digest changes); the harness copy with `symlinks=True` snapshots identically.

Acceptance tests (class `Bound02SnapshotNeverFollowsLinks`): `test_outside_file_and_directory_links_and_broken_links_are_skipped_and_recorded`,
`test_a_link_swapped_in_between_listing_and_open_is_refused_by_the_kernel`, `test_special_files_are_skipped_without_blocking_and_limits_name_themselves`,
`test_import_local_and_the_direct_snapshot_see_the_same_regular_files`, `test_the_semver_example_links_are_skipped_not_fatal_also_in_a_harness_copy`.

Residual limits: a hard link to an outside file is a regular directory entry and cannot be distinguished from a copy (same as
`import_local` before). Materializing in-repository links as copies (what the tarball import does) is deliberately not done for
local directories; a repository that needs such a file has it as a regular file.

## BOUND-03 — archive limits applied after decompression

Files: `attest/core/external.py` (`extract_tarball`, `_safe_member`, `LIMITS["max_tar_members"]=20000`, `LIMITS["max_link_entries"]=500`).

Mechanism: the tarball is iterated header by header (`for member in archive`, no `getmembers()`); the header count, the file
count and the link-entry count are bounded; each file's declared size is checked against the per-file limit and the running
total against the 25 MB limit BEFORE its bytes are read; each read is `extractfile(member).read(size + 1)` and a delivered length
different from the declaration refuses; duplicate paths refuse; unsafe names (`..`, absolute, empty parts) refuse for links as well
as files, because a link may be materialized at that path; `tarfile.TarError` becomes `ImportRefused`. Nothing is written until the
whole archive has passed; the in-tree link materialization and the final `_check_tree` are unchanged.

Acceptance tests (class `Bound03TarballIsStreamedAndBoundedBeforeReading`): `test_an_oversized_declared_member_is_refused_before_any_read`
(the auditor's 64-byte/16-byte shape: zero reads), `test_the_total_bound_is_checked_against_declarations_and_every_read_is_capped`,
`test_excessive_link_entries_and_headers_are_refused_before_contents_are_loaded`, `test_duplicate_paths_unsafe_link_names_and_unreadable_archives_refuse`,
`test_a_highly_compressible_archive_stays_within_a_small_memory_ceiling` (40 MiB declared in a few KB of gzip: tracemalloc peak under 8 MiB).
The pre-existing synthetic python-semver-shaped tests in `tests/test_external.py` (materialized in-tree links, limits, unsafe names) still pass.

Residual limits: the compressed download is still held in memory up to the existing 80 MB download cap; the member bound counts
headers of every type, so a tarball of more than 20,000 entries (directories included) is refused.

## BOUND-04 — guest stream cap applied after unbounded capture

Files: `attest/sandbox/tf_sandboxes.py` (`GUEST_RUNNER`, now `attest-guest/3`; host `_execute` and `_job`); `tests/test_external.py` (runner name).

Mechanism: each step runs with `subprocess.Popen(..., start_new_session=True)` on two `os.pipe()` pairs; two `Drain` threads read
the pipes to EOF while the step runs, keeping only the first and the last `cap // 2` bytes of each stream and counting every byte
(`stream_cap_bytes`, default 65536, unchanged); when a stream passes `output_limit_bytes` (job field, default 64,000,000) the step
is "exhausted". On the deadline or on exhaustion `os.killpg(SIGKILL)` takes the whole session, followed by one bounded wait
(`GRACE_S = 2.0`) for the leader; the pipe readers are then joined with one bounded wait, and if a descendant still holds the pipes
the group is killed (again) and joined once more; on Linux the step's session is swept through `/proc` for stragglers. Every step
record keeps `stdout`, `stderr`, `exit_code`, `timed_out`, `duration_s` (the host reads those) and adds `output_exhausted`,
`stdout_bytes`/`stderr_bytes` (bytes observed), `stdout_truncated`/`stderr_truncated`, and `cleanup` (`killed_group`, `reaped`,
`pipes_closed`, `descendants_killed`). The truncation marker states what was dropped: `...[truncated: N of M bytes omitted]...`.
The host adapter turns `output_exhausted` into a step error, so an exhausted step can never count as a pass. The gzip/base64
transport, the job shape (one added key) and the report markers are unchanged.

Acceptance tests (class `Bound04GuestRunnerCapturesBoundedlyAndCleansUpGroups`, all running the real `GUEST_RUNNER` with
`python -I -c`): `test_a_noisy_child_is_drained_into_bounded_buffers_and_truncation_is_reported` (80 MiB written by the child; the
runner's peak RSS stays within 40 MB of the quiet baseline, measured 8.7 MB above it here), `test_output_exhaustion_kills_the_process_group_and_is_recorded`,
`test_a_grandchild_holding_the_pipes_is_killed_within_the_documented_grace` (about 2.1 s), `test_a_timeout_kills_the_whole_group_including_a_sleeping_grandchild`
(1 s timeout, about 1.0 s), `test_a_large_normal_result_is_read_in_full_on_both_streams` (300 KB each under a 2 MB cap), `test_the_host_adapter_reads_the_report_and_flags_exhaustion_as_a_step_error`.

Why the auditor's sixth flag stays true: its expression is `stdout_bytes == 8193 and len(stdout) < 1100`. In `attest-guest/3`
`stdout_bytes` is the number of bytes OBSERVED on the stream (a truthful count) while at most `stream_cap_bytes` of them are ever
held, so for the 1,024-byte cap the record reads 8193 observed, 1071 chars kept, truncated: the expression cannot distinguish
observed from held. The memory bound is established by the RSS measurement above, not by that expression.

Residual limits: a descendant that calls `setsid()` leaves the session and escapes `killpg` and the `/proc` sweep (the sandbox VM
is disposable, so it dies with the branch); on macOS there is no `/proc` sweep (tests skip nothing but assert only group
semantics); kills are immediate `SIGKILL` (no `SIGTERM` phase); worst-case extra wait per step is three grace periods (6 s);
a killed step reports `exit_code: null`, as before for timeouts. The runner digest recorded in `FREEZE.md` (`attest-guest/2`,
`80999537…`) changes with this revision (now `attest-guest/3`, `db8e2a76…`); the freeze is the orchestrator's step.

## REL-01 — export copied files its scanner never inspected

Files: `scripts/export_public.py` (`exclusion_reason`, `EXCLUDE_NAME_GLOBS`, `ARCHIVE_SUFFIXES`, `DATABASE_SUFFIXES`, `BINARY_SUFFIXES`,
`ALLOW_NAMES`, `ARCHIVE_POLICY`, `decode_for_scan`, `copy_tree`, `scan`, `scan_zip`, `SCAN_PATTERNS`, `build_export`).

Mechanism: the top-level allowlist is unchanged; at every depth, names matching `.env`, `.env.*`, `*.env`, `*.pem`, `*.key`,
`*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `*.ppk`, `id_*` and suffixes of archives (`.zip .tar .gz .tgz .7z .bz2 .tbz .xz .txz .zst .rar .jar .war .whl .egg`),
databases (`.db .db-shm .db-wal .sqlite .sqlite3 .sqlitedb`) and binaries (`.pyc .pyo .pyd .so .dylib .dll .exe .o .a .class .bin .img .iso .dmg .deb .rpm`)
are excluded and listed in `EXPORT.json["excluded"]`; `attest.env.example` (empty values) is the documented exception. Every file
that decodes as UTF-8 is redacted whatever its suffix (an unchanged file is copied byte for byte; a redacted one is rewritten
without newline translation). The final scan covers every staged file: UTF-8 text, or text with replacement characters when the
file does not decode but holds no NUL byte; only an undecodable file with NUL bytes is skipped as binary. Patterns added to the
existing set: PEM private keys (`-----BEGIN ... PRIVATE KEY-----`), written-out bearer tokens
(`authorization: bearer <16+ chars>`, same line) and `token=`/`secret=`/`secret_key=`/`password=` values of 16+ characters on
the same line. Any archive in the staged tree is a hit under the default `ARCHIVE_POLICY = "exclude"`; under `"inspect"` a `.zip`
is inspected member by member (`scan_zip`: bounded member count, declared sizes checked before reading, reads capped at the
declaration plus one, excluded names and binary members are findings, one nested level), every other archive type stays
excluded. An unreadable file is a hit. The scan runs on the exact staged tree and on the record text; any hit fails the export.

Acceptance tests (class `Rel01ReleaseExclusionsAndWholeTreeScan`): `test_credential_environment_archive_database_and_binary_files_are_excluded_at_every_depth`,
`test_every_staged_file_is_scanned_whatever_its_name` (extensionless, `.txt.bak`, PEM, `token=`, Latin-1 text; PNG skipped; header idioms clean),
`test_zip_members_are_inspected_with_bounded_decompression_and_archives_are_excluded_by_default` (nested ZIP member, oversized
compressible member, `.env` member), `test_main_fails_closed_on_a_planted_secret_and_leaves_the_previous_export_intact`.

Real-tree dry run (`export-rules-comparison.txt`, `export-dryrun-output.txt`): on the current working tree the new rules exclude
exactly four files, the evidence archives `reports/attest-deployment-2026-10-15/judge-run-proof-bundle.zip`,
`reports/attest-deployment-2026-10-16/judge-run-proof-bundle.zip`, `reports/attest-deployment-2026-10-17/rle-encode-20261015T181805Z.zip`
and `reports/attest-deployment-2026-10-17/public-bundle-durationkit-units-001-20261015T185629796814Z.zip`; every other exported
file is byte-identical to the old rules' output (the `REDACTION.json`/`manifest.json` pairs differ only because the public copy of
the old script had its `private vault` literal redacted, which changes the recorded rule text). The 157 exported bundles pass
`attest check`. The dry run then fails closed on one hit: line 44 of `tests/test_audit_console.py` (a concurrent repair) assigns a module
constant named `TOKEN` a 20-character synthetic value in one literal, which has exactly the shape the new `token=` pattern
catches; that constant has to be assembled at run time from shorter pieces (the convention `tests/test_external.py` and
`tests/test_audit_boundaries.py` follow) before the public export can succeed.
This evidence folder and `tests/test_audit_boundaries.py` pass the copy-and-scan path with zero hits.

Residual limits: the scan is pattern-based and fails closed, so synthetic token-shaped fixtures block the export until they are
assembled at run time; files that are binary by the NUL rule (PNG screenshots, Sphinx `.inv` inventories) are copied unscanned,
as before; the known gateway key shape is redacted rather than blocked, by the existing design; allowing the four evidence zips
requires the explicit decision `ARCHIVE_POLICY = "inspect"` (then each member is inspected and any finding fails the export).

## REL-02 — a destination could overlap and erase its sources

Files: `scripts/export_public.py` (`destination_problem`, `build_export`, `publish`, `main`, `EXPORT_RECORD`).

Mechanism: `main` resolves `--out` (relative to the project root; an absolute path as given) and refuses with exit 2, before
anything is created or deleted, when the destination is the project root (`.`, `""`, the absolute root), an ancestor of it
(`..`, `/`), inside the project anywhere but strictly under `dist/` (`src`, `dist` itself), a file, a directory holding `.git`
without `EXPORT.json` beside it (a Git checkout this tool did not produce), or a non-empty directory without `EXPORT.json` (not a
previous export). A previous export needs `--force`; an empty directory outside the project needs nothing. The export is built in
a sibling temporary directory (`<name>.staging-*` next to the destination), traced, verified and scanned there; on any failure the
staging directory is removed and the previous export is untouched; on success the previous export's children except `.git` are
removed and the staged children are renamed into place.

Acceptance tests (class `Rel02ExportDestinationsAreRefusedBeforeDeletion`): `test_root_ancestor_and_nested_source_destinations_are_refused_with_exit_2`
(ten destinations, sentinel survives, foreign `.git` and foreign non-empty directories refused), `test_a_normal_export_replaces_only_the_previous_export_and_keeps_its_git`.

Residual limits: a hand-made directory containing an `EXPORT.json` is treated as a previous export; the staging directory lives
next to the destination (under `dist/` for the default destination), so the destination's parent must be writable.
