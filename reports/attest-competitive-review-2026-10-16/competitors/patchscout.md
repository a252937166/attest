# PatchScout — competitor report (Nebius x NVIDIA Global AI Hackathon)

### Identity
- Devpost: https://devpost.com/software/patchscout — fetched 2026-10-16 17:23:43 UTC (HTTP 200 via curl/Chrome UA).
- Title: **PatchScout**. Tagline: "From production failure to evidence-backed patch: research, reproduce, fix, and verify autonomously."
- Team: 1 — Alaric Zhao (Devpost `wobenduoqing1999`). GitHub: repo owner `zhaofeipeter` (61 public repos); all 11 commits by `wobenduoqing1999-max` ("Fei Zhao", account created 2025-07-31, 0 public repos).
- Submitted to: Nebius x NVIDIA Global AI Hackathon; Devpost text: "Primary track: Coding & Agentic Engineering", "Additional prize fit: Best Use of Tavily". Started Sep 26, 2026 12:00 AM EDT; **1 update** (Oct 05, 2026 10:05 PM EDT, "Nebius and NVIDIA tool feedback").
- Built with: nebius-token-factory, next-js, nvidia-nemotron, react, tavily, token-factory-sandboxes, typescript, vercel.
- Links: demo https://patchscout-five.vercel.app/ · repo https://github.com/zhaofeipeter/patchscout · video embed YouTube `XOSVHTOCFdc`.
- Likes/comments: no numeric like counter; no comments.

### User and problem served
JavaScript/npm developers whose service breaks after a major dependency upgrade (worked incident: Express 4→5, `app.all("*")` → "Missing parameter name"). Pitch: retrieve current upstream docs with Tavily, have Nemotron propose the smallest search/replace edit, and only call it fixed when the same `npm test` that failed before passes after, inside a Nebius sandbox.

### Complete workflow a user can actually perform today
Entry points (code): a Next.js web UI (`src/app/page.tsx`) and two routes — `POST /api/agent` `{repoUrl, incident}` (`maxDuration = 300`) and `GET /api/sandbox` (spawns a disposable `tag:ubuntu:latest` instance, returns `{ready, message}`). No CLI, GitHub App/Action, or SDK.
Flow (`src/lib/agent.ts: runPatchScout`): if `PATCHSCOUT_MODE !== "live"` or no `NEBIUS_API_KEY`, it returns a hardcoded `demoResult` (mode `"demo"`, canned "DEMO TRANSCRIPT PASS 8 tests" output and fixed durations). Live: (1) `inspectRepository` — GitHub API tree + raw files, github.com only, top-10 files by priority (package.json, README, test/, src/, JS/TS), 28k-char budget; (2) `researchIncident` — Tavily (keyless or keyed), two domain-restricted queries built from npm/GitHub metadata plus a broad fallback, 24 h on-disk cache, labeled "[Fallback metadata]" sources if all fail; (3) `reasonWithNemotron` — strict JSON with `edits[{path,search,replace}]`, `tests[]`, `confidence`; one re-prompt if no edits; (4) `executeMigrationInSandbox` — `contree-client`: import/reuse `node:22-bookworm` image, `git clone --depth 1 && npm ci`, run the baseline test command, apply edits via an in-sandbox Node script (path may not contain `..` or lead with `/`; `search` must be unique), `git diff --check`, rerun the test; (5) one bounded repair pass if the after-exit is non-zero, reusing the clean dependency-installed checkpoint image. The UI shows a mode badge, 5-stage trace, evidence links, diff, confidence, and a "Token Factory Sandbox" panel with operation id and baseline/after exit codes. "Load demo" only fills in the sample fixture repo and incident text.

### Implemented versus planned
Implemented: `src/lib/agent.ts` (35 KB), `src/lib/sandbox.ts` (16 KB, contree-client), `src/lib/repo-inspector.ts`, `src/lib/outbound-fetch.ts`, `src/app/api/agent/route.ts`, `src/app/api/sandbox/route.ts`, `src/app/page.tsx`, probe scripts `scripts/probe-{nebius,sandbox,tavily}.mjs`, CI (`npm ci`, `build`, `lint`). Public fixture repo `zhaofeipeter/patchscout-fixture-express5` (1 commit, 6 files, `node --test`, intentional `app.all("*")`).
Absent: **no tests at all** (no test directory, no `test` script; CI only builds and lints). No "What's next" section on Devpost. "Rollback" is a stored pointer to the pre-patch image uuid (`rollbackImage`), never an executed action. Non-npm repos are unsupported (setup command hardcodes `npm ci|install`; inspector requires github.com). The supposedly generic research query hardcodes Express-specific terms ("wildcard route syntax", "named wildcard root path splat braces"), so the research stage is tuned to the demo fixture. The README also claims a "Best Apps & Agents" track fit.

### Verification method, trust boundaries, failure handling
- Correctness = `baselineExit !== 0 && afterExit === 0` for the same command inside the sandbox (`sandbox.ts`). Model-reported test status is overwritten by the sandbox result; the prompt says "Do not claim tests passed unless execution evidence is supplied".
- Trust boundaries: the verification command is the model's `tests[0].command` (prompted to copy it verbatim from the incident) or `npm test` — a model-chosen shell command runs in the microVM with networking enabled. There is no guard against the model editing test files or `package.json` scripts; only path-escape and uniqueness checks exist. `confidence` is the model's own number clamped to [0,1] (default 0.7): despite "the model never grades its own work", the displayed confidence is model-graded (pass/fail is not).
- Execution location: Nebius Token Factory Sandboxes (contree-client; project from `NEBIUS_PROJECT_ID`, default `"default-project"`). Repo inspection, Tavily and Nemotron calls run on the Vercel server.
- Failure handling: Nemotron HTTP retries (5 attempts, exponential backoff, 30 s timeout); unparseable JSON throws → route returns HTTP 500 (no retry on parse failure); empty edit list → one re-prompt, then error; Tavily failure → cache → labeled metadata fallback; sandbox setup/patch failure → `sandbox.status = "failed"`, verify step `failed`, message shown. Timeouts: setup 300 s, baseline/after tests 180 s, patch 120 s, inspection 60 s, route `maxDuration` 300 s — the author notes runs "could exceed one minute" and that durable jobs/polling are missing.

