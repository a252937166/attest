# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: NEEDS HUMAN**  
Run `kvparse-refactor-001-attest-a1-20261017T175247088355Z` · profile `eval-attest-a1` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-17T17:52:47.088629+00:00, finished 2026-10-17T17:55:26.051972+00:00.

**Hold this patch.** Tests written after the patch fail on the candidate and were not arbitrated, so each failure is still an open question: a bug in the patch, a defective test or a contract gap.

Key evidence (E3): unusable: the module has a syntax error: expected '(' (test_breaker.py, line 19)



What to do: Read each failing test and classify it yourself; the bundle keeps the test source and the captured output. Fix the patch or the task statement accordingly, then run again.

Reasons: model-written adversarial tests could not be produced: the module has a syntax error: expected '(' (test_breaker.py, line 19); rerun the breaker stage or review manually


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 33 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 6 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 8 of 8 one-line mutants of the changed lines were caught by the sealed tests (E2).
- The tests written after the patch could not be used: unusable: the module has a syntax error: expected '(' (test_breaker.py, line 19) (E3).
- A model audit found the work aligned with the request (score 0.0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 27 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 6 of 33 failed on the unmodified base; 33 of 33 pass on the candidate |
| E2 | Mutation check | pass | bound | 8 of 8 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | unusable: the module has a syntax error: expected '(' (test_breaker.py, line 19) |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c1261d13-9365-4f2f-834e-a24b005fba63`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `166cdcbd46a74cd0` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py to replace the manual index loops in parse_line with str.partition, strip key and value, raise ValueError for missing '=' or empty key, and strip one pair of matching surrounding quotes from values of length >=2. Extract the ignorable-line detection into a module-level function _is_ignorable that returns True for empty/whitespace-only lines or lines whose first non-whitespace character is '#' or ';', and make parse use it. All observable behavior of parse and parse_line for string inputs must remain identical, including exception types and duplicate-key handling. The existing test suite must continue to pass unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_line | parse_line(line: str) -> tuple[str, str] | Splits the input line at the first '=' character using str.partition. The key is the part before '=', stripped of surrounding whitespace. The value is the part  | ValueError: raised when the line contains no '=' character.; ValueError: raised when the stripped key is empty. |
| parse | parse(text: str) -> dict[str, str] | Splits the input text into lines using str.splitlines. For each line, if _is_ignorable(line) returns True, the line is skipped. Otherwise, parse_line(line) is c | TypeError: raised when text is not a str.; ValueError: raised when any non-ignorable line is malformed (propagated from parse_line). |
| _is_ignorable | _is_ignorable(line: str) -> bool | Returns True if the stripped line (line.strip()) is empty or its first character is '#' or ';'. Returns False otherwise. This function is module-private and onl |  |

Acceptance criteria:
1. parse_line('a=b') returns ('a', 'b').
2. parse_line(' a = b ') returns ('a', 'b').
3. parse_line('a==b') returns ('a', '=b').
4. parse_line('a = b = c') returns ('a', 'b = c').
5. parse_line('a=') returns ('a', '').
6. parse_line('q = "x"') returns ('q', 'x').
7. parse_line("q = 'x'") returns ('q', 'x').
8. parse_line('q = "x\'') returns ('q', '"x\'').
9. parse_line('q = "') returns ('q', '"').
10. parse_line("q = ''") returns ('q', '').
11. parse_line('q = " spaced "') returns ('q', ' spaced ').
12. parse_line('k e y = v') returns ('k e y', 'v').
13. parse_line('u = "a" "b"') returns ('u', 'a" "b').
14. parse_line raises ValueError for empty string ''.
15. parse_line raises ValueError for 'novalue' (no '=').
16. parse_line raises ValueError for ' = v' (empty key).
17. parse_line raises ValueError for '   ' (whitespace only, no '=').
18. parse_line raises ValueError for '=' (empty key).
19. parse_line raises ValueError for '\t= 1' (empty key after stripping).
20. parse('') returns {}.
21. parse('k = v') returns {'k': 'v'}.
22. parse('a = 1\nb=2\n') returns {'a': '1', 'b': '2'}.
23. parse('# comment\n\n; other\nname = x\n') returns {'name': 'x'}.
24. parse_line('title = "Hello World"') returns ('title', 'Hello World').
25. parse_line("title = 'single'") returns ('title', 'single').
26. parse raises ValueError for 'novalue\n' (malformed line).
27. parse raises TypeError for None, 3, a list, and bytes inputs.
28. _is_ignorable('   # c') returns True.
29. _is_ignorable('') returns True.
30. _is_ignorable('\t; c') returns True.
31. _is_ignorable('a = 1') returns False.
32. _is_ignorable('a = # not a comment') returns False.
33. The source code of parse_line contains no 'while' loop and uses str.partition.
34. The existing test suite in tests/ passes without modification.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `3641168ddaa8ae1db1bde3c28608ab09d053f07d6795142375bf3ca20fa574e8`, 33 test methods, sealed at 2026-10-17T17:53:53.979758+00:00 by `nvidia/nemotron-3-super-120b-a12b`; attempts: 3.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (6 of 33 methods: ERROR 6): 6 of 33 methods failing, 27 passing; operation `01a14aff-a2de-7327-9fed-3579834365dc`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedAcceptance.test_is_ignorable_hash_comment | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_is_ignorable_hash_not_comment | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_is_ignorable_not_ignorable | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_is_ignorable_semicolon_comment | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_is_ignorable_spaces | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_is_ignorable_whitespace | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_empty_text | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_ignores_comments_and_blanks | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_basic | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_double_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_empty_key_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_empty_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_empty_string_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_empty_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_extra_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_first_eq | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_key_with_spaces | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_multiple_eq | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_no_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_only_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_quote_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_quotes_with_inner_quote | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_single_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_spaced_inside_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_spaces | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_tab_equal_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_title_double_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_title_single_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_line_whitespace_only_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_malformed_line_raises | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_multiple_lines | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_simple | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedAcceptance.test_parse_type_error_nonstr | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -1,4 +1,11 @@
 """A small key = value configuration parser."""
+
+
+def _is_ignorable(line):
+    stripped = line.strip()
+    if not stripped:
+        return True
+    return stripped[0] in '#;'
 
 
 def parse_line(line):
@@ -8,33 +15,18 @@
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
+    if not sep:
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
 
 
@@ -45,12 +37,7 @@
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (14 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (33 of 33 methods, each in its own process). Operation `01a14b00-3c4f-7084-becf-a7832ad61a77`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14b00-6402-764a-a6f9-fc2827b02500`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 8 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | the module has a syntax error: expected '(' (test_breaker.py, line 19) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 8 generated, 8 evaluated: 8 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-aa0792e405 | kvparse/parser.py | 6 | remove `not` | killed | test_sealed.TestSealedAcceptance.test_parse_simple, test_sealed.TestSealedAcceptance.test_parse_multiple_lines, test_sea | 01a14b00-a53f-754e-b587-7ee32625c1a9 |
| m02-0581c731b2 | kvparse/parser.py | 7 | True -> False | killed | test_sealed.TestSealedAcceptance.test_parse_ignores_comments_and_blanks, test_sealed.TestSealedAcceptance.test_is_ignora | 01a14b00-a542-72a8-b9da-b69a43beaf6c |
| m03-fac4ea3cfa | kvparse/parser.py | 8 | 0 -> 1 | killed | test_sealed.TestSealedAcceptance.test_parse_ignores_comments_and_blanks, test_sealed.TestSealedAcceptance.test_is_ignora | 01a14b00-a541-7673-9dcb-83e4d6588d22 |
| m04-f6a23f8184 | kvparse/parser.py | 8 | In -> NotIn | killed | test_sealed.TestSealedAcceptance.test_parse_simple, test_sealed.TestSealedAcceptance.test_parse_multiple_lines, test_sea | 01a14b00-a551-70bb-bd35-6f79aefecdd1 |
| m05-daf4a21971 | kvparse/parser.py | 19 | remove `not` | killed | test_sealed.TestSealedAcceptance.test_parse_line_basic, test_sealed.TestSealedAcceptance.test_parse_line_spaces, test_se | 01a14b00-a52d-7627-9397-e32495ae49e5 |
| m06-6a13393634 | kvparse/parser.py | 27 | 1 -> 2 | killed | test_sealed.TestSealedAcceptance.test_parse_line_double_quotes, test_sealed.TestSealedAcceptance.test_parse_line_single_ | 01a14b00-a50f-7063-867c-c766ac6cfe06 |
| m07-2a22f3690f | kvparse/parser.py | 29 | 1 -> 2 | killed | test_sealed.TestSealedAcceptance.test_parse_line_double_quotes, test_sealed.TestSealedAcceptance.test_parse_line_single_ | 01a14b00-b7e5-7160-af21-83b3f31ec40b |
| m08-66711c6922 | kvparse/parser.py | 29 | 1 -> 2 | killed | test_sealed.TestSealedAcceptance.test_parse_line_double_quotes, test_sealed.TestSealedAcceptance.test_parse_line_single_ | 01a14b00-a4fb-7581-bc65-6e8d283da801 |

E3: model-written adversarial tests: unusable (the module has a syntax error: expected '(' (test_breaker.py, line 19)); the gate fails.



### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fully implements the requested refactoring: parse_line uses str.partition and has no while loop, and _is_ignorable is extracted and used by parse. All tests pass, confirming behavioral equivalence.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 2046 | 2294 | 0 | 0.008928 | 7.7s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2445 | 1437 | 0 | 0.002027 | 6.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-2 | low | 2501 | 2204 | 0 | 0.002734 | 11.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-3 | low | 2490 | 2150 | 0 | 0.002682 | 11.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-1 | medium | 2014 | 110 | 0 | 0.000703 | 2.8s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-2 | medium | 2568 | 2225 | 0 | 0.002773 | 11.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-3 | medium | 2711 | 133 | 0 | 0.000933 | 3.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-4 | medium | 3168 | 326 | 0 | 0.001244 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | implement | implement-5 | medium | 3355 | 475 | 0 | 0.001434 | 4.5s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-1 | low | 2679 | 361 | 0 | 0.001129 | 4.0s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | break | break-tests-2 | low | 2739 | 977 | 0 | 0.001701 | 6.7s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | drift-audit | default | 2844 | 2857 | 0 | 0.011415 | 9.3s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 31560/15549/0; USD: 0.037703.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14afe-d93d-7017-97c3-a7e81cc6bb93 | SUCCESS | 0 | 0.736s | retained | off | 0.0028885300000000003 |
| red-2 | 01a14aff-4dee-73a9-bc36-801b696e05d9 | SUCCESS | 0 | 6.176s | disposable | off | 0.05381569 |
| red-3 | 01a14aff-a2de-7327-9fed-3579834365dc | SUCCESS | 0 | 6.831s | disposable | off | 0.05918114000000001 |
| impl-tests-4 | 01a14b00-1bea-7087-8928-79af0273b712 | SUCCESS | 0 | 0.758s | disposable | off | 0.0028309 |
| verify | 01a14b00-3c4f-7084-becf-a7832ad61a77 | SUCCESS | 0 | 6.699s | disposable | off | 0.058653040000000004 |
| existing | 01a14b00-6402-764a-a6f9-fc2827b02500 | SUCCESS | 0 | 1.775s | disposable | off | 0.01200622 |
| mutant-m01-aa0792e405 | 01a14b00-a53f-754e-b587-7ee32625c1a9 | SUCCESS | 0 | 6.563s | disposable | off | 0.055894110000000004 |
| mutant-m04-f6a23f8184 | 01a14b00-a551-70bb-bd35-6f79aefecdd1 | SUCCESS | 0 | 6.545s | disposable | off | 0.055859540000000006 |
| mutant-m02-0581c731b2 | 01a14b00-a542-72a8-b9da-b69a43beaf6c | SUCCESS | 0 | 6.545s | disposable | off | 0.055636899999999996 |
| mutant-m03-fac4ea3cfa | 01a14b00-a541-7673-9dcb-83e4d6588d22 | SUCCESS | 0 | 6.545s | disposable | off | 0.056004790000000006 |
| mutant-m06-6a13393634 | 01a14b00-a50f-7063-867c-c766ac6cfe06 | SUCCESS | 0 | 6.566s | disposable | off | 0.05646156 |
| mutant-m05-daf4a21971 | 01a14b00-a52d-7627-9397-e32495ae49e5 | SUCCESS | 0 | 6.546s | disposable | off | 0.056231989999999996 |
| mutant-m07-2a22f3690f | 01a14b00-b7e5-7160-af21-83b3f31ec40b | SUCCESS | 0 | 6.538s | disposable | off | 0.05638145 |
| mutant-m08-66711c6922 | 01a14b00-a4fb-7581-bc65-6e8d283da801 | SUCCESS | 0 | 6.333s | disposable | off | 0.05533627000000001 |

Sandbox operations: 14, total guest duration 75.156s, retained images ['c1261d13-9365-4f2f-834e-a24b005fba63'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
