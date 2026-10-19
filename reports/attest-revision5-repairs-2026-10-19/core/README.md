# R5-02, R5-03 and R5-04: evidence completeness, grounded infeasibility, private diagnostics (19 October 2026)

Repairs of three findings of the revision-5 follow-up review (`reports/attest-revision5-review-2026-10-19/README.md`,
`core-review.md`, `api-review.md`). Offline work: no provider call, no sandbox operation, no deployment in this folder. The
original run records, the review folder and the earlier repair reports are unchanged except for the dated corrections named
below, which are appended, never substituted.

## R5-02: mandatory evidence derived from the task, not from surviving records

Finding: a copy of a genuine protocol-2 VERIFIED bundle with `verification.existing` and `verify_raw.existing` both deleted
and the passing `existing_suite` gate retained still checked as complete.

Change (`attest/core/check.py`, `required_evidence_problems`): the mandatory records of a current bundle are derived from the
protocol, the terminal verdict, the frozen task and the recorded execution mode:

- every recorded, non-skipped gate must have the stage record it summarises (`gate <name> has no stage record`), for any verdict;
- for VERIFIED: the gate inventory must be complete (`existing_suite`, `sealed_binding`, `mutation`, `adversarial_tests`,
  `drift_audit`, plus `heldout_suite` exactly when the frozen task carries `heldout_tests_sha256`); the suite binding mode comes
  from the checkpoint's execution record, and the existing-suite stage record is mandatory with a passing result, an evidence
  class equal to that mode and, in bound mode, its raw supervisor result, a passing binding and the module list; held-out
  evidence is mandatory exactly when the task declares held-out tests (its stage record, raw result and binding in bound mode)
  and is an error when the task declares none;
- for INFEASIBLE under protocol 3: see R5-03.

The review's reproduction re-run from a documented copy (`review-repro/core-review-repros.py`, one line changed to take the
project root from the environment because the copy sits two levels deeper; original digests in `review-repro/sha256-originals.txt`;
output in `review-repro/core-review-repros-rerun.txt`, results in `review-repro/core-review-repro-results.json`): the positive
control (the recorded `balanced-brackets` bundle) still checks complete under its protocol 2, and the stripped copy now fails
with two errors, `gates_match_stage_records` ("existing_suite (gate without a stage record)") and `required_evidence`
("gate existing_suite has no stage record; existing-suite stage record missing"). The derivation applies to every current
bundle (protocol 2 and 3), so the seven recorded revision-5 batch bundles remain complete under it (`bundle-checks.txt` in
the parent folder after the suite run).

Acceptance (`tests/test_audit_core.py::R502MandatoryStagesDerivedFromTheTask`): positive controls (a bound run and a run with
held-out tests, both complete under protocol 3); joint omission of the existing-suite stage record with its raw result, with
its gate, with both, the raw result alone, the binding mode alone, and a stage record whose evidence class contradicts the
recorded mode, each failing with a `required_evidence` error naming the existing suite or the binding; joint omission of
held-out stage/raw/gate on a task that declares held-out tests; held-out evidence present on a task that declares none; a
gate without its stage record on a NEEDS HUMAN bundle; a historical copy (no protocol field) still handled as historical.
`tests/test_verification.py` and the audit-core counterexamples of revision 5 all pass unchanged.

Limitation: completeness is about the records a verdict needs, not about their truth. A complete bundle shows that the
recorded verdict follows from the recorded evidence under the recorded rule; whether the patch is correct is measured by the
held-out judge of the evaluation harness, never by `attest check`.

## R5-03: INFEASIBLE only on a grounded conflict; everything less is held

Finding: the recorded `kvparse-refactor-001` refusal rested on a witness that compared the original parser with one chosen
`str.partition` implementation on a `str` subclass whose `__len__` returns 0; disagreement with that implementation does not
show that every implementation the task allows is impossible, and the repair report had attributed the "every str input"
quantifier to the specification model although the frozen task statement contains that sentence itself.

Changes:

