# MUTINY — competitor report

### Identity
- Devpost URL: https://devpost.com/software/mutiny (fetched 2026-10-16 17:23:21 UTC, HTTP 200)
- Title: MUTINY. Tagline: "Every review tool reads the diff and gives you an opinion. MUTINY runs both versions and hands you the input where they disagree. Not a guess about the code. An execution trace of it."
- Team: 1 person, Devpost handle `TusharTechs` (GitHub `TusharTechs`); page says "Solo build."
- Hackathon: Nebius x NVIDIA Global AI Hackathon (nebiusglobalaihackathon.devpost.com). README says "Coding and Agentic Engineering track". Devpost submission timestamp shown: 2026-09-21 15:50 EDT. No winner/prize badge.
- Built with (Devpost tags): agentic-ai, ast, differential-testing, fastapi, github-actions, llm, microvm, nebius, nebius-sandboxes, nebius-token-factory, nemotron-3-super-120b-a12b, nvidia-nemotron, property-based-testing, pytest, python, tavily, upstash-redis, vercel.
- Links: repo https://github.com/TusharTechs/mutiny; demo https://mutiny-verify.vercel.app; example PR comment https://github.com/TusharTechs/mutiny/pull/1; video YouTube rEXkEmhaqmc ("A refactor said nothing changed. Here is the input that proves otherwise!", 178 s, 17 views, published 2026-09-21).
- Likes/comments: like-count element rendered empty (no likes shown); 0 comments visible.

### User and problem served
Reviewers and maintainers merging "refactor, no behaviour change" pull requests (increasingly agent-written) where the existing test suite passes but behaviour silently changed. Instead of an LLM reading the diff, MUTINY executes the before and after versions on model-generated inputs and reports the concrete input on which they disagree, only when the PR does not itself announce a behaviour change.

### Complete workflow a user can actually perform today
Based on `mutiny/cli.py`, `action.yml`, `app/server.py`:
- CLI (`pyproject.toml` script `mutiny = mutiny.cli:main`): `mutiny verify <repo> <Function>` (Nemotron rewrites a function, then differential-tests the rewrite; `--local` runs probes on the host), `mutiny verify-diff <repo> --base --head`, `mutiny verify-url https://github.com/owner/repo[/pull/N]`, `mutiny review-pr` (CI mode), `mutiny pin --url ... --side before|after` (writes a pytest file pinning observed values), `mutiny doctor` / `scripts/doctor.py`.
- GitHub Action: composite `action.yml` runs `mutiny review-pr`; `.github/workflows/mutiny.yml` is the example and runs on the repo's own PRs. Observed output: `github-actions[bot]` comment on TusharTechs/mutiny#1 reporting `_is_source("myconf.py")` before `True` / after `False`, with a pinned test.
- Web UI/API: FastAPI app (`app/server.py`) with `/api/examples`, `/api/run/{example_id}`, `/api/run-url?url=` (SSE stream), `/api/health`; deployed on Vercel. Setup: clone, `pip install -e ".[dev]"`, `.env` with `NEBIUS_API_KEY`, `NEBIUS_PROJECT_ID`, optional `TAVILY_API_KEY`.

### Implemented versus planned
Implemented (files): differential engine `mutiny/differential.py` (canonicalisation, `confirm()` with 3 samples), sandbox executor `mutiny/sandbox.py` (ConTree SDK, checkpoint + forks, thread pool), Token Factory client `mutiny/models.py` (cap, ledger, cache, reasoning-aware retry), GitHub Action `mutiny/ci.py` + `action.yml`, documentation check via Tavily `mutiny/contract.py`, construction recipes `mutiny/construct.py`, pinning `mutiny/pin.py`, hosted demo `app/`, budget guard `mutiny/budget.py` (Upstash Redis), 27 experiment result JSONs under `experiments/*/results/`, findings docs under `docs/`.
Planned / no code: "languages other than Python" (code is Python/AST only), "a confidence signal strong enough that a team could gate a merge on it" (Action never fails builds), decomposed construction of nested objects (sqlalchemy case; `docs/findings-construction.md` says it still cannot build these). The "40 of 45" verdict figure is stated in `docs/findings-construction.md` but the latest committed results file (`experiments/prs/results/prs-20260913-182422.json`) contains 36 verdicts; no results artifact for the 40/45 run is committed.

