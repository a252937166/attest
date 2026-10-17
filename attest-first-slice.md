# Attest first working slice: one Python task end to end

Date: 2026-10-15. Scope: the first complete task lifecycle on the verified infrastructure. This document records runnable
commands, observed results, measured usage, and the integration gaps that remain. Development inference used the
self-hosted Codex gateway; a separate native Nebius pilot is recorded in section 5. Development and Nebius results are
never pooled.

## 1. What was built

`attest/` (Python 3.12, standard library plus optional `jsonschema` and `certifi`):

| Component | Role |
| --- | --- |
| `secrets.py` | Loads `NEBIUS_API_KEY`, `CODEX_API_KEY`, `TAVILY_API_KEY` from the environment or the private vault notes; project ID separate; nothing written to artifacts |
| `models/codex_gateway.py` | Development provider: `POST /v1/run` with `output_schema`, explicit `model` + `effort`, catalog-validated, no streaming, no native tools, no automatic retry |
| `models/nebius_tokenfactory.py` | Submission provider: Nemotron on Token Factory, JSON-schema response format, USD computed from the public price table, per-run USD cap |
| `sandbox/tf_sandboxes.py` | Token Factory Sandboxes REST adapter: retained checkpoint, disposable networking-off branches, base64-stdin JSON job to a stdlib guest runner, accepted operation UUID recorded before polling, no POST replay |
| `core/pipeline.py` | Freeze -> checkpoint -> spec -> seal -> red check -> implement (JSON actions) -> verify -> Proof Bundle |
| `core/workspace.py` | Implementer workspace with allowed/protected path globs and unified diff |
| `core/proof.py` | `proof_bundle.json` and `PROOF.md` |
| `tests/test_core.py` | 8 offline harness tests (parser, policy, freezing, schemas) |

Sample task `examples/durationkit-task`: extend `parse_duration` with unit suffixes (d, h, m, s, ms) in descending
order, keep the six existing tests passing, tests directory protected.

