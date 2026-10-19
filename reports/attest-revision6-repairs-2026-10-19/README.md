# Repairs of the revision-6 review (revision 7, version 0.7.0, 19 October 2026)

The independent review of revision 6 (`reports/attest-revision6-review-2026-10-19/README.md`) left three items open: R5-03 was
partial because the witness constraint could be bypassed by an import alias; malformed admission requests could still start paid
runs (the cause of the 19 Oct verification incident); and the final-tree suite had one failing test. This folder records the
repairs, their acceptance evidence (every negative case next to a positive control), the review's own reproduction re-run from a
documented copy, a small development-gateway batch, the final-tree suite and the deployment. The review folder, the earlier
repair reports and every recorded run are unchanged; the two accounting clarifications of the incident are appended and dated
(`reports/attest-deployment-2026-10-19c/README.md`, `reports/attest-revision5-repairs-2026-10-19/README.md`).

No paid Nebius inference call was made in this pass, and no production POST was sent. The development-gateway batch ran on the
team's gateway for inference and on Token Factory Sandboxes for execution, as every earlier development batch did.

## Item by item

| Item | Fixing commit | Repair | Acceptance | Remaining limitation |
| --- | --- | --- | --- | --- |
| 1. R5-03: enforce witness constraints | `1ddc44f` (`1ddc44fb49fcceb81e45fbc85d3aa8349060ac94`) | the constrained witness language `attest-witness/1` (`attest/core/witness.py`): a positive grammar, imports limited to five standard-library modules and the repository's own modules, every repository name resolved statically to a function or class the repository defines, calls only through resolved origins (including callables passed to built-ins that call them back), no underscore attributes, no definitions; the pipeline records the analysis and copies the repository files it read; `attest check` repeats it and never trusts a recorded flag; evidence protocol 4 | `core/README.md`, `core/unittest-witness-language.txt` (13 tests): 27 bypass programs (imported aliases, assigned aliases, indirect factories and calls) and 6 repository-origin cases are outside the language, held by the real `contract_audit`, and refused by the checker in five forged-bundle variants; positive controls: two literal-input witnesses conform, the recorded revision-6 rle witness conforms against the frozen repository, a genuine grounded bundle is INFEASIBLE and fully verified; the review's reproduction now records `grounded: false` (`core/review-repro/`) | static analysis of the repository's own source; attribute access on repository objects is outside the language (conservative holds); whether a witness's demonstration is sound remains the auditor model's reasoning, not something the language establishes |
| 2. Malformed requests start paid runs | `616a7a5` (`616a7a5f789c6ec4873ad23d7f2741e6d2dc95e1`) | `RunRequest` forbids unknown fields, requires `provider` with no default and validates it in code; a validation handler answers 422 without echoing values, before the handler, so a refused request creates no row, queue entry, reservation or provider | `console/README.md`, `console/unittest-strict-requests.txt` (32 tests): the incident's exact body, missing, empty, unknown, wrongly cased, null, numeric and list providers, extra fields, missing task and non-object bodies all return 422 with no row, queue entry, reservation, enqueue or runtime build; positive controls: public and team requests keep their 200/403/404/429 rules; tickets never authorize admission; the public OpenAPI schema shows the strict body without naming the gateway | a valid public request is still a paid run by design; production admission is verified with GET requests only |
| 3. Final-tree regression failure | `dd361b5` (explicit corpora, on top of the records commit `acd17fc` that adds the evidence they classify); `969f721` (the export publishes executables as executable); `b21782d` (anchored `.gitignore`, fail-closed git-ignore check in the export); `1a6a523` (the 150 previously ignored bundles committed); `a95e261` (`a95e2614d643bc057a1877f81b5ebe774fabaf7e`, deterministic derived manifests, so a repeated export changes nothing; the pinned commit) | the recorded-evidence tests classify their fixtures explicitly: a frozen historical corpus, a modern corpus by declared protocol, and an inventory that fails on any unclassified run directory; the product checker is unchanged. Running the suite on a clean checkout of the first pinned commit then exposed two export defects (non-executable scripts, an unanchored `.gitignore` that kept 150 bundles out of the review repository), both fixed | `corpus/README.md`: six final-tree runs, the last two 367 tests with no failure, error or skip | a new evidence folder must be classified by hand before the suite passes (intended); the export now refuses to publish a file git would ignore |

## Development-gateway batch (semantic outcomes, reported apart from bundle integrity)

Four batches, Attest only, one attempt per cell, all on package `f836cfd0154f…` (37 sources), harness `5af2b4989b2b…`,
examples `6db7a2e937d6…`, the development gateway for inference (profile registered in each `schedule.json`: spec and audit
`gpt-6-astra:low`, arbitrate `gpt-6-astra:medium`, seal, implement and break `gpt-6-sol:medium`, summary `gpt-6-luna:low`) and
Token Factory Sandboxes for execution; $0 committed in every batch (no paid inference). Logs `evaluation-codex*.log`; cells and
labels in each folder's `evaluation.json` and `RESULTS.md`. Every scheduled cell is reported; nothing was merged or selected, and
no uncertain operation was replayed.

