# Attest: competitive review, audit and improvement proposal (16 Oct 2026)

Status: research and design brief for review. It authorises nothing: no repository is published, no entry submitted,
no production redeploy, no paid Nebius run. Everything dated here was checked on 16 Oct 2026 unless stated otherwise.

Contents of this folder: `competitors/*.md` (one evidence report per competitor, with fetch timestamps and an
observed / author-reported / unknown table each), `judging-criteria-2026-10-16.md` (re-verified rules), and this
brief. The UI concept and clickable prototype live in `design/console-redesign-2026-10-16/`.

## 0. The five deliverables in one page

1. **Competitor matrix.** Six submissions examined (gallery still unpublished, so this is a sample, not a ranking).
   All are solo builds with zero stars, forks or external users. Two run live hosted execution (MUTINY, PatchScout);
   two are CLI-only (runanchor, FixFork). Two have committed, recomputable evaluation artifacts (MUTINY's 49-PR corpus
   and runanchor's 54-task bench with a hash-chained ledger our agent re-verified); FixFork's strongest claims lack
   artifacts; PatchScout has one self-authored fixture, no tests and a private video. Agent Forensics Lab is a live
   in-process forensics service with deterministic rule verdicts and templated before/after replays, all aggregates
   matching its claims; NAVIGUIDE is a large live map-briefing app whose on-demand, cached, budget-capped inference
   pattern is the one to borrow. See section 1.
2. **Attest's biggest gaps.** Technical: the existing-suite step runs candidate code as root in the same sandbox
   operation before the sealed supervisor (a real bypass of our privilege separation); existing and held-out suites
   are parsed from stdout and are forgeable in-process; the bundle lacks the Attest code revision and runner digests.
   Evidence: in the controlled evaluation, 4 of 5 tasks fed the judge's held-out suite to Attest as an internal gate,
   so the "zero false acceptances" headline is partly tautological; the headline table is a best-of merge; the
   `rle-encode` "implementation bug" is really an unsatisfiable contract. Product: no public repository, license or
   video yet; no way for an outside developer to run Attest on their own repository. UI: nine equal-weight cards with
   the log above the evidence, no counterexample surfaced, state lost on every 4 s refresh. See sections 3 and 4.
3. **Prioritised plan** with acceptance criteria, effort, dependencies and inference cost: section 5. Routine work
   runs on the Codex gateway or offline fixtures; the only paid Nebius spend is the final frozen evaluation and the
   demo run, proposed for approval in section 8 (cap $6).
4. **User journey and annotated UI concept:** section 6 and `design/console-redesign-2026-10-16/README.md`; the
   prototype is `design/console-redesign-2026-10-16/prototype.html` (built from real Proof Bundles).
5. **First milestone recommended:** M1, "close the verifier bypass and fix the evaluation method" (section 7). It is
   small, it is what Technological Implementation (the first tie-breaker) rewards, and the console redesign and the
   final evaluation both depend on it.

## 1. Competitive baseline (dated 16 Oct 2026)

Method: each Devpost page, repository, demo URL and video page was fetched between 17:23 and 17:40 UTC; repositories
were read through the GitHub API; no competitor code was executed; no competitor demo run was triggered (one
read-only status call to PatchScout's `/api/sandbox`). The official gallery is still unpublished ("The hackathon
managers haven't published this gallery yet"), so these six were found by other means and the field is larger.
Per-project detail, including the full observed / author-reported / unknown tables, is in `competitors/`.

### 1.1 Matrix

| | MUTINY | runanchor | FixFork | PatchScout | Agent Forensics Lab | NAVIGUIDE |
| --- | --- | --- | --- | --- | --- | --- |
| User and problem | Reviewers merging "no behaviour change" refactors; runs both versions and reports the input where they disagree | Teams running autonomous agents who need receipts for "tests pass"; anchors runs to Sandboxes operation and image ids | Python developers with a red suite; races three Nemotron fixes, keeps the one the tests confirm | npm developers broken by a major dependency upgrade; research, patch, verify in a sandbox | Teams shipping tool-using agents; records every tool call of its own built-in agent, flags violations with deterministic rules, minimises the trigger, replays with and without a guardrail, stores regressions | Crew and followers of the team's own catamaran expedition (and "virtual sailors"): a map briefing of EEZ borders, ports, protected areas and weather, a logbook chat and a narrated film, with numbers only from sources |
| Workflow a user can perform today | CLI (`verify`, `verify-diff`, `verify-url`, `review-pr`, `pin`), GitHub Action, hosted web demo with SSE | CLI only: offline `demo` replay of fixtures; live `run`/`verify`/`approve` needs the `contree` CLI and beta access | CLI only; offline `--fake` mode; local subprocess by default, Nebius sandbox opt-in | Web form and `POST /api/agent`; demo mode returns hardcoded text; live mode clones github.com repos | Web UI and REST API on Fly.io: pick a domain and failure category, run an investigation, apply a guardrail and replay, save and rerun regressions; the agent under test is the project's own in-process agent; no Action | React SPA on FastAPI: follow the expedition from precomputed stock, play the film in raw (rules) or written (Super) style, chat, draw custom routes, export GeoJSON; the second product's site returned 502 at three probes |
| Implemented vs planned | Differential engine, sandbox forks, Action, Tavily contract check, budget guard all in code; multi-language, merge gating, nested-object construction not | Receipts, hash-chained ledger, replay, hidden oracle, planner, judge, 54-task bench in code; pristine interpreter mount, cost metering not | Race, judge, guard, patch export, 303 tests, CI in code; sandbox default, more languages, Action not; several claimed runs have no artifacts | Agent, sandbox client, inspector, CI build in code; no tests at all; "rollback" is a stored pointer; research query hardcodes Express terms | Investigation, rule oracle, minimiser, paired replay, regression store, 160-case corpus, CI in code; "patch" is one of four fixed guardrail flags; external agents, SDK hooks, async jobs are future work; no cost accounting | 1,352 commits (87% inside the submission period), 779 server tests, 142 Playwright specs, CI; the Tavily plus Ultra "truth judge" exists but is disabled; object storage and accounts planned |
| Verification and trust boundary | Nemotron writes inputs, never assertions; canonicalised outputs; 3 confirming re-runs; sandbox is the isolation; Action never fails a build | Replay from recorded start image plus hidden pytest oracle under `python -I -S` at a random mount; judge sees the oracle outcome (not independent); fail-safe reject on unparseable judge output | Repo's own tests are the referee after a red baseline; proposals touching tests/CI/config refused; no isolation locally | `baselineExit != 0 and afterExit == 0` for a model-chosen test command, networking on; no guard against editing tests or package scripts; confidence is model-reported | Deterministic rules over recorded events, no LLM judge; before/after explanations are templates over a verification tuple (reproduced, before failed, after failed, completed); execution is in-process Python, no code execution, no Sandboxes; replay is stochastic (a saved regression reran as NOT REPRODUCED) | No ground truth; numeric-fidelity filters drop any sentence with a number not in the facts; provider cascade Token Factory, NIM, OpenRouter, Anthropic, rules, each output labelled with its source; no code execution |
| Evaluation artifacts | 27 result JSONs; 49-PR corpus (12 divergences, $0.39) recomputed; "40 of 45" exists only in a doc (JSON shows 36); 6 false-finding classes documented | v1–v4 bench JSON and ledgers; 11/11 and 42/43 recomputed by us; 455-line hash chain re-verified with zero breaks; one retracted interpretation kept | n=1 cases; tomlkit and greynoise runs red in artifacts; "green run 3", sandbox A/B and humanize runs have no artifacts | Prose only (`E2E_PROOF.md`); no ids, logs or numbers; one fixture authored by the same person | Aggregate summaries match every claim (132/132 cases, 67/67 mitigations, 1.21 M tokens, 13.4 s per case); per-case records absent; author-audited; cost recorded as null | None: no dataset, scores or result files; a September bill of $6.58 appears in a code comment; the live counter showed about $0.09 for 16 Oct |
| UI, demo, video | Live Vercel service, health shows sandboxes on, cap $15, $0.25 per run, 20 per hour per IP; README strong; video 2:58 public | No hosted demo; CLI replay; README strong with CIs; video 1:41 unlisted | Static Netlify replay of one run; README clear; video 1:51 public | Live Next.js service (`/api/sandbox` ready); video **private**, judges cannot watch it | Live Fly.io service plus hosted replay of five saved regressions; one page with steps 01 to 06 and before/after cards; README clear; video 2:48 public | Live simulator (200), dense three-pane map UI; one gallery screenshot shows an unfiltered model refusal; video 1:50 public; no repository link on Devpost (found by code search) |
| External use or adoption | 0 stars, 0 forks, 1 contributor; PRs cited are other people's merged PRs used as a corpus | 0 stars, 0 forks, no PRs anywhere by the author | 1 merged upstream PR (tomlkit#620, merged by a maintainer in 66 min) but the repo README says the patch was hand-completed; 3 open PRs, 1 self-closed; 0 stars | 0 stars, 0 forks, 0 issues | 0 stars, 0 forks, 0 issues; the 132 cases are the author's benchmark | 1 fork; 514 pull requests self-merged by the organisation account (most authored by coding-agent accounts); no users beyond the team's expedition |
| Nebius and NVIDIA usage | Super by default, Nano/Ultra/Lightning defined; Token Factory; Sandboxes via contree SDK; Tavily | Super planner, Lightning judge; Token Factory via urllib; Sandboxes via contree CLI | Super diagnosis, Nano repair; Token Factory; Sandboxes opt-in (no live artifact) | Super only; Token Factory; Sandboxes via contree-client with networking on | Super only via Token Factory, in three roles (agent, attacker, minimiser); Hermes and Qwen used for one comparison; no Sandboxes | Lightning (fast), Super (write), Ultra (deep, judge) via Token Factory with daily caps per tier; non-Nebius fallbacks remain in the default list; Tavily per port; no Sandboxes |
| Repository | Apache-2.0, 94 commits, 95 tests | MIT, 60 commits, 138 tests | MIT, 65 commits, 303 tests, CI | MIT, 11 commits in 15 h, 0 tests, CI | MIT, 14 commits (initial 156-file commit), 193 test functions, CI | MIT and Apache dual, 1,352 commits, 779 server tests, CI, 285 MB |

### 1.2 Attest held to the same standard

| | Attest (this repository, 16 Oct 2026) |
| --- | --- |
| Workflow a user can perform today | CLI `python -m attest run` on bundled tasks; live console at `https://attest.axiqo.xyz` with a public Nemotron profile (3 runs per hour, $0.50 per run, $2 per day) and downloadable Proof Bundles; no external-repository entry |
| Implemented vs planned | Freeze, checkpoint, spec, seal, red check, implementer, bound verification with per-test privilege separation, held-out gate, mutation and adversarial breaker, drift audit, advisory arbitration, console, budget and disk guards: all in code with 36 offline tests. Planned, no code: external repositories, GitHub surface, server-sent events |
| Verification and trust boundary | Sealed tests written before implementation, hidden from the implementer; each test in its own process as uid 65534 against a root-owned copy; nonce and digest binding; mutants and adversarial tests under the same supervisor. Open bypass: the existing-suite step runs candidate code as root in the same operation before the supervisor (section 3.2) |
| Evaluation artifacts | 5-task controlled evaluation, all attempts retained, but 4 of 5 tasks used the judge's held-out suite as an internal gate and the headline is a best-of merge (section 3.3) |
| UI, demo, video | Live service; current UI is a single page of stacked cards (section 4); **no video, no public repository, no license yet** |
| External use | None. No users, no external pull requests, no testimonials |
| Nebius and NVIDIA usage | Ultra for spec, audit and arbitration; Super for seal, implement and break; Lightning for summaries; Token Factory with strict JSON schemas; Sandboxes REST with retained checkpoints and disposable networking-off branches; Tavily grounding |
| Repository | Not yet a git repository; no license file; ~9.8 MB without runs |

### 1.3 Agent Forensics Lab and NAVIGUIDE: what to adapt

Agent Forensics Lab (Best Apps and Agents track by its README, not the coding track) verifies nothing about code; it
investigates an agent's tool calls. Two mechanisms are worth adapting. First, every before/after explanation is a
deterministic template over a recorded verification tuple (reproduced, before failed, after failed, completed), not
model prose, and both full traces sit behind it. Attest's red-on-base, green-on-candidate pairing is the same idea
per test; the console should state it as a tuple per sealed test and per arbitration re-run, with fixed sentences,
and the bundle should carry the tuple. Second, a shorter trigger is accepted only if a fresh execution reproduces the
violation. Our breaker should minimise a failing adversarial input the same way (MUTINY's "input where they disagree"
is the same principle), so the counterexample shown is the smallest that still fails.

NAVIGUIDE is the cost pattern to borrow, with the detail that matters: inference is on-demand by default (a model is
called only on a user action, never in the background, with one documented exception), a SQLite prompt cache and a
story cache are read before any call, daily token caps per model tier carry a USD estimate, per-IP rate limits apply,
and every generated paragraph shows its source (Nemotron Super on Token Factory, rules, cache, budget, fallback). It
has no user-facing remaining-budget meter, which is the one piece Attest should add rather than copy. For Attest:
recorded evidence is the default view; a live run is an explicit action that shows the estimate and today's remaining
budget first; every artifact names the model that produced it; cached or imported results are labelled as such.

### 1.4 Where each competitor is genuinely stronger than Attest today

- **MUTINY**: a minimal, concrete counterexample is the product. The output is an input on which two versions
  disagree, with the two outputs. Our breaker finds counterexamples too, but the console shows a test id and a reason
  string, not the input and the outputs. MUTINY also ships a GitHub Action and accepts any public GitHub URL.
- **runanchor**: replayable records. Every run is a receipt with provider operation and image ids, and the ledger is a
  hash chain anyone can recompute. Our Proof Bundle records operation and image ids too, but there is no cross-run
  ledger, no chain, and no `attest check` command that re-verifies a bundle offline.
- **FixFork**: external outcomes. It is the only one of the six that touched real upstream repositories, and it was
  honest that the merged patch was hand-finished. Attest has not run on a repository it did not author (python-semver
  is the one real repository, and it is bundled).
- **PatchScout**: nothing we should copy; it is the warning case (no tests, private video, fixture-tuned prompt).
- **Agent Forensics Lab**: deterministic verdict rules with templated, tuple-backed before/after explanations, and
  reproduce-before-accept minimisation. Attest's verdict is deterministic from gates, but the console explains it with
  raw reason strings, and the breaker does not minimise.
- **NAVIGUIDE**: cost discipline and source labelling. On-demand by default, cached, capped per tier, labelled per
  paragraph. Attest's console defaults to a paid live run with no estimate, although the budget is already in the
  health endpoint.
- All six have a repository with an open source license (NAVIGUIDE's is not linked from Devpost) and five have a
  public video (PatchScout's is private). Attest has neither yet, and both are Stage One requirements.

## 2. Attest's product position

### 2.1 The workflow, kept central

Frozen requirement, acceptance tests sealed before implementation, candidate patch, isolated verification, explicit
verdict with reproducible evidence. Every run ends in VERIFIED, NEEDS HUMAN, INFEASIBLE, NO CHANGE or ERROR, computed
only from recorded gates.

### 2.2 Why a developer would choose this over the alternatives

| Alternative | What it answers | What it cannot answer | What Attest adds |
| --- | --- | --- | --- |
| Behaviour-diff checker (MUTINY) | "Did the refactor change behaviour?" given two versions | Whether new behaviour is the behaviour that was asked for; needs an existing version to compare against | A contract frozen before the code exists and tests sealed against it, so a feature or a fix is judged against the request, not against the previous version |
| Existing-test repair agent (FixFork, PatchScout) | "Does the repo's own suite go green?" | Whether the suite would catch the agent writing to the test, or the agent satisfying the letter of a weak suite; the tests are the agent's target and its judge | Tests the implementer never sees, shown failing first, then mutants and adversarial tests that attack the patch, and a drift audit over the whole action trail |
| Execution-receipt tool (runanchor) | "Did this command really run with this result in this sandbox?" | Whether the result means the task is done; a receipt of a passing self-written test is still a self-written test | The same anchoring (operation and image ids, nonce, digests) plus the independent evidence: red-then-green sealed tests, per-test privilege separation, a mutation score |

The honest trade: Attest costs 2 to 3 times a plain agent's inference and about twice its wall clock on the tasks we
measured ($0.02 to $0.06 and 2 to 4 minutes per task on Nemotron), and it holds patches a human then has to look at.
That is the product: it never says VERIFIED without the evidence to show for it.

### 2.3 Smallest changes that close the most important gaps

1. Surface the counterexample (input, actual, expected, the test) in the console and in PROOF.md. The data is
   already in the bundle (`captured_tail`, arbitration `contract_basis`). Zero inference cost.
2. `attest check <bundle.zip>`: recompute digests, confirm the nonce binding, the red-then-green set relation and the
   gate-to-verdict derivation offline, and print a one-page verdict. Makes the bundle replayable in runanchor's sense
   without a hosted service. Zero inference cost.
3. Record the Attest code revision, the guest runner and supervisor source digests, the sampling parameters and the
   upstream repository revision in every bundle. Zero inference cost.
4. A bounded "bring your own repository" entry (section 2.4) so a pilot can produce real external outcomes.
5. Publish the repository with a license and the video (Stage One requirements), after review.

### 2.4 Bounded external-repository workflow: recommended, with limits

Yes for the next release, as a CLI-first pilot, with the public console kept on curated tasks. Supported scope:

- Language and runners: Python 3.11 or 3.12, `unittest` or `pytest`; dependencies from a lock file installed once at
  checkpoint time (the only networked operation), as the python-semver task already does.
- Source: a public GitHub repository at a pinned commit, or a local directory; the bundle records the URL and the
  commit, and hashes every file.
- Task types: add a function or method to an existing module, fix a bug reproduced by the requester's statement,
  behaviour-preserving refactor of one module. Not supported: schema or dependency migrations, services, UI, anything
  needing network at test time.
- Limits: at most 2,000 files and 25 MB; test suite under 5 minutes on the base; write scope limited to named
  globs; `tests/**` and packaging files protected; at most 12 implementer turns; per-run cap $0.50 on Nemotron.
- Safeguards: networking off after checkpoint; per-test privilege separation; the existing suite run in its own
  branch (section 3.2); daily cap, disk guard and retention as today; pilot users run with their own `NEBIUS_API_KEY`
  on the CLI, so our balance is not exposed; the console gets external repositories only behind the admin token.

## 3. Engineering and evidence audit

Audited today against the code, not against earlier reports.

### 3.1 Fail-closed behaviour: what holds and what does not

| Condition | Behaviour | Verdict |
| --- | --- | --- |
| Sandbox operation not SUCCESS, guest report markers missing or unparsable | `runner_error` set; every parsed step returns `all_passed: False`; a reason is appended | holds |
| Sealed result missing, forged, wrong nonce, file digest changed, unexpected ids, nonzero exit, signal, timeout | binding check fails with a named reason | holds |
| Mutation: all unknown, or fewer than 4 evaluated with unknowns, or score below threshold | gate fails with reason | holds |
| Adversarial module unusable after two attempts, or its sandbox spawn uncertain | gate fails with reason (POST never replayed) | holds |
| Held-out branch spawn uncertain | gate fails with reason | holds |
| Drift audit call fails or returns a schema-violating object | `ModelError`, gate fails with reason (schema validated with `jsonschema`, one repair retry) | holds |
| Any exception in the pipeline | verdict ERROR with the exception recorded | holds |
| Breaker skipped because verification failed | gates marked `skipped: True`, never counted as pass; arbitration excludes them | holds |
| `adversarial.skipped` truthy | gate would pass with a warning | dead path today (never set), but a latent fail-open; remove |
| No mutable sites on the changed lines (`generated == 0`) | mutation gate passes with a warning | weak: a patch written as data tables or string constants gets a free pass; require the adversarial gate to carry the load and show the warning in the verdict header |
| Arbitration apply mode | VERIFIED with `superseded_reasons` | opt-in only; keep advisory as the default and say so in the UI |

### 3.2 Remaining ways candidate code could influence verification

| Id | Vector | Severity | Fix | Cost |
| --- | --- | --- | --- | --- |
| V1 | In the verification branch the repository's own test command runs **first, as root, in the same operation** as the sealed supervisor (`[existing_step()] + suite_steps(nonce)` in `pipeline.py`; the guest runner executes steps with the operation uid, which is root). Candidate code imported by those tests can write a `sitecustomize.py` or `.pth` into site-packages or replace the interpreter, and the supervisor, started next with the nonce in its argv, would run that code: a forged result with the correct nonce and digests. Mutant branches do not run the existing step, so a wrong candidate would still show mutants "killed"; the held-out branch is also stdout-parsed (V2). | high | Run the sealed supervisor first and the existing suite in its own disposable branch (or as uid 65534 after the supervisor, which needs a writable copy of the repository). Add an offline regression test that fails if the existing step precedes the supervisor in the same step list. | one extra sandbox operation per verification, about 15 s; no inference |
| V2 | Existing-suite and held-out results come from the runner's stdout and exit code (`parse_test_output`), with candidate code imported in-process as root. A candidate can print a fake summary and exit 0. | medium | Run both through the supervisor protocol (one child per test, uid 65534, nonce-bound result) for `unittest`; for `pytest` use a result file written by a trusted plugin under the supervisor and parse that. Until then, label both gates "stdout-parsed" in the bundle and the console. | no inference |
| V3 | Inside a sealed-test child, candidate code runs in the same process after the nonce was read (import-time hooks on `TestResult`, `os.write` or the stdin reader) and can forge its own result. Documented residual. | medium, detected | Add two sealed canaries the supervisor injects: one test that must pass and one that must fail (an assertion against a wrong constant). Blanket forgery flips the must-fail canary and is caught; the mutation gate remains the structural detector; add a static tamper scan of the diff for `sys.modules`, `unittest`, `os.write`, `_exit`, frame introspection, reported as a warning. | no inference |
| V4 | Same model (Super) seals, implements and breaks, so blind spots correlate. | low | Seal with Ultra on the judge profile (about +$0.01 per run), or at least break with a different Nemotron model; record the roles per bundle (already done). | small |
| V5 | A patch with no mutable sites passes the mutation gate with only a warning (3.1). | low | Fail closed when both `generated == 0` and the adversarial module produced fewer than 6 tests. | none |
| V6 | The specification can be wrong or unsatisfiable and the sealed tests follow it (the `rle-encode` case, 3.3). The human never sees the frozen contract before implementation in the console flow. | product | Show the frozen contract and the red-check result as the first visible artifact; add a satisfiability question to the spec prompt ("name any requirement that cannot hold given the fixed code") and treat a positive answer as INFEASIBLE. | none to small |

Not vectors: the implementer's `run_tests` and `run_python` branches are disposable and cannot change the retained
checkpoint; branches never see the sealed directory until verification; the supervisor chowns and chmods the sealed
copy before any child starts; uid 65534 children cannot signal the supervisor or write root-owned files (verified in
real Sandboxes on 16 Oct, `reports/attest-hardening-2026-10-16/`).

### 3.3 Evaluation method: three corrections to make before any result is quoted again

1. **Held-out independence.** The three generated tasks (`rle-encode`, `roman-to-numeral`, `balanced-brackets`) and
   `semver-is-compatible-pr368-v2` configure `heldout_tests` in `task.json` pointing at the same file that
   `SUITE.json` gives the independent judge. Inside Attest the held-out gate therefore saw the judge's suite, and
   Attest could not have said VERIFIED while failing it. Only `durationkit-units-001` had a judge independent of the
   gates. The reported "zero false acceptances" is valid as "Attest never certified a patch that failed its own gates",
   not as an independent measurement. Fix: the harness strips `heldout_tests` from the task it hands to Attest, and
   the judge's suite is written separately from any suite a gate sees.
2. **No best-of headline.** `evaluation-final.json` is a merge that keeps the best completed attempt per cell. The
   brief's rule is right: report every scheduled attempt. The next evaluation pre-registers the attempt count and
   reports infrastructure errors as cells, with no merge.
3. **The `rle-encode` finding is a contract defect, not an implementation bug.** `decode` reads every digit after a
   character as part of the count, so no `encode` can round-trip any string containing a digit while `decode` stays
   fixed. The hold was right; the arbiter's label was wrong; the evaluation README's "real bug the plain agent
   shipped" must be corrected to "a requirement no implementation could satisfy, which Attest held and the plain
   agent shipped silently". A correction note goes next to the original (never edited).

All held-out suites stay independent of implementation and arbitration today: they are never shown to the implementer
or the arbiter, and arbitration refuses to touch a held-out failure (verified in `pipeline.py`).

### 3.4 What a Proof Bundle records today, and what is missing

Recorded: task id and statement, per-file repository digests, specification digest, held-out digests, sealed-suite
digest and author model, base image, checkpoint image and operation ids, networking flag, every sandbox operation id
per stage, per-test exit codes, signals and timeouts, binding checks, gates with details, verdict reasons and
warnings, every model call with model, effort, tokens, cost and the conservative reservation, `max_tokens`,
limitations. Missing: the Attest code revision (there is no git repository yet), the guest runner and supervisor
source digests, `temperature` (hardcoded 0.2, not written), implementer turn limit and thresholds in one place, the
upstream repository URL and commit for externally sourced tasks (python-semver records "parent of PR #368" only in
prose), a per-artifact digest manifest, and an explicit "what this proves / does not prove" section that cites the
exhibits (PROOF.md has "Limitations", which is close).

### 3.5 Usage accounting, deduplicated

76 `proof_bundle.json` files exist in the project; 20 are copies of runs into `reports/` (same `run_id`). Unique
runs: 56 (46 Nebius, 10 Codex). Adding the three runs that exist only on the server (judge-demo and submission-pilot
runs started from the console), the deduplicated Nebius usage is **49 unique runs, $1.80 committed**, all on
15 Oct 2026 (UTC), 3 uncertain calls counted at their reservation. The $2.13 quoted earlier today double-counted the
copies. Codex gateway usage is separate (allowance, no USD). The official figure still needs the Token Factory
console, which only the account owner can read. The console store also holds duplicate rows for three runs started
from the console and re-imported from disk (microsecond and second-resolution ids): a hygiene bug to fix with a
`usage_report.py` that keys by bundle `run_id` and by the per-run directory, and an import that recognises its own
runs.

### 3.6 Entry points and inference defaults (Codex-first policy)

| Entry point | Default | Status |
| --- | --- | --- |
| `python -m attest run` / `preflight` | `--provider codex` | correct |
| `scripts/run_evaluation.py` | `--provider nebius` | **wrong default** for exploratory use; change to `codex`, require `--provider nebius --approve-usd <cap>` with a batch cap and a maximum attempt count; a per-run cap alone does not control a batch |
| `scripts/arbitration_sandbox_check.py`, `scripts/sandbox_adversarial_tests.py`, `scripts/probe_*` | Codex or sandboxes only | correct |
| Console `POST /api/runs` | `provider` defaults to `nebius` for public callers (the judge profile) | intended, but live inference should be an explicit choice with a cost estimate (section 6); the development gateway is named in the public form and should be hidden behind the admin token |
| Worker | builds exactly the provider requested; a Codex failure ends in ERROR, never a Nebius fallback | correct |

The actual provider, model and effort are recorded per call in every bundle (`requested_model`, `requested_effort`).

## 4. Gaps, ranked

Technical: (1) V1 verifier bypass; (2) stdout-parsed existing and held-out gates; (3) evaluation method (3.3);
(4) missing provenance fields and no offline `check`; (5) batch cap and default provider in the evaluation script;
(6) store duplicates and usage accounting.

Product: (1) no public repository, license or video (Stage One); (2) no external-repository workflow, so no external
outcomes possible; (3) no counterexample in the product surface; (4) arbitration policy (advisory vs apply)
undecided and invisible; (5) the Tavily grounding never appears in a shipped bundle.

UI: (1) no hierarchy (verdict, reasons, then a 300-line progress log, then the evidence); (2) no concrete failed input
shown; (3) live, recorded and synthetic indistinguishable; (4) state (tab, expanded sections, focus) lost every 4 s;
(5) no empty, loading or error design; (6) no keyboard model; (7) the launch form defaults to paid live inference with
no estimate.

## 5. Prioritised improvement plan

Effort is working days for one engineer with assistance. "Inference" is paid Nebius USD; Codex gateway use is the
team allowance and is listed as "Codex". Each item names its acceptance criterion.

### M1. Close the bypass and fix the evaluation method (1.5 days, Codex only)

| Item | Acceptance criterion | Depends on | Inference |
| --- | --- | --- | --- |
| 1.1 Sealed supervisor before the existing suite; existing suite in its own branch | Offline test asserts step order; a real-sandbox adversarial scenario that plants `sitecustomize.py` from the existing step is recorded as tamper and the verdict is NEEDS HUMAN | none | Codex, sandboxes free |
| 1.2 Canary tests and static tamper scan | Scenario "forge all results" is caught by the must-fail canary; scan reports the diff pattern as a warning | 1.1 | none |
| 1.3 Label stdout-parsed gates; unittest held-out and existing suites through the supervisor | Bundle marks `evidence_class` per gate (`bound`, `stdout`); durationkit and the three generated tasks run both suites bound | 1.1 | Codex |
| 1.4 Fail closed on `generated == 0` with a thin adversarial module; remove the `skipped` fail-open path | Offline tests | none | none |
| 1.5 Evaluation harness: strip `heldout_tests` for the system under test, pre-registered attempts, no merge, Codex default, `--approve-usd` batch cap and max attempts | A dry run on Codex produces a report with every scheduled attempt and the cap recorded | none | Codex |
| 1.6 Correction note for `rle-encode` and the evaluation README; usage report script; store import dedupe | `reports/attest-evaluation-2026-10-16/CORRECTIONS.md`; `scripts/usage_report.py` prints unique runs and committed USD by provider and day | none | none |

### M2. Bundle provenance and offline check (1 day, no inference)

| Item | Acceptance criterion |
| --- | --- |
| 2.1 Record Attest revision, runner and supervisor digests, sampling parameters, turn limit and thresholds, upstream URL and commit | Present in every new bundle; `PROOF.md` section 1 shows them |
| 2.2 Artifact manifest with sha256 per file; `python -m attest check bundle.zip` | `check` recomputes digests, binding and gate-to-verdict derivation and exits non-zero on any mismatch; offline tests with a tampered zip |
| 2.3 "What this bundle proves, and what it does not" in PROOF.md citing exhibits E1 to E7 | Section present and generated from the gates, not hand-written |

### M3. Console redesign (2 days, no inference; fixtures and recorded runs)

| Item | Acceptance criterion |
| --- | --- |
| 3.1 Decision header, tabs, exhibits, counterexample block, provenance chips, history with filters | Matches the approved prototype; verified in a real browser at 1440 px and 390 px, light and dark |
| 3.2 Keyed updates; tab in URL; expanded exhibits and focus preserved | A running run keeps an open exhibit and keyboard focus across 20 refreshes (manual test recorded with a screenshot sequence) |
| 3.3 Launch form: browse recorded evidence by default; live run shows estimate from recorded runs and remaining daily budget; development gateway hidden until a token is entered | Public page source contains no gateway name |
| 3.4 API additions: run-row summary, provenance field, counterexample fields, artifact manifest | `attest-console.md` updated; offline API tests |

### M4. Bounded external repositories and the pilot (1.5 days, Codex for development)

| Item | Acceptance criterion |
| --- | --- |
| 4.1 `task.json` from a GitHub URL plus commit, or a local path, with limits enforced before any sandbox operation | Limits in section 2.4 enforced with tests; refusal messages name the limit |
| 4.2 One real external task end to end on Codex, kept as evidence | Bundle with upstream URL and commit recorded |
| 4.3 Pilot kit: README section, a `PILOT.md` with the exact commands, and an issue template for feedback | Two outside developers can follow it without us (dry-run by someone who did not write it) |

### M5. Final evaluation and submission materials (1.5 days plus the approved Nebius run)

| Item | Acceptance criterion |
| --- | --- |
| 5.1 Frozen evaluation: 8 tasks (the 5 plus one regression repair, one refactor, one external repository task), independent held-out suites, 2 scheduled attempts per cell, all reported | `METHOD.md` committed before the run; report lists 32 scheduled cells with no merge |
| 5.2 Public repository with license, README highlighting Nemotron and Token Factory, no proposal documents, no secrets | Secret scan clean; license visible in About; prepared on a branch for review before publishing |
| 5.3 Video under 3 minutes, public on YouTube; Devpost description; feedback submission | Script reviewed; video shows a live Nemotron run and the counterexample |
| 5.4 Redeploy with before/after snapshots and scoped rollback | Same procedure as `reports/attest-deployment-2026-10-16/` |

Dependencies: M3 and M5 depend on M1 (the UI shows evidence classes and the evaluation needs the fixed harness);
M4 depends on M1.1 (external code must not run as root before the supervisor); M2 can run in parallel with M3.

Suggested calendar: M1 by Oct 18, M2 and M3 by Oct 22, M4 by Oct 24, M5 evaluation run Oct 25 to 26 after
approval, submission Oct 28, leaving two days of margin before the Oct 30 10:00 PDT deadline.

## 6. User journey and UI concept

The reviewer's journey, in the order the console answers it:

1. Arrive on the console: see at once whether this is the live service or recorded evidence, what today's budget
   allows, and a history of runs with verdict seals.
2. Choose a task; the default action opens the latest recorded run (no cost). Running live is a second, explicit
   choice with an estimate taken from recorded runs of the same task.
3. Queued: position, reservation, what will happen. Running: stage stepper, meters, event log; nothing moves under
   the reader's hands.
4. Finished: the decision header answers "can I accept it" with the verdict, one sentence, the concrete failing input
   or the key check, and the actions. Tabs then answer "what was requested", "what changed", "what evidence supports
   this" and "what happened", with raw data behind disclosure.
5. NEEDS HUMAN says what to decide; ERROR says which component failed and that nothing was certified.

The annotated layouts, tokens, state coverage and open questions are in `design/console-redesign-2026-10-16/README.md`;
the prototype is `design/console-redesign-2026-10-16/prototype.html` with review screenshots in `screens/`. Approval
of that direction is requested before any change to `attest/app/static/`.

## 7. First implementation milestone recommended

M1. It removes a real bypass of the verifier (V1), makes the evaluation defensible before any new result is quoted,
and costs no Nebius inference. It is also what judges score first and use as the tie-breaker. The console redesign
is the second milestone to start, in parallel with M2, once the UI direction is approved.

## 8. Proposed paid Nebius usage, for approval (not started)

| | Proposal |
| --- | --- |
| Purpose | M5.1 frozen evaluation (plain agent vs Attest) and one public demo run for the video |
| Models | Ultra (spec, audit, arbitration), Super (seal, implement, break), Lightning (summary); the plain agent uses Super for implement, as before |
| Maximum calls | 32 cells, at most 20 model calls per cell, so at most 640 calls, plus 20 for the demo run |
| USD cap | $6.00 total: $0.50 per run (existing), batch cap enforced by the harness (new in M1.5), demo run $0.50 |
| Concurrency | 2 cells at a time (the 50-operation Sandboxes limit is far above this) |
| Stop conditions | Batch cap reached; 3 consecutive infrastructure errors (reported, never replayed); any uncertain POST spawn ends that cell as ERROR |
| Reporting | Every scheduled attempt in the report; Codex and Nebius never pooled |

Current balance basis: $1.80 committed across all Nebius runs to date (section 3.5), against the $26 credit seen in
the console on 15 Oct. Please confirm the official console figure before approving.

## 9. Where we remain weaker, stated plainly

- No external user, no external pull request, no testimonial, and no mechanism yet for an outside developer to try
  Attest on their own code. FixFork at least touched upstream repositories.
- The controlled evaluation as published is not an independent measurement for four of five tasks, and its headline
  is a best-of merge; both are corrected in M1 and the numbers must not be quoted until then.
- The verifier's privilege separation has a real bypass through the existing-suite step (V1) until M1.1 lands.
- Stage One requirements (public repository with license, public video) are not met yet.
- Five bundled tasks, three of them small; the evidence story rests on one real repository (python-semver).
- Hosting on a 1 vCPU, 728 MB server; one run at a time; the judging window overlaps a $2 per day cap that would not
  survive a busy judging day without the planned budget review.

---

Appendix. Files produced today: this brief; `competitors/{mutiny,runanchor,fixfork,patchscout,agent-forensics-lab,naviguide}.md`;
`judging-criteria-2026-10-16.md`; `design/console-redesign-2026-10-16/{README.md,prototype.html,screens/}`.
