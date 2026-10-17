# Testing Attest (for judges and reviewers)

Three levels, from no credentials to a live run. Everything here is English, offline where it can be, and leaves no secret
in any artifact.

## 1. Offline, no credentials (about 15 seconds)

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
python3 -m unittest discover -s tests -t .
```

The suite runs the pipeline against a fake provider and a fake sandbox (every verdict path, tampering scenarios, the
bound supervisor executed locally, pacing, provenance, budget accounting under failure, the bounded import, redacted
exports). Then verify a recorded Proof Bundle offline, for example the external-repository run that ended VERIFIED:

```bash
python3 -m attest check reports/attest-m4-2026-10-17/runs/semver-long-prerelease-pr488-20261017T132707Z
```

It recomputes every artifact digest against the manifest, the sealed and adversarial bindings from the raw supervisor
records, the ledger totals, the gate-to-verdict rule and `PROOF.md`. Public copies of development-profile runs are
redacted (the team's gateway host and local paths); such a copy carries `REDACTION.json` naming its source run and the
original manifest's digest, and its manifest is the export's own, so the check still passes and says so.

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
