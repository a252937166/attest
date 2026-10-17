# runanchor — competitor report

### Identity
- Devpost URL: https://devpost.com/software/runanchor-receipts-your-coding-agent-can-t-fake (fetched 2026-10-16 17:23:26 UTC, HTTP 200)
- Title: "runanchor — receipts your coding agent can't fake". Tagline: "Agents say "tests pass." Who checks? runanchor anchors every coding-agent run to provider-issued execution records — replay-verified, oracle-tested, adopted on evidence."
- Team: 1 person, Devpost handle `tatsuya7899` (GitHub `tatsuya7899`); `submit/form-answers.md` says Submitter Type Individual, Japan.
- Hackathon: Nebius x NVIDIA Global AI Hackathon; track "Coding and Agentic Engineering" (form answers). Devpost submission timestamp shown: 2026-10-01 17:49 EDT. No winner badge.
- Built with: ai-agents, code-verification, contree, developer-tools, nebius, nebius-sandboxes, nebius-token-factory, nemotron, nvidia, python.
- Links: repo https://github.com/tatsuya7899/runanchor (only "Try it out" link; no hosted demo); video YouTube 2t0kjMcWIm0 ("runanchor demo — receipts your coding agent can't fake (Nebius × NVIDIA Global AI Hackathon)", 101 s, unlisted, 0 views, published 2026-10-14).
- Likes/comments: like-count element empty; 0 comments visible.

### User and problem served
Developers or teams running autonomous coding agents who need to know whether "done, all tests pass" is true. runanchor records each sandbox run as a receipt anchored to Nebius Sandboxes (ConTree) operation and image UUIDs, re-executes the recorded command from the recorded start image, runs a hidden test oracle against the produced result image, and keeps every outcome (adopted, rejected, unresolved) on a hash-chained append-only ledger.

### Complete workflow a user can actually perform today
From `app/runanchor/cli.py` (`pyproject.toml` script `runanchor = runanchor.cli:main`):
- Offline, no credentials: `pip install .` then `runanchor demo` replays recorded fixtures (`app/fixtures/demo/ops.jsonl`, 3 ops: red, red, green) through `DemoDriver`, issues 3 `[DEMO]` receipts, runs a fixture replay+oracle verify, rejects one, adopts one; `runanchor list`, `show <id>`, `check` (ledger chain audit).
- Live (needs `contree` CLI with Sandboxes beta access and `NEBIUS_API_KEY` or the `contree auth` profile token): `runanchor run "<task>" --image python:3.12-slim --file host:instance` (Nemotron planner loop writes/runs commands in the sandbox, each run receipted), `runanchor verify <id> [--oracle-dir DIR]`, `approve`/`reject --reason`, `bench` (54-item corpus measurement), plus `scripts/bench_live_runanchor.py` and `scripts/e2e_live_runanchor.py`.
- No web UI, no GitHub App/Action, no HTTP API. Sandbox access is via `subprocess` calls to the `contree` binary (`ContreeDriver`), not an SDK.

### Implemented versus planned
Implemented: receipt schema and fingerprinting (`receipt.py`), hash-chained ledger with integrity check (`ledger.py`), replay + isolated hidden oracle (`verifier.py`, runner under `python3 -I -S`, random mount path), gate (`gate.py`), Nemotron planner (`agent_loop.py`) and judge (`judge.py`, retry + `unparseable` flag), secret scrubbing (`sanitize.py`), bench harness (`bench.py`), corpus of 54 tasks with `label.json`, `seed/`, hidden `oracle/` (`app/corpus/`), eval reports v1–v4 and ledgers (`eval/`), bench Docker image (`eval/runanchor-bench-image/Dockerfile`), 138 offline tests.
Planned / no code: pristine-interpreter oracle mount and frozen `sys.path` ("What's next"; the v4 report admits a workspace `os.py` could shadow stdlib inside the oracle), per-run cost metering (receipts carry `consumed_cpu_s`/memory fields from ConTree but no token/cost accounting), `contree op events` payload parsing "unverified" per README. `diff_sha256` is always `None` for ConTree runs.