## 2. Commands

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m attest preflight --provider codex --adapter-smoke --output reports/attest-preflight-2026-10-15.json
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider codex --max-turns 12
python3 -m attest run --task examples/durationkit-task/task.json --out runs --provider nebius --usd-cap 0.5
```

## 3. Observed results, Codex development profile

Evidence: `reports/attest-first-slice-2026-10-15/codex-development-run/` (Proof Bundle, ledger, sealed tests, trajectory,
candidate patch, run log) and `reports/attest-first-slice-2026-10-15/preflight.json`.

| Stage | Result |
| --- | --- |
| Preflight | Gateway idle (no running or waiting requests), six-model catalog, Sandboxes permissions and limits read back, one disposable adapter smoke op `01a13ed2-f1e2-7286-8177-2426054cd0cb` wrote a file and ran Python 3.12.13 |
| Freeze | 5 repository files, spec digest `e51653cf1b31…` |
| Checkpoint | Operation `01a13ed3-47b9-75e1-8e81-44abeacb0edc`, retained image `47f59023-7a06-42c3-b842-452d3473e304`, baseline 6/6 existing tests pass |
| Spec | `gpt-6-astra` / low: feasible, 15 acceptance criteria, one contract entry, 81.9 s |
| Seal | `gpt-6-sol` / medium: 27 unittest tests in one attempt, 49.9 s |
| Red check | Operation `01a13ed5-7594-75c6-9aa6-3815f809f21c`: 27 sealed test methods; 9 methods fail on the unmodified checkpoint through 24 subtest error events, 18 pass (error-case tests already pass, as expected). Corrected per `reports/attest-first-slice-2026-10-15/corrections-2026-10-15.md` |
| Implement | 11 turns, `gpt-6-sol` / medium: read, write, read, run_tests, run_python x2, write, read, run_python, run_tests, finish; two writes to `durationkit/parse.py`, zero policy rejections, zero malformed actions |
| Verify | Operation `01a13eda-47ab-70dd-9364-1b7f32a2e4cb`, fresh disposable branch, networking off: existing 6/6, sealed 27/27 |
| Verdict | VERIFIED; wall clock 09:09:47 to 09:17:33 UTC (7 min 46 s) |

Usage (Codex gateway, ChatGPT allowance, not USD): 13 calls, 175,694 input tokens (36,736 cached), 8,139 output tokens,
420.8 s of model time. Sandboxes: 8 operations, 5.59 s total guest duration, one retained image, raw diagnostic cost sum
0.0191 (no confirmed currency semantics; not a charge). Console balance after the run: still $25.00 plus the $1 trial.

Finding worth keeping: the original function already accepted leading zeros and Unicode decimal digits for plain
numeric input (`str.isdigit()` plus `float()`), so the specification preserved that compatibility; the additional
assumption it introduced was extending the same acceptance to unit-bearing input, which the request did not ask for.
The sealed tests encoded it and the implementation satisfied it. Nothing was wrong in this case, but it is the
scope-drift pattern the planned drift audit is meant to surface, and the restated contract should be shown to the
requester before sealing in the product.

## 4. Integration gaps after this slice

| Gap | Status |
| --- | --- |
| Breaker pass (edge cases, mutants in parallel branches), drift audit, Tavily grounding, arbitration of disputed sealed failures | Not implemented |
| Multi-file repositories with dependencies, pytest, TypeScript | Not implemented; the slice uses unittest and a stdlib-only sample, so the checkpoint needs no network |
| Parallel branches | Adapter runs one operation at a time; the account allows 50 |
| Sandbox file upload API (`files` with uploaded UUIDs) | Documented by the service; not implemented or exercised by the adapter, inputs travel as base64 stdin |
| GitHub App or Action, console | Not started |
| Tavily key | Saved; connectivity and quota unverified |
| Nemotron native profile | See section 5 |
| Checkpoint retention | Retained image per run stays on the service; no image-delete control was found in the current public REST API; listed in every ledger |

## 5. Native Nebius inference pilot (NVIDIA Nemotron on Token Factory)

Same task, same sandbox executor, provider switched to Token Factory with Nemotron 3 Ultra for the specification and
Nemotron 3 Super for sealing and implementation; `--usd-cap 0.5`. Evidence:
`reports/attest-first-slice-2026-10-15/nebius-pilot-run/` and the aborted first attempt in `nebius-pilot-attempt1-http422/`.

**Attempt 1 (09:20 UTC) failed before any inference was billed.** The live API returned HTTP 422 naming one missing
field, `response_format.json_schema.name`. The Token Factory docs' primary structured-output examples pass the raw
schema under `json_schema`; the request wrapped as `{"name", "schema", "strict": true}` then succeeded. Established:
`name` is required and the wrapped form works; whether `schema` and `strict` are individually mandatory was not tested.
The client was changed accordingly and the aborted run's retained checkpoint (`532a8fa2-ec1a-4fd5-99c2-2f21b1d07dc7`) stays in its
ledger. The run also exposed a renderer bug on early aborts, fixed in the same change.

**Attempt 2 (09:21:42 to 09:23:23 UTC, 1 min 41 s): VERIFIED.**

| Stage | Result |
| --- | --- |
| Checkpoint | Retained image `9dc49965-9210-4ec4-a7a8-e772ce72e8ab`, baseline 6/6 |
| Spec | Ultra, 7.5 s: feasible, 8 criteria that reproduce the requester's list without widening, 5 out-of-scope rules |
| Seal | Super, 12.2 s: 28 unittest tests in one attempt; red check 13 of 28 fail on the checkpoint |
| Implement | 10 turns, Super: list, read x2, write (3,530 bytes), read, run_tests, run_python x2, run_tests, finish; zero policy rejections, zero malformed actions |
| Verify | Fresh branch, networking off: existing 6/6, sealed 28/28 |

Measured cost from the public price table: **$0.025468** for 12 calls (Ultra $0.0075 for 1,537 in / 1,973 out; Super
$0.0180 for 34,495 in / 8,514 out over 11 calls), 71.8 s of model time. Every response carried
`prompt_tokens_details.cached_tokens = 0` plus `prompt_cache_hit_tokens`/`prompt_cache_miss_tokens` (an earlier
statement that the field was absent is withdrawn). Official usage-view reconciliation by the account owner: four Nemotron
entries totaling $0.0254671 (rounding difference 0.0000009), console $25.00 main balance and $0.97 trial credit, about
$0.03 consumed and offset by trial credit. Usage view, not a final invoice.

Worth noting from the trajectory: at turn 7 the implementer's own check script asserted that `'1h 30m'` must raise,
which contradicts the contract (whitespace between components is allowed); the code was right and the self-check was
wrong, and the model corrected the check at turn 8. The sealed suite, not the implementer's own tests, is what decided
the verdict.

### Development profile versus native profile on the same task

| Measure | Codex gateway (development) | Nemotron on Token Factory (pilot) |
| --- | --- | --- |
| Verdict | VERIFIED | VERIFIED |
| Wall clock | 7 min 46 s | 1 min 41 s |
| Model calls / model time | 13 / 420.8 s | 12 / 71.8 s |
| Tokens in / out | 175,694 / 8,139 (36,736 cached) | 36,032 / 10,487 (cached_tokens = 0 on every call) |
| Cost | ChatGPT allowance (219,177 tokens on the key today, no daily cap, priority high) | $0.0255 computed |
| Sealed tests (methods red on base) | 27 (9 methods, 24 subtest error events) | 28 (13) |
| Implementer turns | 11 | 10 |
| Malformed outputs / HTTP errors | 0 / 0 | 0 / 1 (the 422 in attempt 1, fixed) |
| Spec behavior | Widened the contract (Unicode digits, leading zeros) | Reproduced the request as given |

One task on one small repository is not a quality benchmark; it establishes that both profiles complete the lifecycle
and that native inference is cheap at this size. Per-call input on the gateway is dominated by its own instruction
overhead (10 to 25 K tokens per call), which is why the gateway profile is slower and heavier.

## 6. Budget implication (superseded by section 9 after the multi-file pilot)

At the pilot's measured rate, a task of this size costs about 2.5 cents of Token Factory inference; a medium multi-file
task with a breaker pass will cost more, but the earlier $0.60-per-task estimate now looks conservative for small tasks.
With $25 confirmed, the formal evaluation should be sized after a second pilot on a real multi-file repository, keeping
at least $10 reserved for judge runs in December, as planned. Sandboxes remained free: no consumption appeared for any
of the 16 operations across the three runs.

## 7. Feedback items collected for the submission

- Token Factory docs: the structured-output page's Python and curl examples pass the raw schema under `json_schema`;
  the live API answered 422 with `response_format.json_schema.name` missing, and the wrapped `{"name", "schema",
  "strict": true}` request succeeded (evidence retained for both; only `name` was shown to be required).
- Token Factory usage objects do report cache fields for Nemotron (`prompt_tokens_details.cached_tokens`,
  `prompt_cache_hit_tokens`, `prompt_cache_miss_tokens`); in the pilot they were all zero, so prompt caching did not
  engage for prompts of 1.4 K to 6.9 K tokens.
- Sandboxes: no image-delete control and no VM CPU/RAM quota fields were found in the current public REST API (every
  run leaves a retained checkpoint); file upload is documented but not yet used by the adapter.
- Sandboxes CLI reads `NEBIUS_AI_PROJECT` while the SDK and REST examples read `NEBIUS_PROJECT_ID`.

## 8. Verification hardening and the multi-file pytest pilot (15 Oct 2026, evening)

Changes made before expanding evaluation, each with offline regression evidence in `tests/test_verification.py`
(17 tests) and `tests/test_core.py`:

| Gap from code review | Change |
| --- | --- |
| Candidate code could edit sealed tests or fake the verdict | Sealed suite runs through a `TestResult` recorder in the sandbox; the result JSON carries a per-run nonce, the sealed file digest before and after, the test IDs and a completion flag, and is written only after the whole suite ran. The verifier binds the verdict to the IDs proven red, the digest and the nonce; console text is never trusted. Adversarial scenarios covered: modified tests, forged result file, missing tests, extra tests, premature exit, forged console output |
| unittest accounting | Methods and subtest events are counted separately; the historical Codex red check is restated as 27 methods, 9 failing through 24 subtest error events (`reports/attest-first-slice-2026-10-15/corrections-2026-10-15.md`) |
| Budget enforcement | Nebius client reserves a conservative cost before each call (prompt chars / 3 as input tokens plus the full `max_tokens` output) against the per-run cap, and bounds prompt size (120 K chars); the Codex client bounds prompt size the same way |
| Breaker pass | AST mutants of the candidate's changed lines (comparison, boolean, `not`, arithmetic, constants, `raise`), each run as its own disposable branch in parallel; mutation score with a warning threshold |
| Real repositories | pytest runner support with `-rA` parsing (quiet summary included), pinned dependency install at checkpoint time with networking on, import-path configuration, optional held-out tests run in a separate branch |

Residual limitation: the sealed suite still runs in the same process as the code under test, so in-process forgery is
mitigated, not impossible; per-test process isolation is future work.

### python-semver pilot: `Version.is_compatible` (upstream PR #368, issue #284)

Task: python-semver at commit `9b475f71` (the parent of the PR merge), BSD-3, 30 files, 312 existing pytest tests,
pinned `pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1`; writable scope `src/semver/**`; the PR's own four
test functions are injected as a held-out suite at verification (reported, not a gate). Development profile (Codex).

| Attempt | Outcome | Cause and fix |
| --- | --- | --- |
| 1 (13:21 UTC) | Aborted at baseline: "no summary" although 312 tests passed | pytest `-q` prints `312 passed in 0.65s` without the `===` bars the parser required; regex fixed with a regression test |
| 2 (13:22 to 13:33 UTC) | NO CHANGE after 14 turns; 16 gateway calls, 442,902 input tokens (170,496 cached) | The implementer inserted the method with a `run_python` snippet inside a throwaway branch (turn 3), found at turn 6 that it had not persisted, then tried to fetch the whole 22.6 KB `version.py` in chunks for a full-file `write_file`, which the 20 K-char read limit made impossible. Harness fix: `replace_in_file` (exact unique snippet), ranged `read_file`, an explicit warning when `run_python` writes files, bounded transcript history, and focused repository dumps (full text only for writable files) |
| 3 (13:35:55 to 13:40:44 UTC, 4 min 49 s) | **VERIFIED** | 5 implementer turns: ranged read, one `replace_in_file`, `run_tests`, one `run_python` check, finish |

Attempt 3 in detail (evidence `reports/attest-first-slice-2026-10-15/semver-pilot-codex-attempt3/`):

| Stage | Result |
| --- | --- |
| Checkpoint | `518b19f1-d9ab-4e47-8444-e4fa17498219`, pinned install 2 s with networking on, baseline 312/312 |
| Spec (`gpt-6-astra` / low, 64 s) | feasible, 16 criteria, one contract entry |
| Seal (`gpt-6-sol` / medium) | 24 unittest methods; red check 24 of 24 methods failing on the checkpoint (36 subtest events) |
| Verify | existing 312/312; sealed 24/24; all ten binding checks pass (result file, completion, nonce, digest before and after, no import error, expected IDs present, no extra IDs, ran count, all pass) |
| Held-out upstream tests (PR #368's own four functions, reported only) | 325 of 328 pass; the three failures are `test_should_fail_with_incompatible_type_for_compatible_match[...]`: upstream matches the TypeError message with `"Expected a Version type .*"` (a space and more text after "type"), the statement only required the prefix, and the candidate raises exactly `"Expected a Version type"`. The sealed suite could not see that; the held-out suite did |
| Breaker | 12 mutants of the 26 changed lines (`not` removal, `raise` to `pass`, comparison, boolean and constant flips), all run as parallel branches in 14 s: 12 killed, 0 survived, mutation score 1.00 |
| Usage (Codex allowance) | 7 calls, 117,407 input tokens (0 cached), 6,251 output, 232 s model time; 18 sandbox operations, 21.4 s guest time |

The held-out gap is the point of the design: a candidate that satisfies its contract and its sealed tests can still diverge
from what the upstream maintainers encoded. Attest reports it instead of hiding it; in the product this becomes the
"NEEDS HUMAN" path when a held-out suite is configured as a gate.

### python-semver on NVIDIA Nemotron via Token Factory (formal-profile pilot)

Same task, same sandbox executor, Nemotron 3 Ultra for the specification and Nemotron 3 Super for sealing and
implementation, `--usd-cap 0.5`. Evidence: `reports/attest-first-slice-2026-10-15/semver-pilot-nebius-run/`.

| Stage | Result |
| --- | --- |
| Run | 13:41:25 to 13:43:02 UTC (1 min 37 s), verdict **VERIFIED**, no warnings |
| Spec (Ultra, 6.4 s) | feasible, 17 criteria; 20,549 input / 1,391 output tokens, $0.0247 |
| Seal (Super, 19.1 s) | 16 unittest methods, all 16 red on the checkpoint |
| Implement (Super, 4 turns) | ranged read, one `replace_in_file`, `run_tests` (312/312), finish |
| Verify | existing 312/312; sealed 16/16; all ten binding checks pass |
| Held-out upstream tests | 325 of 328; the same three `[wrongtype]` failures as the Codex run: both implementers raise exactly `"Expected a Version type"` as the statement demanded, upstream's regex expects a trailing ` .*`. The divergence is in the task statement, not the models |
| Breaker | 12 mutants, 12 killed, mutation score 1.00, 11 s in parallel branches |
| Cost (price table) | **$0.042887** for 6 calls (Ultra $0.0247, Super $0.0182); 58,187 input / 9,029 output tokens, `cached_tokens` 0 on every call; 17 sandbox operations, 20.3 s guest time, free |

Console reconciliation for this run was not repeated; the figure is computed from the public price table.

### Development versus formal profile on the multi-file task

| Measure | Codex gateway, attempt 3 | Nemotron on Token Factory |
| --- | --- | --- |
| Verdict | VERIFIED | VERIFIED |
| Wall clock | 4 min 49 s | 1 min 37 s |
| Model calls / model time | 7 / 232 s | 6 / 49 s |
| Tokens in / out | 117,407 / 6,251 | 58,187 / 9,029 |
| Cost | ChatGPT allowance | $0.0429 computed |
| Sealed methods (red on base) | 24 (24) | 16 (16) |
| Held-out upstream | 325/328 | 325/328 |
| Mutation score | 1.00 (12/12) | 1.00 (12/12) |

## 9. Evaluation sizing from measured costs

Two Nemotron data points: $0.025 for the unittest sample and $0.043 for the 30-file pytest repository, both with a
mutation breaker pass of 12 mutants (sandbox operations are free during the beta). Using $0.10 per task as a planning
figure that leaves room for retries, arbitration and best-of-2 candidates:

| Budget line | Tasks × conditions | Planning cost |
| --- | --- | --- |
| Formal comparison: baseline (plain agent loop) versus Attest-full | 30 tasks × 2 | $6.00 |
| Mined tasks from two real repositories, Attest-full | 20 × 1 | $2.00 |
| Six "we also try to break it" scenarios, with reruns | 12 runs | $1.20 |
| Judge demo reserve, Dec 1 to 15 (pre-funded, rate-limited sample runs) | about 50 runs | $5.00 |
| Development and compatibility retries on Nemotron | | $3.00 |
| **Total against the $25.00 balance** | | **$17.20**, leaving about $7.80 |

Freeze the task list only after the Tavily grounding and drift-audit stages exist, since both add Ultra calls; re-measure
one task after each stage lands and refresh the console reading before the formal batch.

## 10. Phase 1 closure: complete verification (15 Oct 2026, evening, second round)

Everything in this section was produced after the gates were made strict. **Verdicts from earlier sections were produced
under weaker gates (no held-out gate, no adversarial tests, no drift audit, in-process sealed runner) and are superseded as
evidence of the current pipeline; their artifacts are preserved unchanged.**

### Trust boundary and real-sandbox adversarial evidence

- Sealed and adversarial suites run under a **supervisor** that never imports candidate code: static test discovery from the
  sealed file's AST, **one child process per test**, the per-run nonce delivered on stdin only after the child imported the
  module, outcomes derived from exit code, signal, timeout and the presence and integrity of each child's result file, trusted
  JSON written only after the whole suite ran. Host binding rejects any nonzero exit, signal, timeout, missing, forged or
  inconsistent result, digest change, missing or extra test ID, or a static-ID set that differs from the red check.
- **Real Sandboxes scenarios** (`reports/attest-verification-2026-10-15/sandbox-adversarial.json`, eight disposable branches
  from one checkpoint): honest accepted; wrong, sealed-file tampering, premature `os._exit(0)`, forged result files written at
  import, forged console text, a 20-second hang (per-test timeout 5 s) and a SIGSEGV crash all rejected, each with the specific
  failed checks. All eight decided correctly.
- Gates that block VERIFIED: existing suite, sealed binding, held-out suite when configured, mutation score below 0.5 on at
  least four mutants, model-written adversarial tests (unusable module after a feedback retry also fails the gate), drift
  audit score at or above 0.6, unfinished implementer, scope violations, verification runner errors.
- Robustness added from observed failures: repair of double-escaped module sources; a transport-uncertain seal attempt counts
  as a rejected attempt (three allowed); one repair retry for a malformed structured answer (never for transport-uncertain
  failures); implementer output bound raised to 16 K tokens after a Nemotron answer was truncated at 8 K; uncertain sandbox
  spawns inside the breaker mark the mutant unknown instead of aborting the run.
- Tavily: `GET /usage` and one search verified with the saved key (Researcher plan, 1,000 credits, 1 used); grounding runs only
  when the specification names external references (none in these tasks).

### Re-runs under the strict gates (`reports/attest-verification-2026-10-15/evidence-runs/`)

| Run | Verdict | Why | Mutation | Adversarial | Drift | Cost / calls | Wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| durationkit, Codex (`p2-durationkit-codex`) | NEEDS HUMAN | adversarial test `test_very_long_zero_component_is_valid` errors: a 5,000-digit component hits CPython's 4,300-digit int-conversion limit (`ValueError`); the contract never bounded digit count, so a human decides | 11/12 (0.92) | 1 of 10 failed | 0.0 | allowance, 9 calls | 6 min 12 s |
| durationkit, Nemotron (`p2-durationkit-nebius`) | **VERIFIED** | all gates pass: sealed 29/29, mutation 9/12, adversarial 12/12, drift 0.0 | 9/12 (0.75) | 12/12 pass | 0.0 | $0.0753, 15 calls | 4 min 59 s |
| semver, Codex (`p2-semver-codex`) | ERROR | after verification (sealed 27/27, existing 312/312, held-out 325/328) one mutant spawn hit a TLS `UNEXPECTED_EOF` and, by the no-replay rule, the run stopped; the breaker now records such a mutant as unknown instead; re-run in progress | n/a | n/a | n/a | allowance, 7 calls | 5 min 29 s |
| semver, Nemotron (`p2-semver-nebius`) | NEEDS HUMAN | held-out gate (3 of 328, the known message-format divergence) and adversarial `test_docstring_doctests` errors on a `DocTest.obj` attribute that does not exist, a defect in the model-written test | 12/12 (1.0) | 1 of 12 failed | 0.0 | $0.0922, 14 calls (1 malformed answer repaired) | 5 min 29 s |
| semver v2, Nemotron (`p2-semver-v2-nebius`) | NEEDS HUMAN | the **held-out upstream suite passes 328/328** (the contract resolution worked), but three sealed tests error on `cm.exception.message`, a Python 2 idiom in the model-written sealed tests; a contract dispute for a human, flagged precisely | not run | not run | 0.0 | $0.0582, 11 calls | 1 min 40 s |

| semver, Codex, re-run after prompt hardening (`p3-semver-codex`) | NEEDS HUMAN | held-out gate (3 of 328) and one sealed test `test_method_docstring_describes_rules_and_contains_two_examples` fails: the sealed author tested docstring wording, a brittle test that the contract did not require; verification otherwise clean (sealed 17 of 18, existing 312/312) | not run | not run | 0.0 | allowance, 9 calls | 5 min 36 s |
| semver v2, Nemotron, re-run (`p3-semver-v2-nebius`) | NEEDS HUMAN | a genuinely bad patch, caught by every gate: the implementer corrupted `isvalid` and placed the method in the wrong scope, pytest exited 4 (collection error), all 16 sealed tests errored, the drift audit scored 0.85 "off_target" with the corruption named; the implementer also exhausted its 14 turns | not run | not run | 0.85 | $0.0919, 17 calls | 4 min 4 s |
| durationkit, public judge-style run on the deployed console (`reports/attest-deployment-2026-10-15/`) | NEEDS HUMAN | implementer did not finish within 14 turns and one sealed test (`test_number_without_unit_in_multi_component_raises`) failed; 27 progress events streamed to the console; downloadable Proof Bundle fetched from the public API | not run | not run | ok | $0.0596, 17 calls | 2 min 56 s |

Reading of these results: the gates do what they must. A verdict is only VERIFIED when every piece of evidence agrees, and the
three NEEDS HUMAN outcomes each name the exact failing test and why. Of the eight strict-gate runs, one is VERIFIED on every gate (durationkit on Nemotron),
one errored on a transient TLS failure that the breaker now isolates, and six are NEEDS HUMAN for named reasons: three defects
in model-written tests (a Python 2 idiom, a doctest API misuse, a brittle docstring test), one real edge case the contract
never settled (a 5,000-digit component), one genuinely broken patch that every gate and the drift audit caught, and the known
upstream message-format divergence. The implementer's turn efficiency on Nemotron (two runs exhausted 14 turns) and the quality
of model-written tests are the two next engineering targets, with arbitration of sealed-test disputes as the design answer
to the former class.

### Console (Phase 2) evidence

See `attest-console.md`: API and UI verified locally, including an API-started Nemotron run (VERIFIED, $0.0723, 29 progress
events) with its screenshot, rate limiting (429) and admin gating (403).

## 11. Continued (16 Oct 2026): hardening, arbitration, evaluation, hardened redeploy

A later round hardened the verifier (privilege separation — the sealed tests now run as an unprivileged uid against a
root-owned read-only sealed directory, so tampering is prevented, not just detected), made the mutation gate fail on
all-unknown mutants, added atomic budget reservation, a disk guard with bounded retention, restart reconciliation,
advisory arbitration of generated-test failures, and implementer efficiency (syntax-check/undo/test-before-finish). A
controlled evaluation then compared a plain agent against Attest on five frozen tasks with independent held-out suites.
Full write-ups: `reports/attest-hardening-2026-10-16/README.md`, `reports/attest-evaluation-2026-10-16/README.md` (and
`METHOD.md`), `reports/attest-deployment-2026-10-16/README.md`. The hardened build is live at https://attest.axiqo.xyz.
