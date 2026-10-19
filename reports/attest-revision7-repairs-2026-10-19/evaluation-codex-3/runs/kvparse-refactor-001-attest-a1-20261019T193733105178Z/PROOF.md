# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: NEEDS HUMAN**  
Run `kvparse-refactor-001-attest-a1-20261019T193733105178Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T19:37:33.106462+00:00, finished 2026-10-19T19:44:37.809121+00:00.

**Hold this patch.** 1 of the 25 sealed acceptance tests fail on the candidate because the candidate's behaviour contradicts the test written before the patch (an assertion failed or an exception was raised; neither the exception's type nor its frame tells the test from the candidate). The arbiter classified the failing test(s) as defective and its corrected tests pass on the candidate and still fail on the unmodified base. A sealed test is the pre-registered acceptance criterion, so Attest never overrides it on a model's judgement: the hold stands and the arbiter's view, the original test and the corrected test are all recorded for you (E6).

Key evidence (E6): 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded)



What to do: Compare the original sealed test with the arbiter's correction and the contract; decide which encodes the requirement. If the correction is right, accept the patch on that basis and tighten the task statement so the next sealer reads it the same way.

Reasons: child process nonzero exit: test_assignment_lines_are_not_ignorable exit 1
Warnings: arbitration (validated corrections re-run their gates): 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded)

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 1 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 3 of 25 failed on the unmodified base; 24 of 25 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `086031e6-5785-4c3a-86c8-8cfd6d07c8c6`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.8.0 revision `68e9de49df5b22b8` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision7-repairs-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; a request that was never sent (its connection, proxy tunnel or TLS handshake failed before any byte of it was written) sent again at most 2 times after 2/6 s, each attempt recorded; transport-uncertain failures (the request was written) never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its existing string-input behavior: replace parse_line's manual index loops with partitioning at the first '=' and extract blank/comment detection into a module-level _is_ignorable helper used by parse. Preserve whitespace stripping, removal of exactly one matching outer quote pair, malformed-line errors, line splitting, duplicate-key handling, and package exports. Leave existing tests unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a str argument, partition at the first '=' using str.partition. Strip both resulting key and value with str.strip(). Return a two-element tuple of strings.  | ValueError when the string contains no '='.; ValueError when the key before the first '=' is empty after stripping.; Exception messages are unspecified.; Behavi |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Accept str input and return a dict of string keys to string values. Iterate over text.splitlines() in order, skip lines classified as ignorable by _is_ignorable | TypeError when isinstance(text, str) is false, including None, integers, lists, and bytes.; ValueError when any non-ignorable line is malformed according to par |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper for str lines. Return True exactly when line.strip() is empty or starts with '#' or ';'; otherwise return False. Return a bool. This helper  | Behavior for non-string arguments is unspecified. |

Acceptance criteria:
AC1. 1. parse_line uses str.partition with '=' to separate at the first delimiter, contains no while loop, and replaces the manual character-accumulation/index loops.
AC2. 2. parse_line('a=b') == ('a', 'b'); parse_line(' a = b ') == ('a', 'b'); parse_line('a==b') == ('a', '=b'); parse_line('a = b = c') == ('a', 'b = c'); parse_line('a=') == ('a', '').
AC3. 3. parse_line('k e y = v') == ('k e y', 'v'). Surrounding whitespace follows str.strip() semantics, including Unicode whitespace; interior key and unquoted-value characters remain unchanged.
AC4. 4. parse_line('q = "x"') == ('q', 'x'); parse_line("q = 'x'") == ('q', 'x'); parse_line("q = ''") == ('q', ''); parse_line('q = ""') == ('q', '').
AC5. 5. parse_line('q = "x\'') == ('q', '"x\''); parse_line('q = "') == ('q', '"'); a lone single quote is likewise retained. Unmatched or mismatched outer quotes remain unchanged.
AC6. 6. parse_line('q = " spaced "') == ('q', ' spaced '); parse_line('u = "a" "b"') == ('u', 'a" "b'). Remove exactly one outer matching pair, with no recursive unquoting, escape decoding, or interior whitespace stripping.
AC7. 7. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1'. More generally, a str line is malformed exactly when it lacks '=' or its stripped key is empty.
AC8. 8. _is_ignorable exists at module scope and returns True for '', whitespace-only lines, '   # c', and '\t; c'; it returns False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'. Its classification uses str.strip() semantics.
AC9. 9. parse uses _is_ignorable to classify lines. parse('') == {}; parse('k = v') == {'k': 'v'}; text consisting only of blank lines and comments returns {}.
AC10. 10. parse('# comment\r\n\r\n; other\r\nname = x\r\n') == {'name': 'x'}. Preserve text.splitlines() behavior for all recognized line boundaries and trailing line breaks.
AC11. 11. parse('a=1\nb=2\n a =3') == {'a': '3', 'b': '2'}, with key iteration order ['a', 'b']. Duplicate keys are compared after stripping and later values win.
AC12. 12. Comment markers are significant only at the beginning of a stripped line in parse: parse('a = # text\nb = ; text') == {'a': '# text', 'b': '; text'}. parse_line('#=v') == ('#', 'v'), while parse('#=v') == {}.
AC13. 13. parse raises ValueError for a malformed non-ignorable line at the beginning, middle, or end of otherwise valid text, including missing delimiters and empty stripped keys.
AC14. 14. parse raises TypeError for None, 3, a list, and bytes, preserving the existing isinstance(text, str) input guard.
AC15. 15. For every str input, preserve the original functions' returned string contents and exception conditions under the specified semantics. Exception messages are not asserted, and parse_line with non-string arguments is not tested.
AC16. 16. Both 'from kvparse import parse, parse_line' and imports from kvparse.parser continue to work. All existing tests in tests/ pass without modifications.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. For plain str inputs, partitioning at the first '=' reproduces the existing loops exactly; stripping, validation, and quote removal can remain equivalent. Extracting the existing ignorable-line checks preserves parse behavior, and all requirements can be satisfied within kvparse/** without changing exports or tests. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `f72a30972b8188c2608c82d2974e768b17f73b3a7e1819b63c83d8b7e491f0f2`, 25 test methods, sealed at 2026-10-19T19:40:53.486954+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 25 methods: ERROR 3): 3 of 25 methods failing, 22 passing; operation `01a155ad-a42b-709a-ab50-f4a60edd0f58`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIgnorableHelper.test_assignment_lines_are_not_ignorable | ERROR (1 ev) | FAIL (1 ev) |
| test_sealed.TestIgnorableHelper.test_blank_and_comment_lines_are_ignorable | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_all_recognized_line_boundaries_split_assignments | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_blank_and_comment_lines_are_skipped | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_comment_markers_in_values_are_significant | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_duplicate_stripped_keys_overwrite_without_moving | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_empty_text_returns_empty_dict | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_malformed_lines_at_each_position_raise_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_non_string_inputs_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_package_exports_match_parser_module | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_agrees_with_parse_line_on_special_value_characters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_uses_module_ignorable_helper | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_windows_line_endings_and_trailing_break | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_basic_key_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_comment_like_line_is_valid_for_parse_line_when_it_has_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_stripped_key_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_exactly_one_quote_pair_is_removed_without_changing_interior | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_first_equals_separates_key_and_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_key_strips_surrounding_unicode_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_lone_quotes_are_retained | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_matching_outer_quotes_are_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_mismatched_quotes_are_retained | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_missing_delimiter_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_quoted_escapes_are_not_decoded | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_unquoted_value_strips_only_surrounding_whitespace | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

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
-    if key == "":
+    key = key.strip()
+    if not key:
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
+    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
+        value = value[1:-1]
     return key, value
+
+
+def _is_ignorable(line):
+    """Return whether a line is blank or begins with a comment marker."""
+    stripped = line.strip()
+    return not stripped or stripped.startswith(("#", ";"))
 
 
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (14 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (1 of 25 methods: FAIL 1). Operation `01a155b0-4a46-76b4-aeed-3ec32f9761a7`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a155b0-7c70-70c5-a257-3df7fb0150d2`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_assignment_lines_are_not_ignorable exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.





