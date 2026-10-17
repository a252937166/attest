# Attest hardening: verification, budget, disk, arbitration, implementer efficiency (16 Oct 2026)

This round closes the code-review gaps in three areas. Everything here was verified; evidence files are named inline.
Historical run artifacts are preserved; corrected results are recorded separately.

## Phase 1 — verification, budget enforcement, disk protection

### 1a. Unknown or incomplete checks can no longer pass

- The mutation gate now fails `VERIFIED` when mutants were generated but **every one is unknown** (the sandbox could not
  evaluate them), and when so many go unknown that fewer than four were scored. Only a genuine score at or above the
  threshold passes; a changed region with no mutable sites passes with a warning (nothing to detect). Offline test
  `test_all_unknown_mutants_block_verified` (`tests/test_verification.py`).

### 1b. Verifier code and result files are protected from the candidate (prevention, not just detection)

- The sandbox operation now runs as **root**; the sealed supervisor makes the sealed directory and the verifier program
  root-owned and read-only, then runs **each test in a child process under an unprivileged uid (65534)**. Each child
  returns its result over a **pipe the supervisor owns** — there is no shared result file on disk for a candidate to forge.
  The host binding adds a `verifier_isolation_active` check and refuses `VERIFIED` when privilege separation was not active.
- Privilege model confirmed on Nebius Sandboxes (`sandbox-privilege-probe.json`): a root operation can drop children to
  other uids; those children cannot write root-owned files, signal the parent, read its memory or regain root.
- **Real-sandbox adversarial re-run** (`sandbox-adversarial-v3.json`, eight disposable branches): honest accepted; wrong,
  sealed-file tampering, premature `os._exit`, forged result files, forged console text, a hang and a SIGSEGV all rejected.
  `privilege_separation_active: true` and `tamper_prevented_not_only_detected: true` — in the tamper scenario the sealed
  file is **byte-identical** afterward (the candidate's write was denied), where before it was only detected after the fact.

### 1c. Budget is reserved atomically and uncertain calls are counted conservatively

- `Store.create_run_reserving` checks the daily budget and inserts the run **under one lock**, so N concurrent callers
  cannot each pass a stale check: every queued or running Nebius run reserves the per-run cap. The worker **rechecks**
  before execution (a queued run may have waited while others spent). A transport-uncertain model call now carries a
  conservative `reserved_usd`; the ledger reports `cost_usd_committed` (known cost, else the reservation) and the daily
  budget is computed from it, so an uncertain call never undercounts. Offline tests in `tests/test_phase1.py`.

### 1d. Disk monitoring, bounded retention, low-space stop

- The worker refuses new runs when free space is below a threshold (default 500 MB or 7% of the volume); `/api/health`
  reports disk and `accepting_runs`. After each finished run it prunes the oldest console-run directories beyond a cap
  (default 40), **never** touching imported evidence (anything outside the data run directory) and **never** a `VERIFIED`
  run. Offline test `test_prune_keeps_recent_protects_verified_and_imported_evidence`.

### 1e. Interrupted tasks are reconciled after a restart

- On startup the store settles rows left `queued`/`running` by a crash: it finalizes any whose Proof Bundle reached disk and
  marks the rest errored (interrupted). `/api/health` reports what was reconciled. Offline test
  `test_reconcile_marks_interrupted_and_finalizes_from_bundle`.

## Phase 2 — arbitration and implementer efficiency

### 2a. Arbitration of generated-test failures (advisory by default)

When a run is `NEEDS HUMAN` **only** because model-generated tests (sealed and/or adversarial) failed on a candidate that
passed every structural, held-out, mutation and drift check, an independent arbiter classifies each failing test as an
**implementation bug**, a **test defect** or a **contract dispute**. For a set that is entirely test defects it returns a
corrected module, which is re-run under the hardened supervisor and must **pass on the candidate and still fail on the
base** (so a corrected test still discriminates — the anti-abuse check). Arbitration is **advisory by default**: it never
changes the verdict unless apply mode is explicitly set, and it never clears an implementation bug or a contract dispute.
Held-out failures are never arbitrated (they go to a human). Clearing additionally requires that the mutation gate actually
ran and passed, so a sealed failure (which skips the breaker) can only be advisory.

- **Real-sandbox validation with the real arbiter** (`arbitration-sandbox-check.json`): a correct candidate (`f(x)=x+1`)
  falsified by a wrong generated test (`assert f(1)==3`). The arbiter classified it `test_defect` with the contract basis,
  returned a corrected module that **passed on the candidate (5/5) and still failed on the base (5/5 ERROR)**,
  `cleared_module: true`.
- Offline: `test_arbitration_is_advisory_then_clears_in_apply_mode`, `test_implementation_bug_is_not_cleared_by_arbitration`.

### 2b. Implementer efficiency

- `replace_in_file`/`write_file` are **syntax-checked** immediately; an error is reported with a prompt to fix or `undo`.
- A new **`undo`** action reverts the last edit (roll back a bad change instead of patching over it).
- A `finish` with untested edits is **sent back once** with a reminder to run the existing suite first.
- A **turn-budget nudge** appears in the last three turns.
- Measured effect: `semver-is-compatible-pr368-v2` on the Codex profile finished **VERIFIED in 6 turns**
  (`read`, `read`, `replace_in_file`, `run_tests`, `run_python`, `finish`) where an earlier run exhausted 14 turns.
  Evidence: `semver-v2-codex-verified/`.

## Offline suite

`python -m unittest discover -s tests -t .` → **34 tests pass** (`tests/test_core.py`, `tests/test_verification.py`,
`tests/test_phase1.py`).

## Smoke run

`smoke-run-durationkit-codex/`: a full end-to-end run on the hardened pipeline (durationkit, Codex) — `VERIFIED`, all
binding checks including `verifier_isolation_active` pass, 21 sealed methods each in their own privilege-separated process,
mutation 11/12.
