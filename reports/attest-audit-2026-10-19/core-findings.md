# Core verification audit — 19 October 2026

## Scope and evidence

This audit covers sealed supervision, test correction/arbitration, mutation evidence, witnesses, coverage, gate-to-verdict derivation, and offline bundle/manifest checking. It does not audit provider billing, deployment, the web API, or account state. Product code and product tests were not edited. No credentials, network, provider calls, SSH, real sandbox executions, or production services were used.

The findings below are demonstrated with the current Python code and controlled offline executor/process fakes. The tuple example additionally runs a tiny, auditor-authored local unittest against a deliberately incorrect toy function. Fake operation IDs are `op-N`, not real execution evidence. None of these reproductions establishes that an existing production run exploited the defect.

- [Reproduction script](core-repros.py)
- [Machine-readable results and audited-source SHA-256 values](core-repro-results.json)
- [Console output](core-repro-console.txt)
- [Synthetic bundles, clearly marked OFFLINE-AUDIT-ONLY](synthetic-bundles/)

Reproduce from the repository root without generating product bytecode:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B reports/attest-audit-2026-10-19/core-repros.py
```

The script writes only synthetic audit artifacts beneath this report's directory. It exercises vulnerable behavior; it is not a replacement for the acceptance tests proposed below. Source references are repository-relative, with line numbers for the source hashes in `core-repro-results.json`.

Priority: **P1** can incorrectly clear a verification gate or defeat a workload timeout; **P2** undermines correction scope or the advertised completeness/meaning of offline checking.

## Findings at a glance

| ID | Priority | Finding | Observed result |
|---|---|---|---|
| CORE-01 | P1 | Arbitration accepts missing/untrusted discrimination and original adversarial tampering | Missing base, wrong-nonce/FORGED mutant, and original FORGED adversarial failure each permit a validated correction |
| CORE-02 | P1 | A candidate-caused error in the test body can be classified as test-internal and weakened away | Exactly-two-item contract, three-item candidate: original errors, weaker test passes, correction validated |
| CORE-03 | P1 | An incomplete mutant execution is counted as killed | Zero tests, incomplete supervisor, isolation false: killed=1, unknown=0, score=1.0 |
| CORE-04 | P1 | Per-test timeout is followed by unbounded output collection and only kills the direct child | Exact supervisor AST calls `communicate(timeout=None)` after killing its immediate child |
| CORE-05 | P2 | Correction scope omits existing imports/class headers and classification-ID coverage | Import/base changes invisible; unknown classification ID still permits validation |
| CORE-06 | P2 | Offline checking lacks a strict current-protocol evidence schema | Incomplete VERIFIED and witnessless INFEASIBLE bundles pass; legacy flags can override an Oct19 failed gate |
| CORE-07 | P2 | An empty/incomplete manifest can receive `manifest_verified=true` | Zero listed files, unlisted proof bundle: checker returns OK with a warning |

## CORE-01 — Arbitration can turn untrusted evidence into a passing gate

**Source:** `attest/core/pipeline.py:1183–1204`, `1317–1348`, `1351–1374`; application at `873–918`; re-derivation at `924–929`. Offline checking repeats the weak discrimination test at `attest/core/check.py:347–363`.

There are three manifestations of the same missing trust boundary:

1. Corrected-base reruns discard the raw result/binding. `base_outcomes.get(test_id, "MISSING_RESULT") != "ok"` counts a missing result as the corrected test failing on the base. An entirely lost result therefore supplies the required red evidence.
2. Corrected-mutant reruns also discard binding and count every non-`ok` result, including `FORGED`, as evidence that the correction discriminates.
3. `arbitrate_failures` blocks structural failures for sealed tests, but applies no equivalent structural filter to original adversarial failures. A failed adversarial binding and a `FORGED` outcome can enter test-defect correction.

**Observed repros:** `missing_base`, `untrusted_corrected_mutant`, `original_adversarial_forgery_arbitrated` in the results JSON.

```text
base: no trusted sealed result; failing=0
corrected_tests_failing_on_base=[test_a]; validated=true; error=null

