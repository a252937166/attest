# Milestone M3: console redesign (17 Oct 2026)

> Terminology correction (17 Oct 2026, same day): this report and the console API originally called bundles with a manifest "signed" and
> bundles without one "unsigned". A SHA-256 manifest is an integrity and internal-consistency check, not a digital
> signature and not independent proof of execution. The wording below was corrected in place; the code and `attest check`
> now say "manifest verified" and "no manifest".

Implements items 3.1 to 3.4 of the plan in `reports/attest-competitive-review-2026-10-16/README.md` (section 5) on the
approved design `design/console-redesign-2026-10-16/README.md` with its recommended defaults: serif seal and decision
sentence, sticky decision header that compacts on scroll, exhibits E1 to E7 as the citation scheme shared with `PROOF.md`,
and the development gateway hidden from the public form.

No inference and no live run were used: every screen below is rendered from recorded evidence imported from `reports/`,
or from a synthetic replay fixture that is labelled as such on screen. Nothing was deployed; the live console at
`attest.axiqo.xyz` still runs the previous build.

## 1. What changed

| Item | Acceptance criterion | Result |
| --- | --- | --- |
| 3.1 Decision header, tabs, exhibits, counterexample block, provenance chips, history with filters | Matches the approved prototype; verified in a real browser at 1440 px and 390 px, light and dark | Done. 43 screenshots in `screens/` (section 3). Decision copy, exhibits, gates table, counterexamples and "what this bundle proves" come from `attest/core/exhibits.py`, the module `PROOF.md` uses, so the two cannot disagree |
| 3.2 Keyed updates; tab in URL; expanded exhibits and focus preserved | A running run keeps an open exhibit and keyboard focus across 20 refreshes (manual test recorded with a screenshot sequence) | Done. 20 refresh cycles at 300 ms against a replayed running run: the disclosure stayed open, the focused element was unchanged, 7 log rows arrived, and the page rendered its detail pane exactly once (section 4) |
| 3.3 Launch form: browse recorded evidence by default; live run shows an estimate from recorded runs and the remaining daily budget; development gateway hidden until a token is entered | Public page source contains no gateway name | Done. `index.html`, `app.js`, `styles.css` and the unauthenticated responses of `/api/health`, `/api/tasks`, `/api/profiles` contain neither the gateway name nor its host (checked by `capture.py` and by `tests/test_console.py`). The team profile is returned only by `POST /api/profiles` with a valid token |
| 3.4 API additions: run-row summary, provenance field, counterexample fields, artifact manifest | `attest-console.md` updated; offline API tests | Done. `attest-console.md` has the new API table and an M3 section; `tests/test_console.py` adds 14 offline tests (section 2) |

Files: `attest/app/server.py`, `attest/app/db.py`, `attest/app/worker.py`, `attest/app/static/index.html`,
`attest/app/static/styles.css`, `attest/app/static/app.js` (rewritten), `scripts/console_replay.py` (new),
`tests/test_console.py` (new), `attest-console.md`, this folder (`capture.py`, `capture-record.json`, `screens/`,
`refresh-sequence/`).

### 1.1 Page

- **Decision header** (sticky, compacts after 160 px of scroll on wide screens): verdict seal, one-sentence statement,
  explanation, the key exhibit line (`E1` for VERIFIED, the first counterexample for NEEDS HUMAN, `E7` for ERROR), the
  provenance line (live, recorded or synthetic; profile, provider, date, run id) and the actions: Download Proof
  Bundle, Copy patch, Open PROOF.md; for ERROR: Download run record, Open PROOF.md, Start a new run (which switches the
  workspace to live mode for the same task).
- **Tabs** Overview, Patch, Tests and counterexamples, Activity, Files; the selected tab is the URL hash
  (`/runs/{id}#tests`), roving tabindex with arrow keys, Home and End; disabled with a reason while a run is live or
  when no bundle exists.
