# Milestone M1: close the verifier bypass, bind the suites, fix the evaluation method (16 Oct 2026)

Scope: items 1.1 to 1.6 of `reports/attest-competitive-review-2026-10-16/README.md`, section 5. Everything ran on the
Codex gateway (team allowance), Nebius Sandboxes (no USD) and offline fixtures. **No Nebius inference was spent.** The
live console at `attest.axiqo.xyz` was not redeployed; the UI is unchanged until milestone M3.

Evidence files in this folder are named inline. Historical runs and reports are untouched; corrections are recorded
separately in `reports/attest-evaluation-2026-10-16/CORRECTIONS.md`.

## 1. What changed

| Item | Change | Evidence |
| --- | --- | --- |
| 1.1 Verification order | The verify branch runs the sealed supervisor and nothing else; the pipeline aborts if its first step is not the supervisor. The repository's own suite and the held-out suite run afterwards in their own disposable branches. | `tests/test_verification.py::test_supervisor_is_first_and_repo_suite_runs_in_its_own_branch`; real run `runs/balanced-brackets-20261016T192809Z` (operations `verify`, `existing`, `heldout` are three separate sandbox operations) |
| 1.1 Legacy order recorded as tamper | Supervisor v4 scans every import-path root for `sitecustomize`/`usercustomize` before and after the suite and hardens those roots (root-owned, `0755`). A hook planted by a root step before the supervisor is recorded by the new binding check `no_startup_hooks_on_import_path` and flips the must-fail canary. | `sandbox-adversarial-v4.json`, scenario `legacy_order_plant_from_existing_step` (rejected; both checks failed) |
| 1.2 Canaries | Two verifier-injected tests (one must pass, one must fail) run after every supervised suite in a child that has imported the first test module. Blanket forgery flips the must-fail canary; a flipped canary is tampering and is never arbitrated. Mutant branches run without canaries by design. | `sandbox-adversarial-v4.json`, scenario `forge_all_ok`; `tests/test_m1.py::RealSupervisorLocally` runs the real supervisor and child locally with an honest and a forging candidate |
| 1.2 Static tamper scan | Added lines of the patch are scanned for 19 construct classes (import machinery, frame introspection, raw fd writes, process exits, start-up hooks, names of verifier files, ...). Warnings only, in the bundle and `PROOF.md`. | `attest/core/tamper.py`; `tests/test_m1.py::TamperScan`; `test_tamper_scan_warns_on_suspicious_added_lines` |
| 1.3 Bound repository suites | For unittest repositories whose static discovery of the frozen test modules reproduces the baseline's test IDs, the existing and held-out suites run through the supervisor (one child per test as uid 65534) and are bound to the frozen digests. Otherwise they are parsed from console output. Every gate records `evidence_class` (`bound`, `stdout`, `model`). | `runs/balanced-brackets-20261016T192809Z/proof_bundle.json`: `existing_suite` bound (2 of 2, binding ok), `heldout_suite` bound (6 of 6, binding ok); dry-run bundles for `rle-encode`, `roman-to-numeral`, `balanced-brackets`, `durationkit-units-001` (bound) and `semver-is-compatible-pr368-v2` (pytest, `stdout`, labelled) |
| 1.4 Fail closed | A patch with no mutable sites passes the mutation gate only with an adversarial suite of at least six tests; the latent `adversarial.skipped` pass path is removed; an adversarial binding failure is a named reason. | `test_no_mutable_sites_fails_closed_with_a_thin_adversarial_suite`, `test_no_mutable_sites_passes_with_warning_when_adversarial_suite_is_real`, `test_adversarial_result_has_no_skipped_fail_open_path` |
| 1.5 Harness | `scripts/run_evaluation.py` pre-registers every cell in `schedule.json` before any run, strips `heldout_tests` from the task given to both systems, judges through the bound path when possible, reports every scheduled cell (completed, infrastructure error, not run), defaults to Codex, refuses `--provider nebius` without `--approve-usd` and `--max-calls`, stops on the batch cap, three consecutive infrastructure errors or any uncertain operation. `scripts/merge_eval.py` refuses to run. The Nebius provider gained a per-run call cap. | section 4 below; refusal transcript in section 4 |
| 1.6 Corrections, usage, store | `CORRECTIONS.md` next to the original evaluation; `scripts/usage_report.py` (unique runs by bundle `run_id`, by provider and day, optional console store); the store recognises its own run directories on import and removes legacy duplicate rows at startup; console runs share one id between row, directory and bundle; same-second runs of one task get distinct directories. | section 5; `tests/test_phase1.py::ImportDedupe`; `tests/test_m1.py::RunDirectories` |

Version bumped to `0.2.0` (`attest/__init__.py`) so bundles produced with the new supervisor are distinguishable.

## 2. Offline tests

