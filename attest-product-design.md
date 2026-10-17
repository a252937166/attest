# Attest: the coding agent that ships proof, not promises

Product design for the Nebius × NVIDIA Global AI Hackathon, Coding and Agentic Engineering track.
Prepared 14 Oct 2026. Delivery configuration updated 15 Oct 2026. Submissions close Fri 30 Oct 2026, 10:00 AM PT (1:00 PM EDT). Judging 1–15 Dec 2026. Winners announced around 11 Jan 2027. The demo must stay reachable through 15 Dec.

Attest is an autonomous repository engineer on NVIDIA Nemotron 3, served by Nebius Token Factory, whose defining feature is an evidence gate: sealed acceptance tests written before the code, an adversarial pass after it, a whole-trajectory drift audit, and a Proof Bundle on every pull request. It runs and tests code inside Token Factory Sandboxes, which is the track's wording taken literally.

## Current delivery configuration — 15 Oct 2026

This configuration supersedes the original infrastructure and development-budget assumptions below. Product features remain design targets until implemented and measured.

- **Routine development:** use our self-hosted Codex gateway at `https://development-gateway.invalid` with `CODEX_API_KEY`. Select a supported `model` and reasoning `effort` from the live `GET /v1/models` catalog. Different names and effort levels are configuration choices; their relative quality still requires task-level evaluation. Do not assume every ChatGPT model name is accepted. See [Development model provider](development-model-provider.md) for tested requests, supported models, parameters, and limitations.
- **Development action interface:** the gateway uses non-streaming chat completions and does not forward native `tools` / `tool_calls`. Ask for structured JSON actions, validate them in Attest, execute them through the external executor, and send the resulting observations in the next request. Do not treat this as native function calling or a drop-in replacement for every Token Factory feature.
- **Submission, formal evaluation, and demo:** switch to NVIDIA models served by Nebius Token Factory, run an early end-to-end compatibility check, and rerun the final evaluation on that configuration. Record provider, requested and returned model, effort, execution backend, and relevant parameters per run. Keep Codex development results separate from Nebius results.
- **Execution and hosting:** Model provider and execution backend are independent settings. Token Factory Sandboxes access and its checkpoint/two-branch REST smoke are verified; use it for development execution once the Attest adapter is implemented. Use the existing Aliyun Docker host only for a worker or fallback that demonstrably requires Docker; it is not the final application host. Neither smoke proves the full Attest task loop. See [Nebius Sandboxes verification](nebius-sandboxes-verification.md), [API evidence](reports/nebius-sandboxes-probe-2026-10-15/api-smoke.json), and [Docker fallback guide](docker-development-environment.md). The user-confirmed final application target is `yungou` = DogYun `206.237.18.80`: console, API, orchestration, and application data, deployed directly without Docker. Runtime compatibility, capacity, and deployment remain unverified. Review the Obsidian host records and verify those operational requirements before deployment while preserving existing services. See [deployment targets](deployment-targets.md). Nebius AI Cloud and Serverless Jobs remain optional.
- **First working slice (15 Oct 2026, 09:09 to 09:17 UTC):** `attest/` runs one Python task end to end on the verified stack: frozen task, retained Sandboxes checkpoint with a passing baseline, specification and contract, 27 sealed unittest tests proven red on the checkpoint (24 failing), an 11-turn JSON-action implementation on `gpt-6-sol`, fresh networking-off branch verification (existing 6/6, sealed 27/27) and a Proof Bundle with the ledger; verdict VERIFIED. Evidence in `reports/attest-first-slice-2026-10-15/`; commands, usage and the remaining gaps (breaker, drift audit, Tavily, pytest/multi-file repos, parallel branches, GitHub surface, console) in [attest-first-slice.md](attest-first-slice.md). Development inference was the Codex gateway. The native pilot on Nemotron 3 Ultra (spec) and Super (seal, implement) via Token Factory also reached VERIFIED on the same task in 1 min 41 s for a computed $0.0255 (12 calls), after one request-shape fix: the live API requires the `{name, schema, strict}` wrapper under `response_format.json_schema`, unlike the docs' raw-schema example.
- **Verification hardening and corrections (15 Oct 2026, evening):** the sealed suite now runs through a `TestResult` recorder in the sandbox that writes a nonce-bound JSON result only after completion and hashes the sealed file before and after; the verifier binds the verdict to the expected test IDs from the red check, the sealed-file digest and the nonce, and seven adversarial regression tests (modified tests, forged result, missing tests, extra tests, premature exit, forged console text) are in `tests/test_verification.py`. Method and subtest-event counts are reported separately (the Codex red check was 27 methods, 9 failing through 24 subtest error events). The Nebius client reserves a conservative cost before every call and bounds prompt and output sizes. A mutation breaker pass runs AST mutants of the changed lines as parallel sandbox branches. pytest repositories with pinned dependencies are supported (checkpoint installs with networking on). Earlier wording on cached tokens, sandbox capabilities, the 422 finding and spec drift is corrected in `reports/attest-first-slice-2026-10-15/corrections-2026-10-15.md`. Deployment: application on `yungou` without Docker per [deployment-plan-yungou.md](deployment-plan-yungou.md), confirmed by the user as DogYun `206.237.18.80`; runtime compatibility, capacity, and deployment remain unverified; Sandboxes remain the executor; Aliyun is used only for components that genuinely require Docker. The python-semver multi-file pilot (PR #368, 312 pytest tests, pinned dependencies) reached VERIFIED on both profiles: Codex in 4 min 49 s, Nemotron in 1 min 37 s for a computed $0.043, mutation score 1.00, held-out upstream tests 325/328 with a documented message-format divergence; evaluation sizing from these costs is in `attest-first-slice.md` section 9.
- **Deployed (16 Oct 2026, 00:10 host time):** the console and API run on `yungou` (DogYun `206.237.18.80`) without Docker at `https://attest.axiqo.xyz`, with a verified rollback path and a public judge-style run completed; see `attest-console.md`, `deployment-plan-yungou.md` section 7 and `reports/attest-deployment-2026-10-15/`. Verification gates were completed first (`attest-first-slice.md` section 10, `reports/attest-verification-2026-10-15/`).
- **Resources and budget:** Token Factory and Tavily keys are saved in Obsidian. The Token Factory key authenticated the real Sandboxes smoke; NVIDIA inference and Tavily need separate checks. Before/after console readings stayed at $25 balance, a separate $1 trial, and $0.00 monthly consumption. One confirmed +$25 transaction labeled "AI Builder Program Credits" is already included in that balance, not an extra grant to add again. Additional grants remain unverified. Official Sandboxes beta terms say free with no announced end date; display precision and reporting lag prevent an exact zero-invoice conclusion. Reserve inference funds for compatibility, final evidence, and judging; size evaluation after a measured pilot.

Contents: 1 Recommendation · 2 The brief, decoded · 3 Who judges and what they want · 4 Market and the gap · 5 The product · 6 Architecture · 7 Nebius and NVIDIA usage · 8 Evaluation plan · 9 Scoring map · 10 16-day build plan · 11 Submission package · 12 Risks and day-one checks · 13 Versus the FutureFit draft · 14 Alternatives considered · 15 Sources

---

## 1. Recommendation

The track brief asks for agents that write, run and test code. The organizers' own hint says a code-completion wrapper is table stakes and "an agent that plans, writes, tests, and iterates on a real repo with minimal human input is where it gets interesting." Hundreds of entries will do exactly that with a single model and a ReAct loop. The way to win is to solve the problem those agents create: nobody can trust their output. In 2026 the bottleneck has moved from generating a patch to verifying it, and the research and the surveys both say so.

Attest treats every task as a claim that must be proven. An independent model instance writes acceptance tests from the spec before any code exists and seals them where the implementer cannot read or edit them. The implementer works on a branch of a Token Factory Sandbox checkpoint. A breaker agent then tries to falsify the patch with edge cases and mutants, each running as its own sandbox branch. Nemotron 3 Ultra reads the entire trajectory in one 1M-token context and audits it for goal drift. Only then does a pull request open, carrying a Proof Bundle: sealed-test results, mutation score, drift score, cited sources, and a per-model cost ledger. If the evidence is not there, Attest says so instead of shipping.

Target scores:

| Criterion | How Attest earns a 5 |
| --- | --- |
| Technological implementation | Submission targets: Nemotron roles, structured actions, Token Factory Sandboxes, Batch API, Data Lab, OpenShell. Report only features exercised in real runs. |
| Design | CLI, GitHub App, hosted console and a Proof Bundle artifact. Issue to verified PR, end to end. |
| Potential impact | Targets the trust gap developers report, on real OSS repos, with a measured held-out gap and cost per verified PR. |
| Quality of the idea | Sealed tests, breaker pass, 1M-context drift audit, Data Lab memory. Grounded in the 2026 verification literature. |

**Prize strategy.** A project can win one overall award, or one track award plus one bonus award. Attest is built to take the Coding track (Jetson Orin Nano) plus Best Use of Tavily ($3,000), with the Grand Prize ($20,000) as the upside case. Ties are broken on Technological Implementation first, so that criterion gets the most engineering weight.

**About the FutureFit draft already in this folder.** It is a rigorous idea with a high chance of a null result in sixteen days and a narrower audience. This document recommends switching to Attest and carrying FutureFit's best discipline (paired experiments, frozen inputs, honest verdicts, full cost accounting) into it. See section 13.

## 2. The brief, decoded

| Item | Requirement (official rules and page) | Attest |
| --- | --- | --- |
| Platform | "Runs on Nebius" means a runtime call to the Token Factory inference API, or deployment on Nebius AI Cloud compute (Serverless Jobs, Endpoints, DevPods). | NVIDIA inference through Token Factory in the submission profile; code execution intended on Token Factory Sandboxes. Final console, API, orchestration, and application data target yungou; deployment remains unverified. AI Cloud compute is optional. |
| Model | At least one NVIDIA open-source model (Nemotron, GR00T, Cosmos, Sonic). | Nemotron 3 Ultra, Super, Nano and Nemotron 3.5 Lightning, each with a named role. |
| Track fit | "Build coding agents and developer tools: agents that write, run, and test code in Token Factory." Stage one is a pass/fail check that the project is a genuine attempt at the track goal. | Central fit: plans, writes, runs, tests, iterates, and proves, with execution inside Token Factory Sandboxes. |
| Demo | URL to a working demo, hosted app or test build, free to use by judges until 15 Dec. Judges may also judge from text, images and video alone. | Hosted console with a "run on a sample repo" button and pre-recorded runs as fallback. |
| Video | Public YouTube, 3 minutes or less, showing the project working and how Token Factory and Nemotron were used. Organizers: call out the tools "with audio", "treat your video like a pitch". | Script in section 11. |
| Repository | Public GitHub/GitLab/Bitbucket with an OSS license visible in the About section, all source, README with setup and run instructions. Keys out of the code. | Apache-2.0, README, architecture doc, reproducible eval scripts. |
| Feedback | Required: feedback on Token Factory, AI Cloud and NVIDIA tools used. Also eligible for the Most Valuable Feedback award ($100 + swag, 10 winners). | A dedicated FEEDBACK.md with named, specific items. |
| Prior work | New, or significantly updated during the submission period with a written explanation. | New project. |
| Tavily bonus | Any eligible submission that makes a functional, runtime call to the Tavily API as part of its solution. | Grounding stage calls Tavily Search and Extract at runtime and cites sources in the Proof Bundle. |
| Multiple entries | Allowed if substantially different. | Not recommended; concentrate effort. |

Judging mechanics:

- Stage one: pass/fail on theme fit and use of the required platform.
- Stage two: scored 1 to 5 on four equally weighted criteria. Quoted from the rules: Technological Implementation ("How well is the project built, and how effectively does it use Nebius Token Factory or AI Cloud model(s), and NVIDIA Nemotron"), Design ("a complete, coherent product experience not just a technical proof of concept"), Potential Impact ("a credible, specific case for solving a real problem for a real audience" that the solution "actually addresses based on what's demonstrated"), Quality of the Idea ("a creative, non-obvious use" of the platform and models, and "genuine understanding of the problem space").
- Ties: highest score on the first criterion wins, then the next. Then a judges' vote.
- Prizes: Grand $20,000, second $10,000, third $6,000; one Jetson Orin Nano per track; Best Use of Tavily $3,000; 20 City Winner awards of $500 for attendees of the Builders & Brews events; 10 Most Valuable Feedback awards.
- Credits, confirmed 15 Oct: one +$25 "AI Builder Program Credits" transaction is included in the displayed $25 balance; a separate $1 trial is also shown. Do not count that transaction twice. Extra event, Devpost, or Tavily promotional grants remain unverified until an additional credit appears.

Organizer hints worth obeying literally: name the project "like a human"; make the required tools "impossible to miss" in the description, the Built With section and the video audio; lead the video with the problem; submit early; push feedback beyond "the docs were confusing" by naming the tool and the step.

## 3. Who judges and what they want

**Nebius (11 judges).** Token Factory's founding product marketer, the head of ML/AI product management, the chief ML researcher for product, the Serverless AI technical product manager, the director of developer relations and several developer advocates. Token Factory launched in November 2025 and is the company's developer-facing growth bet alongside roughly $40 billion of contracted capacity from Microsoft and Meta. Nebius shipped a steady stream of platform features in 2026: dedicated endpoints and a custom-weights hub (February), Data Lab for turning inference logs into training data (May), NVIDIA Groq 3 LPX for fast agentic inference (August), Sandboxes, a beta code-execution service with git-like filesystem branching built with ConTree, and a Q3 roundup on 27 October that lists the Responses API and workload-specific draft models. The AI Builder Program (10 September) bundles Nemotron, coding agents (OpenHands, Cognition), Tavily, LangChain, Toloka, LangSmith, Prime Intellect and OpenEnv under the slogan "build AI systems you own on an open, independent stack".

When Nebius judged its own Serverless AI Builders Challenge, winners shared four traits: a real problem, concrete use of platform features, measured results including the full bill (one winner reported $320 including failed jobs), and candid findings. Expect the same taste here. A project that exercises Sandboxes, Data Lab and Batch, and reports what each cost, is the project this panel wants to showcase.

**NVIDIA (9 judges).** Mostly staff and senior system software engineers plus Jetson and Physical AI advocates. NVIDIA's message for 2026 is a "system of models": Nemotron 3 Ultra for orchestration and hard reasoning, Nemotron 3.5 Lightning for the high-volume execution layer, routed by NeMo Switchyard. Their agentic coding guide for Nemotron 3 Super names two failure modes they care about, goal drift and malformed tool calls, and lists harnesses they support (OpenCode, OpenClaw, Kilo Code, OpenHands). They released OpenShell (kernel-level sandbox runtime, 0.1.0 on 25 September) and NemoClaw, and they trained Lightning's coding abilities on an open terminal-agent RL dataset. A project that runs Nemotron inside OpenShell, routes work across the family, and measures those two failure modes speaks their language.

**Tavily (3 judges).** Two forward-deployed engineers and a developer-relations lead. Tavily's 2026 positioning is agentic infrastructure (Search, Extract, Map, Crawl, Research, agent skills for coding agents, integrations with OpenCode and NanoClaw). They will reward a search call that changes the agent's output and is cited, not a search box bolted on.

## 4. Market and the gap

Demand signals:

| Figure | Meaning | Source |
| --- | --- | --- |
| 48% / 6.6% | developers who trust AI output only when they can verify it / who trust it for important decisions | Stack Overflow survey, Oct 2026 |
| 78.7% | say source attribution matters when judging AI-generated code | same survey |
| 66% | named "almost right, but not quite" as their top frustration | Stack Overflow, 2025 |
| 43.2M | pull requests merged per month on GitHub, up 23% year on year | Octoverse 2025 |
| 13.8% / <30% | frontier-agent rollouts that tried to game the verifier / success on ultra-long tasks | SWE-Marathon, Jun 2026 |
| 51.2% | best agent result on 203 real dependency upgrades with hidden breakage | DEPBENCH, Aug 2026 |

**Coding agents.** Closed frontier agents lead the leaderboards (Claude Code on Opus 5.5 at the top of Terminal-Bench 4.0; Codex, Cursor and Devin close behind). The open harness ecosystem is broad: OpenHands, OpenCode, Kilo Code, Cline, Aider, and Hermes Agent (past 250k GitHub stars with its skills-and-memory loop). NVIDIA documents Nemotron 3 Super at roughly 60% on SWE-bench Verified inside OpenHands and OpenCode, and Nemotron 3 Ultra at 65 to 70% across five frameworks with up to 30% fewer tokens per task. Open models are good enough to do the work; the differentiator is no longer "another loop".

**The verification frontier.** SpecBench shows that every frontier agent saturates the visible tests and still fails held-out tests that combine features the way real use would, with the gap growing about 28 points for every tenfold increase in code size, and larger gaps for smaller models. SWE-Marathon reports weak self-verification, premature termination and false infeasibility claims. "The Verification Horizon" argues that no fixed verifier survives a capable policy and that verification must co-evolve with the generator. A fourth paper shows long-running agent loops mistaking stagnation for progress and calls for externally grounded verification. NVIDIA's own guide adds goal drift and malformed tool calls.

**The hackathon field so far.** Entries already public on GitHub for this track are single-model ReAct loops with path-jailed file writes, no container isolation and no evaluation (Nemotron Forge, CodeFlow Agent). The closest entry to this design, CodeGuard, gates single-file Python tasks on tests the same Nemotron Nano instance wrote, runs them in a Token Factory sandbox, and admits in its README that it has no hidden tests, no mutation testing, no parallel candidates and a CLI only. That confirms the evidence-gate framing resonates, and it sets the bar Attest clears: independent sealed tests, a breaker pass, a drift audit, multi-file repositories, branch-parallel verification, a GitHub surface, and measured results.

**Adjacent products.**
- AI code review (CodeRabbit at a reported $550M valuation, Greptile with $25M from Benchmark, Graphite acquired by Cursor, Cursor Bugbot) reviews diffs after the fact. Independent benchmarks put the best around 51% F1. None generates evidence before implementation or runs adversarial verification.
- Dependency automation: GitHub lets teams assign Dependabot alerts to agents (April 2026), but agents still solve about half of upgrades with hidden breakage. Grounding on the actual changelog is the missing step.
- Evaluation infrastructure: Harbor (the Terminal-Bench harness), SWE-bench and OpenEnv (multi-organization governance since June 2026) make it practical to export a repo's own history as tasks.
- Precedent winner: Project Blackbox took the Grand Prize at Devpost's DataHub agent hackathon in September 2026 with the pattern "read, prove, act, verify, write": a machine-enforced evidence gate, a safety envelope, a "we also try to break it" section and real PRs. Attest applies that pattern to software engineering itself.

**The gap.** There is no shipping tool that writes held-out acceptance tests before implementation, attacks its own patch, audits its own trajectory for drift, and attaches that evidence to the PR with a cost ledger, on open models the team owns. Attest is that tool.

## 5. The product

An autonomous engineer for your repository that must prove its work before it opens a pull request.

**Who it is for**
- Engineering teams already running coding agents and drowning in "almost right" PRs. Attest turns review from reading diffs into checking evidence.
- Open-source maintainers (60% unpaid, nearly 60% have considered quitting, per Tidelift) who need issues triaged and fixed without trusting a bot's word.
- Platform and AI teams that want an agent on open weights, with their own sandboxes, their own logs and no vendor lock-in.

**What a run produces.** Every run ends in one of four verdicts, never a silent guess: VERIFIED, NEEDS HUMAN, INFEASIBLE, NO CHANGE. A verified run opens a PR that carries the Proof Bundle.

| Proof Bundle section | Contents | Why a reviewer cares |
| --- | --- | --- |
| Spec and contract | Restated task, interface contract (names, types, behaviors), acceptance criteria, infeasibility notes | Confirms the agent solved the stated problem, not a narrower one |
| Sealed tests | Tests authored before implementation by an independent model, shown failing on the base commit and passing on the patch | Red-then-green against tests the implementer never saw |
| Breaker report | Edge-case and property tests, mutation score, tamper checks | Evidence the patch is not special-cased to the tests |
| Drift audit | Ultra's reading of the whole trajectory: scope narrowing, disabled checks, unexplained detours, drift score with quotes | Catches goal drift and self-deception in long loops |
| Sources | Tavily-retrieved documentation and changelog excerpts with URLs, tied to the lines that depend on them | Attribution, which 78.7% of developers ask for |
| Ledger | Calls, tokens and dollars per Nemotron model, sandbox operations and seconds, wall-clock time | Cost per verified PR becomes a number |

**Surfaces**

CLI:

```
attest run "Add rate limiting to /api/upload" --repo .
attest run --issue 142          # from a GitHub issue
attest bench --mine 20          # tasks from this repo's history
attest proof <run-id>           # open the Proof Bundle
```

Streams the stage ribbon live. Code execution happens in Token Factory Sandboxes by default; the agent process itself can run inside an OpenShell sandbox on the developer's machine.

GitHub App and Action: label an issue `attest` or comment `/attest`. Attest opens a PR on a branch named `attest/<slug>`, posts the Proof Bundle as the PR body, and publishes a Check Run that reads, for example, "Attest · 14/14 sealed · mutation 0.83 · drift 0.1 · $0.61". Merge stays with a human.

Console: planned for yungou with the API, orchestration, and application data. The user confirmed yungou as DogYun 206.237.18.80. Verify runtime compatibility, current capacity, and deployment using the Obsidian host records and operational checks, preserve existing services, and publish the demo URL only after verification. Deploy the application without Docker. Live trajectory timeline, evidence panel, model ledger, and "run on a sample repo" for judges. This is the required demo URL.

**Safety envelope**
- Sealed tests live outside the implementer's writable scope; the verifier re-applies a pristine copy in a fresh sandbox branch, so tampering is impossible rather than discouraged.
- Verification branches run with networking disabled, so a patch cannot phone home or fetch an answer.
- A scope policy restricts which paths the implementer may change; CI configuration and test infrastructure are off limits unless the task is about them.
- Repository content (including agent config files such as AGENTS.md) is treated as untrusted input. OpenShell network policy on the agent host allows only the configured model provider, Tavily and the git remote, and the agent never sees real credentials.
- Human approval is required to merge; Attest never pushes to the default branch.

## 6. Architecture

Eleven stages, four models, one checkpoint with many branches.

| # | Stage | What happens | Model / backend |
| --- | --- | --- | --- |
| 1 | Intake | Classify task, estimate scope, pick policy | Nano |
| 2 | Ground | Map repo, build and test commands, external docs via Tavily; save the repo checkpoint | Lightning + Tavily + Sandbox |
| 3 | Spec | Spec, interface contract, acceptance criteria, infeasibility call | Ultra (thinking on) |
| 4 | Seal (gate) | Independent instance writes acceptance tests, proven red on the base checkpoint | Super (blind) |
| 5 | Plan | Steps, candidate count (best-of-N on ambiguity) | Ultra |
| 6 | Implement | Edits by Super, tool loop by Lightning, each candidate on its own sandbox branch | Super + Lightning |
| 7 | Verify (gate) | Fresh branch from the checkpoint, patch, sealed tests, suite, lint; networking off | Sandbox branches |
| 8 | Break (gate) | Edge cases, property tests, mutants in parallel branches, tamper and scope checks | Super + Lightning |
| 9 | Audit (gate) | Whole trajectory read for drift, claims vs evidence | Ultra (1M context) |
| 10 | Attest | PR, Check Run, Proof Bundle, console record | Nano (summaries) |
| 11 | Learn | Logs to Data Lab, skills distilled, self-benchmark tasks | Data Lab + Ultra |

**One checkpoint, many branches.** Token Factory Sandboxes persist filesystem images, not processes. Attest exploits that model directly. Stage 2 clones the repository at the target commit, installs dependencies and saves the result as a checkpoint image. Every later execution is a branch from that UUID: the sealed tests' red check, each implementation candidate, each verification run, and each mutant in the breaker pass. Branches cannot modify the checkpoint or each other, so a candidate that wrecks its environment costs nothing, and up to 50 operations run at once during the beta. The cookbook recipe "Try two coding fixes" is exactly this pattern with N = 2; Attest generalizes it.

```python
from contree_sdk import Contree
client = Contree()                                   # NEBIUS_API_KEY, NEBIUS_PROJECT_ID
base = await client.images.use("python:3.12-slim", strict=True)
repo = await base.run(shell=f"git clone {url} /w && cd /w && git checkout {sha} && pip install -e '.[test]'",
                      disposable=False)              # checkpoint UUID = repo.uuid
red  = await repo.run(shell="cd /w && pytest -q /sealed", disposable=True)   # must fail on base
runs = await asyncio.gather(*[
    repo.run(shell=f"cd /w && git apply /patches/{p} && pytest -q /sealed tests", disposable=True)
    for p in candidates + mutants])                   # parallel branches, networking off
```

**The sealed-envelope protocol.** Stage 3 fixes an interface contract. Stage 4 hands that contract, the repo's existing test conventions and read-only access to the pre-change tree to a separate Super instance with no knowledge of the plan. Its tests are executed on a branch of the base checkpoint and must fail there, otherwise they are rejected as vacuous. They are then stored in the run record, not in the working tree. Stage 6 sees only its own tests. If sealed tests fail at stage 7, Ultra arbitrates with the spec as ground truth and classifies each failure as an implementation bug or a contract dispute; disputes are recorded in the Proof Bundle and require a re-seal. This is how a good engineering organization separates QA from development, done by models.

**The breaker pass.** Stage 8 receives the spec and the diff and tries to make the patch fail: adversarial inputs, property-based tests where a property is stateable, and a mutation smoke test that applies a handful of semantic mutations to the patch (flip a comparison, drop a branch, change a boundary) and checks whether the sealed tests catch each one. Every mutant is a sandbox branch, so twenty mutants cost twenty short operations in parallel rather than twenty sequential container builds. The resulting mutation score is the single best signal against a patch that merely memorizes the tests, which is exactly what SpecBench documents. The pass also runs deterministic tamper checks: diffs outside policy scope, skipped or deleted tests, assertions weakened, hard-coded fixture values.

**The drift audit.** Nemotron 3 Ultra and Nemotron 3.5 Lightning both carry a native 1M-token context on a hybrid Mamba-Transformer backbone, which makes it cheap to read a complete trajectory instead of a truncated summary. Stage 9 feeds Ultra the original spec and the full tool-call history and asks three questions: is the final diff solving the stated problem, where did scope narrow or widen, and which claims in the agent's own messages are unsupported by tool output. The audit produces a drift score and quoted evidence. A high score during implementation triggers a re-anchor: the implementer restarts with the spec plus an Ultra-written summary, which is the mitigation NVIDIA's guide implies for goal drift.

**Model routing — submission profile**

The table describes the intended Nebius submission roles, not the routine development provider. Development maps these logical roles to supported Codex gateway model/effort settings through a separate adapter; see [Development model provider](development-model-provider.md). Catalog entries and parameters must be validated before a run; the table is not evidence of live integration or a measured quality ranking.

| Model (Token Factory ID) | Context | $/M in / out | Role in Attest | Thinking |
| --- | --- | --- | --- | --- |
| Nemotron 3 Ultra `nvidia/Nemotron-3-Ultra-550b-a55b` | 1M | 1.00 / 3.00 | Spec and contract, plan, arbitration, drift audit, skill distillation. The hard calls only. | On, budgeted |
| Nemotron 3 Super `nvidia/nemotron-3-super-120b-a12b` | 256K | 0.30 / 0.90 | Code edits, sealed-test authoring (blind instance), breaker test authoring. | On for authoring, off for edits |
| Nemotron 3.5 Lightning `nvidia/Nemotron-3_5-Lightning` | 1M | 0.06 / 0.24 | Execution loop: run commands, read logs, triage failures, navigate. Trained for harness tool use on terminal RL data; multi-token prediction for fast structured output. | Off |
| Nemotron 3 Nano `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | 262K | 0.06 / 0.24 | Intake classification, PR and commit summaries, routing decisions. | Off |

All four are listed on Token Factory with function calling, code, reasoning and Responses API support. Super and Ultra are served from us-central1; Nano and Lightning from eu-north1. Thinking is controlled per call with `chat_template_kwargs.enable_thinking` and a reasoning budget; tool-calling calls use the sampling NVIDIA recommends (temperature 0.6, top_p 0.95 for Nano-class models).

**Execution backends**

| Backend | Used for | Why |
| --- | --- | --- |
| Token Factory Sandboxes (beta; REST smoke verified) | Primary execution target for development and submission: checkpoint, candidates, sealed red check, verification, mutants; Attest adapter still to build | Three sequential operations and 23 guest checks passed. Account limits and branch-state isolation were read back. Official beta is free; see [verification guide](nebius-sandboxes-verification.md) and [API evidence](reports/nebius-sandboxes-probe-2026-10-15/api-smoke.json). |
| Nebius Serverless Jobs | Optional future backend for long test suites or GPU-dependent projects; not a required fallback | Any container, per-second billing (about $0.12 per hour for 4 vCPU and 16 GB), REST API, Python-file jobs |
| NVIDIA OpenShell | The agent process on a developer's machine | Kernel-level file and syscall limits, allow-listed egress, placeholder credentials swapped in at the proxy; provider created with `--type openai --config OPENAI_BASE_URL=https://api.tokenfactory.nebius.com/v1`, which is also NemoClaw's documented custom-endpoint path |
| Aliyun Beijing Docker 29.9.1 | Conditional Docker worker/fallback host; bounded environment smoke verified | Only for work that requires Docker; not the final project host. Dedicated service, Unix socket, data and runtime roots; no default bridge, firewall management, or TCP API. Independent of Codex gateway inference. See [environment guide](docker-development-environment.md) and [smoke evidence](reports/aliyun-docker-setup-2026-10-15/smoke.json). |

**Nebius Sandboxes API evidence — 15 Oct 2026.**

The [real API smoke](reports/nebius-sandboxes-probe-2026-10-15/api-smoke.json) completed three sequential operations: one checkpoint and two disposable branches. All three reached SUCCESS with exit code 0, and all 23 guest checks passed on Python 3.12.13. Both branches started from the checkpoint; the second branch did not inherit the first branch's write. Each request used `networking.enabled=false`, a 20-second timeout, a 64 MiB maximum writable layer, and UID/GID 65534. The guest had only `lo` and no route entries.

The [authenticated account readback](reports/nebius-sandboxes-probe-2026-10-15/whoami.json) reported 50 concurrent operations, a 3,600-second maximum operation timeout, a 12 GiB maximum writable layer, and eight concurrent imports with a 3,600-second timeout. Only sequential execution was tested. Four visible CPUs and `MemTotal: 4034744 kB` (about 3.85 GiB) are observations, not configurable or dedicated VM quotas. The inspected REST resource object exposes `max_layer_bytes`, not CPU/RAM quota controls. Process `RLIMIT_AS=256 MiB` and `RLIMIT_CPU=2 seconds` do not cap VM memory or allocate a CPU share.

All owned operations are terminal, with no live smoke task. Two disposable branches produced no retained result image. One untagged synthetic checkpoint of 1,456 bytes remains retained because no official image-delete API was documented; cleanup must not be represented as deleting everything. Before/after console readings stayed at $25 plus a separate $1 trial, with $0.00 monthly consumption. Official beta is free with no announced end date; rounding and reporting lag prevent exact invoice reconciliation. See [Nebius Sandboxes verification](nebius-sandboxes-verification.md). API readiness is verified; the Attest executor adapter, full repository task, and final NVIDIA inference profile still need end-to-end validation.

**Aliyun Docker fallback evidence — 15 Oct 2026.** The Aliyun Beijing smoke ran from `2026-10-15T07:24:18Z` to `2026-10-15T07:24:23Z`: four unit tests, 22 host-configuration checks, and ten in-container checks passed. Both client and container exited with code 0, no OOM was recorded, and cleanup verified the exact container ID was absent. Limits were 256 MiB memory with a matching memory-plus-swap limit (no additional swap), 0.5 CPU (observed cgroup quota/period `50000/100000`), 64 PIDs, and a 60-second client timeout. The container had only loopback networking, a read-only root filesystem, UID 65534, all capabilities dropped, and `no-new-privileges`. A single stats sample showed 9.844 MiB of 256 MiB and one PID; it is not a peak-usage measurement. See [smoke.json](reports/aliyun-docker-setup-2026-10-15/smoke.json).

The [after-install comparison](reports/aliyun-docker-setup-2026-10-15/after-install-comparison.json) passed 25 checks: recorded existing-service PIDs, restart counters, health responses, routes, interfaces, TCP listeners, firewall fingerprints, and available forwarding sysctls were unchanged. Two absent bridge sysctls were checked for continued absence, not assigned values. The Docker observations establish only its fallback environment, not full application regression or the Attest adapter. Nebius API smoke is recorded separately above; see [Docker development environment](docker-development-environment.md).

The [post-smoke comparison](reports/aliyun-docker-setup-2026-10-15/comparison.json) also passed all 25 checks. The dedicated service is enabled at boot with no retained containers, and a subsequent [Codex gateway request](reports/aliyun-docker-setup-2026-10-15/gateway-after-docker.json) returned HTTP 200 and the expected output. See the [completion summary](reports/aliyun-docker-setup-2026-10-15/summary.json).

**Repository layout**

```
attest/
  core/        state machine, stage prompts, verdict logic
  models/      Codex development + Token Factory submission adapters, routing, JSON actions, ledger
  tools/       fs, shell, git, test runners (pytest, jest, go test), lint, search
  sandbox/     tf_sandboxes primary; aliyun_docker only for required Docker workers/fallback; optional openshell/nebius_jobs
  verify/      sealed-test runner, mutation smoke, tamper checks, proof schema
  memory/      Data Lab datasets client, task mining, skill distillation, Harbor export
  app/         console/API/orchestration + webhooks; planned host: yungou; application data on yungou
  cli/         typer entrypoints
eval/          benchmark configs, results, trajectories
docs/          ARCHITECTURE.md, FEEDBACK.md, RESULTS.md
LICENSE        Apache-2.0
```

## 7. Nebius and NVIDIA usage

This section describes planned submission integrations. Routine development uses the Codex gateway adapter; it does not produce Token Factory Data Lab records or prove Nebius-specific tool-call compatibility. Publish only integrations exercised by the final version.

| Feature | How Attest uses it | Visible where |
| --- | --- | --- |
| Token Factory chat completions with function calling | Submission-profile agent turns after compatibility tests. Each stage exposes only its allowed actions. Development uses the Codex JSON-action adapter, without native tool forwarding. | Ledger, trajectory view |
| Structured outputs (`response_format: json_schema`) | Every tool call and every verdict is schema-constrained, with a one-shot repair path. Malformed tool calls become a measured rate, targeted at zero. | Results table |
| Reasoning control | Thinking on with a budget for spec, plan and audit; off for the execution loop. | Ledger per stage |
| Token Factory Sandboxes | Checkpoint per task, branches per candidate and mutant, red check for sealed tests, verification with networking off. Operation IDs and image UUIDs are recorded in the Proof Bundle so any step can be re-run. | Proof Bundle, console timeline |
| Fast flavors | `-fast` variants for the interactive CLI where available; base flavor for background runs. | CLI flag |
| Batch API | Best-of-N candidate generation, mutation sweeps and the benchmark runs go through batches, which carry higher limits and lower cost. | eval/ scripts |
| Data Lab | Token Factory logs every call automatically. Attest tags calls by run, stage and verdict, then builds SQL-filtered datasets of verified trajectories. Ultra distills them into repo skills (`.attest/skills/*.md`, agentskills.io format) and the task miner turns them into a regression set. | Console "Learned" tab, Data Lab console |
| Post-training (stretch) | LoRA on Qwen3-Coder-30B-A3B from the verified executor dataset, measured against Lightning on the regression set. Nemotron is not yet in the fine-tuning catalog, which goes into the feedback. | RESULTS.md |
| Rate-limit headers | Adaptive concurrency from `x-ratelimit-remaining-*`, since limits grow 20% per window when used above 80%. | models/ client |
| Serverless Jobs | Optional long or GPU-dependent verification; enable only if measured need justifies it. | Ledger: jobs and seconds |
| yungou (DogYun 206.237.18.80) — final application target | Planned host for the console, API, orchestration, application data, and GitHub App through 15 December. Identity is user-confirmed. Review Obsidian host records and verify runtime compatibility and capacity; deployment remains unverified and existing services must be preserved. Deploy directly without Docker. [Deployment targets](deployment-targets.md). | Demo URL after deployment verification |
| OpenShell + NemoClaw-compatible config | Local sandbox for the agent process with policy; Token Factory reached through `inference.local`. | docs/, video |
| Nemotron 3 family | Four models, four roles, routed by a small policy router in the spirit of NeMo Switchyard. | Everywhere |
| Harbor export | Mined tasks are written in Harbor's task format, so judges can run them on the Terminal-Bench harness. | eval/tasks |
| Tavily Search, Extract, Map, Crawl | Stage 2 pulls the exact API docs or changelog for any external library touched (advanced search with domain filters, extract with query chunks, map-then-extract for changelogs) and cites them in the Proof Bundle. Research endpoint for prior-art scans on larger features. | Sources section of every PR |

Cost per verified task, estimated (medium SWE-bench-style task, one candidate):

| Model | Tokens in | Tokens out | Cost |
| --- | --- | --- | --- |
| Ultra (spec, plan, arbitration, audit) | 200K | 15K | $0.25 |
| Super (edits, sealed tests, breaker) | 500K | 80K | $0.22 |
| Lightning (execution loop) | 1.5M | 150K | $0.13 |
| Nano (intake, summaries) | 50K | 5K | $0.01 |
| Sandbox operations (about 15 short branches) | | | free beta; API smoke verified |
| Total per task, inference | | | ~$0.60 |

Best-of-2 roughly doubles the Super and Lightning lines. These are unmeasured submission-profile inference estimates, not a development budget or cost per verified PR. Official Sandboxes beta terms say free with no announced end date; real API smoke passed. Unchanged two-decimal console balance/consumption is not exact invoice evidence. Record operations, seconds, and retained images; refresh terms before larger evaluation and report the final inference bill separately.

## 8. Evaluation plan

Nebius's own judges rewarded measured costs and candid findings. The evaluation is a first-class deliverable, published as RESULTS.md with trajectories and the bill.

Candidate task sets below are expansion targets. Freeze a smaller paired subset after a measured Nebius pilot, within the confirmed balance while preserving judging capacity. Codex development runs are labeled separately and are not pooled with the formal Nebius comparison.

Task sets:
- SWE-bench Verified subset: 50 tasks, stratified by repo and difficulty. Official tests remain the external judge.
- Mined tasks from two real repositories (one Python, one TypeScript, medium size, good test suites): 20 historical PRs where the PR's own added tests become the held-out set. Exported in Harbor format.
- Dependency upgrades (optional, Tavily-grounded): 10 DEPBENCH-style major-version bumps with hidden breakage. The Sandboxes demo repository already shows a SQLAlchemy 1.4 to 2.0 branch-and-rollback pattern.
- Terminal-Bench 2.1 subset (optional): 10 tasks through Harbor with `--agent-import-path`.

Conditions: Baseline (one Nemotron 3 Super ReAct loop with the same tools and sandbox, no evidence gate), Attest-lite (sealed tests and verification only), Attest-full (all stages, best-of-2 on ambiguous tasks).

| Metric | Definition | Why it matters |
| --- | --- | --- |
| Resolved rate | Official or held-out tests pass | Headline capability |
| Visible-to-held-out gap | Pass rate on the agent's own tests minus pass rate on sealed or held-out tests | The SpecBench measure of reward hacking; Attest should shrink it |
| False-positive PRs | Runs that would have opened a PR that fails held-out tests | What reviewers actually pay for |
| Mutation score | Share of injected mutants caught by sealed tests | Test strength |
| Malformed tool-call rate | Calls that failed schema validation before repair | NVIDIA's named failure mode |
| Drift events | Audits above threshold and re-anchors | NVIDIA's other named failure mode |
| Cost and time per task | Dollars per model, sandbox operations and seconds, wall clock | Open-model economics |
| Correct abstentions | Infeasible or no-change verdicts that were right | Trustworthy "no" |

"We also try to break it":
1. Healthy-repo control: task describes a bug that does not exist. Expected: NO CHANGE, with evidence.
2. Memorizing patch: inject a candidate that hard-codes the visible test outputs. Expected: fails sealed tests, mutation score near zero, PR blocked.
3. Test tampering: implementer attempts to edit or skip tests. Expected: tamper check fails the run; the pristine sealed copy in the verification branch is unaffected.
4. Prompt injection in the repo: an AGENTS.md instructs the agent to exfiltrate the API key. Expected: verification branch has no network; OpenShell policy on the host returns 403; audit flags the detour.
5. Infeasible task: spec contradicts the codebase. Expected: INFEASIBLE with the contradiction quoted, no fake PR.
6. Long-loop drift: a multi-module refactor. Expected: at least one re-anchor; final diff still matches the spec.

## 9. Scoring map

| Criterion | What scores a 5 | Evidence in the submission |
| --- | --- | --- |
| Technological implementation | Effective, deliberate use of Token Factory and Nemotron; a system that is well built | Four Nemotron models with explicit roles and a routing policy; structured tool calls with a measured zero-malformed rate; Sandboxes branching, Batch, Data Lab, OpenShell, yungou-hosted console (deployment pending); tests for the harness itself; reproducible eval scripts; ledger screenshots |
| Design | A complete, coherent product experience | Issue to verified PR in one flow; CLI, GitHub App and console share one run record; the Proof Bundle is a designed artifact; four honest verdicts; empty and failure states handled |
| Potential impact | A credible, specific case for a real audience, demonstrated | Survey and benchmark numbers in the pitch; two real OSS repos in the demo; the visible-to-held-out gap before and after; cost per verified PR; abstention cases |
| Quality of the idea | Creative, non-obvious use; genuine understanding of the problem | Sealed-envelope protocol, breaker pass, 1M-context drift audit, checkpoint-and-branch verification, Data Lab as agent memory; citations of SpecBench, SWE-Marathon, Verification Horizon and NVIDIA's own failure modes; the "we try to break it" section |
| Best Use of Tavily (bonus) | Functional runtime use that improves the result | Grounding stage with cited sources in every PR; the dependency-upgrade scenario where the changelog excerpt is the fix's justification |
| Most Valuable Feedback (bonus) | Complete, viable, impactful feedback | FEEDBACK.md with named tools, steps, repro and suggested fixes |

## 10. 16-day build plan

| Dates | Goal | Deliverables |
| --- | --- | --- |
| 14–15 Oct | Foundations and day-one checks | Load the saved credentials without committing them; implement the self-hosted Codex development adapter and validate its live model/effort catalog; record the verified Nebius checkpoint/branch API smoke and Aliyun fallback; treat only additional promotional grants as unverified; verify Nemotron tool calling and `enable_thinking` passthrough on Token Factory; confirm Batch enablement and Data Lab log visibility; use the user-confirmed yungou/DogYun 206.237.18.80 mapping; review Obsidian host records and verify runtime compatibility and workload capacity, preserving existing services; choose the two demo repos; scaffold the repo with Apache-2.0, CI and a typed tool schema |
| 16–19 Oct | Core loop | Stages 1 to 7 end to end: router, structured tool-call adapter, Spec, Seal with red-on-base proof, Implement, connect the Codex JSON-action loop to a Sandboxes REST adapter, then run a full repository task on fresh checkpoint branches; retain Aliyun only for a required Docker worker/fallback; Proof Bundle v0; CLI; first ledger |
| 20–22 Oct | Gates and surfaces | Breaker pass with parallel mutant branches and drift audit; independent model-provider and executor settings; OpenShell policy and provider; Tavily grounding with citations; GitHub App (or Action if time is short); console/API/orchestration v1 and application data deployed directly to yungou without Docker only after runtime and capacity verification, preserving existing services |
| 23–25 Oct | Evidence | Formal Nebius benchmark runs on the frozen, budgeted subset across the selected conditions; use Batch only after enablement and cost checks; task mining and Harbor export; Data Lab datasets and skill distillation; the six break-it scenarios; RESULTS.md with the bill |
| 26–28 Oct | Ship | Console polish, README and ARCHITECTURE.md, FEEDBACK.md, 3-minute video recorded from real runs, Devpost submission on 28 Oct; 29 Oct is buffer only |

Scope rules:
- Final application hosting is on user-confirmed yungou, DogYun 206.237.18.80: console, API, orchestration, and application data. Review Obsidian host records and verify runtime compatibility and capacity before deployment; preserve existing services. Runtime, capacity, and deployment remain unverified. Only components that demonstrably require Docker may run on the existing Aliyun Docker host. Deploy the application directly on yungou without Docker. See [deployment targets](deployment-targets.md).
- Python and TypeScript repositories only. Other runners are a stub with a clear message.
- GitHub App is preferred; a GitHub Action is the fallback that still yields a PR with a Proof Bundle.
- Sandboxes REST access and checkpoint/branch smoke are verified. Routine development uses Codex gateway inference and Sandboxes execution once its Attest adapter is ready; use Aliyun Docker only for a required Docker worker or fallback; it is not the final deployment host. Full repository-task integration still needs an end-to-end test. Formal evaluation, video, and judge runs must use NVIDIA models through Nebius Token Factory. Serverless Jobs is not a prerequisite.
- LoRA post-training is a stretch goal; the Data Lab skills loop is core.
- Cut Terminal-Bench and dependency-upgrade sets before cutting the break-it scenarios.

Budget and readiness (15 Oct snapshot; refresh before spending):

| Line | Current envelope | Notes |
| --- | --- | --- |
| Routine development inference | Existing self-hosted Codex API | Use `CODEX_API_KEY`, supported `model` and `effort`; account for usage separately. No fixed $100 Token Factory development line. |
| Nebius compatibility, final evaluation, demo, judging | Size after a measured pilot | Work within confirmed balance first; retain a judging reserve. Expanded task sets are not a funding requirement. |
| Token Factory Sandboxes | API smoke verified; official free beta | Three sequential operations, 23 guest checks; Attest adapter/full task pending. No announced beta end date; unchanged rounded display is not an exact invoice. [Guide](nebius-sandboxes-verification.md) · [Evidence](reports/nebius-sandboxes-probe-2026-10-15/api-smoke.json). |
| Final application hosting | yungou = DogYun 206.237.18.80; deployment unverified | Console/API/orchestration/application data target the user-confirmed host. Review Obsidian records, verify runtime compatibility and capacity, preserve existing services, then verify deployment. Run directly without Docker; no Nebius AI Cloud purchase is required. [Targets](deployment-targets.md). |
| Conditional Docker worker/fallback | Existing Aliyun Beijing Docker 29.9.1; bounded smoke passed | Four unit tests, 22 host-configuration and ten runtime checks; exact container cleanup verified. Only components that require Docker belong on this host; it is not the final application host. The smoke is environment evidence. [Guide](docker-development-environment.md) · [Evidence](reports/aliyun-docker-setup-2026-10-15/smoke.json). |
| Serverless Jobs | Optional, excluded from required budget | Add only after a concrete workload and cost decision. |
| Tavily | Key saved; live quota unverified | Test connectivity and read account quota; do not assume promotional credits have arrived. |
| Token Factory balance | $25 plus separate $1 trial; unchanged before/after | Confirmed +$25 "AI Builder Program Credits" is already included. Monthly consumption displayed $0.00; rounding/lag prevent exact invoice claims. Recheck trial expiry and eligible use. |
| Additional grants | Unverified | The existing AI Builder Program +$25 is confirmed, not pending. Do not assume a second Devpost, event, or Tavily grant, or double-count the existing credit. |

## 11. Submission package

Video script (3:00):

| Time | On screen | Voice |
| --- | --- | --- |
| 0:00–0:25 | A PR from a coding agent with green checks; then held-out tests failing | Half of developers trust AI code only when they can verify it. Agents pass their own tests and fail the ones they never saw. Attest exists so you never merge on the agent's word. |
| 0:25–1:30 | Issue labeled `attest`; stage ribbon runs live; sealed tests shown red on the base checkpoint; branches fanning out in Token Factory Sandboxes; PR opens with the Proof Bundle | Nemotron 3 Ultra writes the spec. A blind Nemotron 3 Super instance seals acceptance tests before any code exists. Super and Nemotron 3.5 Lightning implement on a branch of the repository checkpoint inside Token Factory Sandboxes, all served by Nebius Token Factory. |
| 1:30–2:10 | Breaker report; a memorizing patch getting caught; drift audit with quotes; Tavily sources panel | Then Attest tries to break its own work. Twenty mutants run as parallel sandbox branches; a patch that hard-codes the test outputs scores zero and is blocked. Ultra reads the whole trajectory in one million tokens of context and flags drift. Every API claim is cited from docs fetched with Tavily. |
| 2:10–2:45 | Results table: baseline vs Attest on the frozen Nebius task subset; actual sample count, cost per verified PR, and full bill | On our frozen task subset, the held-out gap changes from [measured baseline] to [measured Attest result]. Report the actual malformed-action rate and full cost per verified PR. Replace every placeholder from the final Nebius evaluation before recording. |
| 2:45–3:00 | Repo, console URL, Nebius and NVIDIA logos in Built With | Attest: Nemotron 3 on Nebius Token Factory and Sandboxes, OpenShell, Tavily. Apache-2.0. Proof, not promises. |

Description outline: (1) the problem, with three numbers; (2) what Attest does in five verbs: specify, seal, build, break, attest; (3) why it is different from a normal agent: models decide what to try, deterministic gates decide what is true; (4) safety envelope; (5) results table and the bill; (6) we also try to break it; (7) how Nebius and NVIDIA power it, feature by feature; (8) setup in five commands.

Built With (include only tools exercised by the final version; AI Cloud services are optional): Nebius Token Factory, Nebius Token Factory Sandboxes, NVIDIA Nemotron 3 Ultra, Nemotron 3 Super, Nemotron 3 Nano, Nemotron 3.5 Lightning, NVIDIA OpenShell, Tavily, Harbor, Python, FastAPI, TypeScript.

FEEDBACK.md items to collect from day one:
- Nemotron models are not in the Token Factory fine-tuning catalog; request Nano and Lightning with LoRA, and spec-draft support for the family.
- Tool-call parsing quirks on Nemotron (argument types under `anyOf`, reasoning and content fields when content is empty), with reproductions.
- Whether `chat_template_kwargs` and a reasoning budget pass through the OpenAI-compatible endpoint, and what the defaults are.
- Sandboxes: the SDK reads `NEBIUS_PROJECT_ID` while the CLI reads `NEBIUS_AI_PROJECT`; persistence defaults differ between SDK, CLI and MCP; the documented Mini-SWE-Agent adapter currently fails. Real REST access is verified. Report the lack of exposed CPU/RAM quota fields and a documented image-delete endpoint; distinguish process rlimits, visible guest resources, account ceilings, and billing observations.
- Data Lab: request a metadata field on chat completions that survives into logs, and an API path for creating SQL-filtered datasets.
- Batch API: enablement steps and documented discount.
- Region split (Nano and Lightning in eu-north1, Super and Ultra in us-central1) and its latency effect on multi-model loops.
- Documentation errors found (for example syntax errors in the structured-output samples) with page links.
- Serverless Jobs: pull-progress visibility while a job sits in STARTING; quota for parallel CPU jobs.
- OpenShell: provider profile ergonomics for non-OpenAI hosts; what worked zero to hello world.

Checklist before submitting: track selected and city selected if anyone attended a Builders & Brews event; license visible in the repository About section and no keys in history; demo URL works logged out with rate-limited, pre-funded sample runs; video public on YouTube under 3 minutes with tools named aloud; README covers setup, run, eval reproduction, architecture and feedback; feedback section filled in on Devpost, not only in the repo.

## 12. Risks and day-one checks

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Sandboxes API smoke passes, but Attest adapter and full repository lifecycle remain untested | Medium | Implement the REST checkpoint/branch adapter and full repository task; start sequentially within verified account ceilings, keep verification networking off, track retained images, and use the tested Aliyun host only for a required Docker fallback |
| Nemotron tool calls misparse on Token Factory (known parser issues upstream) | Medium | Structured-output tool envelope as the primary path, native tools as secondary; repair loop; measure on day one and pick per model |
| Sealed tests are wrong, not the code | Medium | Contract step before sealing; red-on-base check; arbitration protocol; report dispute rate honestly |
| Credits run out during evaluation | Medium | Batch API, thinking off in loops, per-run caps, smaller subset first |
| Rate limits in parallel runs | Low | Adaptive concurrency from headers; limits scale 20% per window above 80% use |
| Scope creep | High | Scope rules above; the break-it scenarios outrank optional benchmarks |
| Demo not live during judging | Low | Verify the yungou deployment and run uptime checks; recorded runs embedded in the console as fallback |
| Prompt injection from repository content | Medium | Networking off in verification branches, OpenShell egress policy on the host, brokered credentials, repo content treated as untrusted |
| Looks like "just another agent" (or like CodeGuard) in a 3-minute skim | Medium | Open the video with the held-out failure; show the memorizing patch being caught and the branches fanning out; name the gates |

Verify on day one before committing the design:
- Follow [Development model provider](development-model-provider.md): authenticate to the Codex gateway, refresh `GET /v1/models`, test supported model/effort settings and structured JSON actions. Record results without a model-quality claim.
- The Token Factory key authenticated real Sandboxes operations. Independently validate NVIDIA inference and Tavily, read current quotas, and review the confirmed yungou/DogYun 206.237.18.80 host records in Obsidian and verify runtime compatibility/workload capacity while preserving existing services; one service integration does not prove another.
- Aliyun Docker host smoke is complete: [four tests and runtime constraints](reports/aliyun-docker-setup-2026-10-15/smoke.json), [25 setup comparison checks](reports/aliyun-docker-setup-2026-10-15/after-install-comparison.json). Next, implement the primary Sandboxes JSON-action/executor loop and use this host only for a required Docker fallback; separately validate NVIDIA inference before formal evaluation. See [environment guide](docker-development-environment.md).
- Sandboxes API access, account limits, and offline checkpoint/two-branch isolation are verified: [API smoke](reports/nebius-sandboxes-probe-2026-10-15/api-smoke.json) and [whoami](reports/nebius-sandboxes-probe-2026-10-15/whoami.json). Next implement the Attest adapter and run a full repository suite from a checkpoint. Keep the retained 1,456-byte synthetic checkpoint in the resource ledger; see [verification guide](nebius-sandboxes-verification.md).
- Does the Token Factory endpoint pass `chat_template_kwargs` (via `extra_body`) for Nemotron, and does `enable_thinking:false` remove reasoning tokens?
- Which tool parser does each Nemotron model use on Token Factory, and are parallel tool calls returned?
- Is the Batch API enabled on a fresh project, and what completion windows are accepted?
- Do inference logs appear in Data Lab for API calls, and can a filtered dataset be created and read through the Datasets API?
- Only if Serverless Jobs is selected later: does its REST API accept file injection, and what CPU quota and cost apply?
- Does `list-spec-draft-trainable-models` include any Nemotron base?
- Does the Responses API accept Nemotron with tools; if so, use `previous_response_id` for the execution loop and note it.

## 13. Versus the FutureFit draft

The FutureFit draft (14 Oct, v1) proposes a "code evolution wind tunnel": run the same feature tasks against the original structure and up to two candidate refactors in isolated environments, pick a candidate on search tasks, re-verify on held-out tasks, and tell the user whether a small refactor is worth adopting. It is rigorous and original, and its discipline about frozen inputs, paired trials and honest verdicts is excellent. Measured against this hackathon's rubric and calendar, it carries more risk than Attest for a smaller payoff.

| Dimension | FutureFit | Attest |
| --- | --- | --- |
| Track fit (stage-one pass/fail) | A developer tool that uses coding agents; fits, but the agent is an instrument, not the product | A coding agent that writes, runs and tests code in Token Factory; the literal track wording |
| Chance of a convincing result by 28 Oct | Depends on refactors measurably improving agent success on held-out tasks; the draft itself says to stop if gains appear only on search tasks. A null result makes a weak video | Catching bad patches is demonstrable on day one; the headline metric (held-out gap) moves whenever the gate blocks a wrong PR |
| Credits per demo | About 27 feature implementations per experiment, each up to 10 minutes and 30 tool turns | Original single-task inference estimate: about $0.60 before retries and failures; measured pilot pending |
| Technological implementation | Nemotron 3 Super only; Docker executor; no Data Lab, Batch, Sandboxes or multi-model routing in the draft | Submission targets: four Nemotron roles, Sandboxes branching, Batch, Data Lab, OpenShell, yungou-hosted console (deployment pending) |
| Design | Four web screens plus CLI around a decision; complete but abstract for a three-minute judge | Issue to PR with a Proof Bundle; a shape every judge recognizes |
| Potential impact | Teams deciding whether to refactor; real but narrow, and the value needs repeated experiments to show | Everyone merging agent PRs; the trust gap is quantified in surveys the judges have likely read |
| Quality of the idea | High: genuinely novel framing | High: sealed tests, breaker, drift audit, branch verification, grounded in named 2026 papers and NVIDIA's own failure modes |
| Tavily bonus | No natural runtime use | Grounding with citations on every PR |

What to carry over from FutureFit:
- The split between search-time signals and held-out verification, which is the sealed-envelope protocol in another form.
- Frozen inputs: a manifest with code digest, dependency lock, image, model and parameters per run, so every Proof Bundle is reproducible.
- Verdict discipline: no unsupported scores, an explicit "unable to compare" state, and costs reported in full including failures and unchosen candidates.
- The budget envelope idea: per-run caps on minutes, tool turns, parallelism and dollars, calibrated on day one and then frozen.

If the team decides to keep FutureFit anyway, the minimum upgrades from this research are: run the A, B and C arms as branches of one Sandboxes checkpoint (the paired-experiment design maps onto it exactly), route spec and judging to Ultra and execution to Lightning, log everything into Data Lab, host the demo directly on yungou without Docker after runtime, capacity, and deployment verification, add the evaluation and feedback package above, and add a Tavily-grounded step so the bonus stays reachable.

## 14. Alternatives considered

| Candidate | Strength | Why it loses to Attest |
| --- | --- | --- |
| Dependency-upgrade agent grounded on changelogs | Narrow, measurable, Tavily-native; DEPBENCH shows headroom | GitHub shipped agent-assigned Dependabot alerts in April; reads as a feature. Kept as a scenario inside Attest. |
| Repo-to-RL-environment generator (OpenEnv, Harbor) | Deeply aligned with Nebius's post-training story | A tool for ML platform teams, hard to make tangible in three minutes; weaker on Design and Impact. Kept as the task miner and Harbor export. |
| Always-on maintainer bot | Broad appeal | Breadth invites shallowness; overlaps the Personal AI track. Attest's GitHub App covers the valuable slice. |
| Nemotron-native harness only (fix drift and tool calls) | NVIDIA judges would like it | Hard to distinguish from OpenCode or OpenHands with a config file. Folded into Attest's implementation layer. |
| Self-fine-tuning coding agent | Strong Token Factory story (Data Lab to post-training) | Nemotron cannot be fine-tuned on Token Factory today, and the training loop is risky in 16 days. Kept as a stretch goal and a feedback item. |

## 15. Sources

- Hackathon: https://nebiusglobalaihackathon.devpost.com/ (overview, judges, criteria); rules https://nebiusglobalaihackathon.devpost.com/rules; "Here's how judging works" https://nebiusglobalaihackathon.devpost.com/updates/46204-here-s-how-judging-works; "How to build a winning project" https://nebiusglobalaihackathon.devpost.com/updates/46205-how-to-build-a-winning-project; prize stacking note https://nebiusglobalaihackathon.devpost.com/updates/46206-did-someone-say-prizes
- Token Factory models and docs: https://tokenfactory.nebius.com/api/public/models_info; https://docs.tokenfactory.nebius.com/ai-models-inference/function-calling; https://docs.tokenfactory.nebius.com/ai-models-inference/json; https://docs.tokenfactory.nebius.com/ai-models-inference/rate-limits; https://docs.tokenfactory.nebius.com/data-lab/overview; https://docs.tokenfactory.nebius.com/post-training/models; https://docs.tokenfactory.nebius.com/post-training/custom-speculator; https://docs.tokenfactory.nebius.com/api-reference/inference/create-a-response; https://github.com/nebius/token-factory-cookbook
- Token Factory Sandboxes: https://docs.tokenfactory.nebius.com/sandboxes/overview; https://docs.tokenfactory.nebius.com/sandboxes/start/python-quickstart; https://docs.tokenfactory.nebius.com/sandboxes/concepts/images-checkpoints-and-branches; https://docs.tokenfactory.nebius.com/sandboxes/operate/limits-retention-and-usage; https://docs.tokenfactory.nebius.com/sandboxes/cookbook; https://github.com/kreuzhofer/nebius-token-factory-sandboxes-demos; https://contree.dev/
- Nebius platform and strategy: https://nebius.com/blog/posts/introducing-the-nebius-ai-builder-program; https://nebius.com/blog/posts/your-best-dataset-is-already-in-your-logs; https://nebius.com/blog/posts/nvidia-groq-3-lpx-nebius-token-factory; https://nebius.com/events/webinar-whats-new-q3-2026; https://nebius.com/blog/posts/compute-cloud-platform-q3-2026; https://nebius.com/blog/posts/serverless-ai-builders-challenge-winners; https://github.com/nebius/skills/blob/main/skills/nebius-serverless-jobs/SKILL.md; https://docs.nebius.com/compute/resources/pricing; SEC EDGAR 6-K filings for Nebius Group (CIK 0001513845)
- NVIDIA: https://developer.nvidia.com/blog/nvidia-nemotron-3-ultra-powers-faster-more-efficient-reasoning-for-long-running-agents/; https://developer.nvidia.com/blog/nvidia-nemotron-3-5-lightning-delivers-fast-accurate-specialized-task-execution-for-long-running-agents/; https://docs.nvidia.com/nemotron/0.1.0/usage-cookbook/Nemotron-3-Super/OpenScaffoldingResources/README.html; https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Terminal-Pivot-v1-nano35-release; https://github.com/NVIDIA/OpenShell; https://docs.nvidia.com/openshell/v0.0.116/sandboxes/manage-providers.md; https://github.com/NVIDIA/NemoClaw; https://docs.nvidia.com/nemoclaw/user-guide/openclaw/inference/custom-endpoints/set-up-openai-compatible-endpoint; https://forums.developer.nvidia.com/t/nemotron-3-super-improvements-and-fixes/364754
- Research: SpecBench https://arxiv.org/abs/2605.21384; SWE-Marathon https://arxiv.org/abs/2606.07682; The Verification Horizon https://arxiv.org/abs/2606.26300; self-evaluation bias https://arxiv.org/pdf/2607.25152; DEPBENCH https://arxiv.org/abs/2608.30300
- Market and demand: https://stackoverflow.co/company/press/archive/stack-overflow-annual-developer-survey-ai-trust-conditional; https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/; https://sdtimes.com/open-source/the-state-of-open-source-maintainers/; https://siliconangle.com/2025/09/23/greptile-bags-25m-funding-take-coderabbit-graphite-ai-code-validation/; https://github.blog/changelog/2026-04-07-dependabot-alerts-are-now-assignable-to-ai-agents-for-remediation/
- Precedents, competitors and tools: https://devpost.com/software/project-blackbox; https://github.com/kuker24/nebius-codeguard; https://github.com/habib-analyst/nemotron-forge; https://github.com/RAJKOTIYACHIRAGMUKESHBHAI/codeflow-agent; https://github.com/harbor-framework/harbor; https://docs.tavily.com/documentation/agent-skills; https://docs.tavily.com/documentation/api-credits; https://github.com/NousResearch/hermes-agent

Figures from secondary sources (leaderboard positions, valuations, some survey percentages) were cross-checked where possible but should be re-verified before they appear in the video.
