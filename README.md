# Attest

An evidence-gated coding agent for the Nebius x NVIDIA Global AI Hackathon (Coding and Agentic Engineering track).
Every task is a claim that must be proven: an independent model instance seals acceptance tests before any code exists,
the tests are shown failing on an unmodified checkpoint, the implementer works through validated JSON actions,
a fresh sandbox branch verifies the candidate against the pristine sealed copy, and a Proof Bundle records the evidence
and the usage ledger.

Status (16 Oct 2026): end-to-end pipeline with a hardened, privilege-separated verifier, a web console/API, and a live
deployment, plus a controlled evaluation against a plain agent. Start with the dated reports:
`reports/attest-hardening-2026-10-16/README.md` (verifier privilege separation, budget, disk, arbitration, implementer
efficiency), `reports/attest-evaluation-2026-10-16/README.md` (plain agent vs Attest, independent held-out judge),
`reports/attest-deployment-2026-10-16/README.md` (hardened build live at https://attest.axiqo.xyz). See
`attest-first-slice.md` for the earlier slices, `attest-console.md` for the console, and `attest-product-design.md` for
the full design. Competitive review, audit and plan (16 Oct 2026): `reports/attest-competitive-review-2026-10-16/README.md`;
console redesign (approved 16 Oct 2026, implementation pending): `design/console-redesign-2026-10-16/`. Milestone M1
(16 Oct 2026, `reports/attest-m1-2026-10-16/README.md`): the sealed supervisor is the first step of its own branch and the
repository's own suite runs in a separate branch (closes the root-before-supervisor bypass); verifier canaries and a
start-up-hook check catch blanket result forgery; unittest repository and held-out suites are bound through the same
supervisor and every gate carries an evidence class; the evaluation harness pre-registers every attempt, strips the
held-out suite from the system under test, defaults to Codex and refuses an unapproved Nebius batch. Corrections to the
earlier evaluation: `reports/attest-evaluation-2026-10-16/CORRECTIONS.md`. Milestone M2 (17 Oct 2026,
`reports/attest-m2-2026-10-17/README.md`): provenance in every bundle, an artifact manifest, the offline `attest check`,
one recorded verdict rule and exhibits E1 to E7 in PROOF.md. Milestone M3 (17 Oct 2026,
`reports/attest-m3-2026-10-17/README.md`): the console redesign approved on 16 Oct, implemented in `attest/app/` and
verified in a real browser. Reliability round and milestone M4 (17 Oct 2026, `reports/attest-reliability-2026-10-17/README.md`,
`reports/attest-m4-2026-10-17/README.md`): the three dry-run holds resolved (one verifier defect in the supervisor's result
pipe, one wrong expected value in a generated test, one contract gap), supervisor v6, Codex pacing that adopts the
gateway's declared policy, batches run from an immutable snapshot with provenance checks, the bounded external-repository
import with a real python-semver task, the pilot kit (`PILOT.md`) and the frozen M5 method (`METHOD.md`). License: MIT.

Gateway operations update (17 Oct 2026): the self-hosted Codex API's hourly request cap has been removed and the
Aliyun backend deployed and verified. Authentication, daily caps, one active request/eight waiting slots, priorities,
deadlines and ingress protection remain. See [deployment and regression evidence](reports/codex-gateway-hourly-limit-removal-2026-10-17/README.md).
The Attest application was not redeployed and the recorded evaluation was not rerun by this operation.

## Deployment targets

The final console, API, orchestration, and application data/database when needed belong on the existing `yungou` server, confirmed by the owner as DogYun `206.237.18.80` on 2026-10-15. Prepare that application deployment without Docker. Components that genuinely require Docker run on the existing Aliyun host; Nebius Sandboxes remains the primary isolated task executor. Final deployment and any cross-host Docker worker are not yet verified. See [deployment targets](deployment-targets.md) for the user-selected host policy and required deployment evidence.

## Layout

```
attest/
  secrets.py              private credential loading (env, then the private vault notes; never written to artifacts)
  http.py                 TLS-verified JSON client; POST outcomes are never replayed
  ledger.py               model-call and sandbox-operation ledgers
  models/codex_gateway.py        development provider: self-hosted Codex gateway, POST /v1/run with output_schema
  models/nebius_tokenfactory.py  submission provider: NVIDIA Nemotron on Token Factory, json_schema response format, USD cap
  sandbox/tf_sandboxes.py        Token Factory Sandboxes REST adapter: checkpoint + disposable networking-off branches
  core/task.py            task.json loading and freezing (content digests, pinned install, runner, held-out tests)
  core/workspace.py       implementer workspace with a write-scope policy and unified diff
  core/prompts.py         stage prompts and strict JSON schemas (spec, seal, action)
  core/testparse.py       unittest (subtest-aware) and pytest output parsers for the repository's own suite
  core/sealed.py          sealed-suite supervisor and child (nonce, digests, uid 65534 children, canaries, start-up-hook check),
                          static discovery of repository suites, and the host-side binding
  core/tamper.py          static tamper scan of the candidate's added lines (warnings, never a gate)
  core/mutate.py          AST mutants of the candidate's changed lines for the breaker pass
  core/pipeline.py        freeze -> checkpoint -> spec -> ground -> seal -> red -> implement -> verify (bound, privilege-separated) -> held-out -> break -> drift -> arbitrate -> attest
  core/verdict.py         the one gate-to-verdict rule (used by the pipeline and re-derived by `attest check`)
  core/exhibits.py        exhibits E1 to E7, decision copy per verdict and reason class, counterexamples, "what this bundle proves"
  core/provenance.py      Attest revision digest, supervisor/child/canary/runner digests, sampling parameters, limits, upstream
  core/manifest.py        manifest.json: sha256, size and purpose of every artifact (written last)
  core/check.py           `attest check`: offline recomputation of digests, bindings, ledger totals, verdict rule and PROOF.md
  core/proof.py           Proof Bundle (proof_bundle.json + PROOF.md, exhibits and provenance sections)
  app/                    FastAPI console + API, single worker, SQLite store, static UI (decision header, exhibits E1 to E7,
                          counterexamples, keyed updates, recorded evidence first; development profile only after a team token)
  cli.py                  `python -m attest preflight|run|check` (run: --arbitration-apply, --no-arbitration, ...)
examples/eval/            frozen evaluation suite (SUITE.json) with independent held-out tests
scripts/run_evaluation.py plain agent vs Attest harness: pre-registered attempts, held-out stripped from the system under test,
                          Codex by default, Nebius only with --approve-usd and --max-calls
scripts/usage_report.py   deduplicated usage by provider and day (keyed by bundle run_id; optional console store)
scripts/sandbox_adversarial_tests.py  real-sandbox adversarial scenarios for the supervisor (forgery, hook planting, legacy order)
examples/durationkit-task/     sample repository (unittest) and task.json
examples/semver-is-compatible/ python-semver at the parent of PR #368, pinned pytest, upstream held-out tests
tests/                    offline harness tests: adversarial verification scenarios, verification order, canaries, bound
                          suites, the real supervisor run locally, store hygiene, manifest and tampered-bundle checks
reports/                  dated evidence (preflight, probes, Proof Bundles)
runs/                     run outputs (git-ignored)
```

## Running

Credentials are loaded from the process environment first (`NEBIUS_API_KEY`, `CODEX_API_KEY`, `TAVILY_API_KEY`), then,
only on a developer machine that configures it, from a private credential note mapped in `~/.config/attest/notes.json`.
`NEBIUS_PROJECT_ID` / `NEBIUS_AI_PROJECT` hold the project ID, never the key. The development gateway's URL comes from
`ATTEST_CODEX_BASE_URL`. Nothing secret is written to `runs/` or `reports/`.

```bash
python3 -m unittest discover -s tests -t . -v                       # offline harness tests
python3 -m attest preflight --provider codex --adapter-smoke          # queue, catalog, sandbox limits, one disposable op
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider codex
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider nebius --usd-cap 0.5
python3 -m attest run --task examples/semver-is-compatible/task.json --out runs --provider codex --max-mutants 12
python3 scripts/run_evaluation.py --provider codex --attempts 1 --label dryrun        # exploratory evaluation (allowance)
python3 scripts/run_evaluation.py --provider nebius --attempts 2 --approve-usd 6 --max-calls 20 --label final  # after approval only
python3 scripts/usage_report.py --store data/attest.db                               # unique runs and committed USD
python3 -m attest check runs/<run-id>            # offline: manifest digests, bindings, ledger totals, verdict rule, PROOF.md
python3 -m attest check downloaded-bundle.zip --json
python3 -m attest import --github https://github.com/<owner>/<repo> --commit <40-char sha> --id my-task --out tasks \
    --runner pytest --write-glob 'src/<pkg>/**' --python-path src --pin pytest==8.3.3 --pin pluggy==1.5.0 \
    --pin iniconfig==2.0.0 --pin packaging==24.1 --statement-file statement.txt --criteria-file criteria.txt   # bounded external import (M4)
python3 scripts/replay_holds.py --run <run-dir> --task <task.json> --module original=<tests.py> --out replay.json [--sandbox]  # re-run breaker tests on candidate and base
python3 scripts/run_evaluation.py --resume reports/<batch-dir>     # continue an interrupted batch from its own snapshot (cells never executed only)
python3 scripts/export_public.py --out dist/public                 # allowlisted, redacted copy for the public repository, with a secret scan
```

External repositories (M4, `attest/core/external.py`, `PILOT.md`): a public GitHub repository at a pinned commit, or a local
directory, becomes a task under documented bounds that are enforced before any sandbox operation and named in every refusal:
at most 2,000 files and 25 MB, 200 KB per file by default (hard cap 1 MB), Python with unittest or pytest, pinned
dependencies installed once at checkpoint time, an explicit write scope, protected tests and packaging files, test
timeout at most 300 s, at most 12 implementer turns. The sandbox job is gzip-compressed and a checkpoint larger than one
request (about 400 KB compressed) is built as a chain of retained images.

Codex pacing (`attest/models/pacing.py`): every request of the development profile takes a slot from one process-wide
governor per key (all roles, all workers; shared with other processes on the machine through a small state file). The
governor adopts the gateway's declared policy from `GET /v1/status` (hourly counting is not enforced since 17 Oct 2026),
keeps at most two requests in flight, and treats an HTTP 429 as a definite rejection: the attempt is recorded as a failed
call, the key is blocked for the declared or inferred interval, and the same request is retried after a bounded wait.
When the bound is exceeded the call fails visibly (`ERROR` verdict, infrastructure error in the harness). Nothing ever
falls back to paid Nebius inference. Without a readable policy the governor assumes the limit observed on 16 and 17 Oct
(60 requests per rolling hour, 90% of it planned).

Evaluation provenance (`scripts/run_evaluation.py`): a batch copies the package, the harness and the task files into
`<report>/snapshot/` and re-executes itself from that copy in a fresh process; the schedule records the application
revision, the harness digest, the examples digest and the guest-program digests actually executed, every row records its
bundle's revision, and a task whose cells did not all run the registered revision (or whose snapshot changed) is marked an
invalid comparison. The frozen M5 method is `METHOD.md`; the suite is `examples/eval/SUITE-M5.json`.

Options: `--max-turns` (implementer actions), `--max-mutants` and `--mutant-workers` (breaker pass, parallel branches),
`--mutation-threshold` (warning below this score), `--usd-cap` (hard per-run cap for the Nebius profile, enforced by a
conservative pre-request reservation).

Model roles can be overridden per provider: `ATTEST_CODEX_ROLES="spec=gpt-6-astra:low,implement=gpt-6-sol:medium"`,
`ATTEST_NEBIUS_ROLES="spec=nvidia/Nemotron-3-Ultra-550b-a55b,implement=nvidia/nemotron-3-super-120b-a12b"`.

## Execution model

One retained checkpoint per task (repository unpacked, baseline suite run), then every later execution is a disposable
branch of that image with networking disabled: the sealed-test red check, each implementer `run_tests` / `run_python`
action, and the final verification. Inputs travel as a base64 JSON job on stdin to a small stdlib guest runner that
writes files, runs steps and returns a JSON report. Repositories with dependencies install a pinned set at checkpoint
time (the only operation with networking on). Sealed tests are injected only into red-check, verification and mutant
branches; the implementer never receives them. A root supervisor that never imports candidate code runs one child
process per test as uid 65534, hands each child the per-run nonce only after the test module is imported, hashes every
test module before and after, makes every import-path root root-owned, checks for interpreter start-up hooks, and runs
two verifier canaries (one must pass, one must fail) after the suite. The verdict is bound to the test IDs proven red,
the digests, the nonce and the canaries, so edited tests, forged console output, hidden tests, early exits and blanket
result forgery are recorded as failures (see `tests/test_verification.py`, `tests/test_m1.py`).

Order rule: the sealed supervisor is the only step of the verification branch; nothing that imports candidate code runs
before it in the same sandbox operation. The repository's own suite and the held-out suite run afterwards in their own
disposable branches. For unittest repositories whose tests are statically discoverable they run through the same
supervisor and are bound to the frozen digests (`evidence_class: bound`); otherwise they are parsed from console output
and labelled `stdout`. Every gate in the Proof Bundle carries its evidence class (`bound`, `stdout`, `model`).

Proof Bundle integrity (M2): every run records its provenance (Attest revision digest, supervisor and runner digests,
sampling parameters, limits, upstream commit), the raw supervisor results (`verify_raw.json`) and, written last, a
manifest with the sha256 of every artifact. `python -m attest check` recomputes the digests, the bindings, the ledger
totals and the gate-to-verdict rule offline and re-renders PROOF.md; any mismatch exits 1. The manifest is an integrity and
internal-consistency check, not a digital signature and not independent proof that the sandbox operations happened (that
evidence is the operation ids and the nonce-bound per-test records). PROOF.md opens with the
decision, the key exhibit and "What this bundle proves, and what it does not", generated from the gates and citing the
exhibits E1 to E7 (sealed tests, mutation check, tests written after the patch, held-out tests, drift audit, arbitration,
failure record).

## Profiles

| Profile | Inference | Execution | Label |
| --- | --- | --- | --- |
| development | Codex gateway (`gpt-6-astra` spec, `gpt-6-sol` seal and implement) | Token Factory Sandboxes | `provider=codex_gateway` |
| submission | NVIDIA Nemotron on Nebius Token Factory (Ultra spec, Super seal and implement) | Token Factory Sandboxes | `provider=nebius_tokenfactory` |

Development results and submission results are never pooled.

## Console

```bash
python3 -m venv .venv && .venv/bin/pip install "fastapi==0.115.5" "uvicorn[standard]==0.32.1" jsonschema certifi
ATTEST_DATA_DIR=./data ATTEST_IMPORT_DIRS=./runs ATTEST_ADMIN_TOKEN=change-me \
  .venv/bin/python -m uvicorn attest.app.server:app --host 127.0.0.1 --port 4070
```

Open http://127.0.0.1:4070. The console opens recorded evidence by default (no inference); "Run live on Nemotron" is an
explicit action that shows the cost and duration range of recorded runs of the same task and the remaining daily
budget. Judges run the Nemotron profile (rate-limited, budget-capped); the development profile appears only after the
team token is validated by the server, and the public page source names no gateway. A run reads as a case file: the
verdict seal, one decision sentence, the key exhibit, then tabs for the request, the patch, the exhibits E1 to E7 with
counterexamples, the activity and the artifacts with their digests. `scripts/console_replay.py` replays a recorded run
as a labelled synthetic fixture for development. See `attest-console.md` for the API and the verified behaviour, and
`deploy/yungou/` for the production deployment without Docker (the redesign is not deployed yet).
