# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: NEEDS HUMAN**  
Run `kvparse-refactor-001-attest-a1-20261017T152250877046Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T15:22:50.878087+00:00, finished 2026-10-17T15:35:27.787068+00:00.

**Hold this patch.** A test written after the patch found an input the implementation handles wrongly. The arbiter classified it as an implementation bug, so this is a defect in the candidate, not in the test. The hold stands until a human decides.

Key evidence (E3): test_integer_keyed_mapping_preserves_indexed_input: ValueError: expected 'key = value', got {0: 'a', 1: '=', 2: 'b'}



What to do: Read the counterexample: input, actual result and the arbiter's contract basis. Fix the implementation and run the task again, or reject the patch.

Reasons: adversarial suite binding failed: child process nonzero exit: test_integer_keyed_mapping_preserves_indexed_input exit 1, test_mapping_insertion_order_does_not_change_indexed_input exit 1, test_mapping_missing_zero_preserves_key_error exit 1, test_mapping_noncharacter_key_preserves_type_error exit 1; model-written adversarial tests failed: 4 of 8 (test_breaker.BreakerTests.test_integer_keyed_mapping_preserves_indexed_input, test_breaker.BreakerTests.test_mapping_insertion_order_does_not_change_indexed_input, test_breaker.BreakerTests.test_mapping_missing_zero_preserves_key_error, test_breaker.BreakerTests.test_mapping_noncharacter_key_preserv); each failure is a bug or a contract disagreement to resolve
Warnings: drift audit: score 0.20, widened 1, unsupported claims 2; arbitration (advisory): 4 failing test(s) indicate a real implementation bug; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 32 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 4 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 4 test(s) written after the patch fail on the candidate (E3).
- A model audit found the work aligned with the request (score 0.2, narrowed (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 28 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 4 of 32 failed on the unmodified base; 32 of 32 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 4 of 8 pass; 4 failing: test_integer_keyed_mapping_preserves_indexed_input, test_mapping_insertion_order_does_not_change_indexed_input, test_mapping_missing_zero_preserves_key_error, test_mapping_noncharacter_key_preserves_t; binding FAILED |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.2, narrowed (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | 4 failing test(s) indicate a real implementation bug; human review required |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `e63b9851edc55942cd02c6d232d61876f55a85e01ace5c6da218c56b06d9b2ce`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `1b8a54e0-1413-466f-bdc4-ecc3ea864f73`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `36369c7b57230897` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-freeze-2026-10-17/evaluation-newtasks-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py to split string lines at the first '=' using str.partition, remove the hand-written index loops from parse_line, and extract blank/comment-line detection into _is_ignorable(line) -> bool, which parse must use. Preserve existing parsing results and exception types, including whitespace handling, matching outer quote removal, duplicate-key precedence, and package exports. Exception messages may change; existing tests must remain unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line | parse_line(line) | For string input, partition at the first '=' and strip both resulting fields with Python's default str.strip semantics. Return a two-string tuple (key, value).  | ValueError: a string line contains no '='.; ValueError: the key before the first '=' is empty after stripping.; For non-string inputs, preserve baseline outcome |
| kvparse.parser.parse | parse(text) | Accept input satisfying isinstance(text, str). Iterate over text.splitlines() in order. Use _is_ignorable on each line to skip blank lines and full-line comment | TypeError: text is not an instance of str, including None, integers, lists, and bytes.; ValueError: any non-ignored line is malformed according to parse_line; p |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | For a string line, return True exactly when line.strip() is empty or starts with '#' or ';'; otherwise return False. This is a module-level helper accessible fr | Non-string inputs are outside this new helper's specified input domain; no particular exception behavior is required. |
| kvparse package exports | from kvparse import parse, parse_line | Both imports continue to resolve to the corresponding functions in kvparse.parser. |  |

Acceptance criteria:
1. 1. parse_line uses str.partition with '=' to split string input at the first separator. Its source contains no while statement and no hand-written index loops for extracting the key or value.
2. 2. parse_line('a=b') returns ('a', 'b'); parse_line(' a = b ') returns ('a', 'b'); parse_line('a==b') returns ('a', '=b'); parse_line('a = b = c') returns ('a', 'b = c'); parse_line('a=') returns ('a', '').
3. 3. parse_line('k e y = v') returns ('k e y', 'v'). Leading and trailing whitespace follows default str.strip semantics, including tabs and Unicode whitespace; interior key and unquoted value whitespace remains unchanged.
4. 4. parse_line('q = "x"') and parse_line("q = 'x'") both return ('q', 'x'); parse_line("q = ''") and parse_line('q = ""') both return ('q', '').
5. 5. parse_line('q = "x\'') returns ('q', '"x\''); parse_line('q = "') returns ('q', '"'); a lone single quote is also preserved.
6. 6. parse_line('q = " spaced "') returns ('q', ' spaced '); parse_line('u = "a" "b"') returns ('u', 'a" "b'). Remove only one matching outer quote pair, without recursively unquoting or interpreting escapes.
7. 7. Each of '', 'novalue', ' = v', '   ', '=', and '\t= 1' raises ValueError when passed to parse_line.
8. 8. parse_line does not ignore comments: '# c' raises ValueError, '#=v' returns ('#', 'v'), and 'a = # not a comment' returns ('a', '# not a comment').
9. 9. _is_ignorable is defined at module level with a bool return annotation. It returns True for '', whitespace-only strings, '   # c', and '\t; c'; it returns False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'.
10. 10. parse delegates line-ignore decisions to _is_ignorable and passes original non-ignored lines to parse_line. This integration is verifiable by source inspection or instrumentation.
11. 11. parse('') returns {}; parse('k = v') returns {'k': 'v'}; text consisting entirely of blank lines and full-line comments returns {}.
12. 12. parse preserves str.splitlines semantics, including LF, CRLF, lone CR, and other line boundaries recognized by str.splitlines. Leading whitespace before full-line '#' and ';' comments is accepted.
13. 13. parse('a=1\nb=2\na=3') returns {'a': '3', 'b': '2'}, with iteration order ['a', 'b']. Key comparison remains case-sensitive and uses the stripped key.
14. 14. A malformed non-ignored line at the beginning, middle, or end of otherwise valid text causes parse to raise ValueError. Malformed-looking content on a full-line comment is ignored.
15. 15. parse raises TypeError for None, 3, a list, and bytes, including empty bytes. Ordinary str subclasses remain accepted.
16. 16. The universal behavior-preservation requirement also covers legacy non-string parse_line inputs. Regression checks include None and 3 raising TypeError, b'a=b' raising ValueError, and ['a', '=', 'b'] and ('a', '=', 'b') returning ('a', 'b'). A direct partition rewrite must retain compatibility where needed.
17. 17. Both public functions remain importable from kvparse and kvparse.parser. All existing tests in tests/ pass without modification.
18. 18. Return values and exception types remain identical to the supplied baseline; exception-message text is excluded from equivalence requirements.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `4086562a25a5d744b3d31cd89b192019d73be6bc901e923a10c019689cd480fc`, 32 test methods, sealed at 2026-10-17T15:26:04.460170+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (4 of 32 methods: ERROR 4): 4 of 32 methods failing, 28 passing; operation `01a14a78-340f-7336-a162-0a3bc2b077fc`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIgnorableLines.test_helper_has_bool_return_annotation | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIgnorableLines.test_helper_keeps_assignments_with_comment_markers | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIgnorableLines.test_helper_recognizes_blank_and_full_line_comments | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_blank_lines_and_full_line_comments_are_skipped | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_empty_text_returns_empty_dict | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_inline_comment_markers_remain_values | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_invalid_text_types_raise_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_keys_are_stripped_and_case_sensitive | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_later_duplicate_wins_without_moving_key | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_malformed_line_at_any_position_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_package_exports_reference_parser_functions | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_delegates_ignore_decisions_to_helper | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_passes_original_non_ignored_line_to_parse_line | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_single_assignment | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_splitlines_boundaries | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_str_subclass_is_accepted | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_backslashes_are_not_interpreted | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_basic_assignment | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_comment_markers_are_ordinary_line_content | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_matching_quotes_are_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_stripped_key_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_value_is_allowed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_first_equals_is_the_separator | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_interior_whitespace_is_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_legacy_character_sequences | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_legacy_non_string_error_types | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_matching_single_and_double_quotes_are_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_missing_separator_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_only_one_outer_quote_pair_is_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_surrounding_whitespace_is_stripped | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_unmatched_and_lone_quotes_are_preserved | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_whitespace_inside_quotes_is_preserved | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -1,56 +1,52 @@
 """A small key = value configuration parser."""
+
+
+def _split_non_string_line(line):
+    """Keep the legacy sequence behavior of parse_line for non-string inputs."""
+    len(line)  # Preserve TypeError for inputs without a sequence length.
+    chars = list(line)
+    try:
+        separator = chars.index("=")
+    except ValueError:
+        raise ValueError("expected 'key = value', got %r" % (line,)) from None
+    return "".join(chars[:separator]), "".join(chars[separator + 1:])
 
 
 def parse_line(line):
     """Parse one `key = value` line into a (key, value) tuple.
 
-    Keys are stripped of surrounding whitespace; values are stripped, and a value wrapped in matching single or double
-    quotes loses the quotes (nothing inside the quotes is changed). Raises ValueError for a line without '=' or with an
-    empty key.
+    Keys and values are stripped of surrounding whitespace. A value wrapped
+    in matching single or double quotes loses exactly that outer quote pair.
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
-        raise ValueError("expected 'key = value', got %r" % (line,))
-    key = "".join(key_chars).strip()
+    if isinstance(line, str):
+        key, separator, value = str.partition(line, "=")
+        if not separator:
+            raise ValueError("expected 'key = value', got %r" % (line,))
+    else:
+        key, value = _split_non_string_line(line)
+
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
+    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
+        value = value[1:-1]
     return key, value
 
 
+def _is_ignorable(line) -> bool:
+    """Return whether a line is blank or a full-line comment."""
+    stripped = line.strip()
+    return not stripped or stripped.startswith(("#", ";"))
+
+
 def parse(text):
-    """Parse `text` into a dict. Blank lines and lines whose first non-blank character is '#' or ';' are ignored; later
-    duplicates of a key win. Raises TypeError for non-string input and ValueError for a malformed line."""
+    """Parse text into a dict, ignoring blank lines and full-line comments."""
     if not isinstance(text, str):
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (32 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (32 of 32 methods, each in its own process). Operation `01a14a7c-33c0-75de-ba3f-ca0babbf0535`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14a7c-eb72-762f-bed4-00e35770e774`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (4 of 8 methods: ERROR 4) |
| drift_audit | Drift audit | pass | model | E5 | score 0.2 (narrowed) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-f9aa2870a4 | kvparse/parser.py | 11 | Mod -> Sub | killed | test_sealed.TestParseLine.test_legacy_non_string_error_types | 01a14a7c-fc8a-76fa-b19b-5b5e99d2f914 |
| m02-6dece4f6eb | kvparse/parser.py | 11 | raise -> pass | killed | test_sealed.TestParseLine.test_legacy_non_string_error_types | 01a14a7c-fcec-773c-abe6-3ae829f4faf3 |
| m03-cedf74b5d0 | kvparse/parser.py | 12 | Add -> Sub | killed | test_sealed.TestParseLine.test_legacy_character_sequences | 01a14a7c-fc70-77d4-854e-67b860f81605 |
| m04-7bdb8d49a2 | kvparse/parser.py | 23 | remove `not` | killed | test_sealed.TestParseLine.test_basic_assignment, test_sealed.TestParseLine.test_first_equals_is_the_separator, test_seal | 01a14a7c-fc60-7770-b153-c9b8b8ba2035 |
| m05-7a894ec8a7 | kvparse/parser.py | 24 | raise -> pass | killed | test_sealed.TestParseLine.test_missing_separator_raises_value_error, test_sealed.TestParse.test_malformed_line_at_any_po | 01a14a7d-74f4-766f-b0df-913bc42fc596 |
| m06-ff4a80f768 | kvparse/parser.py | 32 | 2 -> 3 | killed | test_sealed.TestParseLine.test_empty_matching_quotes_are_removed | 01a14a7c-fc5a-76f6-a1ac-52d26402341b |
| m07-46252d695d | kvparse/parser.py | 32 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_single_and_double_quotes_are_removed, test_sealed.TestParseLine.test_whitespace_ | 01a14a7c-fc97-741e-b0ed-95cb2d93362d |
| m08-e9e66242b7 | kvparse/parser.py | 32 | Eq -> NotEq | killed | test_sealed.TestParseLine.test_matching_single_and_double_quotes_are_removed, test_sealed.TestParseLine.test_empty_match | 01a14a7c-fcd7-72a2-868f-d53412d1eda1 |
| m09-3e68feb7e5 | kvparse/parser.py | 32 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_single_and_double_quotes_are_removed, test_sealed.TestParseLine.test_whitespace_ | 01a14a7d-347a-7765-aca0-05522b4fa2ee |
| m10-444d052f24 | kvparse/parser.py | 32 | And -> Or | killed | test_sealed.TestParseLine.test_basic_assignment, test_sealed.TestParseLine.test_first_equals_is_the_separator, test_seal | 01a14a7d-374c-74e6-9e0e-35f9bb4b896e |
| m11-cd83456dbb | kvparse/parser.py | 33 | 1 -> 2 | killed | test_sealed.TestParseLine.test_matching_single_and_double_quotes_are_removed, test_sealed.TestParseLine.test_whitespace_ | 01a14a7d-37a0-71af-9795-66e146c986f9 |
| m12-222d2cf56c | kvparse/parser.py | 40 | remove `not` | killed | test_sealed.TestIgnorableLines.test_helper_recognizes_blank_and_full_line_comments, test_sealed.TestIgnorableLines.test_ | 01a14a7d-388e-70f7-8b27-1ab136f68852 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `90bd148ae495b3aea1863eb738604367652f98e05fbc78a8eafd048f065cf3d3`): FAILED (4 of 8 methods: ERROR 4); binding FAILED; operation `01a14a7e-70c4-7448-98a3-6da265ee4f03`. Notes: Targets legacy indexed mapping behavior and exception types, plus Unicode whitespace, uncommon line boundaries, and additional input types.

