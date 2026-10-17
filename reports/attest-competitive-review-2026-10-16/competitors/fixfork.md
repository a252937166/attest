# FixFork — competitor report (Nebius x NVIDIA Global AI Hackathon)

### Identity
- Devpost: https://devpost.com/software/fixfork — fetched 2026-10-16 17:23:41 UTC (HTTP 200 via curl/Chrome UA).
- Title: **FixFork**. Tagline: "An autonomous debugging agent that races three AI fixes and keeps only the one your tests confirm."
- Team: 1 — Tuyen Tran (Devpost `tuyentran4992`; GitHub `tuyentran4992`, location Viet Nam, 2 followers).
- Submitted to: Nebius x NVIDIA Global AI Hackathon (README: Coding & Agentic Engineering track). Devpost "started this project — Sep 30, 2026 02:44 AM EDT"; 0 project updates posted.
- Built with (Devpost tags): ai-agents, developer-tools, git, llm, nebius-token-factory, nvidia-nemotron, python, tavily, unit(test).
- Links: repo https://github.com/tuyentran4992/fixfork · demo https://fixfork.netlify.app · video https://youtu.be/A6xS5TFVJs4 (embedded on Devpost).
- Likes/comments: no numeric like counter is rendered (button reads "Like"); no comments present.

### User and problem served
Python developers holding a repo with a red test suite. Instead of a single LLM suggestion, FixFork asks Nemotron for three divergent root-cause hypotheses, applies each on its own forked branch, runs the suite per branch, and exports only a branch that goes green (ties → fewest changed lines). If nothing goes green it exports no patch and names the least-failed branch "a lead, not a fix".

### Complete workflow a user can actually perform today
The only entry point is a CLI (`fixfork/__main__.py`; console script `fixfork` in `pyproject.toml`; stdlib-only, no pip dependencies):
- `python3 -m fixfork run --repo <path> --test "<cmd>" [--fake] [--sandbox local|nebius] [--branches 3] [--max-rounds 2] [--research off|tavily] [--timeout 300] [--max-tokens N --max-tokens-cap N] [--max-file-chars N --max-total-chars N] [--out report.md] [--patch p.patch] [--html] [--json] [--events run.jsonl] [--strict]`
- `python3 -m fixfork research --query "..."` (one keyless Tavily call).
Pipeline (`fixfork/pipeline.py`): baseline run (must be red) → `read_tree` + checkpoint → one Tavily search (`research.py`) → Nemotron Super diagnosis prompt (`hypotheses.py`) → `guard.check_edits` (→ `blocked`) → `preflight_edits` (→ `not_run`) → fork per hypothesis → apply exact-match edits (two guarded fuzzy fallbacks) → run tests → up to `--max-rounds` repair rounds with Nemotron Nano → `judge.pick_winner` → roll back losers → `build_patch` re-checked by `guard.diff_violations`. Outputs: Markdown/HTML report, `git apply`-able `.patch`, `.diagnosis.json`, `.loops.jsonl`, `.attempts.jsonl`, optional JSONL event log. Exit code 0 only when a branch wins. Without `NEBIUS_API_KEY` the live router silently falls back to `FakeRouter` unless `--strict`. There is no web UI, GitHub App/Action, or HTTP API; the Netlify page is static.

### Implemented versus planned
Implemented (verified files): `pipeline.py`, `judge.py`, `guard.py` (protected paths incl. `tests?/`, `__tests__/`, `.github/`, `*.yml|yaml|ini|cfg|toml|sh`, `requirements*.txt`, path escapes), `model_router.py` (budget-doubling retry ladder 4096→32768, ≤5 attempts, per-call attempt log, hardcoded price table), `research.py` (Tavily, header `X-Tavily-Access-Mode: keyless`), `sandbox_runner.py` (`LocalSandbox` + `NebiusSandbox`), `patch_export.py`, `report.py`, `testparse.py`, `events.py`, `fakes.py`; 21 unittest files with **303** `def test_` functions (count verified; Devpost claim matches); CI `.github/workflows/tests.yml` on Python 3.10/3.12 (47 runs, latest all success).
Described with no code: making Sandboxes the default backend (default is `local`); "more languages beyond Python" (`testparse.py` parses unittest/pytest summaries; guard patterns are Python-centric); "packaging as a GitHub Action" (no `action.yml`). The python-humanize run and the 2026-09-29 sandbox race (13 ops, $0.0044) have no artifacts in the repo (a test docstring cites `nghien-cuu/thi-nghiem-sandbox-29-09/REPORT.json`, which is not committed).

