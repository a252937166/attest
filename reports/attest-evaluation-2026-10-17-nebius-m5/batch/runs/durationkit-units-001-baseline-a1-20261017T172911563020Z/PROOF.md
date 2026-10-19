# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: BASELINE**  
Run `durationkit-units-001-baseline-a1-20261017T172911563020Z` · profile `eval-baseline-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:29:11.563656+00:00, finished 2026-10-17T17:30:44.693615+00:00.

**Baseline run: no verification.** This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, and the candidate was judged only by the harness. It certifies nothing.

Key evidence (trajectory): candidate produced for the independent judge; no gates recorded



What to do: Compare with the Attest run of the same task in the evaluation report.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- nothing: no gate was reached

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `durationkit-units-001`, spec digest `52f44d7aa75262eecd969a37464e8a7ece88ce0eaa3f4ef17e12e86fa71dc6f5`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `5a08c3cc-d3d2-49b4-8aaf-099cfe5c2e76`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Numbers are written with the ASCII digits 0-9. Whether other Unicode decimal digits (for example Arabic-Indic or fullwidth digits) are accepted by their numeric value or rejected with ValueError is unspecified, and tests must not depend on either choice; characters that are not decimal digits (letters, Roman numerals, fractions, circled numbers) are malformed text and raise ValueError. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

(none)

Acceptance criteria:
1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
3. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
4. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError.
5. '0s' and '0' return 0.0.
6. ValueError for: '', '   ', '-1h', '1.5h', '1x', '1h1h', '30m1h', 'h', '1h30', 'abc'.
7. TypeError for non-string input such as 90 or None.
8. The return type is float for every accepted input.
9. Unspecified, not to be tested: acceptance or rejection of non-ASCII Unicode decimal digits such as '١٢h'.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 9 implementer turn(s).

```diff
--- a/durationkit/parse.py
+++ b/durationkit/parse.py
@@ -4,12 +4,82 @@
 def parse_duration(text: str) -> float:
     """Parse a duration string and return the number of seconds as a float.
 
-    Only a plain non-negative integer number of seconds is accepted at the
-    moment, for example ``"90"``. Surrounding whitespace is ignored.
+    Accepts a plain non-negative integer number of seconds (e.g. ``"90"")
+    or one or more components made of a non-negative integer followed by a unit:
+    d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds).
+    Components must appear in descending unit order (e.g. ``"2d4h"``,
+    ``"1h30m"``), each unit may appear at most once, and whitespace is allowed
+    around the whole string and between components (but not between a number
+    and its unit). Returns the total number of seconds as a float.
+
+    Raises:
+        TypeError: if ``text`` is not a string.
+        ValueError: for empty or whitespace-only input, negative numbers,
+                    fractional numbers, unknown units, repeated units,
+                    components out of descending order, a unit without a
+                    number, or any other malformed text.
     """
     if not isinstance(text, str):
         raise TypeError("duration must be a string")
     stripped = text.strip()
-    if not stripped.isdigit():
+    if not stripped:
         raise ValueError(f"unsupported duration: {text!r}")
-    return float(stripped)
+    # Plain integer seconds (no whitespace allowed inside)
+    if stripped.isdigit():
+        return float(stripped)
+    # Otherwise parse as sequence of components
+    import sys
+    pos = 0
+    n = len(stripped)
+    total = 0.0
+    seen_units = set()
+    # order: d > h > m > s > ms
+    order = {'d': 0, 'h': 1, 'm': 2, 's': 3, 'ms': 4}
+    prev_order = -1
+    while pos < n:
+        # Skip whitespace between components
+        while pos < n and stripped[pos].isspace():
+            pos += 1
+        if pos >= n:
+            break
+        # Parse number
+        start_num = pos
+        while pos < n and stripped[pos].isdigit():
+            pos += 1
+        if start_num == pos:
+            raise ValueError(f"unsupported duration: {text!r}")
+        number = int(stripped[start_num:pos])
+        # Parse unit
+        if pos >= n:
+            raise ValueError(f"unsupported duration: {text!r}")
+        # Check for ms first (two letters)
+        if stripped[pos:pos+2] == 'ms':
+            unit = 'ms'
+            pos += 2
+        elif stripped[pos] in 'dhms':
+            unit = stripped[pos]
+            pos += 1
+        else:
+            raise ValueError(f"unsupported duration: {text!r}")
+        # Validate unit constraints
+        if unit in seen_units:
+            raise ValueError(f"unsupported duration: {text!r}")
+        cur_order = order[unit]
+        if cur_order <= prev_order:
+            raise ValueError(f"unsupported duration: {text!r}")
+        seen_units.add(unit)
+        prev_order = cur_order
+        # Convert to seconds
+        if unit == 'd':
+            total += number * 86400
+        elif unit == 'h':
+            total += number * 3600
+        elif unit == 'm':
+            total += number * 60
+        elif unit == 's':
+            total += number
+        elif unit == 'ms':
+            total += number * 0.001
+        # Loop continues to parse next component (if any)
+    return total
+
```




## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: sealed supervisor and existing suite in one branch (bundle predates the order rule).

Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite.

(none)

Existing suite (evidence class `stdout`): n/a (0 passed of 0); operation `None`; parsed from console output ().

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

(none)

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Drift audit not run.



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1476 | 88 | 0 | 0.000522 | 3.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 1567 | 95 | 0 | 0.000556 | 2.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 1768 | 121 | 0 | 0.000639 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 1971 | 120 | 0 | 0.000699 | 2.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 2245 | 1868 | 0 | 0.002355 | 12.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 2459 | 5235 | 0 | 0.005449 | 33.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 3681 | 145 | 0 | 0.001235 | 3.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 3942 | 1568 | 0 | 0.002594 | 11.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 4659 | 424 | 0 | 0.001779 | 4.5s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 23768/9664/0; USD: 0.015828.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14ae9-3062-75f8-be03-98746c80cf49 | SUCCESS | 0 | 0.754s | retained | off | 0.00287163 |
| impl-tests-7 | 01a14aea-29e5-71e3-b4e9-2c2395c91074 | SUCCESS | 0 | 1.059s | disposable | off | 0.00302922 |
| impl-python-8 | 01a14aea-64b5-75a1-af77-7ff5bf8a4be3 | SUCCESS | 0 | 0.944s | disposable | off | 0.00125138 |

Sandbox operations: 3, total guest duration 2.757s, retained images ['5a08c3cc-d3d2-49b4-8aaf-099cfe5c2e76'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
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
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
