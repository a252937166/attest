# Evaluation M5: Attest versus a plain agent on Nemotron (17 Oct 2026)

The frozen evaluation of milestone M5: eight tasks, two systems, two attempts per cell, every scheduled cell reported.
The method is `METHOD.md` and the pin is `FREEZE.md` (code commit `6b786a2e51bba634d63cc8b4ee75bb215c168fa7`, package
digest `166cdcbd46a74cd0…`, harness `3214d2b3a1fd1fbc…`, examples `e95a28aa36336616…`, suite `examples/eval/SUITE-M5.json`),
both written before the run. Every number below comes from `batch/evaluation.json`, rendered cell by cell in `RESULTS.md`
by `scripts/render_evaluation.py`; nothing is merged, filtered or selected. Inference: NVIDIA Nemotron 3 Ultra (spec,
audit, arbitrate), Nemotron 3 Super (seal, implement, break) and Nemotron 3.5 Lightning (summary) on Nebius Token
Factory; execution: Nebius Token Factory Sandboxes. The plain agent is the same implementer with the same model, tools
and turn budget and no sealed tests, breaker, audit or verdict; both arms are judged by the same held-out suite, which
is stripped from the system under test.

## Result

| | Plain agent (16 cells) | Attest (16 cells) |
| --- | --- | --- |
| Correct patch accepted (`true_accept`) | 10 | 4 |
| Broken patch shipped (`false_accept`) | 2 | 2 |
| Correct patch held for a human (`false_reject`) | 0 | 5 |
| Nothing shipped and nothing correct to ship (`true_reject`) | 1 | 2 |
| Infrastructure error (`infra_error`) | 3 | 3 |
| Committed cost | $0.2259 | $0.8637 |
| Mean wall time per cell | 92.9 s | 200.3 s |

Definitions (frozen in the schedule): accepted = verdict VERIFIED for Attest, implementer finished for the plain agent;
correct = the existing and the held-out suites pass on the final patch in a fresh branch, except that for the task whose
ground truth is `unsatisfiable` (rle-encode) no patch counts as correct and a hold is the right outcome.

