# Revision 5 independent follow-up review — 19 October 2026

**Disposition: substantial verified repairs, but not an unconditional closure of all 35 findings. Keep new paid validation pending.** The main application is live on version 0.5.0 and its ordinary regression checks pass. Three original areas remain partially open (AC-03, CORE-06 and API-09), the recorded kvparse refusal remains unjustified, and the proposed smoke/profile/credential boundaries need tightening.

The follow-up reviewed the owner's pasted completion report, repaired source/tests, freeze and recorded batches, public export and deployment records. Product code/tests, the original audit, repair reports and original run evidence were not edited. Only this new review folder and disposable local audit files were written. No credential was read, paid provider/Sandbox operation performed, production POST issued, service restarted or deployment changed. Independent live evidence is limited to low-frequency public GETs; server filesystem/release-layout details remain deployment-record claims rather than a new SSH readback.

## Independent readback

| Check | Result |
|---|---|
| Complete offline suite | **314 tests passed**, zero failures, errors or skips, 86.40 seconds |
| Public exported run directories | **164/164 accepted** by the current checker; 7 marked evidence-complete, the remaining 157 historical; 444 total historical warnings |
| New development batches | 5/5 and 2/2 accepted; all seven marked evidence-complete for their respective verdicts; this is record checking, not seven correct patches |
| Live public service around 09:36 UTC | HTTP 200, **0.5.0**, worker alive, ready, idle, queue 0, no active reservations |
| Public list | 39 rows; no requester, out_dir, raw error or error_detail row fields |
| Assets | Served home HTML, JS and CSS exactly match the reviewed local files |
| Disk | 1,212 MB free / 8.77%; accepting runs, no low-disk outage observed |
| Local package fingerprint | `1e12d46217fb6b8a27a08b4463f42f361e7309257b211103c08777c91cb10ce5`, 35 Python sources; matches the revision-5 pin |
| Local review repository | Clean `dist/public`, code pin `320651d`, records HEAD `e5b5236`, no configured remote |

The first five-cell batch's package differs from the final package only in `core/check.py`'s human-readable result formatting; the second two-cell batch matches the final package. Both used the earlier harness snapshot, and the later pinned harness corrects confusion labels. Keep the original and corrected interpretations distinct.

## Outstanding work

### R5-01 — P1 budget recovery: partial settlement corrupts the next reservation's framing

**Original area:** AC-03. **Source:** `attest/ledger.py:42–52`, `150–164`, `187–195`; journal reader `276–280`.

A settlement append can write an incomplete JSON prefix and then fail. That failure is swallowed. A later successful reservation is appended directly onto the unfinished line and `reserve()` returns success, but restart parsing skips the combined invalid line. The bounded fake observes **$0.06 committed in memory versus $0.02 recovered**, with reservation `r2` lost. No HTTP request was made; this demonstrates the dispatch precondition being satisfied without a recoverable reservation.

**Repair:** halt subsequent paid dispatch after any journal append failure unless a deliberate durable tail-recovery protocol has restored framing. Preserve prior reservations conservatively; do not merely catch the parse error on restart. Add partial-write/flush failure followed by another request and restart to the acceptance cases.

See [accounting review](accounting-review.md), [reproduction](partial-settlement-repro.py) and [results](partial-settlement-results.json).

### R5-02 — P2 evidence completeness: jointly omitted existing-suite evidence still passes

**Original area:** CORE-06. **Source:** `attest/core/check.py:217–220` and conditional stage/gate matching.

In a temporary copy of a genuine protocol-2 VERIFIED bundle, remove both `verification.existing` and `verify_raw.existing`, retain its passing existing-suite gate, and regenerate proof/manifest. The actual current checker still returns `ok=true`, `fully_verified=true`, `evidence_complete=true`, **zero errors and warnings**. The original positive bundle also passes. This is a semantic completeness defect, not a claim that an unsigned hash manifest authenticates execution.

**Repair:** derive required stages from the protocol, terminal verdict, execution mode and frozen task—not from whether the stage record survived. Require every applicable existing-suite record and raw binding before a modern VERIFIED bundle can be called complete. Test joint omission of stage/raw/gate combinations.

See [core review](core-review.md), [reproduction](core-review-repros.py) and [results](core-review-repro-results.json).

### R5-03 — P1 product correctness: the kvparse witness does not prove task impossibility

The recorded run still ends INFEASIBLE on `kvparse-refactor-001`. Its witness compares the original parser against one particular partition-based implementation; disagreement with that implementation does not establish that every allowed refactor is impossible. A small guarded partition implementation defeats this witness's example and matches seven ordinary/invalid examples. This does **not** claim to solve every hostile string subclass.

The repair report's diagnosis also needs correction: the frozen and current task already say **“every str input”**. It is inaccurate to attribute that entire quantifier to a new model requirement. The input domain, original requirements, derived specification and witness assumptions need explicit provenance and interpretation.