- **Tests tab**: the gates table first (pass, fail, not run; evidence class per gate; a skipped gate is never a pass),
  then E1 to E7 with a one-line "why" each: the sealed table (base and candidate, with a "only the tests that failed on
  the base" filter) and the binding checks; surviving mutants as weak spots and the full mutant list; the generated
  tests with a counterexample block per failing test (test, outcome, the test's first and second assertion arguments
  when the bundle recorded them, captured output, the arbiter's classification, contract basis and rationale);
  held-out failures; drift findings; the arbitration table and corrected re-runs; the failure record for ERROR.
- **Activity tab**: stage stepper, meters (wall clock, model calls, sandbox operations, committed cost), the event log
  (or the implementer's action trail when a recorded run has no events), the model calls with roles, execution
  identifiers and, when the bundle carries one (milestone M2), the provenance record.
- **Files tab**: every artifact with purpose, size and sha256 (from `manifest.json` when the run wrote one, otherwise
  computed on request and said so), mutants grouped, the zip, and "What this bundle proves, and what it does not"
  generated from the gates.
- **History rail**: seal, provenance dot, cost and duration per row; filters All, Verified, Needs human, Errors;
  `aria-current` on the open run; arrow keys move, Enter opens; rows are updated in place by run id.
- **Workspace**: "Browse recorded evidence" (default) opens the latest recorded run of the task at no cost; "Run live"
  shows the cost and duration ranges of completed public-profile runs of the same task (ERROR and baseline runs and
  replay fixtures excluded) and the remaining daily budget; the team token under "Team sign-in" is validated by the
  server and only then does the profile select appear. The external-repository entry is a note, not a control.
- **Queued and running**: statement and explanation per state, the stage stepper with one pulsing dot (none under
  `prefers-reduced-motion`), meters from the store's live ledger numbers, the event log in a polite live region and
  "What each stage does". Replay fixtures say "Synthetic fixture" in the header and in the history.
- **Narrow screens** (under 900 px): the rail becomes a "Workspace and history" disclosure above the run, the header
  stacks with two action columns, tables scroll horizontally, the log drops its stage column.

### 1.2 API

| Addition | Where |
| --- | --- |
| `summary` {verdict, status, stage, cost_usd, cost_committed_usd, duration_s, provenance, model_calls, sandbox_ops} and `provenance` on every run row | `GET /api/runs`, `GET /api/runs/{id}` |
| `provenance`: `live` (started from this console), `imported` (recorded evidence registered from disk), `synthetic` (replay fixture, requester `replay`) | derived in `server.py` from the requester and the run directory |
| `exhibits` = `attest.core.exhibits.summary(bundle)`: `decision`, `exhibits` E1 to E7, `gates`, `counterexamples`, `proves` | `GET /api/runs/{id}` |
| `manifest` with `recorded: true` from `manifest.json`, or computed with `recorded: false` for runs recorded before M2 (an integrity check, not a signature) | `GET /api/runs/{id}` |
| `estimate` per task {runs, cost_min_usd, cost_max_usd, duration_min_s, duration_max_s, latest_run_id, latest_verdict, recorded_runs, estimate_provider} | `GET /api/tasks` |
| `budget.remaining_usd`, `committed_today_usd`, `reserved_usd`, `active_runs`, `public_runs_per_hour` | `GET /api/health` |
| `GET /api/profiles` (public list) and `POST /api/profiles {admin_token}` (team list only with a valid token) | new |
| live `meters`, `queue`, `current`, `error` on the polling endpoint | `GET /api/runs/{id}/events` |
| artifact allowlist as a closed regular expression of path shapes (adds `manifest.json`, `verify_raw.json`, `tamper_scan.json`, `task.frozen.json`, `baseline.json`, `judge.json`, `red.attemptN.json`, `sealed/test_sealed.attemptN.py`, `breaker_tests.attemptN.py`, `breaker_response.attemptN.json`, `mutants_*.py`) | `GET /api/runs/{id}/artifacts/{name}` |
| store: `model_calls` column (migrated), live meter updates from the worker's progress callback, `task_estimates`, `nebius_remaining`, import of archived progress events from `console-record.json` | `db.py`, `worker.py` |

Existing fields and routes are unchanged; `POST /api/runs` keeps its rules (public callers: judge profile only, 3 per
hour per visitor, daily budget; the development profile needs the token, HTTP 403 otherwise).

## 2. Offline tests

`python3 -m unittest discover -s tests -t .` (with `.venv/bin/python`): **94 tests, OK** on 17 Oct 2026, including the
58 tests that existed before this milestone, the M2 tests written in parallel and the 14 new tests in
`tests/test_console.py`:

- health reports the remaining budget and the public rate; run rows carry `summary` and `provenance: imported`;
- task estimates come from completed public-profile runs only (the ERROR run of the same task is excluded) and name the
  latest recorded run;
- run detail carries exhibits (decision statement, reason class `adversarial_implementation_bug` for the rle-encode
  evaluation run, E1 to E7, gates, counterexamples with the arbiter's contract basis, proves) and a manifest computed on request (no manifest.json recorded)
  with one sha256 per file; the ERROR run's decision cites E7 with `retried: false`;
- archived progress events of the judge run are importable and served (29 events, meters from the ledger);
- the artifact allowlist serves listed shapes and refuses traversal and unlisted names;
- the public profile list and page sources name no gateway; the development provider still needs the token; unknown
  profile ids are rejected;
- deep links `/runs/{id}` serve the console; the replay fixture is reported as `synthetic` and refuses production data
  directories; store helpers (`duration_seconds`, `nebius_remaining`, `task_estimates`).

`fastapi.testclient` needs `httpx`; it was installed into the development `.venv` only (`.venv/bin/pip install httpx`,
httpx 0.28.1). No deployment requirement changed; the tests skip themselves when `httpx` is absent.

## 3. Real-browser screenshots

`capture.py` starts its own console (uvicorn, a temporary data directory, the recorded runs below imported through
`ATTEST_IMPORT_DIRS`), replays the judge run as synthetic fixtures for the queued and running states, and drives Google
Chrome 155 through Playwright for Python 1.61 (`channel="chrome"`, headless). Results: `capture-record.json`.

Recorded runs used (all imported, provenance `imported`): the public judge run
`reports/attest-verification-2026-10-15/console-run-durationkit-nebius` (VERIFIED, Nemotron), the semver run with
held-out tests `reports/attest-hardening-2026-10-16/semver-v2-codex-verified` (VERIFIED), the evaluation runs
`rle-encode-20261015T180226Z` (NEEDS HUMAN, implementation bug by the arbiter) and `roman-to-numeral-20261015T184550Z`
(NEEDS HUMAN, contract dispute), the M1 run `balanced-brackets-20261016T192809Z` (NEEDS HUMAN, test defect, bound
suites), the first-slice run `nebius-pilot-attempt1-http422` (ERROR before any gate) and the M1 dry-run cell
`rle-encode-20261016T193214Z` (INFEASIBLE).

Screenshots, `screens/<state>-<width>-<scheme>.png`, 43 files (13 MB):

| State | 1440 px light and dark | 390 px light and dark |
| --- | --- | --- |
| `empty` | yes | yes |
| `queued-overview` (synthetic replay, delayed start) | yes | yes |
| `running-overview` (synthetic replay, one event every 6 s) | yes | yes |
| `verified-overview`, `verified-tests`, `verified-patch`, `verified-activity`, `verified-files` (judge run) | yes | overview only |
| `semver-heldout-overview` | yes | no |
| `needs-human-overview`, `needs-human-tests` (implementation bug, counterexample blocks) | yes | tests only |
| `contract-dispute-tests` (roman-to-numeral) | yes | no |
| `error-overview`, `error-tests` (E7 failure record) | yes | overview only |
| `infeasible-overview` | yes | no |
| `verified-tests-scrolled-compact` (header compacted after 900 px of scroll) | light only | no |

Browser console: no errors or page errors during the capture. Public-source check during the capture: `/`,
`/static/app.js`, `/static/styles.css`, `/api/health`, `/api/tasks`, `/api/profiles` contain 0 occurrences of the
gateway name and 0 of its host.

Keyboard checks recorded in `capture-record.json`: ArrowRight from the Overview tab selects and focuses Patch and sets
`#patch`; End selects Files; ArrowDown in the history moves focus to the next row; Enter opens it and marks it
`aria-current`. The compact header class was present after scrolling.

Note on the judge run: its bundle predates milestone M1, so its adversarial gate carries the removed `skipped` pass
path. The first capture showed the decision sentence counting that gate as passed while E3 said "not run". The shared
module (`attest/core/exhibits.py`, milestone M2) was corrected the same day: the decision sentence now counts only
exhibits that actually passed, the gates table reports that gate as "not run" (so the Overview says "4 of 5 gates pass,
1 not run"), and a weak-spot line says that no test written after the patch ran. The 43 screenshots and the refresh
sequence in this folder were re-captured after that fix (record `capture-record.json`, 06:33 UTC).

## 4. Keyed updates: the 20-refresh record

Procedure (`capture.py`): a dedicated replay of the judge run (`scripts/console_replay.py`, one event every 0.8 s),
the page opened at `/runs/replay-refresh?poll=300` (one refresh every 300 ms), the "What each stage does" disclosure
opened and its summary focused, then wait until the client had completed 20 further refresh cycles
(`window.attestDebug.polls`), taking a screenshot every 5 cycles (`refresh-sequence/refresh-005.png` to
`refresh-020.png`).

| | Before | After 20 refreshes |
| --- | --- | --- |
| Disclosure open | true | true |
| Focused element (`data-focus`) | `det-stages-help` | `det-stages-help` |
| Log rows | 5 | 12 |
| Selected tab | overview | overview |
| Run status | running | running |
| Full renders of the detail pane (`renders` / `panelRenders`) | 1 / 1 | 1 / 1 |

Result: **pass**. The log grew by 7 rows, the stepper and meters changed, and the pane was never rebuilt; the open
disclosure and the focus survived every refresh. The sequence screenshots show the same page with more log rows.

## 5. Limitations and what is not done

- **Not deployed.** The live console still serves the previous build; publishing M3 needs a redeploy on `yungou`
  (snapshot, bundle, install, health check, rollback path as in `reports/attest-deployment-2026-10-15/README.md`) and the
  owner's approval. The deployment bundle (`deploy/yungou/build_bundle.sh`) packages `reports/`, so these 14 MB of
  screenshots would travel with it unless excluded.
- **Counterexample values.** Bundles recorded before milestone M2 carry no assertion text for failing tests, so their
  counterexample blocks show the test, its outcome and the arbiter's classification, contract basis and rationale, but
  "captured output: none recorded for this test" instead of input, actual and expected values. New bundles will carry
  `failure_tail` (M2); the client already renders the first and second assertion arguments when present, labelled as
  the test's arguments rather than guessed as actual and expected.
- **Provider names in evidence.** Recorded development runs carry `provider: "codex"` in their run row and the gateway
  host inside their own `proof_bundle.json`, `ledger.json` and `PROOF.md` (as before this milestone). The page displays
  the provider as "development provider (team allowance)" and the public form never names it; whether the host should
  be redacted from public bundles is an owner decision, not made here.
- **Polling, not push.** Live runs poll every 4 s (`?poll=` overrides it for tests); no server-sent events.
- **Live estimates.** The estimate mixes every completed public-profile run of a task regardless of date; with one or
  two recorded runs per task the ranges are narrow and should be read as "what it cost last time".
- **Not staged**: a real queued run behind a real running run (both would need live inference); the queued view was
  exercised with a delayed replay fixture, whose queue position is reported as "starting next" because fixtures are
  not in the worker queue.
- Google Fonts (IBM Plex) load from the network; the declared system fallbacks render the page offline. The capture
  machine was online, so the screenshots show Plex.