`python3 -m unittest discover -s tests -t .` → 58 tests pass (`tests/test_core.py`, `tests/test_verification.py` with 29
pipeline scenarios on fake provider and executor, `tests/test_m1.py` with the real supervisor executed locally,
`tests/test_phase1.py`). New scenarios: verification order and separate branches, evidence classes per gate, bound
existing-suite failure, blanket forgery caught by the canary, held-out bound and held-out stdout fallback, no mutable
sites with thin and with real adversarial suites, tamper-scan warning, start-up hook on the import path, module digest
mismatch, store import dedupe, same-second run directories.

## 3. Real-sandbox adversarial scenarios (supervisor v4)

`scripts/sandbox_adversarial_tests.py` → `sandbox-adversarial-v4.json` (12 sandbox operations, 32 s guest time, no
inference). One retained checkpoint, one disposable networking-off branch per scenario, root operation, children as uid
65534, same import path as the pipeline (`/tmp/deps:/tmp/w`).

| Scenario | Expected | Result | Decisive checks |
| --- | --- | --- | --- |
| honest | accept | accepted | all 20 binding checks pass, `canary_ok: true`, no start-up hooks |
| wrong | reject | rejected | tests fail |
| tamper_sealed_file | reject | rejected; sealed file byte-identical afterwards (write denied) | nonzero exit, canaries error (module unimportable) |
| premature_exit | reject | rejected | missing results |
| forged_results_at_import | reject | rejected | nonzero exit |
| forged_stderr_text | reject | rejected | tests fail; console text ignored |
| timeout | reject | rejected | timeout, signal |
| crash_signal | reject | rejected | signal |
| **forge_all_ok** (new) | reject | rejected: every real test reported `ok`, must-fail canary reported `ok` | `canary_must_fail_failed` |
| **plant_startup_hook** (new) | accept, writes denied | accepted; child stderr: `denied /tmp/w PermissionError; denied /tmp/deps PermissionError; denied /tmp/sealed PermissionError; denied /tmp/w PermissionError`; no hook present afterwards | `no_startup_hooks_on_import_path` passes |
| **legacy_order_plant_from_existing_step** (new) | reject | rejected: `/tmp/w/sitecustomize.py` present before and after; every real test reported `ok` | `no_startup_hooks_on_import_path`, `canary_must_fail_failed` |

Aggregate flags in the file: `all_correct`, `privilege_separation_active`, `tamper_prevented_not_only_detected`,
`forgery_caught_by_canary`, `hook_planting_prevented`, `legacy_order_detected_as_tamper` are all `true`.

