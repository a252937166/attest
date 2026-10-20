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
minute of the total, bash required). Revision 8 adds `tests/test_transport.py`: the real HTTP client against servers on the
loopback interface that fail at each point (a TLS handshake dropped or timed out, a proxy that accepts the CONNECT tunnel and
then drops it, a proxy that refuses it, a request read but never answered, a body cut off while sending), which must classify
the first four as never sent and the others as uncertain; the gateway, Token Factory and Sandboxes adapters' bounded resend of
never-sent requests, their refusal to resend anything uncertain, the reservation of a never-sent paid attempt closed at a known
$0, the accepted Sandboxes operation id journaled before polling, the harness's reconciliation list and the checker's
recomputation of the transport counters; `ExplicitStart` in `tests/test_audit_console.py` (428 without the confirmation
header, no trace); the installer's memory-limit readback (`test_audit_ops.py` scenarios 9 and 10); and the console's
confirmation step in `tests/console_client_test.mjs`. Then verify a recorded Proof Bundle offline, for example the
external-repository run that ended VERIFIED:

```bash
python3 -m attest check reports/attest-m4-2026-10-17/runs/semver-long-prerelease-pr488-20261017T132707Z
```

It recomputes every artifact digest against the manifest (and, since revision 5, that the manifest lists every file, with
unique contained paths, correct counts and no symbolic link), the sealed and adversarial bindings from the raw supervisor
records, every evaluated mutant's classification and the mutation score, the base and mutant evidence of any correction, the
digests of corrected test modules and of contract-audit witnesses, that a correction kept the test set and changed only the
failing tests' bodies and was classified for exactly the failing tests, that an INFEASIBLE verdict rests on an executed and
demonstrated witness, the ledger totals, the gate-to-verdict rule and `PROOF.md`. The header of the report names the bundle's
evidence protocol: a bundle written by revision 5 declares version 2, one written by revision 6 version 3 and one written
by revision 7 or later version 4, and each must carry the complete evidence for its verdict (the result line then reads `OK, EVIDENCE COMPLETE for verdict ...`;
under version 3 the mandatory records are derived from the frozen task and the execution mode, and an INFEASIBLE verdict
needs a conflict grounded in the task's own criteria with a constrained witness; under version 4 the checker repeats the
witness-language analysis `attest-witness/1` from the witness file and the repository copies in the bundle); every bundle recorded before that is checked as a historical bundle for
internal consistency only, with warnings for the checks its records cannot support, and is never reported as fully verified.
Public copies of development-profile runs are redacted (the team's gateway host and local paths); such a copy carries
`REDACTION.json` naming its source run and the original manifest's digest, and its manifest is the export's own, so the
check still passes and says so.

Isolation (revision 9): the suite needs no credential, no private configuration and no network, and proves it. `tests/_isolation.py`,
imported by `tests/__init__.py` before any test, removes provider credentials and private configuration from the test process,
disables urllib's proxy discovery, and turns every connection or name lookup outside the loopback interface into a failure of the
test that caused it; `tests/test_zz_isolation.py`, the last module of a discovery run, fails if any was attempted. The run also gets
its own new home directory (HOME, with the XDG base-directory variables removed), and the same module fails if a test left anything
in it, so no test reads or writes a developer's home and no run sees what an earlier one left there. Revision 9's own
tests (`tests/test_revision9.py`) stop a run at an uncertain sandbox operation at every stage and check that nothing is sent afterwards,
classify cut and stalled HTTP error bodies, 4xx and 5xx answers to spawns, polls and model calls, make the journal fail (disk full, I/O
error, a half-written line, a read-back mismatch) before a spawn and before a poll, recover interrupted runs from their journals, and
hold the console and the harness after a stop. `reports/attest-revision9-repairs-2026-10-20/repro/repro_revision9.py --code <checkout>`
reproduces each of the revision-8 defects against a checkout and reports PASS or FAIL per check, so it can be run on the code before
and after the repair.

## 2. The live console (no credentials; one click costs us, not you)

https://attest.axiqo.xyz shows recorded evidence first. Open any run: the decision header, the exhibits E1 to E7, the
gates, the counterexample when there is one, and the downloadable bundle. Download a bundle zip and run `attest check` on
it. Starting a live Nemotron run on a curated task takes two explicit steps (Run, then the confirmation that states the cap),
limited per visitor and by a daily cap.

The layout check of revision 8 is reproducible: `python3 scripts/console_layout_audit.py --out <dir>` (Playwright with the
installed Chrome) starts a local console with no credentials over the recorded runs and reports every element or text that
leaves the viewport at 320 to 1440 px, on every tab with every panel open, with error states simulated inside the browser;
`--base https://attest.axiqo.xyz` audits the live console. Every request that is not a GET is blocked in the browser before it
is sent (aborted on the live console, answered synthetically on the local one), and the report counts them.

## 3. Your own repository (your Nebius key)

Follow `PILOT.md`: import a public GitHub repository at a pinned commit, write the statement, run on Nemotron with your own
`NEBIUS_API_KEY` and `NEBIUS_PROJECT_ID`, check the bundle.

## What the evidence folders contain

`reports/attest-*/README.md` are dated records; every run directory they cite is kept, including failed and inconclusive
ones. Internal rehearsals by the project's own agents are labelled as such and are never presented as external testing.
The evaluation method is frozen in `METHOD.md` and the pinned version in `FREEZE.md`; the paid comparison runs only after
the owner approves its budget.

Export provenance (revision 8): `python3 scripts/check_export_provenance.py` runs `attest check` on every bundle of the
export (`dist/public`), compares each exported file with its source (byte for byte, or through `REDACTION.json`), and compares
each batch bundle's package digest and provider profile with its batch's registration (`schedule.json`, `evaluation.json`).
`--no-source` checks an export on its own.

Final-tree rule (revision 7): the suite counts that a pin records come from a clean checkout of the pinned commit of the
review repository (`git worktree add --detach <dir> <commit>`, then `python -m unittest discover -s tests -t .` inside it),
run after the batch, the reports and the export exist. A run in the private working tree is reported separately: it holds
private evidence and file modes that a clean checkout does not have. Since revision 9 that run is made with an empty environment
(no credential, HOME pointing to an empty directory) and with outbound network access blocked by the operating system, in addition
to the suite's own guard. Correction (20 Oct 2026): the directory given as HOME to the first clean runs of revision 9 was reused from
run to run, and one test wrote the gateway pacing state of its dummy key there, so from the second run on it was not empty; the suite
now moves HOME to a new directory of its own on every run and fails if anything is left in it
(`reports/attest-revision9-repairs-2026-10-20/README.md`, "Correction: the suite's home directory").
