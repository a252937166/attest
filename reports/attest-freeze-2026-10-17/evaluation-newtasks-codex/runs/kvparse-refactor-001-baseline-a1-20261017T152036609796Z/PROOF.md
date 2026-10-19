# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: BASELINE**  
Run `kvparse-refactor-001-baseline-a1-20261017T152036609796Z` · profile `eval-baseline-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T15:20:36.613340+00:00, finished 2026-10-17T15:26:59.074535+00:00.

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
Task `kvparse-refactor-001`, spec digest `e63b9851edc55942cd02c6d232d61876f55a85e01ace5c6da218c56b06d9b2ce`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `362b9181-cf4e-45d9-b45b-81e8ca8a478d`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `36369c7b57230897` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-freeze-2026-10-17/evaluation-newtasks-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

(none)

Acceptance criteria:
1. parse_line behaviour unchanged: 'a=b' -> ('a','b'); ' a = b ' -> ('a','b'); 'a==b' -> ('a','=b'); 'a = b = c' -> ('a','b = c'); 'a=' -> ('a',''); 'q = "x"' -> ('q','x'); "q = 'x'" -> ('q','x'); 'q = "x\'' -> ('q','"x\''); 'q = "' -> ('q','"'); "q = ''" -> ('q',''); 'q = " spaced "' -> ('q',' spaced '); 'k e y = v' -> ('k e y','v'); 'u = "a" "b"' -> ('u','a" "b').
2. parse_line raises ValueError for '', 'novalue', ' = v', '   ', '=' and '\t= 1'.
3. parse behaviour unchanged: comments ('#' or ';' as the first non-blank character), blank lines and Windows line endings are handled as before; later duplicate keys win; parse('') == {}; parse('k = v') == {'k': 'v'}.
4. parse raises ValueError for a malformed line anywhere in the text and TypeError for non-string input (None, 3, a list, bytes).
5. kvparse.parser._is_ignorable exists, returns True for '   # c', '' and '\t; c', and False for 'a = 1' and 'a = # not a comment'.
6. The source of parse_line contains no 'while' loop and uses str.partition.
7. The existing tests in tests/ pass unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -8,34 +8,22 @@
     quotes loses the quotes (nothing inside the quotes is changed). Raises ValueError for a line without '=' or with an
     empty key.
     """
-    i = 0
-    n = len(line)
-    key_chars = []
-    found = False
-    while i < n:
-        c = line[i]
-        if c == "=":
-            found = True
-            i += 1
-            break
-        key_chars.append(c)
-        i += 1
-    if not found:
+    key, separator, value = line.partition("=")
+    if not separator:
         raise ValueError("expected 'key = value', got %r" % (line,))
-    key = "".join(key_chars).strip()
+    key = key.strip()
     if key == "":
         raise ValueError("empty key in %r" % (line,))
-    value_chars = []
-    while i < n:
-        value_chars.append(line[i])
-        i += 1
-    value = "".join(value_chars).strip()
-    if len(value) >= 2:
-        first = value[0]
-        last = value[len(value) - 1]
-        if (first == '"' and last == '"') or (first == "'" and last == "'"):
-            value = value[1:len(value) - 1]
+    value = value.strip()
+    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
+        value = value[1:-1]
     return key, value
+
+
+def _is_ignorable(line) -> bool:
+    """Return whether a line is blank or begins with a comment marker."""
+    stripped = line.strip()
+    return stripped == "" or stripped.startswith(("#", ";"))
 
 
 def parse(text):
@@ -45,12 +33,7 @@
         raise TypeError("text must be a str")
     result = {}
     for raw in text.splitlines():
-        stripped = raw.strip()
-        if stripped == "":
-            continue
-        if stripped[0] == "#":
-            continue
-        if stripped[0] == ";":
+        if _is_ignorable(raw):
             continue
         key, value = parse_line(raw)
         result[key] = value
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
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10075 | 98 | 7168 | - | 24.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 21482 | 739 | 10496 | - | 75.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11046 | 125 | 7168 | - | 33.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11252 | 462 | 7168 | - | 25.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 11720 | 86 | 7168 | - | 92.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 11896 | 619 | 7168 | - | 75.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 12415 | 114 | 7168 | - | 41.4s | ok |

Model calls: 7 (0 failed, 0 malformed); tokens in/out/cached 89886/2243/53504; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14a73-77af-712a-93fa-5ac847c7dfeb | SUCCESS | 0 | 0.763s | retained | off | 0.00284683 |
| impl-tests-5 | 01a14a77-61ea-70cf-b13b-c86a2d04f667 | SUCCESS | 0 | 0.896s | disposable | off | 0.0028231899999999997 |
| impl-python-6 | 01a14a78-9807-77dd-ae89-240b10668fa3 | SUCCESS | 0 | 0.537s | disposable | off | 0.00122867 |

Sandbox operations: 3, total guest duration 2.196s, retained images ['362b9181-cf4e-45d9-b45b-81e8ca8a478d'].

## 11. Limitations of this bundle
- Profile 'eval-baseline-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
