# Testing Attest (for judges and reviewers)

Three levels, from no credentials to a live run. Everything here is English, offline where it can be, and leaves no secret
in any artifact.

## 1. Offline, no credentials (about two minutes)

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
python3 -m unittest discover -s tests -t .
```

The suite runs the pipeline against a fake provider and a fake sandbox (every verdict path, tampering scenarios, the
bound supervisor executed locally, pacing, provenance, budget accounting under failure, the bounded import, redacted
exports, the executed contract-audit witnesses, validated corrections with gate re-runs, the never-overridden sealed
oracle, breaker escalation, the unfinished NO CHANGE, the ledger journal and the console's reconciliation from it), and
since revision 5 the audit's counterexamples next to their positive controls: `tests/test_audit_core.py` (lost, forged and
untrusted evidence never clears a gate; candidate-caused exceptions stay held; incomplete mutant runs are unknown; the real
supervisor kills a timed-out test's process group within a bound; correction scope and classification ids; the evidence
protocol; manifest completeness), `tests/test_audit_accounting.py`, `tests/test_audit_console.py`, `tests/test_audit_boundaries.py`
and `tests/test_audit_ops.py` (the deployment scripts rehearsed under shims that stand in for systemd, nginx and pip; about one
minute of the total, bash required). Then verify a recorded Proof Bundle offline, for example the external-repository run
that ended VERIFIED:

```bash
python3 -m attest check reports/attest-m4-2026-10-17/runs/semver-long-prerelease-pr488-20261017T132707Z
```

It recomputes every artifact digest against the manifest (and, since revision 5, that the manifest lists every file, with
unique contained paths, correct counts and no symbolic link), the sealed and adversarial bindings from the raw supervisor
records, every evaluated mutant's classification and the mutation score, the base and mutant evidence of any correction, the
digests of corrected test modules and of contract-audit witnesses, that a correction kept the test set and changed only the
failing tests' bodies and was classified for exactly the failing tests, that an INFEASIBLE verdict rests on an executed and
demonstrated witness, the ledger totals, the gate-to-verdict rule and `PROOF.md`. The header of the report names the bundle's
evidence protocol: a bundle written by revision 5 declares version 2, one written by revision 6 or later version 3, and
either must carry the complete evidence for its verdict (the result line then reads `OK, EVIDENCE COMPLETE for verdict ...`;
under version 3 the mandatory records are derived from the frozen task and the execution mode, and an INFEASIBLE verdict
needs a conflict grounded in the task's own criteria with a constrained witness); every bundle recorded before that is checked as a historical bundle for
internal consistency only, with warnings for the checks its records cannot support, and is never reported as fully verified.
Public copies of development-profile runs are redacted (the team's gateway host and local paths); such a copy carries
`REDACTION.json` naming its source run and the original manifest's digest, and its manifest is the export's own, so the
check still passes and says so.

## 2. The live console (no credentials; one click costs us, not you)

https://attest.axiqo.xyz shows recorded evidence first. Open any run: the decision header, the exhibits E1 to E7, the
gates, the counterexample when there is one, and the downloadable bundle. Download a bundle zip and run `attest check` on
it. Starting a live Nemotron run on a curated task is one explicit action, limited per visitor and by a daily cap.

## 3. Your own repository (your Nebius key)

Follow `PILOT.md`: import a public GitHub repository at a pinned commit, write the statement, run on Nemotron with your own
`NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID`, check the bundle.

## What the evidence folders contain

`reports/attest-*/README.md` are dated records; every run directory they cite is kept, including failed and inconclusive
ones. Internal rehearsals by the project's own agents are labelled as such and are never presented as external testing.
The evaluation method is frozen in `METHOD.md` and the pinned version in `FREEZE.md`; the paid comparison runs only after
the owner approves its budget.