| Failing adversarial test | Outcome |
| --- | --- |
| test_integer_keyed_mapping_preserves_indexed_input | ERROR |
| test_mapping_insertion_order_does_not_change_indexed_input | ERROR |
| test_mapping_missing_zero_preserves_key_error | ERROR |
| test_mapping_noncharacter_key_preserves_type_error | ERROR |

### Counterexamples
- E3 `test_integer_keyed_mapping_preserves_indexed_input`: ERROR; ValueError: expected 'key = value', got {0: 'a', 1: '=', 2: 'b'}; arbiter: Implementation bug, by the arbiter; contract basis: The contract explicitly requires preserving baseline outcomes for non-string parse_line inputs; ordinary dictionaries are not excluded.
- E3 `test_mapping_insertion_order_does_not_change_indexed_input`: ERROR; ValueError: expected 'key = value', got {2: ' b ', 0: ' a ', 1: '='}; arbiter: Implementation bug, by the arbiter; contract basis: The universal behavior-preservation requirement covers legacy non-string inputs and their parsing results.
- E3 `test_mapping_missing_zero_preserves_key_error`: ERROR; ValueError: expected 'key = value', got {1: '=', 2: 'b'}; arbiter: Implementation bug, by the arbiter; contract basis: Baseline exception types for non-string parse_line inputs must be preserved; only exception messages are exempt.
- E3 `test_mapping_noncharacter_key_preserves_type_error`: ERROR; ValueError: expected 'key = value', got {0: 7, 1: '=', 2: 'b'}; arbiter: Implementation bug, by the arbiter; contract basis: The contract requires preserving baseline exception types for non-string parse_line inputs. This test uses a built-in dictionary without overridden behavior.

