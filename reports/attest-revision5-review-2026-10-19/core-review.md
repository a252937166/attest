# Revision 5 — bounded independent core review, 19 October 2026

**Verdict:** substantial repairs, but “all findings closed” is too strong. CORE-01/02/03/04/05/07 close the original counterexamples within this review's scope. **CORE-06 remains partial:** the current protocol-2 checker still certifies a bundle whose existing-suite stage record and corresponding raw result are absent. The kvparse refusal also remains an open release-quality issue, and its explanatory correction misquotes the frozen task.

This review reads the completion attachment, repair README/core reports, current source/tests, and recorded runs. It runs only the two bounded offline reproductions below, not the full test suite, real supervisor workload, providers, Sandbox or production. Original source, original reports and original runs are untouched. The temporary synthetic bundle is removed automatically. Closure means the original counterexample is addressed by the current mechanism and recorded regression evidence, not exhaustive proof of correctness.

## CORE-01 to CORE-07

| Finding | Status | Evidence and remaining boundary |
|---|---|---|
| CORE-01 | Closed for original cases | `attest/core/pipeline.py:264–300` binds base/mutant discrimination; structural filtering also protects original adversarial arbitration. `tests/test_audit_core.py:73–153` covers missing base, forged mutant/original failure and positive controls. `core/core-repro-after-fix.json` records the original failing examples unvalidated. Targeted in-interpreter forgery remains the expressly documented residual, not a newly closed guarantee. |
| CORE-02 | Closed for original tuple/exception bug | `pipeline.py:104–113` makes every non-timeout executed failure an oracle disagreement. The adapted tuple repro now has `sealed_assertion_hold=true`, `validated=false`, NEEDS HUMAN. Tests at `test_audit_core.py:154–189` include the tuple and exception cases. Timeout-only correction still weakens the executed workload; this is admitted and is not semantic proof that a performance requirement was preserved. |
| CORE-03 | Closed for original invalid-kill case | `pipeline.py:302–325` classifies structurally untrusted or timed-out mutants unknown. Adapted incomplete result now has killed=0, unknown=1. Tests at `test_audit_core.py:190–267` include eleven invalid shapes, gate behavior and offline tampering. |
| CORE-04 | Closed for original unbounded-communicate path | `attest/core/sealed.py:337–358` bounds the final drain and records cleanup; the repaired fake uses killpg and a five-second grace. Recorded real-supervisor regression cases are at `test_audit_core.py:269–409`. This review does not independently rerun those OS process tests. `/proc` escape detection and targeted child forgery retain the report's stated limits. |
| CORE-05 | Closed for original AST/classification gaps | `pipeline.py:163–231` freezes the module skeleton/existing imports and requires exact classification coverage. Adapted import/base changes include `<module>` and unknown classification IDs are rejected. Regression cases: `test_audit_core.py:411–478`. This does not prove the semantics of an arbitrarily rewritten failing method. |
| CORE-06 | **Partial; new bounded counterexample below** | Protocol and historical separation are implemented, including dated legacy handling at `attest/core/verdict.py:38–45,77–80`, explicit isolation and witness requirements. However, required existing-stage evidence is conditional on the stage record already being present (`check.py:217–220`). Modern full-completeness checking still fails open on joint deletion. |
| CORE-07 | Closed for original zero-file manifest/badge bug | `attest/core/manifest.py:98–162` checks containment, duplicates, counts/totals/exclusions and listing completeness; the adapted empty-list manifest fails and loses its verified flag. Tests: `test_audit_core.py:619–697`. Hashes remain unsigned integrity records, as correctly documented. |

Repair evidence read here is under `reports/attest-audit-repairs-2026-10-19/core/`. No full-suite pass count is independently claimed by this review.

## P2 — CORE-06 still permits missing existing-suite evidence

**Source:** `attest/core/check.py:217–220`; gate/stage comparison is also conditional on `existing` being present. `required_evidence_problems` requires the gate inventory but not the existing stage itself. It checks the raw result only if a bound record exists.

**Reproduction:** copy the recorded protocol-2 balanced-brackets run to a temporary directory; retain its passing `existing_suite` gate but remove `proof_bundle.verification.existing` and `verify_raw.existing`. Re-render PROOF and regenerate the unsigned manifest to isolate semantic checking from expected hash failures. Run the actual current `check_bundle` against both original and modified copy.

```text
Original: ok=true, fully_verified=true, evidence_complete=true,
          manifest_verified=true, errors=0, warnings=0, protocol=2
Modified: ok=true, fully_verified=true, evidence_complete=true,
          manifest_verified=true, errors=0, warnings=0, protocol=2
```

This is **semantic incompleteness after stage deletion**, not cryptographic forgery, proof of a live execution attack, or a claim that an unsigned regenerated manifest should authenticate its author. Other duplicate stage files may remain in the copied directory; the checker neither requires nor reconstructs the missing primary stage evidence from them. It still claims full completeness without doing that check.