**Semantic outcomes** (judged by each task's independent held-out suite):

| Batch | Task | Verdict | Label | What happened |
| --- | --- | --- | --- | --- |
| 1 (`evaluation-codex/`, 2 workers) | `rle-encode` (unsatisfiable) | INFEASIBLE | `true_reject` | the auditor named TC5 only and wrote a literal-input witness in `attest-witness/1` (`decode('a1' + '11')` returns 111 copies of `a`, so the format the task fixes cannot round-trip `'a1'`); origins resolved through `rle/__init__.py` to `rle/core.py`; demonstrated, grounded, INFEASIBLE in 177 s, 2 model calls |
| 1 | `balanced-brackets` | VERIFIED | `true_accept` | held-out 8 of 8; audit consistent |
| 1 | `durationkit-units-001` | ERROR | `infra_error` | audit consistent; during implementation a Sandboxes spawn failed with a TLS end-of-file, outcome uncertain, not replayed |
| 1 | `kvparse-refactor-001` | not run | `not_run` | the batch's stop rule (any transport-uncertain operation) started no further cell |
| 2 (`evaluation-codex-2/`) | `durationkit-units-001` | ERROR | `infra_error` | audit consistent; a sealing call failed with a TLS end-of-file (uncertain, not retried), the next attempt got HTTP 502 "model at capacity" |
| 2 | `kvparse-refactor-001` | ERROR | `infra_error` | audit consistent; an implementer call failed with a TLS end-of-file (uncertain, not retried) |
| 3 (`evaluation-codex-3/`) | `durationkit-units-001` | ERROR | `infra_error` | audit consistent; an implementer call failed with a remote disconnect (uncertain, not retried) |
| 3 | `kvparse-refactor-001` | ERROR | `infra_error` | audit consistent; a Sandboxes spawn failed with a TLS handshake timeout (uncertain, not replayed) |
| 4 (`evaluation-codex-4/`, 1 worker) | `durationkit-units-001` | ERROR | `infra_error` | the contract-audit call itself failed with a remote disconnect (uncertain, not retried) |
| 4 | `kvparse-refactor-001` | not run | `not_run` | stop rule |

Reading: 10 cells scheduled, 2 judged, both correct; 6 infrastructure errors and 2 cells not run. The unsatisfiable task was
refused on a witness that the language accepted and the checker re-derives, which is the end-to-end positive control of item 1 on
real model output. The task revision 5 refused wrongly (`kvparse-refactor-001`) was audited consistent in both batches that
reached its audit, so it was not refused again, but it reached no verdict in this pass; its last recorded verdict is VERIFIED
(revision 6, `reports/attest-revision5-repairs-2026-10-19/evaluation-codex/`). The positive control `durationkit-units-001` was
audited consistent three times and reached no verdict. The failures were transport failures on the path from this machine to the
gateway and to the Sandboxes API (TLS end-of-file, handshake timeout, remote disconnect; one capacity 502); that path runs through
the machine's system HTTPS proxy on 127.0.0.1, which was not changed. Between batches 1 and 2 the gateway's status endpoint failed
once in three probes and then answered five of five; batch 4 ran its cells one at a time and failed in the same way. The attempts
stopped after batch 4. An uncertain Sandboxes spawn may have created an operation the ledger could not record. These batches are a
reliability check of the repaired mechanics, not an evaluation; the M5 results stand.

**Bundle integrity** (`bundle-checks.txt`, `bundle-checks-2.txt`, `bundle-checks-3.txt`, `bundle-checks-4.txt`, reported apart
from the outcomes above): all eight bundles read `OK, EVIDENCE COMPLETE` for their verdict under protocol 4 with the manifest
verified, 0 errors and 0 warnings; the INFEASIBLE bundle's `witness_language_rederived` check repeats the language analysis from its
two repository copies. Complete evidence establishes that each recorded verdict follows from its recorded evidence (for the six
ERROR bundles: that the run stopped where it says, with a public reason from the fixed vocabulary); it does not establish that a
verdict is correct. The held-out judge establishes the two judged outcomes.

## Final-tree offline suite

The complete offline suite, run after the final batch, the reports and the export (`corpus/final-tree-suite-*.log`, local paths
masked):

| Run | Tree | Tests | Failures | Errors | Skips |
| --- | --- | --- | --- | --- | --- |
| 1 | clean checkout (`git worktree`) of the first pinned commit `dd361b5` | 365 | 18 | 20 | 4 |
| 2 | the review repository's directory at the first pin record `6f6bf76` (clean git status, but holding the git-ignored run directories) | 365 | 15 | 19 | 0 |
| 3 | private working tree, same code | 365 | 0 | 0 | 0 |
| 4 | clean checkout of `969f721` (scripts executable again) | 366 | 4 | 1 | 4 |
| 5 | clean checkout of `1a6a523` (anchored `.gitignore`, run evidence committed) | 367 | 0 | 0 | 0 |
| 6 | private working tree after the fixes | 367 | 0 | 0 | 0 |
| 7 | clean checkout of `a95e261` (deterministic export; the pinned commit) | 367 | 0 | 0 | 0 |

Runs 1 and 2 failed in `tests/test_audit_ops.py` (the rehearsal shims were not executable) and in every test that reads run evidence
under `reports/**/runs/` (git ignored it); run 4 still lacked that evidence. A full run after the deployment record is reported in the
closure summary rather than in this file, so that the record does not change the tree it describes.

## Frozen and deployed

REV7-DEPLOY-SECTION

## Paid calls in this pass

REV7-PAID-SECTION