### Verification method, trust boundaries, failure handling
- Correctness = the target repo's own test command exits 0 and did not time out (`ExecResult.ok`), after a confirmed red baseline. Ranking: green > red > error > not_run > blocked, then fewer failures, then fewer changed lines, then lowest id. Proposals touching tests/CI/config are refused before any sandbox op; the exported diff is re-scanned. `tests/test_race_replay.py` replays a recorded race in which a "fix the tests" branch used to win.
- Execution: default `LocalSandbox` runs the test command with `subprocess.run(shell=True)` in a temp dir — README: "no isolation". Opt-in `NebiusSandbox` (`--sandbox nebius`) uses Token Factory Sandboxes: `POST /files` upload, `POST /instances` with `Project` header, poll `GET /operations/{id}`; checkpoint/fork/rollback are pointer moves over content-addressed state-image uuids; default image `3d64cfd9-f318-3755-8375-64e0f4580db1` (python3.11-alpine).
- Trusted: the repo's tests ("the referee"), the user-supplied test command, Token Factory responses (token counts coerced to ints ≥0). Tavily results are injected as "hints".
- Failures: test timeout → returncode 124 / `timed_out=True` (a failure); `finish_reason=length` (empty or truncated) → retry with doubled budget; empty content → retry same budget; `content_filter` → fail fast; malformed JSON → tolerant repair and "salvage complete objects" (Nuitka run salvaged 2 of 4); diagnosis call failure → run ends with a note and 0 branches; fork failure → that branch `error`, others continue; follow-up edit apply failure → keep last measured outcome; Nebius op not terminal after `timeout+90 s` → `SandboxError`.

### Evaluation quality, reproducibility, cost, latency
Claimed vs present in repo:
- "303 unit tests" — verified.
- Demo run "26.4 s, ≈$0.003" (Devpost) / "≈$0.0042, 7,543 tokens" (demo page) / "$0.0029–$0.0042" (README): one live web-grounded run is committed (`examples/live-run-web-grounded/`: $0.0037, 5,071 tokens, events with `t` offsets); the 26.4 s figure is not in an artifact I found.
- tomlkit #619: two live runs, both **red** (reports, `diagnosis.json`, events, stdout committed; ~$0.047 and ~$0.098); final patch hand-written (`final-patch/`, "1060 passed" text log).
- greynoise #7778: run-1 parse failure, run-2 all red (committed; 82.9 s, $0.0095). The claimed "third run went green 11/11 on its own" exists only as a raw model reply used as a test fixture (`tests/data/greynoise-reply-run3-2026-10-01.txt`); the claimed Sandboxes runs A/B ("34/34 ops, ≈$0.0259/$0.0253") have **no committed artifacts**, although the demo page says "raw logs ship in the repository".
- Nuitka #4063: full run artifacts (`report.md`, `winner.patch`, `diagnosis.json`, `attempts.jsonl`, `loops.jsonl`, `run.log`, referee logs, `MANIFEST-sha256.txt`); $0.0245 / 91,587 tokens.
- humanize (6 failing → green, 7.6 min, $0.026): no artifacts.
Cost figures are computed client-side from a hardcoded table ($0.30/$0.90 Super, $0.06/$0.24 Nano per M tokens), not billing exports. There is no benchmark set, success-rate table, or aggregate results file; each case is n=1, and 2 of the 3 upstream-PR cases were hand-completed. Offline `--fake` mode is deterministic; live runs are re-runnable from the documented commands.

### UI clarity, onboarding, presentation
- Demo https://fixfork.netlify.app: HTTP 200 (Netlify), 13.7 KB static HTML, no scripts/forms/API. It is a **hosted replay** of one recorded run ("generated from the run's raw artifacts by script on 2026-10-07"): race table, hypotheses, winning diff, a sandbox A/B table, models/cost, quickstart, YouTube embed. Not a live execution service.
- README: clear offline quickstart (no key) and live quickstart, Mermaid flow, an explicit "Status: early development" block, badges.
- Video: YouTube `A6xS5TFVJs4`, "FixFork — race 3 AI fixes, keep the proven one (Nebius x NVIDIA demo)", **1 min 51 s**, public, uploaded 2026-09-28, 5 views at fetch.