### Verification method, trust boundaries, failure handling
- Method: two axes. Replay: `driver.use(receipt.image_uuid)` then rerun the recorded command disposable (`-D`), compare exit code and sha256 fingerprints of streams normalised for timings/timestamps/tmp paths. Oracle: fork `result_image_uuid`, mount hidden tests at `/tmp/.runanchor-oracle-<random>`, run pytest via an isolated runner; exit 0 pass, 1 fail, other "error" (not counted as defect). A Nemotron judge then reads evidence (task, command/exit/tails, replay verdict, oracle outcome) and returns adopt/reject JSON; humans can approve/reject directly.
- Trust: the anchor is the provider's operation UUID (`anchor_source` run-json / head / demo); demo receipts are force-marked and cannot verify against live driver. The oracle trusts the image's interpreter and site-packages; an agent that modified those could still poison it (documented). `result_image_uuid` equality was dropped as an axis after measuring it is not reproducible across sessions. Planner-emitted file mounts are ignored (confused-deputy guard).
- Failure handling: missing binary or 600 s subprocess timeout yields a `DRIVER_ERROR` record that still lands on the ledger; replay infra failure yields "unverifiable", not mismatch; scrubbed commands (`REDACTED`) are unverifiable; unparseable judge output is retried once then recorded as fail-safe reject with `unparseable=True`; series that never reach green are marked `unresolved`; `runanchor check` fails closed on a missing ledger. The planner loop ends on planner exception, empty command, or `max_iter`.

### Evaluation quality, reproducibility, cost, latency
- Claimed (Devpost/README): on 54 run series, gate sensitivity 100% (11/11, Wilson 95% CI 74–100%), specificity 98% (42/43); evidence-only judge 64% / 91%; 0/108 unparseable verdicts; 455 anchored ledger snapshots; sandbox cost $0 (beta); $0.30 total project inference through 10-01 with the v4 increment "est. ~$0.4".
- Artifacts: `eval/bench-20261001-v4.json` (54 rows; recomputed here: truth good 43 / defective 11, gate (good→adopted 42, defective→rejected 11, good→rejected 1 = `seeded-manual-exit`), evidence-only matrix tp7 fn4 tn39 fp4, all truths oracle-derived, all replays match); `eval/bench-ledger-20261001-v4.jsonl` (455 snapshots, 344 distinct receipts, 54 tasks; hash chain independently recomputed with no breaks; 455/455 `anchor_source=run-json`, all `model=nvidia/nemotron-3-super-120b-a12b`, decisions by `judge:nvidia/Nemotron-3_5-Lightning`, 54 replay and 54 oracle op UUIDs, issued 2026-10-01 13:26–14:15 UTC). Earlier v1–v3 reports and ledgers are also committed, including a retracted v1 interpretation. The judge is shown the oracle outcome that also defines truth, so the two layers are not independent (stated by the authors).
- Reproducibility: corpus, judge prompt, bench script and Dockerfile are committed; live reproduction requires Sandboxes beta access. Provider-side op UUIDs cannot be verified without the team's Nebius account. Cost figures come from the console, not per-run metering; no latency figures beyond per-op `duration_s` (mean 0.55 s in ledger).

### UI clarity, onboarding, presentation
- No hosted demo; the Devpost "Try it" is `git clone`, `pip install -e .`, `runanchor demo` (fully offline). This is a CLI replay of recorded fixtures, not live execution; live mode needs beta sandbox access. Demo status: not applicable (no URL).
- README is clear: measured table with CIs, architecture ASCII diagram, a "Token Factory / Nebius usage depth" table with live-verified dates, demo and live command lists, reproduce section. Some internal docs (`bd/`, `eval/BASELINE.md`) are in Japanese with English summaries.
- Video present (1:41, unlisted); `submit/form-answers.md` says it was re-captured 2026-10-14 after Devpost flagged an earlier rendered version. Gallery: 4 images (title card, measured result, receipt fields, under-the-hood). Narration claims are mapped to evidence in `submit/narration-claims.md`.

