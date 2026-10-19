# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: VERIFIED**  
Run `kvparse-refactor-001-attest-a1-20261017T154750158947Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T15:47:50.159251+00:00, finished 2026-10-17T15:57:05.216722+00:00.

**Accept this patch.** All 30 sealed tests pass on the candidate in a fresh sandbox, and 3 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 30 of 30 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 30 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 3 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 27 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 3 of 30 failed on the unmodified base; 30 of 30 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `05d1a764-ab2a-4a93-827e-9bc1367bed3e`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.3.0 revision `bd896d025d3ab872` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-freeze-2026-10-17/evaluation-revalidation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its specified string-input behavior: replace parse_line's index loops with partition at the first '=', preserve whitespace stripping, validation and removal of exactly one matching outer quote pair, and extract blank/comment-line detection into a module-level _is_ignorable helper used by parse. Preserve public imports, parsing order, duplicate-key handling and exception types, and leave the existing tests unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a string, partition at the first '='. Strip both resulting key and value using Python str.strip semantics. Require a separator and a nonempty stripped key.  | ValueError: the string contains no '='.; ValueError: the portion before the first '=' is empty after stripping.; Non-string arguments are unspecified and must n |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Require isinstance(text, str). Iterate over text.splitlines() in order. Use _is_ignorable to skip blank and comment lines, and parse each remaining original lin | TypeError: text is not an instance of str, including None, integers, lists and bytes.; ValueError: any non-ignored line has no '=' or an empty stripped key; pro |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper for string lines. Return True exactly when line.strip() is empty or starts with '#' or ';'; otherwise return False. Return an actual bool. I | Non-string arguments are outside the contract; no exception behavior is prescribed. |

Acceptance criteria:
1. 1. parse_line uses str.partition with '=' to separate the first delimiter, contains no while statement, and replaces the hand-rolled index loops rather than moving them elsewhere.
2. 2. parse_line('a=b') == ('a', 'b'); parse_line(' a = b ') == ('a', 'b'); parse_line('a==b') == ('a', '=b'); parse_line('a = b = c') == ('a', 'b = c'); parse_line('a=') == ('a', '').
3. 3. parse_line('k e y = v') == ('k e y', 'v'). Leading and trailing whitespace on keys and unquoted values follows str.strip, including tabs and Unicode whitespace; internal characters remain unchanged.
4. 4. parse_line('q = "x"') == ('q', 'x'); parse_line("q = 'x'") == ('q', 'x'); parse_line("q = ''") == ('q', ''); parse_line('q = ""') == ('q', '').
5. 5. parse_line('q = "x\'') == ('q', '"x\''); parse_line('q = "') == ('q', '"'). Mismatched outer quotes and single-character quote values remain unchanged.
6. 6. parse_line('q = " spaced "') == ('q', ' spaced '); parse_line('u = "a" "b"') == ('u', 'a" "b'). Remove only one matching outer quote pair; do not recursively unquote, decode escapes or strip the resulting interior.
7. 7. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=' and '\t= 1'. Tests assert exception types, not messages.
8. 8. Direct parse_line calls treat '#' and ';' as ordinary characters: parse_line('# = v') == ('#', 'v') and parse_line('; = v') == (';', 'v'); parse_line('# comment') raises ValueError.
9. 9. _is_ignorable exists at module scope with signature _is_ignorable(line) -> bool. It returns True for '', whitespace-only strings, '   # c' and '\t; c', and False for 'a = 1', 'a = # not a comment' and 'a = ; not a comment'. Its definition uses str.strip semantics.
10. 10. parse delegates its per-line ignore decision to _is_ignorable and passes each remaining original line to parse_line.
11. 11. parse('') == {}; parse('k = v') == {'k': 'v'}; text containing only blank lines or comments produces {}. Comments are ignored even if they contain '=' or otherwise resemble malformed assignments.
12. 12. parse preserves text.splitlines() behavior for LF, CRLF, CR and all other Python-recognized line boundaries, including trailing line boundaries. For example, parse(' # c\r\n\t; c\r\na = 1\r\n\r\nb=2\r\n') == {'a': '1', 'b': '2'}.
13. 13. Later duplicate keys win after key stripping. For parse('a=1\nb=2\n a =3'), the result equals {'a': '3', 'b': '2'} and its key iteration order is ['a', 'b']. Keys remain case-sensitive.
14. 14. Inline '#' and ';' characters remain part of values. parse('a = # not a comment\nb = ; not a comment') == {'a': '# not a comment', 'b': '; not a comment'}.
15. 15. parse raises ValueError for a malformed non-ignored line at the beginning, middle or end of otherwise valid text, including lines without '=' and lines with whitespace-only keys.
16. 16. parse raises TypeError for None, 3, [], and b'a=1', retaining the existing isinstance(text, str) input check.
17. 17. For string inputs, return contents and prescribed exception situations remain identical to the supplied implementation; no normalization, interpolation or other transformations are introduced.
18. 18. Both 'from kvparse import parse, parse_line' and imports from kvparse.parser continue to work. The existing tests in tests/ pass without modifications.
19. 19. Verification must not test or constrain parse_line behavior for non-string arguments.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `f40725d811e89703b828decb24640e75c5c919738dcb4a7280d427fbc229ddef`, 30 test methods, sealed at 2026-10-17T15:50:41.964668+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 30 methods: ERROR 2, FAIL 1): 3 of 30 methods failing, 27 passing; operation `01a14a8e-c455-70e0-8191-01a0b7a0f22f`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestIgnorableLines.test_module_helper_returns_bool_for_blank_comments_and_assignments | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestIgnorableLines.test_parse_delegates_ignore_decisions_to_helper | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestImports.test_package_and_parser_module_exports_work | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_all_splitlines_boundaries_are_supported | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_blank_and_comment_only_text_returns_empty_dict | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_comments_with_separators_or_malformed_assignments_are_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_duplicate_keys_replace_values_without_moving_keys | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_empty_key_at_any_position_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_empty_text_returns_empty_dict | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_inline_comment_markers_remain_in_values | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_keys_are_case_sensitive | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_missing_separator_at_any_position_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_non_string_text_raises_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_passes_original_nonignored_line_to_parse_line | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_single_assignment | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_basic_assignment | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_comment_markers_are_ordinary_key_characters | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_matching_quotes_are_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_stripped_key_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_value_is_allowed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_first_separator_only | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_internal_key_and_value_characters_remain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_line_separation_does_not_index_the_input | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_matching_quotes_are_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_mismatched_and_single_quotes_remain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_missing_separator_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_only_one_outer_quote_pair_is_removed | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_quoted_escape_sequences_are_not_decoded | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_quoted_interior_whitespace_remains | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_surrounding_whitespace_uses_strip | ok (1 ev) | ok (1 ev) |

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

Static tamper scan of the added lines: no suspicious constructs on the added lines (13 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (30 of 30 methods, each in its own process). Operation `01a14a91-ea4d-76d4-8349-8da2633a601c`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a14a92-230f-75f7-a132-bb8fab5c2da7`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-12e2687b48 | kvparse/parser.py | 12 | remove `not` | killed | test_sealed.TestParseLine.test_basic_assignment, test_sealed.TestParseLine.test_first_separator_only, test_sealed.TestPa | 01a14a93-57fa-7772-8d96-666b70e05d5e |
| m02-44add1b17d | kvparse/parser.py | 18 | 2 -> 3 | killed | test_sealed.TestParseLine.test_empty_matching_quotes_are_removed | 01a14a92-3329-7262-8792-2ad9496a7568 |
| m03-52a6edae5d | kvparse/parser.py | 18 | GtE -> Gt | killed | test_sealed.TestParseLine.test_empty_matching_quotes_are_removed | 01a14a92-3345-7104-bfe4-68430e5a4cf4 |
| m04-ec7d55a79a | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_quoted_interior_whitespace_re | 01a14a92-3361-7571-8c94-583a3d983aeb |
| m05-1382766bab | kvparse/parser.py | 18 | 1 -> 2 | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_quoted_interior_whitespace_re | 01a14a92-3352-72ea-acef-a88805d847dd |
| m06-71e0cf0675 | kvparse/parser.py | 18 | Eq -> NotEq | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_empty_matching_quotes_are_rem | 01a14a92-334d-70c4-909c-6b51447455f6 |
| m07-3f6379b421 | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_quoted_interior_whitespace_re | 01a14a92-33ba-76c3-bdc0-c9ed23e00654 |
| m08-f6e2b8453d | kvparse/parser.py | 18 | In -> NotIn | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_empty_matching_quotes_are_rem | 01a14a92-3334-7356-a658-27959372c136 |
| m09-4d2ff35498 | kvparse/parser.py | 18 | And -> Or | killed | test_sealed.TestParseLine.test_basic_assignment, test_sealed.TestParseLine.test_first_separator_only, test_sealed.TestPa | 01a14a92-659a-7446-a347-9c02eae6864f |
| m10-8858f5bec9 | kvparse/parser.py | 19 | 1 -> 2 | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_quoted_interior_whitespace_re | 01a14a92-6748-7734-a67a-0c29de58d589 |
| m11-d7ab25b2e8 | kvparse/parser.py | 19 | 1 -> 2 | killed | test_sealed.TestParseLine.test_matching_quotes_are_removed, test_sealed.TestParseLine.test_quoted_interior_whitespace_re | 01a14a92-72ad-725d-90db-7877b788368f |
| m12-2497227a52 | kvparse/parser.py | 26 | remove `not` | killed | test_sealed.TestIgnorableLines.test_module_helper_returns_bool_for_blank_comments_and_assignments, test_sealed.TestIgnor | 01a14a92-7381-7092-b9f5-e49a0bc07b63 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `5193ee3a2cf459563347989876d38f8fa94cff1d7e291a49d560a8330eb19f1f`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14a94-4383-7622-9ee3-ca16734f6cc9`. Notes: Targets Unicode strip boundaries, exact quote removal, delimiter interactions, comment detection, mixed line endings, duplicate order, and error types.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff satisfies both requested changes: `line.partition("=")` replaces all index loops while preserving stripping, validation and matching-pair quote removal, and module-level `_is_ignorable(line) -> bool` uses `line.strip()` and is called with each original line by parse. Input checking, splitlines iteration, duplicate-key handling and exports remain unchanged; no tests were modified, and the observed test run supports the claim that all four existing tests pass.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 11096 | 1631 | 0 | - | 59.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11384 | 4192 | 0 | - | 73.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10981 | 96 | 7168 | - | 19.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11523 | 600 | 7168 | - | 40.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11959 | 124 | 7168 | - | 40.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12208 | 489 | 7168 | - | 20.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12678 | 99 | 7168 | - | 28.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12857 | 126 | 7168 | - | 38.3s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11652 | 1983 | 0 | - | 45.7s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12349 | 136 | 0 | - | 30.7s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 118687/9476/43008; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14a8c-83dc-7175-9376-fb1bf4ad039f | SUCCESS | 0 | 3.237s | retained | off | 0.0028647100000000003 |
| red-1 | 01a14a8e-c455-70e0-8191-01a0b7a0f22f | SUCCESS | 0 | 11.205s | disposable | off | 0.09719013 |
| impl-tests-5 | 01a14a91-45a6-7799-a10b-1f79760c162d | SUCCESS | 0 | 1.016s | disposable | off | 0.0029008899999999997 |
| verify | 01a14a91-ea4d-76d4-8349-8da2633a601c | SUCCESS | 0 | 10.844s | disposable | off | 0.09683512 |
| existing | 01a14a92-230f-75f7-a132-bb8fab5c2da7 | SUCCESS | 0 | 1.75s | disposable | off | 0.01195692 |
| mutant-m02-44add1b17d | 01a14a92-3329-7262-8792-2ad9496a7568 | SUCCESS | 0 | 10.135s | disposable | off | 0.09070233999999999 |
| mutant-m01-12e2687b48 | 01a14a93-57fa-7772-8d96-666b70e05d5e | SUCCESS | 0 | 10.241s | disposable | off | 0.09154761 |
| mutant-m03-52a6edae5d | 01a14a92-3345-7104-bfe4-68430e5a4cf4 | SUCCESS | 0 | 10.296s | disposable | off | 0.0914636 |
| mutant-m04-ec7d55a79a | 01a14a92-3361-7571-8c94-583a3d983aeb | SUCCESS | 0 | 10.231s | disposable | off | 0.09118557 |
| mutant-m05-1382766bab | 01a14a92-3352-72ea-acef-a88805d847dd | SUCCESS | 0 | 10.269s | disposable | off | 0.09119885 |
| mutant-m06-71e0cf0675 | 01a14a92-334d-70c4-909c-6b51447455f6 | SUCCESS | 0 | 10.266s | disposable | off | 0.09082794 |
| mutant-m07-3f6379b421 | 01a14a92-33ba-76c3-bdc0-c9ed23e00654 | SUCCESS | 0 | 10.285s | disposable | off | 0.09160324999999998 |
| mutant-m08-f6e2b8453d | 01a14a92-3334-7356-a658-27959372c136 | SUCCESS | 0 | 10.266s | disposable | off | 0.09107528 |
| mutant-m09-4d2ff35498 | 01a14a92-659a-7446-a347-9c02eae6864f | SUCCESS | 0 | 10.352s | disposable | off | 0.09284606 |
| mutant-m10-8858f5bec9 | 01a14a92-6748-7734-a67a-0c29de58d589 | SUCCESS | 0 | 10.308s | disposable | off | 0.09223956 |
| mutant-m11-d7ab25b2e8 | 01a14a92-72ad-725d-90db-7877b788368f | SUCCESS | 0 | 10.277s | disposable | off | 0.09121678999999999 |
| mutant-m12-2497227a52 | 01a14a92-7381-7092-b9f5-e49a0bc07b63 | SUCCESS | 0 | 10.596s | disposable | off | 0.09407363 |
| breaker-tests | 01a14a94-4383-7622-9ee3-ca16734f6cc9 | SUCCESS | 0 | 4.28s | disposable | off | 0.0215919 |

Sandbox operations: 18, total guest duration 155.854s, retained images ['05d1a764-ab2a-4a93-827e-9bc1367bed3e'].

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
