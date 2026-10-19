# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: NEEDS HUMAN**  
Run `kvparse-refactor-001-attest-a2-20261017T175533783849Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:55:33.784006+00:00, finished 2026-10-17T17:56:58.596648+00:00.

**Hold this patch.** 1 of the 32 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request.

Key evidence (E1): test_parse_line_quote_only: Tuples differ: ('q', '') != ('q', '"') (the test's first argument against its second)



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: child process nonzero exit: test_parse_line_quote_only exit 1; drift audit unavailable: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 1 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- The drift audit judged the work misaligned with the request (audit call failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried; E5).

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
| E1 | Sealed tests, written before the patch | FAIL | bound | 6 of 32 failed on the unmodified base; 31 of 32 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | FAIL | model | audit call failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `dd6da55f-e207-4da8-9f95-6895caef1004`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py to replace the manual index loops in parse_line with str.partition, stripping, and quote removal, while preserving all existing behavior for string inputs. Additionally, extract the logic for detecting ignorable lines (blank, comment starting with '#' or ';') into a private module-level function _is_ignorable and use it in parse. The public functions parse and parse_line must remain exported and behave identically for all string inputs, including same return values, same exception types (TypeError for non-string input to parse, ValueError for malformed lines), duplicate key handling, and quote stripping rules. The existing test suite must continue to pass unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_line | parse_line(line: str) -> tuple[str, str] | Splits the input line at the first '=' character using str.partition. The key is the part before '=', stripped of surrounding whitespace. The value is the part  | ValueError: raised when the line contains no '=' character, or when the stripped key is empty. |
| parse | parse(text: str) -> dict[str, str] | Parses the input text into a dictionary. The text is split into lines (using splitlines). For each line, if _is_ignorable(line) returns True, the line is skippe | TypeError: raised when text is not a string.; ValueError: raised when any non-ignorable line causes parse_line to raise ValueError (i.e., malformed line). |

Acceptance criteria:
1. 1. parse_line('a=b') returns ('a', 'b').
2. 2. parse_line(' a = b ') returns ('a', 'b').
3. 3. parse_line('a==b') returns ('a', '=b').
4. 4. parse_line('a = b = c') returns ('a', 'b = c').
5. 5. parse_line('a=') returns ('a', '').
6. 6. parse_line('q = "x"') returns ('q', 'x').
7. 7. parse_line("q = 'x'") returns ('q', 'x').
8. 8. parse_line('q = "x\'') returns ('q', '"x\'').
9. 9. parse_line('q = "') returns ('q', '"').
10. 10. parse_line("q = ''") returns ('q', '').
11. 11. parse_line('q = " spaced "') returns ('q', ' spaced ').
12. 12. parse_line('k e y = v') returns ('k e y', 'v').
13. 13. parse_line('u = "a" "b"') returns ('u', 'a" "b').
14. 14. parse_line raises ValueError for empty string ''.
15. 15. parse_line raises ValueError for 'novalue' (no '=').
16. 16. parse_line raises ValueError for ' = v' (empty key after stripping).
17. 17. parse_line raises ValueError for '   ' (only whitespace, no '=').
18. 18. parse_line raises ValueError for '=' (empty key).
19. 19. parse_line raises ValueError for '\t= 1' (key empty after stripping).
20. 20. parse('') returns {}.
21. 21. parse('k = v') returns {'k': 'v'}.
22. 22. parse('a = 1\nb=2\n') returns {'a': '1', 'b': '2'}.
23. 23. parse('# comment\n\n; other\nname = x\n') returns {'name': 'x'} (comments and blank lines ignored).
24. 24. parse('title = "Hello World"\n') returns {'title': 'Hello World'} (quotes removed).
25. 25. parse("title = 'single'\n") returns {'title': 'single'} (single quotes removed).
26. 26. parse raises ValueError for 'novalue\n' (malformed line).
27. 27. parse raises TypeError for non-string input (e.g., None, 3, [], b'bytes').
28. 28. _is_ignorable('   # c') returns True.
29. 29. _is_ignorable('') returns True.
30. 30. _is_ignorable('\t; c') returns True.
31. 31. _is_ignorable('a = 1') returns False.
32. 32. _is_ignorable('a = # not a comment') returns False.
33. 33. parse_line contains no 'while' loop and uses str.partition.
34. 34. The existing test suite (tests/test_parser.py) passes without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `6986ed0be86a7b409a9762d4307026e461c500a42f1b6f4dbac5ce14ee9d354e`, 32 test methods, sealed at 2026-10-17T17:56:06.427559+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (6 of 32 methods: ERROR 5, FAIL 1): 6 of 32 methods failing, 26 passing; operation `01a14b01-a744-7660-aca2-ec078edad091`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestKVParseAcceptance.test_is_ignorable_blank | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_is_ignorable_comment_hash | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_is_ignorable_comment_semicolon | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_is_ignorable_hash_not_first_nonblank | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_is_ignorable_not_comment | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_empty_text | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_ignores_comments_and_blanks | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_a_eq_b | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_double_eq | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_empty_key_after_strip_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_empty_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_eq_with_empty_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_key_with_spaces | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_multiple_eq | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_multiple_quoted_parts | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_no_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_only_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_only_whitespace_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_quote_only | FAIL (1 ev) | FAIL (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_quote_with_escape_inside | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_quoted_double | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_quoted_single | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_single_quote_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_spaced_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_spaces_around_eq | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_line_tab_then_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_malformed_line_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_multiple_lines | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_removes_double_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_removes_single_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_simple_kv | ok (1 ev) | ok (1 ev) |
| test_sealed.TestKVParseAcceptance.test_parse_type_error_non_string | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -1,4 +1,10 @@
 """A small key = value configuration parser."""
+
+
+def _is_ignorable(line):
+    """Return True if line is blank or a comment (starting with # or ; after stripping)."""
+    stripped = line.strip()
+    return not stripped or stripped[0] in '#;'
 
 
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
+    key, sep, value = line.partition('=')
+    if not sep:
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
+    value = value.strip()
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (13 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (1 of 32 methods: FAIL 1). Operation `01a14b02-3fbd-719f-a553-ee77010923fe`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14b02-6cd0-72bc-b5e4-e78a2b23ca7b`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_parse_line_quote_only exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | FAIL | model | E5 | audit call failed: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: sealed_binding, drift_audit, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
- E1 `test_parse_line_quote_only`: FAIL; AssertionError: Tuples differ: ('q', '') != ('q', '"'); first `Tuples differ: ('q', '')` vs second `('q', '"')` (the test's argument order decides which is the actual value)

## 8. E5 Drift audit
Drift audit unavailable: inference outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); not retried



## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 2046 | 2522 | 0 | 0.009612 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2497 | 1545 | 0 | 0.002140 | 8.4s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 2117 | 97 | 0 | 0.000722 | 2.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2671 | 2490 | 0 | 0.003042 | 13.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2816 | 133 | 0 | 0.000964 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3296 | 109 | 0 | 0.001087 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3481 | 148 | 0 | 0.001177 | 3.2s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | - | - | - | - | 5.0s | error |

Model calls: 8 (1 failed, 0 malformed); tokens in/out/cached 18924/7044/0; USD: 0.018744.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14b01-563a-772c-91a7-25f626897110 | SUCCESS | 0 | 0.751s | retained | off | 0.00284027 |
| red-1 | 01a14b01-a744-7660-aca2-ec078edad091 | SUCCESS | 0 | 6.617s | disposable | off | 0.05748457999999999 |
| impl-tests-4 | 01a14b02-249f-77cf-83a9-3ef0cd5c2907 | SUCCESS | 0 | 0.748s | disposable | off | 0.0028740199999999997 |
| verify | 01a14b02-3fbd-719f-a553-ee77010923fe | SUCCESS | 0 | 6.595s | disposable | off | 0.05722867 |
| existing | 01a14b02-6cd0-72bc-b5e4-e78a2b23ca7b | SUCCESS | 0 | 1.806s | disposable | off | 0.01211576 |

Sandbox operations: 5, total guest duration 16.517s, retained images ['dd6da55f-e207-4da8-9f95-6895caef1004'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
