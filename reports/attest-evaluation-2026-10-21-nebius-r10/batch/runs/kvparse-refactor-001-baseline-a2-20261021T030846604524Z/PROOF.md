# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: BASELINE**  
Run `kvparse-refactor-001-baseline-a2-20261021T030846604524Z` · profile `eval-baseline-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:08:46.606331+00:00, finished 2026-10-21T03:09:50.856938+00:00.

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
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `919b0fae-ca46-4db5-8065-ea35854912a4`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate False, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

(none)

Acceptance criteria:
AC1. parse_line behaviour unchanged: 'a=b' -> ('a','b'); ' a = b ' -> ('a','b'); 'a==b' -> ('a','=b'); 'a = b = c' -> ('a','b = c'); 'a=' -> ('a',''); 'q = "x"' -> ('q','x'); "q = 'x'" -> ('q','x'); 'q = "x\'' -> ('q','"x\''); 'q = "' -> ('q','"'); "q = ''" -> ('q',''); 'q = " spaced "' -> ('q',' spaced '); 'k e y = v' -> ('k e y','v'); 'u = "a" "b"' -> ('u','a" "b').
AC2. parse_line raises ValueError for '', 'novalue', ' = v', '   ', '=' and '\t= 1'.
AC3. parse behaviour unchanged: comments ('#' or ';' as the first non-blank character), blank lines and Windows line endings are handled as before; later duplicate keys win; parse('') == {}; parse('k = v') == {'k': 'v'}.
AC4. parse raises ValueError for a malformed line anywhere in the text and TypeError for non-string input (None, 3, a list, bytes).
AC5. kvparse.parser._is_ignorable exists, returns True for '   # c', '' and '\t; c', and False for 'a = 1' and 'a = # not a comment'.
AC6. The source of parse_line contains no 'while' loop and uses str.partition.
AC7. The existing tests in tests/ pass unchanged.
AC8. Unspecified, not to be tested: parse_line with a non-string argument.

## 2b. Contract audit (executed witnesses)
Not run (bundle predates the contract audit, or the run ended before the specification).

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


## 4. Candidate patch
1 changed path(s); scope check passed; 9 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -1,4 +1,10 @@
 """A small key = value configuration parser."""
+
+
+def _is_ignorable(line):
+    """Return True if line is empty or a comment (starts with # or ; after stripping)."""
+    stripped = line.strip()
+    return stripped == "" or stripped.startswith("#") or stripped.startswith(";")
 
 
 def parse_line(line):
@@ -8,33 +14,18 @@
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
+    head, sep, tail = line.partition('=')
+    if sep == '':
         raise ValueError("expected 'key = value', got %r" % (line,))
-    key = "".join(key_chars).strip()
+    key = head.strip()
     if key == "":
         raise ValueError("empty key in %r" % (line,))
-    value_chars = []
-    while i < n:
-        value_chars.append(line[i])
-        i += 1
-    value = "".join(value_chars).strip()
+    value = tail.strip()
     if len(value) >= 2:
         first = value[0]
-        last = value[len(value) - 1]
+        last = value[-1]
         if (first == '"' and last == '"') or (first == "'" and last == "'"):
-            value = value[1:len(value) - 1]
+            value = value[1:-1]
     return key, value
 
 
@@ -45,12 +36,7 @@
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
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 1649 | 103 | 0 | 0.000587 | 2.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2203 | 1018 | 0 | 0.001577 | 10.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2709 | 1606 | 0 | 0.002258 | 9.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 2880 | 443 | 0 | 0.001263 | 6.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3368 | 87 | 0 | 0.001089 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-6 | medium | 3548 | 688 | 0 | 0.001684 | 5.3s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-7 | medium | 3741 | 796 | 0 | 0.001839 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-8 | medium | 4153 | 179 | 0 | 0.001407 | 3.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-9 | medium | 4342 | 121 | 0 | 0.001412 | 2.6s | ok |

Model calls: 9 (0 failed, 0 malformed); tokens in/out/cached 28593/5041/0; Inference USD: 0.013116.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c6e-ea8b-7490-983e-fc4101c1a4dd | SUCCESS | 0 | 0.862s | retained | off | 0.00286703 |
| impl-tests-5 | 01a15c6f-6f9a-7692-b32f-8e8cc8669e2e | SUCCESS | 0 | 0.856s | disposable | off | 0.0028628300000000002 |
| impl-python-7 | 01a15c6f-ae97-70ef-8e95-b06b3c4b9328 | SUCCESS | 0 | 0.97s | disposable | off | 0.0021289200000000003 |
| impl-tests-8 | 01a15c6f-c7c0-76c4-a9ae-232bc69a852d | SUCCESS | 0 | 0.91s | disposable | off | 0.00284114 |

Sandbox operations: 4, total guest duration 3.598s, retained images ['919b0fae-ca46-4db5-8065-ea35854912a4'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-baseline-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
