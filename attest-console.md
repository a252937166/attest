# Attest console and application API

Status 2026-10-18: implemented and exercised locally (`attest/app/`), FastAPI + uvicorn, single background worker,
SQLite store, static single-page UI redesigned in milestone M3 (approved design: `design/console-redesign-2026-10-16/`)
and given a home page, a brand, a contextual guide and motion in the second pass of 18 Oct 2026 (below).
Deployment target: `yungou` (DogYun `206.237.18.80`) without Docker, see `deployment-plan-yungou.md` and `deploy/yungou/`;
the deployment reports under `reports/attest-deployment-*/` say which build the public console runs.

## Architecture

| Part | Responsibility |
| --- | --- |
| `attest/app/server.py` | FastAPI application: JSON API under `/api/`, static UI at `/` and `/runs/{id}`; imports finished run directories from `ATTEST_IMPORT_DIRS` on startup so evidence runs appear in the console; derives each run's provenance (live, imported, synthetic); serves exhibits E1 to E7, the decision copy and the artifact manifest from the same modules PROOF.md uses (`attest/core/exhibits.py`, `attest/core/manifest.py`) |
| `attest/app/worker.py` | One worker thread, one run at a time, bounded queue (5); builds the provider (`nebius` for judges, the development provider for the team), the Sandboxes executor and the Tavily client from the private credentials; streams pipeline progress into the store together with the live ledger meters (model calls, sandbox operations, committed USD); enforces the per-run USD cap and a daily Nebius budget for console runs |
| `attest/app/db.py` | SQLite (`runs`, `events`) with a single writer lock; import of historical runs from their `proof_bundle.json` (and their archived progress events from `console-record.json` when present); per-task recorded estimates; remaining daily budget |
| `attest/app/static/` | UI: workspace (browse recorded evidence by default, run live as an explicit action), history rail with verdict filters, and the case file for a run: decision header, tabs (Overview, Patch, Tests and counterexamples, Activity, Files), exhibits E1 to E7, counterexample blocks, provenance, artifact manifest, "what this bundle proves, and what it does not" |
| `scripts/console_replay.py` | Development fixture: replays a recorded run into a test store as a synthetic run (requester `replay`) so the queued and running views can be exercised and screenshotted offline; refuses production data directories |
| `attest/core/pipeline.py` | unchanged pipeline with a `progress` callback; verdicts are computed only from the gates recorded in the bundle, so the console cannot show a verdict the evidence does not support |

## API

| Method and path | Purpose |
| --- | --- |
| `GET /api/health` | version, worker liveness, queue length, current run, **disk** (free MB/fraction, `low`, `accepting_runs`), **budget** (daily/per-run caps, whether another Nebius run fits, `remaining_usd`, `committed_today_usd`, `reserved_usd`, `active_runs`), `public_runs_per_hour`, and what was **reconciled** and **deduplicated** at startup |
| `GET /api/profiles` | the public inference profile list (the judge profile only) |
| `POST /api/profiles` `{admin_token}` | the profile list for the caller; only a valid team token returns the development profile, so the public page and its responses never name the development gateway |
| `GET /api/tasks` | sample tasks from `examples/*/task.json`, each with a recorded **estimate**: `runs` and the cost and duration ranges of completed public-profile runs of that task (ERROR and baseline runs and replay fixtures excluded), `recorded_runs`, `latest_run_id`, `latest_verdict` |
| `GET /api/runs?limit=` | run list, newest first; every row carries `provenance` and a `summary` {verdict, status, stage, cost_usd, cost_committed_usd, duration_s, provenance, model_calls, sandbox_ops} so the history renders without loading bundles |
| `POST /api/runs` `{task_id, provider, admin_token?}` | enqueue a run; public callers: the judge profile only, 3 runs per hour per visitor, daily budget check; the development profile requires the admin token (HTTP 403 otherwise; unknown profile ids are HTTP 400) |
| `GET /api/runs/{id}/events` (pacing) | since 17 Oct 2026 the development profile's pacing waits and gateway rejections appear as events with stage `pacing`, next to the stage messages |
| `GET /api/runs/{id}` | run record (with `summary`), full Proof Bundle JSON when finished, progress events, `provenance`, `exhibits` (= `attest.core.exhibits.summary(bundle)`: `decision`, `exhibits` E1 to E7, `gates`, `counterexamples`, `proves`) and `manifest` (from `manifest.json` with `recorded: true`, or computed on request with `recorded: false` for runs recorded before milestone M2; a SHA-256 integrity check, not a signature) |
| `GET /api/runs/{id}/events?after=` | incremental progress for polling, with the run `status`, `stage`, `verdict`, live `meters` (model calls, sandbox operations, committed USD, tokens, timestamps), queue length and current run |
| `GET /api/runs/{id}/artifacts/{name}` | artifacts from a closed allowlist of path shapes (no traversal possible): `PROOF.md`, `proof_bundle.json`, `manifest.json`, `candidate.patch`, `ledger.json`, `spec.json`, `verify.json`, `verify_raw.json`, `breaker.json`, `drift.json`, `grounding.json`, `arbitration.json`, `trajectory.jsonl`, `tamper_scan.json`, `task.frozen.json`, `baseline.json`, `judge.json`, `breaker_tests.py`, `red.attemptN.json`, `breaker_tests.attemptN.py`, `breaker_response.attemptN.json`, `mutants_*.py`, `sealed/test_sealed.py`, `sealed/test_sealed.attemptN.py`, `arbitration/{sealed,adversarial}_corrected.py` |
| `GET /api/runs/{id}/bundle.zip` | the whole run directory as a zip (downloadable Proof Bundle) |

