# Milestone M4 (17 Oct 2026): bounded external repositories and the pilot kit

Scope: items 4.1 to 4.3 of the plan (`reports/attest-competitive-review-2026-10-16/README.md`, section 5). Development on the
Codex gateway and Nebius Sandboxes only; **no Nebius inference was spent**. Files in this folder: `runs/` (every attempt of
the external task, including the two failed ones), `external-run-codex*.log` (one log per attempt),
`sandbox-payload-probe.json` (the request-size measurement), and the pilot dry-run findings below.

## 4.1 Import with enforced limits (`attest/core/external.py`, `python -m attest import`)

| Bound | Enforced where | Refusal text names |
| --- | --- | --- |
| Source: public GitHub repository at a **full 40-character commit sha**, or a local directory | `parse_github`, `require_commit` | the URL form; "pinned as a full 40-character hexadecimal sha (branches and tags are not accepted)" |
| At most 2,000 files and 25 MB; 200 KB per file by default (`--max-file-bytes`, hard cap 1 MB) | before any file is written (`extract_tarball`, `import_local`); again by the pipeline before the checkpoint | the count, the byte total or the first oversized file |
| Regular files only; links inside the repository become copies, other links and caches are listed and dropped; unsafe member names refuse the whole import | `extract_tarball` | "unsafe path" |
| Python; `unittest` or `pytest` | `external_policy_problems` | the runner |
| Named write scope (`**` refused); `tests/**` protected; every packaging file present must be protected | `external_policy_problems` | the glob or the packaging file |
| Pinned install (`name==version`) with `requirements_lock` recorded; test timeout at most 300 s; checkpoint at most 600 s | `external_policy_problems` | the unpinned requirement, the timeout |
| At most 12 implementer turns | `Pipeline.__init__` caps `max_turns` for any task with `upstream` | recorded in `provenance.limits` |

The pipeline calls the same checks before creating the checkpoint and aborts with `ERROR: refused before any sandbox
operation: ...` (offline test `tests/test_external.py::PipelineRefusesOutOfBoundsBeforeSandbox`, which also asserts that
no executor operation was issued). `SOURCE.json` records the URL, commit, tarball sha256, tree sha256, counts and the
skipped or materialised entries; `task.json` carries `upstream` into the frozen task and the Proof Bundle.

Transport finding during 4.2: the sandbox job travelled as base64 JSON on stdin, and the API answered `HTTP 413 Content Too
Large` for the 645 KB python-semver tree. A probe (`sandbox-payload-probe.json`) accepted a 534 KB body and stalled the write
at about 1 MB. The job is now gzip-compressed (the guest runner detects the gzip stream the API hands it after base64
decoding), each request is capped at 400 KB after compression, and a checkpoint that still does not fit is built as a chain
of retained images (files first, install and baseline in the last operation; `execution.checkpoint_chain` records the earlier
operation ids). The guest runner is `attest-guest/2`; its digest is in every bundle's provenance. Tests:
`tests/test_external.py::SandboxTransport`.

## 4.2 A real external task end to end

`examples/semver-long-prerelease-pr488/`: python-semver at `887d057e66b7fdfe0adf5a206ac810766b5af938` (the parent of
upstream pull request #488, which fixed issue #487: comparing a version whose numeric prerelease identifier has more than
4,300 digits raised `ValueError` because `_nat_cmp` used `int()`). Imported with
`python -m attest import --github https://github.com/python-semver/python-semver --commit 887d057e… --runner pytest
--write-glob 'src/semver/**' --python-path src --python-path tests --pin … --max-file-bytes 300000 --heldout
tests/test_heldout_pr488.py=…` (119 files, 645,175 bytes, two docs symlinks materialised, zero policy problems; the first
attempt was refused because `uv.lock` is 238 KB, which is what `--max-file-bytes 300000` is for). The statement and criteria
restate the pull request's semantics (ASCII numeric identifiers compared without `int()`, legacy behaviour for constructor
prereleases, eager `ValueError` for digit-like non-decimal identifiers); the held-out suite is the pull request's own seven
test functions, extracted verbatim and never shown to the implementer.

Attempts on the Codex development profile (all kept under `runs/`):