### Verification method, trust boundaries, failure handling
- Method: Nemotron generates call expressions only ("the model writes inputs, never assertions"); both versions run on the same inputs; `differential.compare` diffs canonicalised repr/type/exception. Canonicalisation strips memory addresses (`_strip_addresses`), sorts sets/dicts, pins `PYTHONHASHSEED=0`; `confirm()` reruns each version 3 times and discards self-inconsistent probes; opaque values (no usable repr) are excluded.
- Execution: Nebius Sandboxes via `contree_sdk.ContreeSync`; one non-disposable checkpoint (`disposable=False`) then forks per probe batch, up to 40 concurrent, with the head version laid over the fork via file overlay. `--local` subprocess fallback exists. The hosted demo installs and runs arbitrary public GitHub repos inside sandboxes, not on the server (`app/server.py`).
- Trust boundaries: Token Factory key + project id in secrets; GitHub token only needs `pull-requests: write`. The sandbox is the isolation for untrusted PR code. Tavily-quoted sentences are verified against the fetched page or dropped (README; `contract.py`).
- Failure handling: `_check()` raises on non-zero sandbox exit; driver payload marker missing raises; `BudgetExceeded` before overspend; truncated empty Nemotron replies are detected and abandoned (`models.py`); one fork failure does not kill the run (`session.py`); Action exits 0 always but emits `::error` annotations and a step summary when it cannot run (`ci.py.annotate`), explicitly added after a credential-less run went green silently. Public demo: per-run cap $0.25, total cap $15 (Redis-backed), 20 runs/hour/IP.

### Evaluation quality, reproducibility, cost, latency
- Claimed: 49 merged PRs from 12 libraries, 45 with behaviour to check, 36 (docs) / 40 (Devpost) verdicts, 12 divergences; 18 agent refactors, 17% rejected by tests, 0 false alarms on 14 accepted; 62% detection on 24 fix commits; 40 forks in 3.7 s vs 50.4 s sequential; Django 2,932 files end to end in 83 s; ~$0.005 per verification; $0.39 for the PR corpus.
- Artifacts present: `experiments/prs/results/prs-20260913-182422.json` (49 rows; outcomes preserved 24, divergence 12, no-probes 4, new-code 3, error 3, no-target 2, nothing-to-verify 1; recorded cost sum $0.39 over 30 rows with cost, mean run 56 s, max 164.5 s), `experiments/limits/results/limits-20260913-144808.json` (django/django: 2932 files, 12 probes, stage times summing to ~82.7 s), refactor/diff/thin result JSONs, `docs/findings-*.md` including a documented retraction. Runner scripts `experiments/*/run.py` are committed; reproduction requires a Nebius key and GitHub access. The 40-fork timing and model-comparison table are described in README/docs with no raw timing file identified. Six false-finding classes documented in `docs/findings-limits.md` / `findings-differential.md` / `findings-pull-requests.md`.

### UI clarity, onboarding, presentation
- Demo: https://mutiny-verify.vercel.app GET 200 (HEAD returns 405). Page is a single-page UI: URL box ("Point it at your own code"), four example cards, live timeline, fork grid, verdict. `/api/health` returned `{"ok":true,"sandboxes":true,"detail":"concurrency limit 50","spent":0.0271,"cap":15.0,"cap_enforced":true}`; `/api/examples` returned four real PR/repo URLs. `app/server.py` streams `verify_url` events over SSE, so this is a live execution service with a spend cap, not a replay. A run was not triggered during this research (it would spend the team's budget); end-to-end behaviour of the hosted run is therefore not independently exercised.
- README: long, well structured, with setup for macOS/Linux/Windows, architecture diagram, reproduction commands, limitations section, and an "On AI assistance" disclosure. Badge claims "106 tests passing"; 95 `def test_` functions counted in 17 files (parametrisation may explain the gap; tests not run).
- Video present (YouTube, 2:58, public).