Attempt history (kept, not selected away): `sandbox-adversarial-v4-attempt1-pathmismatch.json` ran the scenarios with an
import path that did not include `/tmp/deps`; the candidate created `/tmp/deps` (world-writable `/tmp`) and wrote a hook
there, inert because that directory was not on the children's import path, but a real gap for the pipeline whose path
does include it. The supervisor now hardens every root of the job path, the process `PYTHONPATH` and the working
directory before any child starts, and the scenario mirrors the pipeline's path. `sandbox-adversarial-v4-attempt2-
uncertain-spawn.log`: one `POST /instances` timed out on the transport; per the no-replay rule the request was not
retried and the batch was abandoned; the third attempt (the file of record) ran with two workers.

## 4. Evaluation harness dry run on Codex

See `evaluation-dryrun-codex/` (`schedule.json` written before the first run, `evaluation.json` with every scheduled
cell) and `evaluation-dryrun-codex-2/` (same schedule after the directory-collision fix). Both are reported; neither is
a performance result: the Codex gateway is the development profile, and these runs exist to prove the method.

### 4.1 First dry run (`evaluation-dryrun-codex/`, schedule registered 19:28 UTC)

10 cells pre-registered (5 tasks x baseline, attest x 1 attempt), 2 workers, Codex gateway, held-out stripped from both
systems, judge bound for the four unittest tasks and `stdout` for python-semver. Every cell is in `evaluation.json`:

| # | Task | System | Verdict | Judge | Label | What happened |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | HARNESS_ERROR | not judged | infra_error | the baseline and the Attest run of the same task started in the same second and the pipeline's second-resolution run id collided (`FileExistsError`); fixed afterwards (explicit per-cell ids in the harness, suffix fallback in the pipeline, `tests/test_m1.py::RunDirectories`) |
| 1 | roman-to-numeral | attest | NEEDS HUMAN | correct | false_reject | all five gates bound; 5 of 8 adversarial tests failed on `int` subclasses with overridden comparisons; arbiter: implementation bug; held for a human |
| 2 | rle-encode | baseline | BASELINE | correct | true_accept | the plain agent shipped an `encode` that passes the (digit-free) held-out suite |
| 3 | rle-encode | attest | INFEASIBLE | incorrect | true_reject | the specification stage refused the contract with the digit round-trip counterexample (`encode('a1') == 'a111'` decodes to 111 `a`s): the V6 behaviour, reached before any implementation, one model call |
| 4 | balanced-brackets | baseline | BASELINE | correct | true_accept | |
| 5 | balanced-brackets | attest | NEEDS HUMAN | correct | false_reject | all five gates bound; 1 of 8 adversarial tests failed (a `str` subclass whose contents differ from its value); arbiter: implementation bug |
| 6 | durationkit-units-001 | baseline | BASELINE | correct | true_accept | |
| 7 | durationkit-units-001 | attest | NEEDS HUMAN | correct | false_reject | the Codex gateway answered `HTTP 429 hourly limit reached for this key` during the breaker: adversarial suite unusable and drift audit unavailable, so the run failed closed instead of certifying; sealed, existing and mutation gates were bound and green |
| 8 | semver-is-compatible-pr368-v2 | baseline | BASELINE | correct (`stdout` judge) | true_accept | |
| 9 | semver-is-compatible-pr368-v2 | attest | ERROR | not judged | infra_error | `HTTP 429` from the gateway during sealing; recorded, not retried |

Reading: the harness did what M1 asked (every cell reported, the cap recorded, no merge, held-out independent). The
rows are not a performance comparison: this is the development profile, the gateway's hourly limit shaped two cells,
and the three `false_reject` rows are the breaker and arbiter being stricter than the held-out judge on subclass
semantics (a contract question for the task author, carried into the M5 method freeze). `model_calls_failed` is now
recorded per row so a provider refusal is visible next to the verdict.

### 4.2 Second dry run after the collision fix (`evaluation-dryrun-codex-2/`, registered 19:53 UTC)

Two cells (durationkit, baseline and attest) with two workers, so both cells start in the same second on purpose. They
received distinct run directories (`durationkit-units-001-baseline-a1-20261016T195335899862Z`,
`durationkit-units-001-attest-a1-20261016T195335899904Z`): the collision is fixed. Both cells then ended `ERROR` on the
first model call: `HTTP 429 from the Codex gateway: hourly limit reached for this key`. Both are reported as
`infra_error` with `model_calls_failed: 1`; nothing was retried and nothing fell back to Nebius.

**Blocker, reported as the policy requires:** the team Codex gateway's hourly allowance for this key was exhausted by the
day's runs (eleven pipelines between 19:28 and 19:53 UTC). The clean ten-cell dry run on the fixed harness is therefore
still to be produced; the command is pre-registered and costs no USD:

```
python3 scripts/run_evaluation.py --provider codex --workers 2 --label m1-dryrun-3 --out reports/attest-m1-2026-10-16/evaluation-dryrun-codex-3
```

Until then, section 4.1 is the dry run of record for acceptance criterion 1.5 (every scheduled attempt reported, caps
recorded, no merge), with its harness-error cell shown rather than removed.

Refusal of an unapproved Nebius batch (verbatim):

```
$ python3 scripts/run_evaluation.py --provider nebius --tasks durationkit-units-001 --out <scratch>
refusing: --provider nebius needs an explicit batch approval: --approve-usd TOTAL (and --max-calls N). A per-run cap
alone does not control a batch. Exploratory runs use --provider codex.
exit 2
```

### 4.3 Third dry run after the gateway limit reset (`evaluation-dryrun-codex-3/`, registered 06:11 UTC, 17 Oct 2026)

Run with the milestone M2 code (supervisor v5, provenance and manifest in every bundle). All 10 scheduled cells are
reported: 9 ended with a verdict (5 baseline, 3 Attest NEEDS HUMAN on candidates the held-out judge accepts, 1 Attest
INFEASIBLE at the specification stage) and the last Attest cell (python-semver) hit `HTTP 429 hourly limit reached for
this key` at its first model call after 57 successful calls in 27 minutes; it is recorded as an infrastructure error and
nothing fell back to Nebius. The directory-collision fix of section 4.2 held (10 distinct run directories). Per-cell
table, `attest check` results and the method observations: `reports/attest-m2-2026-10-17/README.md` section 5. The
remaining blocker for a 429-free 10-cell batch is pacing below the key's hourly budget (one worker or a pause between
tasks), which the M5 run plan has to include.

## 5. Usage accounting

`python3 scripts/usage_report.py --store data/attest.db`: 56 unique runs from 76 bundle files (20 copies of the same
`run_id` skipped); Nebius 46 runs on 15 Oct 2026, $1.574 known, $1.620 committed (3 uncertain calls at their
reservation); Codex 10 runs (allowance, no USD). The three server-only console runs ($0.18) are not on this machine;
the deduplicated total stays 49 unique Nebius runs, $1.80 committed, as in the competitive review. Today's work added no
Nebius inference. The Token Factory console remains the authoritative invoice.

## 6. Where we remain weaker (unchanged by M1)

- pytest suites (`semver`) are still `stdout` evidence; a trusted result-file plugin under the supervisor is future work.
- A targeted forgery that spares the canaries and the mutation gate is not detected by the binding; it remains a
  documented residual, caught structurally or not at all.
- The specification can still be unsatisfiable (`rle-encode`); the satisfiability question in the spec prompt is
  scheduled with the M5 method freeze.
- The console still shows the old layout; evidence classes appear only in its gates table until M3.
