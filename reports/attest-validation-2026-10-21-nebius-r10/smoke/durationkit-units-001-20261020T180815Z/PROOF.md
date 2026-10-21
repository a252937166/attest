# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: NEEDS HUMAN**  
Run `durationkit-units-001-20261020T180815Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-20T18:08:15.524696+00:00, finished 2026-10-20T18:13:52.033261+00:00.

**Hold this patch.** 2 of the 17 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request.

Key evidence (E1): test_ac4_combined_descending: ValueError: missing or invalid number for unit 'm'



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: implementer did not finish within 12 turns; child process nonzero exit: test_ac4_combined_descending exit 1, test_ac6_return_type_float exit 1
Warnings: drift audit: score 0.40, widened 0, unsupported claims 2

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 2 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0.4, narrowed (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 5 of 17 failed on the unmodified base; 15 of 17 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.4, narrowed (threshold 0.6) |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `eaccd597-e133-43fc-880c-738a681d2271`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components, each a non‑negative integer followed by a unit (d, h, m, s, ms) in strictly descending unit order, with optional whitespace around the whole string and between components. The function returns the total seconds as a float. It must preserve existing behavior for plain integer strings, reject malformed input with ValueError, and reject non‑string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepts two forms: (1) a plain non‑negative integer (ASCII digits) optionally surro | TypeError: if text is not a string.; ValueError: if text is empty or whitespace‑only after stripping.; ValueError: if any component contains a negative number ( |

Acceptance criteria:
AC1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
AC2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
AC3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
AC4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
AC5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
AC6. Return type is float for every accepted input.
AC7. ValueError for empty string '' and whitespace‑only '   '.
AC8. ValueError for negative numbers: '-1h'.
AC9. ValueError for fractional numbers: '1.5h'.
AC10. ValueError for unknown units: '1x'.
AC11. ValueError for repeated units: '1h1h'.
AC12. ValueError for components out of descending order: '30m1h'.
AC13. ValueError for unit without a number: 'h'.
AC14. ValueError for number without a unit in a multi‑component string: '1h30'.
AC15. ValueError for completely malformed text: 'abc'.
AC16. TypeError for non‑string input such as 90 or None.
AC17. Existing tests in tests/test_parse.py must continue to pass without modification.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. The contract is satisfiable. The new requirements extend the existing plain-integer behavior with a well-defined component format (units d,h,m,s,ms in descending order, optional whitespace between components but not within them). All error cases are disjoint and clearly specified. Existing tests cover only the plain-integer form and error cases that remain valid (empty string, non-string input, whitespace handling). No requirement forces two different outputs for the same input, and no requirement conflicts with the frozen test suite or the unchanged function signature. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `56272e88fea8088b04e3258dfd4e1ba808d7d73bc7890e8ee0d17a7ff4bf0254`, 17 test methods, sealed at 2026-10-20T18:09:16.320220+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (5 of 17 methods: ERROR 5): 5 of 17 methods failing, 12 passing; operation `01a15a80-d24c-743a-ad1e-6dd580047aa6`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParseDurationSealed.test_ac10_unknown_unit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac11_repeated_units | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac12_out_of_order | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac13_unit_without_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac14_number_without_unit_in_multi | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac15_completely_malformed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac16_non_string_input | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac17_existing_behaviour_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac1_plain_integer_with_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac2_zero_and_zero_unit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac3_single_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac4_combined_descending | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac5_whitespace_allowed_between_components | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac6_return_type_float | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac7_empty_and_whitespace_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac8_negative_number | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseDurationSealed.test_ac9_fractional_number | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -2,14 +2,56 @@
 
 
 def parse_duration(text: str) -> float:
-    """Parse a duration string and return the number of seconds as a float.
+    """Parse a duration string and return the total number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer (seconds) or a sequence of components
+    like ``"1h30m"``, ``"2d4h"``, etc. Components must be in descending order
+    of units (d > h > m > s > ms) and each unit may appear at most once.
+    Whitespace is allowed around the string and between components.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
-        raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    if not stripped:
+        raise ValueError("empty duration string")
+    tokens = stripped.split()
+    if not tokens:
+        raise ValueError("empty duration string")
+    unit_info = {
+        'd': (86400.0, 0),
+        'h': (3600.0, 1),
+        'm': (60.0, 2),
+        's': (1.0, 3),
+        'ms': (0.001, 4),
+    }
+    total = 0.0
+    seen_units = set()
+    prev_rank = -1
+    for token in tokens:
+        if token.endswith('ms'):
+            unit = 'ms'
+            number_part = token[:-2]
+        elif token[-1] in 'dhms':
+            unit = token[-1]
+            number_part = token[:-1]
+        else:
+            unit = None
+            number_part = token
+        if unit is None:
+            if len(tokens) != 1:
+                raise ValueError("number without unit in multi-component string")
+            if not number_part.isdigit():
+                raise ValueError(f"invalid number: {number_part!r}")
+            total += int(number_part)
+            continue
+        if number_part == '' or not number_part.isdigit():
+            raise ValueError(f"missing or invalid number for unit {unit!r}")
+        if unit in seen_units:
+            raise ValueError(f"repeated unit: {unit}")
+        factor, rank = unit_info[unit]
+        if rank <= prev_rank:
+            raise ValueError(f"units out of descending order: {unit}")
+        seen_units.add(unit)
+        prev_rank = rank
+        total += int(number_part) * factor
+    return float(total)
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (48 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (2 of 17 methods: ERROR 2). Operation `01a15a84-ce1c-728d-aacb-b58f672e34ec`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| supervisor_cleanup_complete | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (6 of 6 methods, each in its own process) (6 passed of 6); operation `01a15a84-e7e7-75b6-9fb7-42fd66831eba`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (6 of 6 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_ac4_combined_descending exit 1, test_ac6_return_type_float exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.4 (narrowed) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run), implementer did not finish.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
- E1 `test_ac4_combined_descending`: ERROR; ValueError: missing or invalid number for unit 'm'
- E1 `test_ac6_return_type_float`: ERROR; ValueError: missing or invalid number for unit 'm'

## 8. E5 Drift audit
Score 0.400 (narrowed; threshold 0.6). The diff preserves existing behavior and adds validation for whitespace-separated components, but it fails to parse the concatenated component forms (e.g., '1h30m') that the task explicitly requires. This narrows the scope by omitting a core parsing requirement.

Scope narrowed: The implementation only splits the input on whitespace (tokens = stripped.split()), so it cannot parse concatenated components like '1h30m' or '2d4h' as required by the specification. The spec explicitly allows components to appear without whitespace between them (e.g., '1h30m'), but the current code treats such strings as a single token and fails to recognize multiple components.; Descending-order validation only works when components are separated by whitespace; for concatenated components the order check is never reached because the token is rejected as an invalid number.  
Scope widened: none  
Unsupported claims: Turn 3 claim: 'Replace parse_duration implementation to support multiple components and stricter validation' – the implementation does not support multiple components without whitespace, as evidenced by the failing comprehensive test in turn 5 (exit 1).; Turn 4 claim: 'existing test suite: OK' – while existing tests pass, the new required behavior (concatenated components) is not covered by those tests and the implementation fails it.

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1737 | 1883 | 0 | 0.007386 | 8.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 3768 | 3161 | 0 | 0.013251 | 12.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2175 | 1875 | 0 | 0.002340 | 25.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 2048 | 113 | 0 | 0.000716 | 10.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2341 | 99 | 0 | 0.000791 | 6.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2554 | 3483 | 0 | 0.003901 | 34.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3383 | 108 | 0 | 0.001112 | 9.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3646 | 1749 | 0 | 0.002668 | 20.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | - | - | - | 0.000000 | 33.4s | not sent |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 4603 | 5807 | 0 | 0.006607 | 47.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 5152 | 719 | 0 | 0.002193 | 9.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 5708 | 1621 | 0 | 0.003171 | 11.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 5753 | 496 | 0 | 0.002172 | 4.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-10 | medium | 5712 | 1766 | 0 | 0.003303 | 11.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-11 | medium | 6108 | 2606 | 0 | 0.004178 | 17.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-12 | medium | 5828 | 2792 | 0 | 0.004261 | 20.6s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 3219 | 3371 | 0 | 0.013332 | 10.8s | ok |

Model calls: 17 (1 failed, 0 malformed); tokens in/out/cached 63735/31649/0; Inference USD: 0.071382; 1 attempt(s) were never sent (the connection failed first) and cost nothing.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15a80-10d2-772d-8911-719d86161bb9 | SUCCESS | 0 | 0.809s | retained | off | 0.002856 |
| red-1 | 01a15a80-d24c-743a-ad1e-6dd580047aa6 | SUCCESS | 0 | 4.048s | disposable | off | 0.03312497 |
| impl-tests-4 | 01a15a81-e794-7418-8b0b-f5fe57094b63 | SUCCESS | 0 | 0.816s | disposable | off | 0.0028941899999999996 |
| impl-python-5 | 01a15a82-4ad0-7595-a30c-741939fb4546 | SUCCESS | 0 | 0.597s | disposable | off | 0.00125132 |
| impl-python-8 | 01a15a83-eef0-7732-866c-69e347edfa12 | SUCCESS | 0 | 0.601s | disposable | off | 0.00126699 |
| verify | 01a15a84-ce1c-728d-aacb-b58f672e34ec | SUCCESS | 0 | 4.092s | disposable | off | 0.03335397 |
| existing | 01a15a84-e7e7-75b6-9fb7-42fd66831eba | SUCCESS | 0 | 2.169s | disposable | off | 0.015321819999999998 |

Sandbox operations: 7, total guest duration 13.132s, retained images ['eaccd597-e133-43fc-880c-738a681d2271'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
