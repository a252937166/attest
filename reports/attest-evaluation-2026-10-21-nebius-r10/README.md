# The revision-10 evaluation on Nemotron (21 Oct 2026)

The frozen M5 suite and method (`METHOD.md`, `examples/eval/SUITE-M5.json`), re-run on version 0.10.0 with the exact command of
`FREEZE.md` (revision 10) from a clean checkout of the pin, after the owner's approval of the paid work on 21 Oct 2026:

    python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest \
        --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 22 --max-turns 14 --approve-usd 9.00 --label r10-final \
        --out reports/attest-evaluation-2026-10-21-nebius-r10

8 tasks x 2 systems x 2 attempts, 32 cells pre-registered at 01:54 UTC, all 32 run by 03:18 UTC. Provenance as the harness recorded it:
publication commit `953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a` (review commit `c0ddb486`), package `7e72364f135c…` (0.10.0), harness
`243ab12f3879…`, examples `e95a28aa3633…`, snapshot intact at the end, no invalid comparison. Every cell is in `RESULTS.md` (rendered
by `scripts/render_evaluation.py` from `batch/evaluation.json`); the batch record itself is `batch/` (runs, schedule, the
acknowledgements in `reconciliations.jsonl`); the logs of every segment are in `logs/`. How each stop was reconciled is recorded in
`reports/attest-validation-2026-10-21-nebius-r10/`.

## Results

| | Plain agent (16 cells) | Attest (16 cells) |
| --- | --- | --- |
| Correct patch accepted (true accept) | 8 | 2 |
| Broken patch shipped (false accept) | 2 | 0 |
| Correct patch held for a human (false reject) | 1 | 2 |
| Correct refusal of the task that cannot be satisfied (true reject) | 0 | 2 |
| Hold without a patch on a satisfiable task (false refusal) | 0 | 3 |
| Unfinished, no patch | 1 | 1 |
| Sandboxes error after a request was sent: stopped, reconciled, never replayed | 4 | 6 |
| Committed inference cost | $0.3448 | $1.0423 |

Total committed inference: $1.3871 of the approved $9.00 (303 model-call records, 1 never sent). Nebius Token Factory Sandboxes, kept
apart: 141 operations in the run ledgers and 22 held-out judge operations, 163 in all, 343 s. (`RESULTS.md`, rendered by the frozen harness,
prints "163 operations in the run ledgers and 22 judge operations": its per-row counter already includes each run's judge operation, so the
22 are counted in both figures; the measurement is unaffected.) Tavily: no call (no specification named an external
reference). An Attest run that was not stopped by a Sandboxes error cost 5.8 cents of inference on average (10 runs).

What this shows, and only this:

- On the task that cannot be satisfied (`rle-encode`: a string containing digits cannot round-trip through the given `decode`), the
  plain agent shipped a broken patch both times; Attest refused both times, once as INFEASIBLE with a contract contradiction demonstrated
  by an executed witness, once as NEEDS HUMAN when two sealed round-trip tests failed. In the 17 Oct evaluation of an earlier version
  (`reports/attest-evaluation-2026-10-17-nebius-m5/`) Attest had shipped both of those broken patches.
- Attest accepted far fewer correct patches: 2 (both `slugkit-regression-001` attempts, VERIFIED) against the plain agent's 8. Its other
  holds: two correct `balanced-brackets` patches (the implementer did not finish within its turns; an adversarial test the arbiter did not
  clear), three holds where the test writer could not produce a valid sealed suite (an incomplete coverage map on `semver-is-compatible`,
  a module with a syntax error twice on `kvparse-refactor-001`), and one unfinished task (NO CHANGE, turn budget). The sealing failures are
  Attest's own weak spot on this suite.
- Ten cells (4 plain, 6 Attest) are infrastructure errors: six times the Sandboxes API answered `POST /sandboxes/v1/instances` with HTTP
  500 after the request was sent, and each time the method stopped the batch with every cell in flight. Read-only checks found that none of
  the six spawns had executed; nothing was replayed. These cells are reported, not re-run.
- Attest cost three times as much inference as the plain agent, as in M5 ($0.86 against $0.23 there).

These are the numbers of one batch of 32 cells on one suite. They are not a benchmark, and the difference in shipped broken patches rests
on two cells of one task.

## Compared with the 17 Oct evaluation of an earlier version (M5)

| | M5 plain | M5 Attest | 21 Oct plain | 21 Oct Attest |
| --- | --- | --- | --- | --- |
| Correct patch accepted | 10 | 4 | 8 | 2 |
| Broken patch shipped | 2 | 2 | 2 | 0 |
| Correct patch held for a human | 0 | 5 | 1 | 2 |
| Correct refusal | 0 | 0 | 0 | 2 |
| Hold without a patch, or unfinished | 1 | 2 | 1 | 4 |
| Infrastructure error | 3 | 3 | 4 | 6 |
