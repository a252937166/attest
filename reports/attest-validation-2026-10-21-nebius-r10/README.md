# Paid validation of revision 10 on Nemotron (20-21 Oct 2026)

The owner approved the paid work proposed in `FREEZE.md` (revision 10, "Proposed paid work": a two-run Nemotron smoke test through
the CLI, about $0.15 and at most $1.00, then the revised 32-cell evaluation, about $3 to $4 and at most $9.00 through
`--approve-usd`; total at most $10.00) on 21 Oct 2026 ("Follow the process you established above, including all payment-related
actions"). This folder records the smoke test, how every stop of the evaluation was reconciled, and the host work done alongside it.
The evaluation itself is `reports/attest-evaluation-2026-10-21-nebius-r10/`.

## The checkout

A fresh clone of the local publication repository at `953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a`, the commit FREEZE.md names for
revision 10 (the same tree as review commit `c0ddb486f8c91f061678a2b6239cbbdbddd21f87`), under the project folder
(`scratchpad/r11-eval/attest-eval`). Before any paid call its digests were checked against the pin: `attest/` package
`7e72364f135c45c8a69a3a59c9cba5c954ebbb843cc7752b76c8303550548cb6` (37 sources, version 0.10.0), harness
`243ab12f3879ffc6d7a0eef5c08c147141a13915457fb7ff1b8e02aa7e0e4ac7`, `examples/` tree `e95a28aa363366160062107128950e9ff4c1888d52dccfdf578299e14e341b78`,
`SUITE-M5.json` `a43da6c3…`, `METHOD.md` `ec415afc…`: all equal. Interpreter: Python 3.12.0 on macOS (arm64). Credentials came from the
operator's private notes through `attest.secrets` (never on a command line, never in a file of this repository).

## Smoke test (`smoke/`)

The two runs the proposal names, with the exact commands
`python3 -m attest run --provider nebius --task examples/durationkit-task/task.json --out runs --usd-cap 0.5 --max-calls 22` and the same with
`--task examples/eval/rle-encode/task.json`:

| Run | Verdict | Model calls | Inference committed | Sandboxes operations | Notes |
| --- | --- | --- | --- | --- | --- |
| `durationkit-units-001-20261020T180815Z` (20 Oct 18:08 UTC) | NEEDS HUMAN | 17 (Ultra 3, Super 14) | $0.071382 | 7 (13.1 s) | the implementer did not finish within its 12 turns and 2 of 17 sealed tests failed (errors); one call failed while its connection was being set up (never sent) and was retried; no uncertain, malformed or halted call |
| `rle-encode-20261021T015058Z` (21 Oct 01:50 UTC) | NEEDS HUMAN | 13 (Ultra 4, Super 9) | $0.044771 | 9 (14.3 s) | the implementer reported "Encode function implemented correctly, passes all tests and acceptance criteria"; two sealed round-trip tests failed and the arbiter classified both as implementation bugs (a string with digits cannot round-trip: `encode("a1")` is `"a111"`, which decodes to 111 a's) |

Both bundles pass `attest check` with complete evidence under protocol 5 (0 errors, 0 warnings), from their original directory and from
this copy. Every real Token Factory answer was read through revision 10's strict decoding and adapter checks without a single malformed
stop. Smoke total: $0.116153 of inference (estimate $0.15, cap $1.00). Neither specification named an external reference, so neither run
called Tavily.

## Stops and reconciliation (`reconciliation/`)

The frozen method stops the batch at the first operation of uncertain outcome and never replays it; a resumed batch starts nothing
until every unresolved item is acknowledged by id with a note saying what read-only checks found (revision 10). During the evaluation
the Nebius Sandboxes API answered `POST /sandboxes/v1/instances` with `500 Internal Server Error` after the request had
been sent: six times in all, 6 of the 141 operations in the batch's run ledgers (4.3%); the public status page (status.nebius.com) reported
every service operational and no incident on 20 or 21 Oct. Each 500 stopped the batch; the other cell in flight stopped with it
(`batch_stop`), so each stop cost two cells as infrastructure errors.

`reconcile_uncertain.py` is the read-only check: for a spawn of uncertain outcome it lists the account's instance operations from two
minutes before the run started to the time of the check (`GET /operations?kind=instance&since=&until=`, paged), requires that every
operation the run itself recorded appears in the listing (positive control), and looks for an operation on the spawn's source image
(the run's own checkpoint image) that no record of the batch names, created after the spawn was sent; for an operation the service had
accepted but the halted run never read, it reads the record (`GET /operations/{id}`). Every request it makes is a GET, asserted.
A spawn is acknowledged only after a check made at least ten minutes after it was sent (on 17 Oct an operation appeared 4 min 22 s after
its spawn). The first stops were handled by hand (`item-u-3fe0bf36cb94/`, `segment2/`, `segment3/`, `segment4/`); from 02:52 UTC
`operator_loop.py` repeated exactly those steps (`loop/`): resume, list, check, wait, check again, acknowledge by id, resume, stopping for a
person on any inconclusive finding, at most 15 resumptions.

| Item | Run | Operation | Sent (UTC) | Finding (read-only) |
| --- | --- | --- | --- | --- |
| `u-3fe0bf36cb94` | roman-to-numeral baseline a2 | spawn `impl-python-6`, HTTP 500 | 01:55:19 | no operation found up to 02:05:20 (positive control 3 of 3) |
| `u-08be0f038547`, `u-f630a0043968` | roman-to-numeral attest a1 | spawns `mutant-m02`, `mutant-m07`, HTTP 500 | 02:07:32 | no operation found up to 02:17:51 |
| six items | roman-to-numeral attest a1 | accepted mutants m01, m03-m06, m08 (in flight at the stop) | 02:07:32 | the service reports SUCCESS for all six |
| `u-b579f63fe452` | durationkit baseline a1 | spawn `impl-tests-6`, HTTP 500 | 02:30:46 | no operation found up to 02:40:53 |
| `u-bfaa6f65e2b9` | durationkit attest a2 | spawn `red-1`, HTTP 500 | 02:42:17 | no operation found up to 02:52:28 |
| `u-11905c7a7e76` | semver-long-prerelease attest a1 | spawn `impl-tests-11`, HTTP 500 | 03:18:26 | no operation found up to 03:28:40 (`final-item/`); the batch had no cell left, so the acknowledgement was recorded by a resume that ran nothing |

No uncertain spawn turned out to have executed. One lapse is recorded: the first check of `u-3fe0bf36cb94` (01:57:14) overwrote its raw
listing file with the second one; its summary (`reconciliation-20261021T015714Z.json`) is kept, and the script names every later listing by
the time of its check. The acknowledgements, as the harness stored them, are in `reports/attest-evaluation-2026-10-21-nebius-r10/batch/reconciliations.jsonl`.

## yungou (`disk/`, kept out of the public export)

The owner allowed removing Docker images that no running container uses. Before the change free space on `/` had already risen from
1.33 GB (9.17%, 20 Oct 16:10 UTC) to 3.09 GB (21.3%) because other projects' folders had been removed outside this work (an inventory
diff is in `disk/`); Attest's release, data, journals and backups were unchanged. The only image no container referenced,
`alphapilot-s2-financial:20260725` (355 MB), and the build cache (92.5 MB) were removed; images of stopped containers were kept, and no
container was touched. Free space afterwards: 3.50 GB (24.2%); the console's health read 3338 MB free, `accepting_runs` true, 0 holds.
The record names other projects' containers, so it stays private (`EXCLUDE_PATHS` of the export).

## The one-hour sweep (`reconciliation/final-sweep/`, 04:19:47 UTC)

The six uncertain spawns were checked once more, 61 minutes after the last of them and 2 h 24 min after the first. The check used the same
script, unchanged. All six items are acknowledged, so the batch's pending file is empty. The script therefore read the six `sandbox_spawn`
items, rebuilt from `reconciliations.jsonl` (`items-rebuilt-from-reconciliations.json`), through a scratch directory that links the
batch's `runs/` and `evaluation.json`. It made 6 requests, all GETs.

| Item | Sent (UTC) | Listed in its window | Positive control | Candidates |
| --- | --- | --- | --- | --- |
| `u-3fe0bf36cb94` | 01:55:19 | 163 | 3 of 3 | none |
| `u-08be0f038547` | 02:07:32 | 151 | 13 of 13 | none |
| `u-f630a0043968` | 02:07:32 | 151 | 13 of 13 | none |
| `u-b579f63fe452` | 02:30:46 | 103 | 1 of 1 | none |
| `u-bfaa6f65e2b9` | 02:42:17 | 71 | 1 of 1 | none |
| `u-11905c7a7e76` | 03:18:26 | 13 | 4 of 4 | none |

Every operation listed in these windows is accounted for. The only operations that no batch record names are six in the first window,
created between 01:52:13 and 01:52:48. They are the second smoke test's own operations (`impl-python-5`, `impl-python-6`,
`impl-tests-7`, `verify`, `existing`, `heldout` of `rle-encode-20261021T015058Z`), which finished before the batch started. The finding
stands: none of the six spawns answered with HTTP 500 executed.
