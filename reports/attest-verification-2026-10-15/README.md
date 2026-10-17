# Verification hardening evidence (2026-10-15)

## Trust boundary

The sealed suite no longer runs inside the candidate-controlled process that reports results. A **supervisor** program
(stdlib only, never imports the sealed module or candidate code) hashes the sealed file, discovers the expected test IDs
statically from its AST, runs **one child process per test** with a timeout, feeds the per-run nonce to each child on stdin
only after the child has imported the test module, and derives every outcome from facts it owns: exit code, signal,
timeout, and the presence and integrity of the child's result file. It writes the trusted JSON only after the whole suite
ran. The host binds the verdict to the expected IDs proven red, the sealed-file digest before and after, the nonce, and
rejects any nonzero exit, signal, timeout, missing, forged or inconsistent result. Code: `attest/core/sealed.py`.

Residual risk, stated: a candidate can still tamper from inside a child after the nonce was read (for example by inspecting
the wrapper's frames). The mutation gate and the held-out suite are the structural detectors for that case.

## Real-sandbox adversarial scenarios

Checkpoint `53affb28-c70a-43bf-a7ad-5d8498d9b93b` (operation `01a1401c-f820-70e0-abe5-522bb0a666a0`), one disposable networking-off
branch per scenario, all at 2026-10-15T15:10:24.732268+00:00. Expected: only `honest` accepted. Result: **all 8 decided
correctly** (`all_correct = True`). Raw report: `sandbox-adversarial.json`.

| Scenario (candidate behaviour) | Decision | Supervisor summary | Failed binding checks | Operation |
| --- | --- | --- | --- | --- |
| `honest` | accepted | OK (3 of 3 methods, each in its own process) | - | `01a1401d-061b-75cb-a487-3314d00513de` |
| `wrong` | rejected | FAILED (3 of 3 methods: FAIL 3) | no_nonzero_exit, all_expected_pass | `01a1401d-0638-77d6-80f3-9837a1f2aaef` |
| `tamper_sealed_file` | rejected | FAILED (2 of 3 methods: ERROR 2) | sealed_file_unchanged_after, no_nonzero_exit, all_expected_pass | `01a1401d-0674-773d-8898-694edc295555` |
| `premature_exit` | rejected | FAILED (3 of 3 methods: MISSING_RESULT 3) | no_missing_or_forged_result, all_expected_pass | `01a1401d-065a-744f-b206-a2192aa49bfa` |
| `forged_results_at_import` | rejected | FAILED (3 of 3 methods: FORGED 3) | no_missing_or_forged_result, all_expected_pass | `01a1401d-160a-71e9-9529-19733b73035c` |
| `forged_stderr_text` | rejected | FAILED (3 of 3 methods: FAIL 3) | no_nonzero_exit, all_expected_pass | `01a1401d-162b-73bc-ad3b-6523d26b15a9` |
| `timeout` | rejected | FAILED (3 of 3 methods: TIMEOUT 3) | no_nonzero_exit, no_signal, no_timeout, all_expected_pass | `01a1401d-176d-77d9-8b20-172d5b8f5497` |
| `crash_signal` | rejected | FAILED (3 of 3 methods: CRASH 3) | no_nonzero_exit, no_signal, all_expected_pass | `01a1401d-24bf-70d2-bc93-a2f0360c91b8` |

The same scenarios were first exercised with real local processes (`attest/core/sealed.py` self-check during development),
and the offline fakes in `tests/test_verification.py` cover the host-side binding for modified tests, forged nonce, missing
and extra test IDs, premature exit, forged console text, child crash, child timeout, held-out failures, surviving mutants,
failing adversarial tests and high drift.

## Gates that now block VERIFIED

existing suite, sealed binding (all checks), held-out suite when configured, mutation score below threshold (0.5) once at
least 4 mutants were evaluated, model-written adversarial tests, drift audit score at or above 0.6, implementer not finished,
scope policy violations, verification runner errors. Each gate and its detail is recorded in `proof_bundle.json` under
`gates` and rendered in `PROOF.md`.