### Evidence of external use, feedback, or maintainer adoption
- Stars 0, forks 0, watchers 0, open issues 0, 1 contributor (tatsuya7899), no issues or PRs from anyone. GitHub PR search for author `tatsuya7899`: 0 PRs anywhere. No PRs opened against other repositories, no testimonials. The 54 "runs" are the team's own benchmark corpus, not users. `bd/review-*` files are self/adversarial reviews by the author's own process.

### Nebius / NVIDIA usage
- Inference: Token Factory `https://api.tokenfactory.nebius.com/v1/chat/completions` (`agent_loop.py`, `judge.py`) via `urllib`. Models: planner default in code is `nvidia/Nemotron-3_5-Lightning` (`DEFAULT_MODEL`, CLI `--model`), while the committed v4 bench and Devpost text use `nvidia/nemotron-3-super-120b-a12b` as planner (ledger confirms 455/455) and `nvidia/Nemotron-3_5-Lightning` as judge (ledger decision `by` confirms). `seed` passed but documented as non-deterministic.
- Sandboxes: yes, via the `contree` CLI (`contree -S <session> -o json run|use|op show|op events|session delete`), image `runanchor-bench` built from `python:3.12-slim`; all 455 ledger ops carry UUID-shaped operation and image ids. Tavily: "No" (form answers).

### Observed vs author-reported vs unknown
| Claim | Observed | Author-reported | Unknown |
|---|---|---|---|
| Receipts anchored to ConTree op/image UUIDs | Driver code; 455 ledger records with UUIDs | | Whether UUIDs resolve on Nebius (needs their account) |
| Replay + hidden oracle verification | `verifier.py`; v4 rows show replay/oracle fields | | |
| Hash-chained ledger intact | Recomputed: 0 breaks over 455 lines | | |
| Gate 100% (11/11) / 98% (42/43) | Recomputed from committed rows | | Generalisation beyond this self-built corpus |
| Evidence-only 64% / 91% | Recomputed from rows | | |
| 0/108 unparseable | `gate_unparseable`/`evidence_unparseable` fields exist | Count stated in report | Not recounted here |
| Planner Super-120B, judge Lightning in bench | Ledger model/decision fields | | |
| $0.30 inference, $0 sandbox | | Console figures in README | No per-run metering |
| `runanchor demo` works offline | Code + fixtures | | Not executed here |
| Live `runanchor run` works | | README "live-verified" dates | Not exercised; needs beta |
| External users/adoption | None found | | |

### Repository facts
- owner/repo: tatsuya7899/runanchor; created_at 2026-09-29T03:22:20Z; pushed_at 2026-10-14T12:19:18Z; default branch `main`.
- Commits: 60 (first 2026-09-29T03:22:08Z "Initial: 企画書(runanchor・旧agent-receipt)..."; last 2026-10-14T11:36:18Z "submit: record published YouTube URL for the re-captured demo"), all by tatsuya7899.
- Languages: Python 270,299 B; Shell 6,964; Swift 5,137 (terminal capture script); Dockerfile 289.
- License: MIT in metadata and `LICENSE` file.
- Stars 0, forks 0, watchers 0, open issues 0, contributors 1.
- CI: none (no `.github/`; `feature-map.yaml` and `scripts/verify` are local). Tests: `app/tests/` 9 files, 138 test functions (offline). Evaluation data: `eval/bench-2026093{0,1}-v{1..4}.json/.md`, four ledgers (up to 731 KB), 54-item corpus. Size 11,886 KB (includes `submit/runanchor-demo.mp4` ~2 MB and narration audio). Repo fetch 2026-10-16 17:25:50 UTC.