| Attempt | Outcome | Cause |
| --- | --- | --- |
| 1 (`…T122152Z`) | ERROR at checkpoint | `HTTP 413 Content Too Large`: the uncompressed job exceeded the API's request size (fixed as above) |
| 2 (`…T122652Z`) | ERROR at checkpoint | the first gzip version expected base64 text on stdin, but the API delivers the decoded bytes (`UnicodeDecodeError` in the guest); fixed, with a test that feeds the runner exactly what the API feeds it |
| 3 (`…T122907Z`) | see below | checkpoint built from the compressed job: 424 tests passed and 1 skipped on the base; specification 12 criteria, 7 contract entries |

Attempt 3 (`runs/semver-long-prerelease-pr488-20261017T122906Z`, 12:29 to 13:25 UTC, 18 model calls of which 4 failed, 20
sandbox operations, 309,778 input and 12,950 output tokens, no USD) ended **NEEDS HUMAN** with a candidate that every
independent measure accepts:

| Gate or check | Result |
| --- | --- |
| Held-out suite (the upstream pull request's 7 tests plus the repository suite, run by the task's held-out gate) | 450 passed, 1 skipped (`evidence_class: stdout`, pytest) |
| Sealed tests (20 methods, 6 red on the base) | 20 of 20 pass on the candidate, binding ok |
| Existing suite | 424 passed, 1 skipped |
| Mutation check | 11 of 11 mutants killed, score 1.0 |
| Drift audit | 0.0, aligned |
| Adversarial tests | 9 of 10 pass; `test_empty_components_and_length_after_equal_prefix` fails |
| Arbitration | call failed: HTTP 502 from the gateway, invalid schema |
| Provenance | `upstream.url` and `upstream.commit` recorded; `attest check`: OK, 0 errors, 0 warnings |

The failing adversarial test calls the private `Version._nat_cmp` directly (the breaker rules require the public API) and
asserts `_nat_cmp('a..0', 'a..') == 1`; under the stated contract an empty identifier is non-numeric and a numeric
identifier is lower than any non-numeric one, so `-1` is the contract-conforming answer, which is also what the upstream fix
returns. The test is defective. The arbiter never got to say so because the arbitration schema I had changed in the morning
declared `defect_kind` optional, and the gateway's strict structured-output mode rejects any schema whose `required` list
omits a property (`'schema.properties.classifications.items.required' is required to include every key in properties`).
Fixed the same hour: the field is required and nullable, and `tests/test_reliability.py::StrictSchemas` now checks every
schema for strict-mode compatibility (required lists complete, additional properties forbidden). The two "uncertain" seal
attempts were gateway transport failures (a response body cut at 16 KB after HTTP 200; a TLS EOF), never retried; the
process also waited 33 minutes in total on the pre-change pacing model (60 per hour) that the gateway no longer enforces.
Attempt 4, started 13:27 UTC with the fixed schema and the policy-adopting governor, is recorded below.

Attempt 4 (`runs/semver-long-prerelease-pr488-20261017T132707Z`, 13:27 to 13:37 UTC, 16 model calls, none failed, no
pacing wait, 20 sandbox operations, 389,270 input and 12,383 output tokens, no USD) ended **VERIFIED**:

| Gate or check | Result |
| --- | --- |
| Sealed tests (21 methods, 7 red on the base) | 21 of 21 pass on the candidate, binding ok |
| Existing suite | 424 passed, 1 skipped (`stdout`) |
| Held-out suite (upstream pull request #488's tests plus the repository suite) | 450 passed, 1 skipped (`stdout`) |
| Mutation check | 11 of 12 mutants killed, score 0.917 (one survivor listed in E2) |
| Adversarial tests | 10 of 10 pass, binding ok |
| Drift audit | 0.08, "narrowed" (below the 0.6 threshold; a warning, not a hold) |
| Verdict rule, manifest, PROOF.md | `attest check`: OK, 0 errors, 0 warnings; `upstream` recorded |

Both attempts are kept. The verdict difference between attempts 3 and 4 is the breaker's output, not the candidate: attempt
3's breaker wrote one defective test, attempt 4's did not. Each attempt is one sample of the development profile; neither
is an evaluation result (the M5 comparison runs on Nemotron).

## 4.3 Pilot kit and the dry run by someone who did not write it

`PILOT.md` (prerequisites, credentials, preflight, import, run, check, limits, feedback), `PILOT_FEEDBACK.md` and
`.github/ISSUE_TEMPLATE/pilot-feedback.md`. The public console is unchanged for pilots: external repositories run on the CLI
with the pilot's own `NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID`.

**Dry run 1** (a fresh agent with no project context, on the first public export, following `PILOT.md` literally; the
development profile substituted for Nemotron so no USD was spent). Install (37 s) and import (3 s; `tkem/cachetools` at
`eba200635273fe45b67e669b84cb45f995b27c24`, 44 files, zero policy problems) worked as documented. Preflight failed before any
sandbox or model call: the copy still carried the credential loader's hard-coded vault paths (redacted in the export), so
the missing environment variable surfaced as a ten-frame traceback naming a private note. The agent stopped there, as the
brief required, and reported 14 friction points. Fixed the same day: credential failures are one-line messages with exit
code 2; `NEBIUS_PROJECT_ID` is required unless the team's note config exists (nobody runs against the team's project by
accident); credential-note paths live in `~/.config/attest/notes.json` outside the repository; `--import-hint` flag; the
import's `next` line names only the fields still empty and the output echoes the write scope, protected files, test command,
install and held-out files; `PILOT.md` now states that both variables and `--provider nebius` are mandatory, shows the
preflight output, lists the default protected globs, explains the pins, marks placeholders, documents exit codes, points to
the python-semver task as a complete worked example and budgets the statement-writing time.