**Fix:** derive mandatory stages from the frozen task, declared runner/mode and gate inventory, not from the presence of optional records. Require an existing-suite record for a passing existing gate, its raw result/binding when bound, and explicit supported evidence for any documented fallback. Apply the same rule to task-declared held-out tests. Recompute the gate from mandatory evidence, rather than skipping comparison when that evidence is absent.

**Acceptance:** for a genuine current-protocol VERIFIED bundle, jointly delete stage+raw evidence, stage+gate, and stage+raw+gate; each applicable stage must cause a named completeness error and `fully_verified=false`. Preserve positive complete and explicitly historical/partial controls. Existing single-field deletion tests did not catch joint omission.

## P1 product correctness — kvparse INFEASIBLE remains unjustified

**Recorded mechanism:** `pipeline.py:795–805` audits the model-produced specification and immediately aborts INFEASIBLE when any conflict is marked demonstrated. Requirement IDs are validated against that specification (`pipeline.py:1195–1206`), with no source-entailment mapping to the user's task. Marker/exit execution is still model-authored reasoning, not a proof of impossibility.

Relevant recorded run:

`reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/runs/kvparse-refactor-001-attest-a1-20261019T082112441408Z/`

- Its frozen statement is byte-for-byte equal to `examples/eval/kvparse-refactor/task.json:29`: **“byte-for-byte identical for every str input.”** The task does not say only “existing inputs.” Therefore `evaluation-codex-2/CORRECTIONS.md:22–24` cannot attribute the universal quantifier exclusively to a model-added requirement. The original task itself leaves built-in strings versus adversarial `str` subclasses insufficiently explicit.
- The witness at `contract_audit/witness_1.py:4–18,26–30` defines a `str` subclass with `__len__ == 0`, compares the original parser with one particular partition-based rewrite, and sees ValueError versus `('a','b')`.
- The spec's AC2 (`spec.json:36`) prescribes an ordinary string literal. It does not itself require that every subclass with the same displayed contents behave as that literal. AC16 (`spec.json:50`) concerns universal preservation. The witness's chosen `required_parse_line` is not established as the only permitted implementation.

**Bounded counterexample to that witness's reasoning:** the review's `guarded_partition` uses `str.partition`, no while loop, and adds `if len(line) == 0: raise ValueError`. It returns the original ValueError for the witness's `ZeroLengthString('a=b')`, while matching the original on seven ordinary valid/invalid examples. The program and exact outputs are saved alongside this report.

This does **not** prove a complete solution for every hostile subclass or silently resolve the input-domain ambiguity. It proves the observed difference between the original and the witness's chosen rewrite does not establish that *every* allowed refactor must differ. Consequently, neither “the task is proven impossible” nor “the derived specification is proven internally contradictory” follows from this witness alone.

**Safest immediate fix:** stop promoting untrusted derived-contract conflicts directly to user-task INFEASIBLE. Record them as `NEEDS HUMAN` / contract conflict until authoritative criteria, input domain and the relation from witness observations to those criteria are established. Preserve the original task and witness; do not weaken the benchmark after seeing this result and call it the same task. If intended inputs are exact built-in strings (`type(x) is str`), document that as a versioned task/domain decision and freeze new evidence accordingly. Auditing only the task text is insufficient by itself: a model can still compare one arbitrary implementation and overclaim impossibility.

**Acceptance:** a specification that invents an obligation, an ambiguous subclass domain, and this exact one-implementation witness must remain held rather than end INFEASIBLE. A supported contradiction in authoritative requirements needs a constrained check or explicit human confirmation, with requirement provenance preserved. Keep the false-refusal record visible; a checksum-complete bundle does not make its semantic verdict correct.

This is the previously disclosed model-witness limitation materializing in a real run, plus a concrete error in the report's diagnosis. It is not a newly discovered integrity/execution failure or permission to rerun paid validation.

## Version and result interpretation

The first five-cell batch records package `722cd6dd…`; the two-cell retry records `1e12d462…` (`evaluation-codex/RESULTS.md:5`, `evaluation-codex-2/RESULTS.md:5`). Comparing their frozen `snapshot/attest` file hashes finds **only `core/check.py` differs**. The statement that the implementation/witness runtime was unchanged across those two snapshots is supported; do not present all seven cells as having the final package digest.

Both recorded batches used harness `6e77617b…`. The pinned `2aa28413…` harness subsequently adds `false_refusal`; the second batch's preserved evaluation still labels kvparse true_reject and its correction is separate. Keep the recorded and corrected interpretations distinct.

## Reproductions

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B reports/attest-revision5-review-2026-10-19/core-review-repros.py
```

- [Both bounded reproductions](core-review-repros.py)
- [Exact results and source hashes](core-review-repro-results.json)

The script writes only its result JSON in this new review directory and removes its temporary copied bundle. No original audit, product code or test files are changed.