**Repair:** classify derived, ambiguous or insufficiently established contract conflicts as NEEDS HUMAN. Do not let a model restatement plus a marker/exit code establish impossibility of the user's task. Preserve requirement provenance, define the supported input domain, and require constrained validation or human confirmation for the stronger INFEASIBLE claim. Keep the false-refusal correction visible and accurately describe its cause.

See the [core review and bounded witness counterexample](core-review.md).

### R5-04 — P2 diagnostic publication: row sanitization does not cover bundles and events

**Original area:** API-09. **Source:** `attest/core/pipeline.py:563–569`, `attest/app/worker.py:320–325`, public detail/artifact routes.

Row/global errors are sanitized, but model/generic exception text still enters bundle reasons and progress events. A pipeline-shaped synthetic public ERROR record exposes a diagnostic sentinel through list, detail, events, proof JSON, rendered proof and ZIP. This proves publication of seeded carriers; the review did not trigger a real failing provider call or find a real leaked credential.

**Repair:** use approved public codes/correlation IDs at the pipeline event/reason boundary, keep diagnostics private, and apply the publication policy to all proof/artifact paths. Historical redaction must create a traceable derived export rather than silently rewrite original sealed evidence.

See [API review](api-review.md), [reproduction](api-review-repro.py) and [results](api-review-repro-results.json).

### R5-05 — P2 paid proposal mismatch: the CLI smoke does not enforce 22 calls

**Source:** `FREEZE.md:178`, `attest/cli.py:24`, `attest/app/worker.py:254`, `attest/models/nebius_tokenfactory.py:52`.

The harness supplies the 22-call cap, but CLI and worker construction omit it and the provider default is `None`. The promised CLI smoke is therefore not governed by that request-count limit. A separate USD cap still applies; this is not a demonstrated bypass of that cap.

**Repair:** supply and record an enforced cap at the actual smoke entry point, or run smoke through a registered entry point that enforces it. Verify call 23 is refused before dispatch using a fake provider. Make command, schedule, proposal and runtime description agree.

### R5-06 — P2 frozen-profile gap: role/effort overrides escape comparison validation

The harness-level resume repairs are present, but effective role mappings and effort overrides are not fully compared. A changed implementation model can remain marked as a valid comparison. This residual is disclosed in the repair report; it still limits reproducibility.

**Repair:** freeze and compare the effective provider configuration, including roles, model IDs, effort, sampling and relevant limits, rather than only the provider name and high-level limits. Reject drift or register a new profile/batch.

### R5-07 — P2 team credential delivery: download URL carries full administrative authority

**Source:** `attest/app/server.py:164–170`, `401–408`, and client artifact URL construction.

Team visibility itself is implemented. However, download links carry the master team token in a query parameter, and that token is accepted as full administrative authority on POST admission as well. A synthetic token enables team enqueue and bypasses the public visitor quota; it is not a run-scoped read-only download credential. Credential-bearing URLs may be copied or retained in diagnostic/history/logging systems. No actual token exposure or security incident was observed.

**Repair:** avoid master tokens in URLs. Use an appropriate authenticated session/header/download flow or short-lived, run-scoped, read-only download credentials that cannot authorize POSTs. This is a routine-team-use improvement, not by itself a reason to block source publication or an anonymous demo where no team token is entered.

## Closure and release interpretation

- The original CORE-01/02/03/04/05/07 examples are addressed within this source/regression review. CORE-06 remains partial.
- Accounting recovery/import/metering/day and harness resume repairs are substantial; the partial settlement framing issue reopens AC-03. CLI cap and role/effort qualifications remain.
- API-01–08 and API-10–11 are addressed in the reviewed single-process/offline scope; API-09 remains partial. Team read visibility is now real, with the credential-delivery residual above.
- Boundaries/export/ops have concrete code changes and passing tests in the full suite. Real service migration and rollback availability are supported by deployment records, while failure rehearsals use command shims; this review did not execute production rollback or independently read its server files.
- No new formal revision-5 Nemotron comparison was found. Existing Codex bundles and a checksum-complete record do not establish semantic correctness or a measured advantage over the baseline.

## Recommended next action

Fix R5-01/02/03 first, then complete public diagnostic sanitization and make the proposed smoke/profile limits concrete. Remove master-token URLs before routine team downloads. Run the specific negative and positive acceptance cases, the offline suite and a small Codex-only batch, then create a **new pin** rather than modifying the frozen record in place. Only afterwards request bounded paid smoke/evaluation approval; the proposed $10 remains unapproved.

Keep the main application on **yungou** and any necessary Docker component on **Aliyun**, with deployments scoped to Attest and verified not to disrupt existing services.

Delivery remains separate: damaged final video/voice provenance, public repository, updated Devpost submission, real external pilot and official credit balance/expiry are still outstanding. Do not infer paid authorization or current account balance from this review.