base: OK
mutant: wrong nonce and FORGED; validated=true; error=null

original adversarial: FORGED, binding_ok=false
arbitration entered; validated_modules=[adversarial]
```

The corrected candidate uses the real binding function and passes it. Applying the resulting `validated` flag as the pipeline does, with other gates passing, derives `VERIFIED`. This is a control-flow reproduction, not a real model or sandbox demonstration. The checker cannot repair it: it treats a nonempty discrimination string as sufficient and the raw base/mutant evidence is not retained for re-derivation.

**Fix:** define one validator for negative execution evidence. Require completion, explicit isolation, nonce/digest/ID correspondence, intact canaries when used, and a result for each relevant corrected test. Reject lost results, runner failures, forged/mismatched records and structural failures; these must remain unknown/held, not red. Distinguish authentic ordinary `FAIL`/candidate `ERROR` from execution infrastructure failures. Apply the same original-binding structural filter to adversarial and sealed arbitration. Persist the raw base/mutant results, expected IDs/digests/nonces, structural binding and test-specific discrimination reasons, and independently recompute them in `check`.

**Acceptance:** missing base result, missing corrected test ID, wrong nonce/digest, incomplete supervisor, disabled isolation, `FORGED`, `MISSING_RESULT`, signal and infrastructure timeout must never clear a correction gate. Valid bound candidate-pass/base-fail and candidate-pass/base-pass/mutant-fail examples must continue to work. Tampered original adversarial evidence must never be converted into a test defect.

## CORE-02 — “Test-internal” location does not establish a test defect

**Source:** `attest/core/pipeline.py:75–105`, `1287–1293`, `1340–1341`; sealed correction application at `890–918`.

`test_internal_errors` treats certain exception strings whose innermost frame is the sealed test file as test-internal. A bad candidate return value can cause exactly such an exception in correct test code. Exception type and traceback location do not establish causation.

**Observed repro:** `candidate_caused_test_internal_error`.

```python
# Contract: return exactly the two-item tuple (1, 2).
def candidate(): return (1, 2, 3)  # violates the contract

# Correct original test: errors in its own file with ValueError.
a, b = candidate()
assert (a, b) == (1, 2)