Per task (attempt 1 / attempt 2; the judge's view in brackets):

| Task | Plain agent | Attest |
| --- | --- | --- |
| roman-to-numeral | BASELINE (correct) / BASELINE (correct) | ERROR (spawn uncertain) / VERIFIED (correct) |
| rle-encode (unsatisfiable: the held-out suite passed in all four cells, but the frozen rule counts no patch as correct) | BASELINE (not correct) / BASELINE (not correct) | VERIFIED (not correct) / VERIFIED (not correct) |
| balanced-brackets | BASELINE (correct) / BASELINE (correct) | VERIFIED (correct) / ERROR (spawn uncertain) |
| durationkit-units-001 | BASELINE (correct) / ERROR | VERIFIED (correct) / NEEDS HUMAN (correct) |
| semver-is-compatible-pr368-v2 | BASELINE (correct) / BASELINE (correct) | NEEDS HUMAN (correct) / NEEDS HUMAN (correct) |
| slugkit-regression-001 | BASELINE (correct) / BASELINE (correct) | ERROR (spawn uncertain) / VERIFIED (correct) |
| kvparse-refactor-001 | BASELINE (correct) / ERROR | NEEDS HUMAN (correct) / NEEDS HUMAN (correct) |
| semver-long-prerelease-pr488 (external, pinned commit) | not finished (not correct) / ERROR | NO CHANGE (nothing correct to ship) / NO CHANGE (nothing correct to ship) |

What this shows, and only this:

- On this suite Attest did not ship fewer broken patches than the plain agent. Both arms shipped the two rle-encode
  patches. The task's contract is self-contradictory (round trip through an unchanged decoder for every string); the
  sealer did not write a test that exposes the contradiction in either attempt, so every gate passed. The recorded run
  from 15 Oct on the public console (`rle-encode-20261015T181805Z`) shows the other outcome, a sealed round-trip test that
  fails and holds the patch; which outcome occurs depends on the sealed tests the model writes.
- Every Attest hold was on a patch the held-out judge accepted. Four holds (durationkit attempt 2, semver-is-compatible
  attempts 1 and 2) came from one failing adversarial test each that the arbiter classified as a test defect, with the
  corrected test passing on the candidate; arbitration is advisory, so the frozen rule keeps the hold. kvparse attempt 1
  held because the breaker produced a test module with a syntax error (recorded as mutation incomplete); attempt 2 held on
  one failing sealed test plus a drift audit lost to a transport-uncertain inference call.
- The two NO CHANGE verdicts on the external python-semver task are correct refusals: the implementer exhausted its turn
  budget without editing; the plain agent did the same in its first attempt and produced no correct patch either.
- Attest cost 3.8 times the plain agent per cell and took 2.2 times longer; the extra calls are the sealer, the breaker,
  the auditor and the arbiter.
- Six cells ended in infrastructure errors, three per arm. The three Attest errors were sandbox spawns whose outcome was
  uncertain (TLS EOF on the POST twice, a read timeout once); the three plain-agent errors were inference calls whose
  outcome was uncertain (a TLS record error from the Token Factory endpoint), not retried. The frozen rule records such a
  cell as ERROR and never replays the operation, because a replay could create a second billed sandbox or a second billed
  completion; the batch stops and the operator resumes the remaining cells.

## How the batch ran

Registered 17:15:49 UTC from an immutable snapshot of `attest/`, the harness and `examples/` (`batch/snapshot/`); every cell
ran the registered revision `166cdcbd…` and the snapshot was intact at the end (`provenance_check`), so no comparison is
invalid. The batch stopped six times on a transport-uncertain sandbox spawn and was resumed from the same snapshot each
time with `scripts/run_evaluation.py --resume` (cells never executed only): segments started 17:15:49, 17:22:33, 17:34:53,
17:50:41, 17:55:33, 18:02:53 and 18:07:37 UTC (`batch-segment1.log` to `batch-segment7.log`; the resume loop is
`operator-resume.sh` with its log); the last cell finished 18:10:42 UTC. 293 model calls, 7 of them failed (transport),
0 rate-limited, 0 s of pacing waits. A first registration at 17:08:14 UTC from the previous pin (`batch-aborted-1/`, one
completed cell, $0.0077) was stopped by the operator at 17:10 UTC after the fourth smoke test's ledger had shown a sealing
call hitting the 16,000-token cap at medium reasoning effort, rescued only by the repair retry; the sealer and the breaker
moved to low effort, the pin moved to `6b786a2e…` and the batch was registered again (see the freeze report).

Before the batch, five smoke tests of the frozen task on Nemotron (`smoke/`, $0.291 in total) and two reasoning probes
($0.011) established the reasoning controls now in the client; they are described in `reports/attest-freeze-2026-10-17/README.md`.

## Budget (approved $11.00 on 17 Oct 2026: $9.00 evaluation, $0.50 smoke, $1.50 demonstrations)

| Item | USD |
| --- | --- |
| Smoke tests (5 runs) | 0.291 |
| Reasoning probes (2) | 0.011 |
| Aborted first registration (1 cell; the interrupted second cell's calls, at most $0.03, are in no ledger) | 0.008 |
| The 32-cell batch (committed, every cell's ledger kept on error) | 1.090 |
| Demo run 1 on the public console (`durationkit-units-001-20261017T172421506287Z`, NEEDS HUMAN) | 0.092 |
| Total | 1.49 (plus at most 0.03 unrecorded) |

Demo runs 2 and 3 of the demonstration allocation were not started; $1.41 of that allocation is unspent. Costs are from
the public Token Factory price table applied to the returned usage; the account balance was read as $25.00 at 16:55 UTC
before any of this spending.

## Internal rehearsals, not user testing

Everything in this folder was run by the project's own agents and scripts. The demo run and the video reels were
recorded by a script driving the public console; no outside developer has used Attest yet (the pilot kit in `PILOT.md`
and `PILOT_FEEDBACK.md` is ready and the two pilot dry runs in `reports/attest-m4-2026-10-17/` were rehearsals).

## Limitations

- Eight tasks and two attempts give no statistical claim; the table is the whole result.
- The sealed-test weakness on an unsatisfiable contract is a real gap: a sealer that does not probe the contract's
  consistency lets a hold-worthy task pass every gate.
- Advisory arbitration produces holds on correct patches; an "apply" mode exists in the design but the frozen rule does
  not use it, by choice.
- Transport flakiness of the Sandboxes API cost six cells; the never-replay rule is deliberate and the resumptions are
  recorded, but a judge should expect ERROR cells in any rerun.
- The verdicts are Attest's own; the only independent check is the held-out judge, whose suites are in `examples/eval/`.