### Evidence of external use, feedback, or maintainer adoption
- Repo: 0 stars, 0 forks, 0 watchers, 0 issues, 0 PRs; 1 contributor. 63 of 65 commits are authored as `agent-hackathon <hackathon-agent@local>` (unlinked identity), 1 as `agent <agent@local>`, 1 by `tuyentran4992`.
- All PRs authored by `tuyentran4992` (GitHub search: 5; none in team-owned repos):
  1. **python-poetry/tomlkit#620** — merged by `frostming` (top maintainer, 179 commits) 2026-09-30T00:38:54Z, 66 min after opening; +52/−1, 2 files, 24/24 checks; 0 review comments. Issue #619 filed by external user `mgorny`. The repo's own `examples/tomlkit-619/README.md` states: "The final patch was **not** produced end-to-end by the tool." Head commit authored as `agent-hackathon`, unsigned.
  2. **OpenCTI-Platform/connectors#7820** — closed by the author himself 2026-10-01 ("signed commits required"), superseded.
  3. **OpenCTI-Platform/connectors#7821** — open since 2026-09-30; labels `community`, `vibe-coded` (Filigran automation); Copilot bot "Approval recommended"; checks 17 success / 3 failure / 3 skipped; no human maintainer review as of fetch. Issue #7778 filed by Filigran staff.
  4. **habit-hooks/habit-hooks#200** — open since 2026-10-06; maintainer `devill` left two change requests 2026-10-15 (ruff `max-args`, `details.content`); author pushed fixes 2026-10-16; CI gated `action_required` (first-time contributor).
  5. **habit-hooks/habit-hooks#201** — open, created 2026-10-16 (not mentioned on Devpost).
- Tally: 3 external repositories, **1 merged** PR, 3 open, 1 self-closed; maintainers involved: `frostming` (merge), `devill` (review). Nothing indicates any maintainer ran or adopted FixFork — merges/reviews are of human-finished patches submitted by the author. "Pointed at N upstream issues" ≠ N users: no user other than the author is observable, and no testimonials exist.

### Nebius / NVIDIA usage
- `model_router.py`: `nvidia/nemotron-3-super-120b-a12b` (diagnosis) and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` (repair loop) via `https://api.tokenfactory.nebius.com/v1/chat/completions`, Bearer `NEBIUS_API_KEY`, temperature 0.2, stdlib `urllib`; committed raw replies and attempt logs evidence real Token Factory calls.
- Sandboxes: `NebiusSandbox` implemented against `https://api.tokenfactory.nebius.com/sandboxes/v1` (opt-in; local temp dirs by default). Its 18 unit tests use an injected fake transport; no live sandbox-run artifact (ops JSON) is committed, so live sandbox execution is author-reported.

### Observed vs author-reported vs unknown
| Claim | Observed | Author-reported | Unknown |
|---|---|---|---|
| 3-branch race, judge, referee guard, patch export | code + 303 tests | | |
| Nemotron Super + Nano via Token Factory | code, raw replies, attempt logs | | |
| Token Factory Sandboxes backend | code (`NebiusSandbox`) | live runs: 13 ops/$0.0044; A/B 34/34 ops | |
| Demo run 26.4 s / ≈$0.003–0.0042 | one run's report + events ($0.0037) | 26.4 s timing | |
| tomlkit #620 merged by maintainer in 66 min | GitHub API (frostming) | | |
| tomlkit patch produced by the tool | contradicted by repo README (hand-completed) | | |
| greynoise run 3 "all three branches green" | raw reply fixture only | run report | |
| connectors #7821 "automated review recommends approval" | Copilot bot review | | human review pending |
| habit-hooks #200 "6/6 green on every branch" | | yes (no artifacts) | |
| humanize 310/310, 7.6 min, $0.026 | | yes (no artifacts) | |
| Nuitka #4063 one-line fix verified by referee | full artifacts | | |
| Demo page is live | no — static replay | | |
| Video public, under 2 min | yes (1:51) | | |
| External users / testimonials | none | | |

### Repository facts
`tuyentran4992/fixfork` — created 2026-09-28T10:04:32Z; pushed 2026-10-13T05:10:41Z; default branch `master`; **65 commits**; first commit 2026-09-27T15:53:23Z, last 2026-10-13T05:10:33Z; languages: Python 100% (372,308 bytes); license MIT (API metadata `mit` + `LICENSE` file, 1,067 bytes); 0 stars, 0 forks, 0 watchers, 0 open issues; 1 contributor; CI present (`.github/workflows/tests.yml`, 47 runs); tests present: 21 files / 303 test functions (unittest); size 271 KB, 99 files (52 under `examples/`).