Configuration: `ATTEST_DATA_DIR` (SQLite and run directories), `ATTEST_EXAMPLES_DIR`, `ATTEST_IMPORT_DIRS`,
`ATTEST_ADMIN_TOKEN`, `ATTEST_PER_RUN_USD_CAP` (0.5), `ATTEST_DAILY_USD_CAP` (2.0), `ATTEST_PUBLIC_RUNS_PER_HOUR` (3),
`ATTEST_RETENTION_KEEP` (40), `ATTEST_MIN_FREE_FRAC` (0.07), `ATTEST_MIN_FREE_MB` (500).
Credentials come from the environment or the private vault notes; they are never written to the store or the artifacts.
The client accepts `?poll=<ms>` (minimum 300, default 4000) to change the live polling interval; it is used by the browser tests.

### Budget, disk and restart safety (16 Oct 2026)

- **Atomic budget reservation.** A console run is created and budget-checked under one store lock, so concurrent requests
  cannot each pass a stale check: every queued or running Nebius run reserves the per-run cap against the daily cap. The
  worker rechecks before execution, and uncertain (unpriced) model calls are counted at a conservative reservation so the
  daily total never undercounts.
- **Disk guard and retention.** New runs are refused when free space is low (`ATTEST_MIN_FREE_MB` / `ATTEST_MIN_FREE_FRAC`);
  health reports it. After each finished run the oldest console-run directories beyond `ATTEST_RETENTION_KEEP` are pruned,
  never imported evidence (anything outside the data run directory) and never a `VERIFIED` run.
- **Restart reconciliation.** On startup, runs left `queued`/`running` by a crash are finalized from their Proof Bundle if it
  reached disk, otherwise marked errored (interrupted). Health reports what was reconciled.

### Store hygiene and run identifiers (16 Oct 2026, M1)

- A run started from the console now passes its id into the pipeline, so the store row, the run directory and the
  bundle's `run_id` are one identifier.
- `import_run_dir` skips a directory that any row already points at (`has_out_dir`), so the console's own runs are never
  re-imported under a second id. At startup `dedupe_imports` removes legacy duplicate rows (same directory, later row),
  never touching run directories; `/api/health` reports them under `deduplicated_at_startup`.
- `scripts/usage_report.py --store data/attest.db` reports unique runs and committed USD by provider and day.

### Console redesign (17 Oct 2026, M3)

The page follows the approved design (`design/console-redesign-2026-10-16/README.md`) with its recommended defaults:
serif verdict seal and decision sentence, a sticky decision header that compacts on scroll, exhibits E1 to E7 as the
citation scheme shared with `PROOF.md`, and the development gateway hidden from the public form.

- **Decision header.** Seal, one-sentence statement, explanation, the key exhibit line (the concrete failing input or
  the key check), provenance (live, recorded or synthetic, with profile, provider, date and run id) and the actions
  (download Proof Bundle, copy patch, open PROOF.md; for ERROR: download run record, open PROOF.md, start a new run).
  The copy is authored per verdict and reason class in `attest/core/exhibits.py`, never per run, so the console and
  PROOF.md say the same thing.
- **Tabs.** Overview (what was requested, what changed, can I accept it, what the evidence says), Patch (files, write
  scope, per-file digests, the unified diff as a focusable scroll region), Tests and counterexamples (gates table first
  with pass / fail / not run and the evidence class, then E1 to E7 with a one-line "why" each, the sealed table with a
  "only tests that failed on the base" filter, binding checks, surviving mutants, the counterexample block with the
  arbiter's classification, contract basis and rationale, held-out failures, drift findings, arbitration re-runs and the
  failure record), Activity (stage stepper, meters, event log or the implementer's action trail, model calls with
  roles, execution identifiers, and the bundle's provenance record when present), Files (every artifact with purpose,
  size and sha256 from the manifest, mutants grouped, the zip, and "What this bundle proves, and what it does not").