- `attest/core/prompts.py` (`contract_audit_prompt`): the auditor sees the requester's own acceptance criteria as `TC1..n`
  (authoritative) apart from the specification's derived criteria `AC1..m`; a PROVENANCE RULE (only a conflict whose
  requirements are all `TC` ids can end the run), an INPUT DOMAIN RULE (`WITNESS_INPUT_DOMAIN`: literals of the built-in types
  the task names and values the unchanged repository computes from them; subclasses of built-in types, objects with overridden
  special methods and other adversarial values are outside the domain unless the task names them) and a CONSTRAINED witness
  requirement (no `def`, `class`, `lambda`, dynamic `type(...)`, and none of `exec`, `eval`, `compile`, `__import__`,
  `globals`, `locals`, `vars`, `setattr`, `getattr`: the witness may only call the public interface on literal inputs and
  print the marker).
- `attest/core/pipeline.py`: `requirement_provenance(ids, task_ids, derived_ids)` returns `task`, `derived`, `mixed` or
  `unknown`; `witness_constraint_problems(source)` lists every forbidden construct found by an AST walk; `contract_audit()`
  records per conflict `provenance`, `witness_constrained`, `constraint_problems` and `grounded` (`provenance == "task"` and
  constrained), plus the bundle fields `requirement_ids_known` (the `TC` and `AC` id sets) and `input_domain` (the rule text).
  The audit outcome is `contradiction demonstrated` only for a grounded conflict; a demonstrated conflict that is derived, mixed
  or unconstrained is `conflict demonstrated on derived criteria or by an unconstrained witness`. Stage 2a ends the run
  INFEASIBLE only on a grounded conflict ("contract contradiction demonstrated by an executed, constrained witness on the task's
  own criteria (requirements TC…)"); any other demonstrated conflict aborts to NEEDS HUMAN with the reason "contract conflict
  demonstrated but not grounded: …" and the witness recorded.
- `attest/core/exhibits.py`: reason class `contract_conflict_held` with decision copy that says why the demonstrated
  conflict did not end the run (derived criteria, or an unconstrained witness) and leaves the call to a person; the
  INFEASIBLE copy names the grounded conflict.
- `attest/core/verdict.py`: `EVIDENCE_PROTOCOL_VERSION = 3`. `attest/core/check.py`: under protocol 3 an INFEASIBLE verdict
  needs a grounded conflict whose requirement ids are all the task's own and whose recorded witness program, re-parsed from
  the file in the bundle, is constrained; a forged `grounded` flag, a derived id list or an unconstrained witness is a
  `required_evidence` error. Protocol-2 bundles keep their own rule (the recorded `rle-encode` INFEASIBLE bundle still checks
  complete under protocol 2 and is not re-labelled).

Report corrections (appended, originals kept): `reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/CORRECTIONS.md`
(new section: the quantifier is the task's own sentence, restated by the specification model, not introduced by it; the witness
disproves one implementation; under the revision-6 rule the recorded witness classifies `provenance: derived`,
`witness_constrained: false`), the batch-2 row of `reports/attest-audit-repairs-2026-10-19/README.md`, and a bracketed
correction next to the revision-5 narrative in `FREEZE.md` (pin values untouched). The recorded cell stays labelled
`false_refusal`; the evaluation harness keeps that label.

Acceptance (`tests/test_audit_core.py::R503GroundedInfeasibility`, `tests/test_verification.py`): a grounded conflict (TC ids,
constrained witness) ends INFEASIBLE and checks complete under protocol 3, and forging derived ids onto it is caught offline;
derived, mixed and unconstrained demonstrations each end NEEDS HUMAN with reason class `contract_conflict_held`, no sealing,
a complete bundle, and a forged INFEASIBLE verdict on them fails the required-evidence check; the recorded kvparse witness
classifies as unconstrained (defines a class and a function) and the recorded rle-encode witness as constrained;
`requirement_provenance` and the constraint vocabulary are checked on literal cases; the recorded protocol-2 INFEASIBLE bundle
still checks under its own protocol. `WitnessValidation` (revision 5) now runs its grounded case on TC ids.

Limitations: grounding is by reference and execution. The checker verifies that the named ids are the task's own, that the
witness program is syntactically constrained and that it ran with the marker and exit code; the semantic link between the
witness's literal inputs and the named criteria remains the auditor's claim, which is why an INFEASIBLE verdict still reads
"demonstrated by an executed witness" and why anything less is held. The input-domain rule is prompt text plus a recorded
field; a constrained witness can still choose inputs the requester would call outside the domain, and a person reviewing a
hold decides that. Whether Nemotron or the development models name `TC` ids reliably under the new prompt is measured by the
development-gateway batch recorded in the parent folder and remains to be measured on Nemotron (unapproved paid work).

## R5-04: raw exception text stays private

Finding: sanitized row errors (API-09) did not cover bundle reasons, stage records, progress events, PROOF.md or downloads;
a pipeline-shaped ERROR record exposed a diagnostic sentinel through list, detail, events, proof JSON, rendered proof and ZIP.

Changes:

- `attest/core/diagnostics.py` (new): `classify_error(error)` maps an exception or text to a fixed public vocabulary
  (`provider_http` with the status code as the only variable part, `provider_transport_uncertain`, `provider_rate_limited`,
  `provider_schema`, `provider_cap_usd`, `provider_cap_calls`, `provider_halted`, `provider_error`, `sandbox_error`,
  `sandbox_uncertain`, `internal_error` with the exception type name); `Diagnostics(run_id, sidecar_dir)` appends the full
  text, stage, code and context to a private sidecar `<runs dir>/diagnostics/<run id>.jsonl` outside the run directory and
  returns `<public sentence> [ref <8 hex>]`.
- `attest/core/pipeline.py`: every failure site (specification, contract audit, sealing attempts and rejected attempts, breaker
  authoring and its sandbox spawn, mutant execution, arbitration re-runs, drift audit, the schema-repair suffix sent back to the
  model, stage aborts and the terminal ERROR reason) records through `self.diagnostics.public_text(stage, error)`; the drift
  record and the contract-audit record store the public text only.
- `scripts/export_public.py`: `diagnostics/` is excluded from every export; the sidecar is never part of a bundle, a manifest,
  a zip or an artifact route because it lives next to the run directories, not inside one.
- The console's row-level sanitization (API-09) is unchanged; the worker's failure path keeps the traceback in `error_detail`
  (never published) and the service log.

Acceptance (`tests/test_audit_core.py::R504DiagnosticsStayPrivate`, with a provider that raises an error carrying a private
marker and a host path): a failure at the first model call ends ERROR with a public reason ("the model provider returned HTTP
502 [ref …]"), no file of the run directory and no progress event carries the marker, the sidecar carries it with the same
reference, the manifest lists no sidecar and the bundle checks; a failure in the drift stage leaves a public gate detail and no
marker anywhere; the console imported over that run serves list, detail, events, proof JSON, rendered proof and the zip without
the marker and without the sidecar. The export scanner's run over the repaired tree is in the parent folder.

Limitations: the raw supervisor results keep the sandbox operation's own status text (`runner_error`, for example "operation
status failed: …") because they are the faithful execution records `attest check` reclassifies; that text is the Sandboxes
API's operation message, never a request body or a credential, and the public export's redaction pass still applies to it.
Historical bundles recorded before this change keep whatever reasons they recorded; the public export redacts the known private
strings (gateway host, local paths) and records the redaction in `REDACTION.json` of the derived copy rather than rewriting
the sealed original. Model-call records are covered as well: the ledger carries a private diagnostics sink that the pipeline
attaches (`Ledger.public_error`), both providers route the raw text of a failed call (URL, response body, transport message)
through it, so the call record, the journal line and the bundle's ledger section carry the public sentence with its reference,
and the schema-violation record no longer quotes the model's content head (`R504CallRecordsStayPublic`). The CLI tells the
operator how many private entries a run recorded and where the sidecar is.