### Evaluation quality, reproducibility, cost, latency
- Claimed: one fail-before/pass-after run on the Express 5 fixture (baseline exit 1 → patched exit 0), "verified locally on 2026-09-26" and again as "production verification" on the deployed app. Artifacts: `E2E_PROOF.md`, `ONLINE_E2E.txt`, `PROJECT-RETROSPECTIVE.md` — prose statements only; no operation IDs, stdout logs, JSON/CSV results, or screenshots are committed.
- The Devpost update states: "Our current evidence demonstrates one migration fixture, not broad reliability across arbitrary repositories" and "We did not record onboarding time". No token, cost, or latency figures anywhere; the code does not record usage.
- Reproducibility: demo mode is deterministic hardcoded text; the live path can be re-run by anyone with keys. The single fixture was authored by the same person on 2026-09-25 ("Deliberately broken Express 5 wildcard fixture").

### UI clarity, onboarding, presentation
- Demo https://patchscout-five.vercel.app/: HTTP 200 (Vercel; `x-vercel-cache: HIT`, `age` ≈ 20.5 days for the static shell). Dark single-page UI: "Incident intake" form (Repository, Incident), "Load demo", "Run PatchScout", a 5-stage agent trace, and an "Evidence pack" results panel. Liveness: by code it is a **live execution service** (the client POSTs to `/api/agent`; the deployed JS chunk references `/api/agent` and the `"live"` badge). I did not trigger a run (it would spend the team's model/sandbox budget), but `GET /api/sandbox` returned `{"ready":true,"message":"Token Factory Sandboxes spawn access is active."}` in 4.3 s at 17:35 UTC, confirming live sandbox credentials on the deployment.
- README: clear `.env.example`, `npm install/dev`, demo-vs-live explanation, API contract.
- Video: YouTube `XOSVHTOCFdc` is **private** ("This is a private video. Please sign in to verify that you may see it."; oEmbed 403). The Devpost embed will not play for judges.

### Evidence of external use, feedback, or maintainer adoption
0 stars, 0 forks, 0 watchers, 0 issues, 0 PRs on both the main repo and the fixture repo; 1 contributor; no PRs to external repositories; no testimonials. `PROJECT-RETROSPECTIVE.md` frames the project as an exercise for an "AI Company OS" delivery pipeline (onboarding to Nebius/Tavily/Vercel/YouTube/Devpost "without repeated human decision-making"), not as a tool with users.

### Nebius / NVIDIA usage
- Inference: `nvidia/nemotron-3-super-120b-a12b` only (no Nano), via `https://api.tokenfactory.nebius.com/v1/chat/completions` with `response_format: json_object`, `reasoning_effort: "low"`, `reasoning_budget: 1024`, `max_tokens: 2800`, temperature 0.1 (`agent.ts`, `scripts/probe-nebius.mjs`).
- Sandboxes: `contree-client ^0.4.0` against `https://api.tokenfactory.nebius.com/sandboxes`, image import `docker://docker.io/library/node:22-bookworm` tagged `patchscout-node22-bookworm`, `InstanceNetworking enabled`; live access confirmed by my `GET /api/sandbox` probe. Nebius AI Cloud: not used (author states this).

### Observed vs author-reported vs unknown
| Claim | Observed | Author-reported | Unknown |
|---|---|---|---|
| Web UI + `/api/agent` + `/api/sandbox` | code; deployed, HTTP 200 | | |
| Nemotron 3 Super via Token Factory | code | | |
| Token Factory Sandboxes execution | code; `GET /api/sandbox` → ready:true | | |
| Tavily research with official-domain ranking | code | | |
| Express 5 fixture: exit 1 → exit 0 | | prose only (`E2E_PROOF.md`) | |
| "Production verification" on deployed app | | yes | not re-run by me |
| Bounded automatic repair | code | | exercised live? |
| "Model never grades its own work" | pass/fail is executable | | `confidence` is model-reported |
| Build/lint green, CI included | 4 runs, all success | | |
| Generality beyond the Express fixture | contradicted: Express terms hardcoded in research query | | |
| Demo video | private — not viewable | | |
| External users / feedback | none | | |

### Repository facts
`zhaofeipeter/patchscout` — created 2026-09-25T13:06:39Z; pushed 2026-09-26T04:06:25Z (no code changes since); default branch `main`; **11 commits**; first 2026-09-25T13:04:51Z, last 2026-09-26T04:05:23Z (~15 h span); languages: TypeScript 86,822 / JavaScript 5,693 / CSS 488 bytes; license MIT (API metadata `mit` + `LICENSE` file, 1,065 bytes); 0 stars, 0 forks, 0 watchers, 0 open issues; 1 contributor (`wobenduoqing1999-max`); CI present (`.github/workflows/ci.yml`, 4 runs, all success); tests: **none (0)**; size 118 KB; 34 files (package-lock.json is 236 KB of it).