# Weakened correction: passes the same incorrect candidate.
a, b, *extra = candidate()
assert (a, b) == (1, 2)
```

The actual local unittest confirms the original `ValueError` and the corrected test passing. `oracle_disagreement` returns false. Actual `arbitrate_module` with controlled execution evidence returns `sealed_assertion_hold=false`, `validated=true`, and a valid corrected-candidate binding; the unmodified base remains red. Other independent gates can still catch the bad candidate, but this intended sealed-oracle protection does not.

**Fix:** candidate-derived exceptions must remain oracle disagreements unless a separate, auditable mechanism establishes an error independent of candidate behavior. The safest immediate rule is to keep all executed sealed assertion/runtime failures on human hold and allow only clearly established pre-execution test construction/syntax defects to be regenerated before sealing. Do not automatically weaken an already executed oracle based on an exception-name allowlist. A proposed correction must preserve contract assertions, not merely remain red on a stub base.

**Acceptance:** wrong tuple shape, missing returned object attributes, wrong return type and a zero denominator supplied by a bad candidate must remain held when the failure occurs in test code. A weaker test that accepts extra tuple members must not restore VERIFIED. Keep a separate positive example of a genuine test-construction defect whose repair is established independently.

## CORE-03 — Mutation score can be inflated by incomplete executions

**Source:** `attest/core/pipeline.py:1085–1095`, score at `1101–1110`, gate at `945–979`.

Normal mutation classification checks only result presence, the top-level nonce and the post-execution sealed digest before scoring. Any test-discovery mismatch is treated as a kill. Other failed structural checks are ignored.

**Observed repro:** `incomplete_normal_mutant` supplies a result with the correct nonce/digest but `completed=false`, `privilege_separation=false`, no tests/IDs, and a discovery error. The real mutation stage produces:

```text
generated=1 evaluated=1 killed=1 survived=0 unknown=0 score=1.0
failing_methods=0 killed_by=[]
```

This invalid execution can pass the mutation threshold. It also feeds the list of allegedly killed mutants used for corrected-test discrimination. An authentic mutant-caused import/behavior error can legitimately be a kill; missing or untrusted supervision cannot establish one.

**Fix:** structurally validate every mutant run before assigning killed/survived. Preserve expected discovery identity, verify all structural binding facts and classify incomplete/untrusted runs as unknown. Define which bound failures count as a kill, with timeout/crash policy explicit and separate from infrastructure failure. Record the binding and raw evidence and recompute counts/score/gate in `check`.

**Acceptance:** matching nonce/digest alone with zero tests, incomplete supervision, false isolation or missing expected IDs must be unknown and must not increase the score. A completed bound test assertion against a mutant must still count as killed. Test the resulting gate, not only the intermediate counter.

## CORE-04 — Descendant pipes can defeat the per-test timeout

**Source:** `attest/core/sealed.py:272–285` within `SUPERVISOR_SRC`.

On timeout, the supervisor kills only `proc`, then calls `proc.communicate()` without a timeout. A candidate/test can leave a descendant holding inherited stdout/stderr. Killing the direct child does not close those descendant descriptors, so the second communicate can wait indefinitely. The result-drain thread's later join timeout does not bound this earlier call. A separate outer sandbox timeout may eventually abort the operation, but it does not make the promised per-test timeout work or guarantee a complete trusted result.

**Observed repro:** `per_test_timeout_descendant_pipes` executes the exact `run_child` AST with a fake process, descriptors and clock; no OS process is spawned.

```text
communicate(timeout=1.0)
kill(immediate child)
communicate(timeout=None)
simulated elapsed=3601.0s; configured per-test timeout=1.0s
```

The simulated delay is not a measured live delay. It demonstrates the unbounded call and absence of descendant cleanup in the real function.

**Fix:** start each test in its own process session/group (or a dedicated workload cgroup), terminate the whole group on timeout, use bounded escalation and bounded final pipe draining, then close pipes and reap known children. Preserve an outer hard deadline for the supervisor and ensure all cleanup waits share a remaining-time budget. Do not signal the supervisor's own group. Treat cleanup failure as infrastructure failure and prevent VERIFIED.

**Acceptance:** in an isolated offline Linux test environment, fork a bounded sleeping descendant that retains stdout/stderr; the parent/test times out, the supervisor returns within deadline plus a small documented cleanup grace, and no descendant remains. Include a descendant retaining the result fd, a TERM-ignoring child, and normal large-result regression. Do not run an unbounded workload or test this against shared production services.

## CORE-05 — Correction scope checks omit semantic changes and classification coverage

**Source:** `attest/core/pipeline.py:109–137`, `1256`, `1266–1286`; the checker reuses the same helper at `attest/core/check.py:214–230`.

The AST scope comparison discards all imports, including replacement/removal of existing imports, and omits test class bases/decorators/keywords. Rebinding a function used by previously passing tests or changing their TestCase base can change those tests without changing their method AST. This contradicts the revision report's narrower “imports may be added” description. Separately, `all_defect` does not ensure returned classification IDs cover exactly the actual failing IDs.

**Observed repros:** `correction_scope`, `classification_ids_not_matched`.

```text
replace existing imported function + change test_bad:
  methods_changed = {test_bad}, no <module>
replace TestCase base + change test_bad:
  methods_changed = {test_bad}, no <module>
classifications=[unknown.T.not_a_failing_test: test_defect]:
  actual failure=test_breaker.B.test_a; validated=true; error=null