### Counterexamples
- E1 `test_assignment_lines_are_not_ignorable`: FAIL; AssertionError: True is not False; arbiter: Defective test, by the arbiter; contract basis: _is_ignorable returns True exactly when line.strip() is empty or starts with '#' or ';'.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fulfills both requested refactors: `line.partition("=")` replaces all manual loops, matching quotes are removed with `value[1:-1]`, and parse calls the module-level `_is_ignorable(raw)` helper. String-input behavior, input guarding, duplicate handling, and exports remain unchanged; no tests were modified, and the observed test run reports all four existing tests passing.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
1 failing sealed test(s) classified as test defects and the correction was validated by execution, but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the hold stands for a human (the arbiter's view and the corrected tests are recorded) (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_assignment_lines_are_not_ignorable | test_defect | The string ' #=v\nvalue' starts with '#' after stripping, so the helper must return True. The embedded newline does not change that classifi | _is_ignorable returns True exactly when line.strip() is empty or starts with '#' or ';'. |

- `sealed` corrected re-run: candidate OK (25 of 25 methods, each in its own process); base FAILED (3 of 25 methods: ERROR 3); validated=False; sealed assertion or exception failure: never overridden, the hold stands

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11096 | 1548 | 0 | - | 65.7s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13491 | 116 | 7552 | - | 17.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11486 | 3422 | 0 | - | 54.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11052 | 90 | 7168 | - | 20.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11594 | 627 | 0 | - | 23.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11718 | 102 | 7168 | - | 19.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11890 | 155 | 7168 | - | 17.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12052 | 122 | 7168 | - | 17.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12509 | 126 | 7168 | - | 16.6s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12275 | 173 | 0 | - | 18.1s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-sealed | medium | 14267 | 1937 | 0 | - | 43.2s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 133430/8418/43392; Inference USD: n/a (development gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a155ab-70cb-719e-9030-6ed5fe5a0434 | SUCCESS | 0 | 0.813s | retained | off | 0.00285224 |
| red-1 | 01a155ad-a42b-709a-ab50-f4a60edd0f58 | SUCCESS | 0 | 9.876s | disposable | off | 0.08406012000000002 |
| impl-tests-3 | 01a155af-704e-77d2-bb83-5bd0623a7051 | SUCCESS | 0 | 0.812s | disposable | off | 0.0028408299999999995 |
| verify | 01a155b0-4a46-76b4-aeed-3ec32f9761a7 | SUCCESS | 0 | 9.244s | disposable | off | 0.08190556 |
| existing | 01a155b0-7c70-70c5-a257-3df7fb0150d2 | SUCCESS | 0 | 1.869s | disposable | off | 0.012103810000000001 |
| arbitrate-sealed-candidate | 01a155b1-839a-77d9-a310-c1c3208af840 | SUCCESS | 0 | 9.36s | disposable | off | 0.08219455 |
| arbitrate-sealed-base | 01a155b1-b363-712a-8fdc-689ebba7c41a | SUCCESS | 0 | 9.276s | disposable | off | 0.08195005000000001 |

Sandbox operations: 7, total guest duration 41.25s, retained images ['086031e6-5785-4c3a-86c8-8cfd6d07c8c6'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
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