- **History rail.** Verdict seal, provenance dot (live, recorded, synthetic), cost and duration per row; filters All,
  Verified, Needs human, Errors; `aria-current` on the open run; arrow keys move between rows and Enter opens.
- **Workspace.** "Browse recorded evidence" is the default and opens the latest recorded run of the selected task at no
  cost; "Run live" is an explicit action whose estimate comes from recorded public-profile runs of the same task (cost
  and duration ranges) plus the remaining daily budget from `/api/health`. The team token is entered under "Team
  sign-in" and validated by `POST /api/profiles`; only then does an "Inference profile" select appear with the team
  profile. The external-repository entry is a text note, not a control.
- **Queued and running.** Stage stepper (Freeze to Attest), meters (elapsed, model calls, sandbox operations, cost so
  far, all from the store's live ledger numbers), an event log in a polite live region and "What each stage does".
  Tabs without data are disabled with a reason. Replay fixtures are labelled as synthetic on screen.
- **Keyed updates.** A live run is rendered once; polling appends log rows and changes texts and classes in place and
  never rebuilds the detail pane, so open disclosures, the selected tab and keyboard focus survive every refresh. The
  selected tab lives in the URL hash (`/runs/{id}#tests`), open exhibits are remembered per run in session storage
  (every access guarded; the page works without storage), and focus is restored by a stable `data-focus` id after
  the few full renders that remain (opening a run, a run finishing, switching tabs).
- **Keyboard and motion.** Skip link, visible focus rings, roving tabindex on the tab strip (arrow keys, Home, End),
  native `details` disclosures, one pulse on the current stage dot disabled under `prefers-reduced-motion`. Under 900 px
  the rail collapses into a "Workspace and history" disclosure, the header stacks, tables scroll horizontally and the
  log drops its stage column.

Verification record, screenshots (1440 px and 390 px, light and dark) and the 20-refresh test:
`reports/attest-m3-2026-10-17/README.md`.

### Console redesign, second pass (18 Oct 2026)

Owner feedback on the M3 console: the brand was not visible, a newcomer got no guidance, there was too little motion
and the page did not look like a finished product. The second pass keeps the evidence-file structure of M3 (decision
header, tabs, exhibits E1 to E7, keyed live updates, a public form that never names the development gateway) and
changes the presentation and the entry. Only `attest/app/static/` changed; the server, the API and the package digest
recorded in bundles (`attest_revision()`, computed over `attest/**/*.py`) are untouched.

- **Two views, one page.** `/` is a home page: the problem (a plausible patch is not a verified one), how a run earns its
  verdict (a five-phase chain naming the model or the deterministic component responsible for each phase and the
  exhibits it produces), who provides the core capabilities (NVIDIA Nemotron 3 Ultra, Super and 3.5 Lightning on Nebius
  Token Factory, Token Factory Sandboxes, Attest's own supervisor and verdict rule), how to use it (three steps ending
  with `python -m attest check`), the recorded evidence of this console, and the frozen M5 evaluation table with its
  narrow reading. `/runs/{id}` is the case file as before, with a breadcrumb back to the home and a "What am I looking
  at?" link that opens the guide. Both routes serve the same `index.html`; the numbers on the home page (recorded runs
  by verdict, per-run cap, runs per hour, recorded durations) come from `/api/runs`, `/api/health` and `/api/tasks` and
  are never typed into the page.
- **One entry point.** The workspace form (task, browse or live, estimate, run button, team sign-in) exists once; the
  script places it in the "Start here" panel of the home and moves it into the rail on a run page, so the selected task
  and mode survive the switch. The live tile shows the recorded cost of the task; the brief under the task select shows
  the statement, the number of acceptance criteria and the latest recorded verdict.
- **Brand.** An inline SVG mark (a seal ring around an A whose crossbar is a check) in the navigation, the footer, the
  guide and the favicon, with the wordmark in the display face.
- **Guide.** A contextual panel on run pages whose steps depend on the state of the run: finished (the decision, can I
  accept it, the gates, the counterexample when there is one, take it with you), queued, running (the current stage
  taken from the event stream, what it does, what comes next) and error (what happened, start again). "Show me" switches
  to the right tab, scrolls to the element and spotlights it; "Done" or the close button dismisses the guide for this
  browser (`localStorage`, every access guarded, the page works without it) and a launcher brings it back. On screens up
  to 900 px wide it starts collapsed.
- **Motion.** One orchestrated reveal of the hero, a pulse travelling along the phase chain, the verdict seal stamping
  in, the sticky decision header compacting on scroll, log rows and meter changes animating in place, a sliding tab
  indicator, skeleton rows while a bundle loads. Everything stops under `prefers-reduced-motion`.