```

The scope example demonstrates the AST guard's blind spot; it does not claim those synthetic unresolved import/base names were executed in a sandbox. The classification example exercises actual arbitration with controlled candidate/base evidence.

**Fix:** compare the full AST while replacing only the bodies of explicitly permitted failing methods with placeholders. Preserve class metadata and all existing bindings. If additive imports are permitted, reject alias collisions/rebindings/removal, and restrict them to correction-local imports where possible. Require exactly one classification per failing ID, no unknown/duplicate IDs, and `test_defect` for every test whose correction may apply. Recompute these facts offline from the original raw failures.

**Acceptance:** replacing/removing an existing import, changing a class base/decorator/metaclass, and changing helper/class setup code must be rejected. A new noncolliding import confined to an approved failing method may pass policy. Unknown, duplicate and omitted classification IDs must prevent validation; a complete correct mapping must remain valid.

## CORE-06 — Conditional checking permits incomplete modern evidence and protocol downgrade

**Source:** `attest/core/check.py:163–209`, `234–296`, `339–399`; `attest/core/verdict.py:22–36`, `42–57`; isolation binding at `attest/core/sealed.py:607–608`.

Checks run only when the corresponding evidence field/file exists. Missing raw results are labelled “predates milestone M2” without establishing the bundle's protocol. Required gate names/stage records, candidate facts, task/ledger and witness execution fields are not enforced by a current-version schema. Legacy arbitration application is enabled by flags with no version/date boundary. Missing isolation is treated as active (`is not False`). These are one root cause: modern mandatory facts are handled as optional historical data.

**Observed repros:** `incomplete_verified_bundle`, `modern_bundle_legacy_bypass`, `infeasible_without_witness`, `missing_isolation_field`.

- A synthetic bundle with only one passing gate and no verification/raw/task/ledger passes `check`: `ok=true`, `errors=0`, verdict `VERIFIED`, manifest verified. The manifest genuinely matches the few files present, so this is semantic incompleteness, not a hash mismatch.
- A synthetic bundle labelled Oct19 with a failed held-out gate, `arbitration.applied=true` and `cleared=true` is re-derived as VERIFIED and passes. This demonstrates the absence of a protocol boundary; it does not show the current live pipeline invokes the legacy path. Legitimate pre-Oct19 artifacts should remain readable with explicitly limited historical checking.
- INFEASIBLE with only `conflicts:[{demonstrated:true}]`, no witness file, digest, operation, output or exit code, passes.
- Removing `privilege_separation` from an otherwise valid raw result still yields `binding_ok=true` and `verifier_isolation_active=true`. The current supervisor normally emits this field; the repro concerns malformed/older evidence, not an observed live omission.

**Fix:** introduce an explicit versioned evidence protocol and enforce mandatory records per terminal verdict and execution mode. For modern VERIFIED require the full gate inventory, non-skipped pass states, true candidate scope/finished facts, raw results/bindings for each bound gate and correction-discrimination evidence. For modern INFEASIBLE require the witness source/digest plus complete, internally linked execution record. Require isolation explicitly true for modern bound results. Reject unsupported/downgraded protocol claims as modern verification; expose a separate historical/partial consistency result instead of inferring old age from absence. Remove legacy overrides from modern derivation and restrict historical interpretation to a deliberate legacy mode.

**Acceptance:** strip each mandatory section/file/field from a current-version bundle and require a nonzero checker result with a specific error. Fail current bundles carrying legacy-clear flags over any failed gate. Keep known genuine historical examples readable as historical/partial evidence, without a modern fully-verified badge. Reject witnessless INFEASIBLE and missing isolation. Preserve the documented boundary: hashes/internal checks cannot authenticate sandbox execution by themselves.

## CORE-07 — Incomplete manifests are warnings while the integrity badge stays true

**Source:** `attest/core/manifest.py:84–100`; `attest/core/check.py:137–159`, `438–439`.

`verify_manifest.ok` ignores unlisted files. `check` reports an incomplete manifest as only a warning and sets `manifest_verified` from `manifest_digests`. An empty list therefore verifies zero bytes while the important proof bundle remains unlisted. The declared file count/total, duplicate entries and the allowed exclusion set are also not schema-enforced.

**Observed repro:** `empty_manifest_listing`: manifest `files=[]`, file_count/total=0, existing proof bundle unlisted. `check` returns `ok=true`, `errors=0`, `manifest_verified=true`; incompleteness is one warning.

**Fix:** for a supported current manifest, require an exact one-to-one listing of all required regular in-bundle artifacts except the fixed manifest file, no duplicate entries, correct count/total, supported algorithm/version, and an allowlisted exclusion set. Fail completeness errors; calculate a full-integrity badge only after digest and completeness validation both pass. Treat unsupported/historical partial manifests as partial, not verified. Also validate relative contained paths and reject symlinks before opening artifact entries; these are hardening requirements, not additional path exploits reproduced here.

**Acceptance:** empty listing, unlisted required proof/raw file, duplicate path, wrong count/total, arbitrary exclusion and escaping/symlink path must fail modern validation. A generated complete manifest must pass. Do not describe regeneration by an attacker as cryptographic authentication; the product already correctly states that the manifest is unsigned.

## Evidence limits and product claims to retain or tighten

### Witnesses are executed model claims, not formal contradiction proofs

`pipeline.py:1015–1058` checks a marker prefix and exit code 3. It does not validate that requirement IDs exist, that the marker matches the named conflict, or that a calculation establishes impossibility. `marker_only_witness` shows an `AC999` claim for a one-criterion spec accepted as demonstrated by the fake executor's marker/exit record. No actual witness process or contradictory repository was executed by this audit.

The revision report already explicitly documents false INFEASIBLE risk at `reports/attest-revision-2026-10-19/README.md:51–53`. This is a known limitation, not a claim that the recorded real RLE witness is invalid: that witness computes the mandated `a1 -> a111` case and uses the unchanged decoder. Require valid requirement IDs, structured observable claims and reviewable witness output; label conclusions accordingly. A human/restricted trusted oracle is needed for a stronger semantic guarantee. A marker alone cannot supply it.

### Coverage gaps remain nonblocking, by design

`pipeline.py:695–712` retries gaps before the last attempt but then accepts and records them; they are not a verdict gate. `coverage_gaps(None, ...)` also returns no gaps, although the current sealer schema requires an array, so the `None` repro is helper-level compatibility/hardening evidence, not a demonstrated current-model response path. An empty array correctly produces all missing criteria. The current schema and report already call the map the sealer's own claim; it cannot prove behavioral coverage.

If the product promises every acceptance criterion has an executable check, make nonempty complete mapping a strict gate, reject missing maps, and keep semantic coverage as an explicitly limited claim. Acceptance: an unmapped criterion stays held in strict mode after retry exhaustion, with a documented partial/research mode if desired.

### Targeted child-result forgery remains a documented trust limitation

`sealed.py:12–15`, `35–37` explicitly admits a candidate in the same test interpreter can forge its own result while sparing canaries. This audit did not execute such an exploit. Root-owned test files, nonces and per-test processes prevent several attacks but do not authenticate a report produced inside the same interpreter as untrusted candidate code. Mutation and held-out tests are additional detectors, not a proof that targeted forgery cannot pass. Do not strengthen the product wording beyond that boundary without moving outcome observation outside the untrusted interpreter or constraining the threat model.

## Recommended repair order

1. Keep arbitration application advisory while fixing CORE-01 and CORE-02; preserve failed/tampered evidence and holds.
2. Unify structural validation of all candidate/base/mutant evidence; fix CORE-03 and persist enough raw facts for offline reconstruction.
3. Bound and reap test descendants/pipe collection (CORE-04).
4. Freeze correction semantics and match classification IDs (CORE-05).
5. Add explicit current/historical evidence protocols and exact manifest completeness (CORE-06/07).
6. Run the targeted offline acceptance cases, then a frozen Codex-only reliability evaluation. Any paid-provider validation requires separate bounded authorization; it was not performed here.