**Dry run 2** (a fresh agent on the revised export, same substitution of the development profile). Install, preflight,
import and run all completed as documented: repository `tkem/cachetools` at `eba200635273fe45b67e669b84cb45f995b27c24`
(44 files), task "`TTLCache` must reject a negative `ttl` with `ValueError`", import hint supplied with the new flag, run
`cachetools-ttl-negative-20261017T125812Z` from 12:58 to 13:04 UTC (9 model calls, none failed, 11 sandbox operations).
Verdict **NEEDS HUMAN**, correctly fail-closed and for an infrastructure reason: the sealed suite (15 methods) passed on the
candidate, the existing suite (360 tests) and the adversarial suite passed, drift was aligned, but one of the four mutant
branches ended in a transport-uncertain spawn (`POST /instances` read timeout; recorded as `UNCERTAIN`, never replayed),
so only 3 of 4 mutants could be scored, below the minimum of 4, and the mutation gate held the verdict with the reason
"mutation gate incomplete: only 3 of 4 mutants could be evaluated (1 unknown)". `attest check` on the bundle: OK, 0 errors,
0 warnings; `upstream` records the cachetools URL and commit. The agent's friction list for this round is appended below
when it arrives; the interim notes already led to one more `PILOT.md` paragraph (pytest suites are judged from console
output, unittest suites are supervisor-bound).

The agent's report (its own words, condensed; 11 friction points, no CLI command failed): install 16 s, preflight 10 s,
import 2 s, run 6 min 24 s, writing the statement from the repository's code was the longest step, as the doc warns. Fixed
after the report: (1) the decision copy for a mutation gate held by unknown mutants no longer says "look at the surviving
mutants" when none survived; it names the infrastructure cause and says to run again (new reason class
`mutation_incomplete`), and `PILOT.md` documents the minimum of 4 evaluable mutants and this failure mode; (2) `PILOT.md`
now says to choose `unittest` whenever the tests are `unittest.TestCase` classes, even when the project runs them through
pytest, because that gives supervisor-bound evidence and needs no pins; (3) consistency: the python-semver example's
`import_hint` was empty although the doc quoted it (set); `pyproject.toml` said version 0.1.0 while the package says
0.3.0 (synced, and `attest.app` added to the package list); the import's next-step hint now matches the documented run
command and notes that log timestamps are UTC; the doc says where `statement.txt` and `criteria.txt` are read from and
that the sealed-test "shown failing" is a count with the tests in `sealed/test_sealed.py`. Not changed: the fail-closed
rule itself (one unknown mutant below the minimum still holds the verdict), which is the behaviour the pilot should see.

## Limitations

- Repositories larger than one compressed request take several retained operations to checkpoint (about 400 KB of
  compressed files per request); each leaves an image on the service, which cannot be deleted through the current public
  REST API.
- pytest repositories are judged from parsed console output (`evidence_class: stdout`); only unittest repositories are
  bound through the supervisor.
- The pilot dry runs were performed by fresh agents, not by outside developers; the kit is ready for the owner to hand to
  pilots, and nothing here claims adoption or feedback that did not happen.