- **Type and colour.** Instrument Serif for the headline, the seal and the decision sentence; IBM Plex Sans and Mono as
  before. One dark scheme (`color-scheme: dark`). The only accent is the indigo used for live execution, links and
  actions; verdict colours are reserved for seals, gates and counterexamples.

Second round, same day, after the owner reviewed the live page against their reference sites: a gradient brand lockup
with the seal mark above the headline and a "built on" line; a two-row navigation (brand and status, then a section bar
with an underlined active link); pill buttons; a stronger aurora with grain; a drawn underline; totals that count up
once; blocks that rise once when they scroll into view; a guide line with a beacon that follows the reading position.
Reduced motion now stops the looping and travelling effects and makes one-shot entrances instant rather than removing
every animation. The SVG that defines the mark's gradient is visually hidden with zero size, not `display:none`, because
Chrome does not resolve paint servers from hidden SVGs (the mark had rendered as a bare caret).

**Caching rule.** `index.html` references `styles.css?v=<stamp>` and `app.js?v=<stamp>`; bump the stamp whenever a static
file changes, and the vhost sends `Cache-Control: no-cache` so browsers revalidate against the ETag. On 18 Oct 2026 a
browser that had cached the previous build's assets rendered the new markup with the old stylesheet and script.

Unchanged and re-verified: the ids and selectors the browser tests and the M3 capture rely on (`#main`, `.decision`,
`#decision-h`, the tab strip, `#log`, `#stepper`, `#history`, `data-focus`), keyed updates (an open disclosure and
keyboard focus survive 20 refresh cycles of a running run with one render), keyboard navigation, a public page that
names no gateway, and the offline suite (145 tests). Verification record and screenshots: `reports/attest-ui-2026-10-18/`.

## Verified locally (2026-10-15)

| Check | Result |
| --- | --- |
| Startup import of historical runs | 7 run directories registered with provider and verdict |
| `GET /api/health`, `/api/tasks`, `/api/runs`, run detail, `PROOF.md` (17 KB), `bundle.zip` (130 KB), `/` and `/runs/{id}` | all HTTP 200 |
| Unknown task | HTTP 404 |
| `provider=codex` without admin token | HTTP 403 |
| Public rate limit (instance started with limit 0) | HTTP 429 |
| End-to-end run started from the API (admin, Nemotron profile, durationkit task) | 29 progress events streamed; finished VERIFIED in 4 min 38 s; $0.0723; 17 model calls; 23 sandbox operations; evidence in `reports/attest-verification-2026-10-15/console-run-durationkit-nebius/` |
| Memory of the console process | 25 to 56 MB RSS idle, 33 to 48 MB during the run (macOS; the pipeline runs inside the worker thread) |
| UI rendering | `reports/attest-verification-2026-10-15/console-running-screenshot.png` (headless Chrome, dark scheme) |

## Limitations

- Imported historical runs have progress events only when a `console-record.json` was archived with them; otherwise
  the Activity tab shows the implementer's action trail from the bundle.
- One worker, one run at a time; the queue holds five. A restart loses queued (not finished) runs; the store marks them.
- Judge-facing runs use the Nemotron profile with a $0.5 per-run cap and a $2 daily cap for console-started runs; the
  admin token is required for the development provider. There is no login; rate limiting is per client address.
- The UI polls (4 s by default); no server-sent events yet. Live meters update at each poll.
- Bundles recorded before milestone M2 carry no assertion text for failing tests, so their counterexample blocks show
  the test, its outcome and the arbiter's classification, contract basis and rationale, but not the captured values.
- Recorded development runs name their provider in the run row (`provider`) and their bundle (`profile.provider`), as
  evidence; the console displays it as "development provider (team allowance)".

## Deployment

Live at `https://attest.axiqo.xyz` on `yungou` (`206.237.18.80`) since 2026-10-16 00:10 host time, without Docker:
`attest.service` (uvicorn on 127.0.0.1:4070, `MemoryMax=200M`, measured 42 to 55 MB), nginx vhost with Let's Encrypt,
evidence runs imported from the bundled reports. Procedure, snapshots, judge run and rollback test:
`reports/attest-deployment-2026-10-15/README.md`; scripts: `deploy/yungou/`. The M3 console is not deployed; a
redeploy (same procedure: snapshot, bundle, install, health check, rollback path) is required to publish it.

### Imported evidence and the development profile (17 Oct 2026)

Run directories named in `ATTEST_IMPORT_DIRS` are registered at startup only when their provider is in
`ATTEST_IMPORT_PROVIDERS` (default `nebius`): recorded development-profile runs are never imported into the public console,
so their bundles and ledgers (which name the development gateway in runs recorded before 17 Oct) are not downloadable there.
New development-profile bundles record only a digest of the gateway URL. Deployment bundles are built from the redacted
public export (`scripts/export_public.py`), so the reports shipped to the server carry no gateway host either.