## 8. E5 Drift audit
Score 0.200 (narrowed; threshold 0.6). The diff implements partition-based string parsing and the required _is_ignorable integration, and the observed test output supports all four existing tests passing. It does not fully solve the task because the compatibility helper changes outcomes for some non-string inputs.

Scope narrowed: Legacy exception behavior is not fully preserved: _split_non_string_line joins both fields before checking the stripped key. For ['=', 1], the baseline raises ValueError for an empty key; the new return "".join(chars[:separator]), "".join(chars[separator + 1:]) raises TypeError first.  
Scope widened: Replacing indexed sequence access with chars = list(line) newly accepts some mappings. For {'a': 1, '=': 2, 'b': 3}, the baseline raises KeyError at line[0], whereas the new implementation returns ('a', 'b').  
Unsupported claims: "preserved legacy non-string behavior" — contradicted by the exception-order and mapping regressions.; "The refactor satisfies the contract" — the universal behavior-preservation requirement is violated despite the reported passing checks.

## 8b. E6 Arbitration of generated-test failures
4 failing test(s) indicate a real implementation bug; human review required (mode: advisory). Classifications: {'implementation_bug': 4, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_integer_keyed_mapping_preserves_indexed_input | implementation_bug | The baseline reads dictionary values at integer indices 0, 1, and 2 and returns ('a', 'b'). The candidate instead iterates dictionary keys a | The contract explicitly requires preserving baseline outcomes for non-string parse_line inputs; ordinary dictionaries are not excluded. |
| test_mapping_insertion_order_does_not_change_indexed_input | implementation_bug | The baseline accesses indices in numeric order regardless of dictionary insertion order, yielding fields ' a ' and ' b ', which strip to ('a | The universal behavior-preservation requirement covers legacy non-string inputs and their parsing results. |
| test_mapping_missing_zero_preserves_key_error | implementation_bug | The baseline first accesses line[0], which raises KeyError for this dictionary. The candidate raises ValueError instead. | Baseline exception types for non-string parse_line inputs must be preserved; only exception messages are exempt. |
| test_mapping_noncharacter_key_preserves_type_error | implementation_bug | The baseline collects integer 7 as the key content, finds '=' at index 1, and raises TypeError when joining the key content. The candidate i | The contract requires preserving baseline exception types for non-string parse_line inputs. This test uses a built-in dictionary without ove |

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11031 | 1762 | 0 | - | 99.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11379 | 3184 | 0 | - | 69.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10974 | 93 | 7168 | - | 32.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 23483 | 1431 | 18560 | - | 62.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11625 | 614 | 7168 | - | 29.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12125 | 99 | 7168 | - | 20.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12298 | 144 | 7168 | - | 27.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 26198 | 550 | 19840 | - | 34.5s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11973 | 2068 | 7040 | - | 46.1s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12586 | 361 | 0 | - | 88.6s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | 14037 | 510 | 0 | - | 75.2s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 157709/10816/74112; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14a75-8427-76af-b2cc-2cb1c5cf4801 | SUCCESS | 0 | 0.76s | retained | off | 0.0028536100000000003 |
| red-1 | 01a14a78-340f-7336-a162-0a3bc2b077fc | SUCCESS | 0 | 11.365s | disposable | off | 0.10271767000000001 |
| impl-python-3 | 01a14a7a-598a-73aa-a546-bbbd924eb7fb | SUCCESS | 0 | 0.669s | disposable | off | 0.00209998 |
| impl-tests-4 | 01a14a7a-b4ae-7438-90d8-95ef2b97ac81 | SUCCESS | 0 | 0.777s | disposable | off | 0.00285948 |
| verify | 01a14a7c-33c0-75de-ba3f-ca0babbf0535 | SUCCESS | 0 | 11.639s | disposable | off | 0.10358598000000001 |
| existing | 01a14a7c-eb72-762f-bed4-00e35770e774 | SUCCESS | 0 | 1.781s | disposable | off | 0.01204108 |
| mutant-m01-f9aa2870a4 | 01a14a7c-fc8a-76fa-b19b-5b5e99d2f914 | SUCCESS | 0 | 11.075s | disposable | off | 0.09873106000000001 |
| mutant-m03-cedf74b5d0 | 01a14a7c-fc70-77d4-854e-67b860f81605 | SUCCESS | 0 | 10.876s | disposable | off | 0.09679714 |
| mutant-m02-6dece4f6eb | 01a14a7c-fcec-773c-abe6-3ae829f4faf3 | SUCCESS | 0 | 10.836s | disposable | off | 0.09662632000000002 |
| mutant-m04-7bdb8d49a2 | 01a14a7c-fc60-7770-b153-c9b8b8ba2035 | SUCCESS | 0 | 11.152s | disposable | off | 0.09913857000000001 |
| mutant-m05-7a894ec8a7 | 01a14a7d-74f4-766f-b0df-913bc42fc596 | SUCCESS | 0 | 10.848s | disposable | off | 0.09746266 |
| mutant-m07-46252d695d | 01a14a7c-fc97-741e-b0ed-95cb2d93362d | SUCCESS | 0 | 10.834s | disposable | off | 0.09676486999999999 |
| mutant-m06-ff4a80f768 | 01a14a7c-fc5a-76f6-a1ac-52d26402341b | SUCCESS | 0 | 10.966s | disposable | off | 0.09754243 |
| mutant-m08-e9e66242b7 | 01a14a7c-fcd7-72a2-868f-d53412d1eda1 | SUCCESS | 0 | 10.98s | disposable | off | 0.09795797999999999 |
| mutant-m09-3e68feb7e5 | 01a14a7d-347a-7765-aca0-05522b4fa2ee | SUCCESS | 0 | 10.792s | disposable | off | 0.09689899999999999 |
| mutant-m10-444d052f24 | 01a14a7d-374c-74e6-9e0e-35f9bb4b896e | SUCCESS | 0 | 10.976s | disposable | off | 0.09734345999999999 |
| mutant-m11-cd83456dbb | 01a14a7d-37a0-71af-9795-66e146c986f9 | SUCCESS | 0 | 10.976s | disposable | off | 0.09720971 |
| mutant-m12-222d2cf56c | 01a14a7d-388e-70f7-8b27-1ab136f68852 | SUCCESS | 0 | 10.891s | disposable | off | 0.09704925 |
| breaker-tests | 01a14a7e-70c4-7448-98a3-6da265ee4f03 | SUCCESS | 0 | 2.452s | disposable | off | 0.018434350000000002 |

Sandbox operations: 19, total guest duration 160.645s, retained images ['1b8a54e0-1413-466f-bdc4-ecc3ea864f73'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