### Evidence of external use, feedback, or maintainer adoption
- Stars 0, forks 0, watchers 0, 1 contributor (TusharTechs), 1 open issue which is the team's own demo PR #1. No issues or PRs from other accounts.
- PRs authored by TusharTechs (GitHub search, 7 total): none related to MUTINY in external repositories. One unrelated docs PR to CALLE-AI/awesome-phone-call-agents (#334) closed unmerged 2026-10-10; older merged PRs (2023–24) to harshagrawal2503/SOMnew are unrelated.
- The PRs cited (jd/tenacity#679, python-semver#401/#480, rich#3845, shortuuid#103) are other people's already-merged PRs that MUTINY was run against; no evidence any maintainer saw or adopted MUTINY's output. "49 merged PRs measured" is a test corpus, not 49 users. No testimonials found.

### Nebius / NVIDIA usage
- Models (code `mutiny/models.py`): SUPER `nvidia/nemotron-3-super-120b-a12b` default for probe generation, refactoring, explanation; NANO, ULTRA (`nvidia/Nemotron-3-Ultra-550b-a55b`, fallback on empty reply per README), LIGHTNING defined for comparisons.
- Inference: Nebius Token Factory, OpenAI-compatible, base URL `https://api.tokenfactory.us-central1.nebius.com/v1/` (`config.py`, `.env.example`); `docs/img/token-factory.png` shows a `doctor` run (image, not verified independently).
- Sandboxes: yes, `contree-sdk==0.3.6` in `requirements.txt`, `ContreeSync` in `sandbox.py`, `NEBIUS_PROJECT_ID` required; hosted `/api/health` reports Sandboxes available with concurrency limit 50.
- Tavily used for documentation lookup (`contract.py`, optional key).

### Observed vs author-reported vs unknown
| Claim | Observed | Author-reported | Unknown |
|---|---|---|---|
| Runs both versions in Nebius Sandboxes forks | Code in `sandbox.py`; `/api/health` sandboxes:true | | |
| Nemotron 3 Super via Token Factory | Model IDs and base URL in code | | |
| GitHub Action comments on real PR | Bot comment on own repo PR #1 | | |
| Hosted demo is live execution | SSE server code; health/examples endpoints | | End-to-end hosted run not exercised |
| 49 PRs, 12 divergences, $0.39 | Results JSON matches | | |
| 40 of 45 verdicts | | Only in `findings-construction.md`; committed JSON shows 36 | |
| 40 forks in 3.7 s vs 50.4 s | | README/docs text | No raw timing artifact found |
| Django 83 s end to end | Limits JSON stages sum ~82.7 s | | |
| Zero false alarms on 14 accepted refactors | | README/docs; refactor JSONs present but not re-scored here | |
| Model comparison (42 vs 44 vs 1 inputs) | | README table | No raw file identified |
| 106 tests passing | 95 test functions counted | Badge | Not run |
| Any external user or maintainer adoption | None found (0 stars/forks, no external PRs) | | |

### Repository facts
- owner/repo: TusharTechs/mutiny; created_at 2026-09-12T06:19:39Z; pushed_at 2026-09-21T20:02:30Z; default branch `main`.
- Commits: 94 (first 2026-09-12T04:47:11Z "Gate 2: proof-test verification with anti-gaming rules"; last 2026-09-21T20:02:20Z), all by TusharTechs.
- Languages: Python 372,171 B; JavaScript 12,756; CSS 11,219; HTML 3,522.
- License: Apache-2.0 in metadata and `LICENSE` file (plus `NOTICE`).
- Stars 0, forks 0, watchers 0, open issues 1 (own PR), contributors 1.
- CI: `.github/workflows/mutiny.yml` present (runs MUTINY action on PRs; no test-runner workflow). Tests: `tests/` with 17 files, 95 test functions, plus a `tests/fixtures/samplerepo`. Evaluation data: 27 result JSONs under `experiments/`. Size 2,396 KB. Repo fetch 2026-10-16 17:24:53 UTC.
