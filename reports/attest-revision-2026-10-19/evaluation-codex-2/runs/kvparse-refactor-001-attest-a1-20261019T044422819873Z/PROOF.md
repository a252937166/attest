# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: VERIFIED**  
Run `kvparse-refactor-001-attest-a1-20261019T044422819873Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:44:22.820280+00:00, finished 2026-10-19T04:58:06.976835+00:00.

**Accept this patch.** All 28 sealed tests pass on the candidate in a fresh sandbox, and 3 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 28 of 28 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 28 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 3 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 25 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 3 of 28 failed on the unmodified base; 28 of 28 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `5997b19f-5f1b-4642-b7bb-e0b176ee7a16`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its string-input behavior: replace parse_line's index loops with partitioning at the first '=' and retain whitespace stripping, validation, and removal of exactly one matching outer quote pair; extract blank/comment-line detection into module-level _is_ignorable(line) -> bool and have parse use it. Preserve parse's input validation, splitlines semantics, duplicate-key handling, and public exports, with existing tests unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line | parse_line(line) | For a str input, return a two-element tuple of strings. Split at the first '=' using str.partition (line.partition('=') is acceptable). Strip both resulting key | ValueError: the string contains no '='.; ValueError: the key before the first '=' is empty after stripping.; Behavior for non-string arguments is unspecified an |
| kvparse.parser.parse | parse(text) | Accept input satisfying isinstance(text, str) and return a dict mapping parsed string keys to string values. Iterate over text.splitlines() using its existing d | TypeError: text is not an instance of str, including None, integers, lists, and bytes.; ValueError: any non-ignored line is malformed according to parse_line; n |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper for string lines. Return True exactly when line.strip() is empty or begins with '#' or ';'; otherwise return False. Return a bool. The helpe | Behavior for non-string arguments is unspecified and must not be tested. |

Acceptance criteria:
AC1. 1. parse_line('a=b') == ('a', 'b'); parse_line(' a = b ') == ('a', 'b'); parse_line('a==b') == ('a', '=b'); parse_line('a = b = c') == ('a', 'b = c'); parse_line('a=') == ('a', '').
AC2. 2. parse_line('q = "x"') == ('q', 'x'); parse_line("q = 'x'") == ('q', 'x'); parse_line("q = ''") == ('q', ''); parse_line('q = ""') == ('q', '').
AC3. 3. parse_line('q = "x\'') == ('q', '"x\''); parse_line('q = "') == ('q', '"'); a lone single quote is likewise preserved. Mismatched outer quotes are never removed.
AC4. 4. parse_line('q = " spaced "') == ('q', ' spaced '); parse_line('k e y = v') == ('k e y', 'v'); parse_line('u = "a" "b"') == ('u', 'a" "b'). Quote removal occurs once, with no recursive removal, unescaping, or subsequent stripping.
AC5. 5. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1'. More generally, every string lacking '=' or having an empty stripped key raises ValueError.
AC6. 6. Default str.strip semantics are preserved, including Unicode whitespace. Keys retain internal whitespace and quotes. Values retain internal whitespace, additional equals signs, backslashes, and comment markers.
AC7. 7. parse_line treats its argument as one string, without splitting lines or skipping comments: parse_line('#k=v') == ('#k', 'v'), and embedded line separators are retained unless removed as surrounding whitespace by strip.
AC8. 8. _is_ignorable returns True for '', '   ', '   # c', and '\t; c'; it returns False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'. For all string inputs its result matches the specified stripped-empty-or-comment-prefix rule.
AC9. 9. parse('') == {}; parse('k = v') == {'k': 'v'}; parse('# comment\n\n; other\nname = x\n') == {'name': 'x'}. Whitespace-prefixed comments and whitespace-only lines are ignored, including comment lines containing '='.
AC10. 10. parse preserves text.splitlines() semantics, including CRLF, lone CR, LF, and other Python-recognized line separators. For example, parse('a=1\r\nb=2\r\n') == {'a': '1', 'b': '2'}.
AC11. 11. Later duplicate stripped keys win: parse(' a = 1\nb=2\na=3') == {'a': '3', 'b': '2'}, with dictionary iteration order ['a', 'b']. Keys remain case-sensitive.
AC12. 12. Inline comment markers are ordinary value content: parse('a = # not a comment\nb = ; also a value') == {'a': '# not a comment', 'b': '; also a value'}.
AC13. 13. parse raises ValueError when a malformed non-ignored line occurs at the beginning, middle, or end of otherwise valid text. Ignored comment lines need not contain '='.
AC14. 14. parse raises TypeError for None, 3, [], and b'a=b', and retains its isinstance(text, str) input guard. No assertions constrain exception messages.
AC15. 15. Source inspection confirms that parse_line uses str.partition to split at the first '=' and contains no while loop or replacement hand-written index-scanning loops.
AC16. 16. Source inspection confirms that _is_ignorable is defined at module level with return annotation bool and that parse calls it to determine which lines to skip.
AC17. 17. from kvparse import parse, parse_line continues to work and exposes the corresponding functions from kvparse.parser.
AC18. 18. All existing tests in tests/ pass without modifying those files. No tests assert behavior of parse_line or _is_ignorable for non-string inputs.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The specified partition, stripping, validation, and quote removal match the existing string parsing behavior. The helper extraction, public exports, and unchanged tests can all be satisfied within kvparse/**. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `b99ed41d9af411c685d1aa5ae5287fb75c1256e14224a19012ee5814d62195e5`, 28 test methods, sealed at 2026-10-19T04:50:19.074806+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 28 methods: FAIL 3): 3 of 28 methods failing, 25 passing; operation `01a1527e-e5d2-73d0-9af9-25c8d12c49b3`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParse.test_blank_and_whitespace_only_lines_are_ignored | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_comment_markers_after_equals_are_values | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_duplicate_stripped_keys_replace_values_without_moving_position | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_empty_text | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_helper_is_module_level_and_bool_annotated | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_keys_are_case_sensitive | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_malformed_non_ignored_line_raises_at_any_position | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_non_string_input_raises_type_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_parse_calls_helper_on_raw_lines | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_public_exports_are_parser_functions | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_single_assignment | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_splitlines_recognizes_python_line_separators | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_str_subclass_is_accepted | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParse.test_whitespace_prefixed_comments_are_ignored_even_with_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_basic_assignment_and_surrounding_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_comment_marker_in_key_is_not_skipped | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_embedded_line_separator_is_not_split | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_stripped_key_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_empty_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_internal_key_and_value_characters_remain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_lone_quote_remains | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_matching_outer_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_mismatched_outer_quotes_remain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_missing_equals_raises_value_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_partition_without_index_scanning | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_quote_removal_happens_once_without_stripping_inside | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_split_at_first_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestParseLine.test_unicode_surrounding_whitespace_is_stripped | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 5 implementer turn(s).

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
+    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
+        value = value[1:-1]
     return key, value
+
+
+def _is_ignorable(line) -> bool:
+    """Return whether a line is blank or begins with a comment marker."""
+    stripped = line.strip()
+    return not stripped or stripped[0] in ("#", ";")
 
 
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

Sealed suite: OK (28 of 28 methods, each in its own process). Operation `01a15283-a45d-7456-b46d-d4fb86b5fb74`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a15283-d591-71bf-a861-e3dc970b9c9d`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-55ec49488a | kvparse/parser.py | 12 | remove `not` | killed | test_sealed.TestParseLine.test_basic_assignment_and_surrounding_whitespace, test_sealed.TestParseLine.test_split_at_firs | 01a15283-ef19-7166-bdda-833e3fbd5aac |
| m02-cab0e00a17 | kvparse/parser.py | 18 | 2 -> 3 | killed | test_sealed.TestParseLine.test_matching_outer_quotes | 01a15283-ef19-7535-80b1-a4c5624a767a |
| m03-d027657631 | kvparse/parser.py | 18 | GtE -> Gt | killed | test_sealed.TestParseLine.test_matching_outer_quotes | 01a15283-fb0e-7734-8725-5ec66ca1acb2 |
| m04-d9740fe1dc | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_outer_quotes, test_sealed.TestParseLine.test_quote_removal_happens_once_without_ | 01a15283-ef1b-71cf-bd6c-8d11edb355a0 |
| m05-a52b340800 | kvparse/parser.py | 18 | Eq -> NotEq | killed | test_sealed.TestParseLine.test_matching_outer_quotes, test_sealed.TestParseLine.test_mismatched_outer_quotes_remain, tes | 01a15283-eea2-715d-bc9d-4849e898690a |
| m06-41efa47fe4 | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestParseLine.test_matching_outer_quotes, test_sealed.TestParseLine.test_quote_removal_happens_once_without_ | 01a15283-eefd-7529-9eca-c710af1caf0b |
| m07-13cc78ffe9 | kvparse/parser.py | 18 | In -> NotIn | killed | test_sealed.TestParseLine.test_matching_outer_quotes, test_sealed.TestParseLine.test_quote_removal_happens_once_without_ | 01a15283-ef69-70f1-8cdc-b01bf732e16a |
| m08-f427053313 | kvparse/parser.py | 18 | And -> Or | killed | test_sealed.TestParseLine.test_basic_assignment_and_surrounding_whitespace, test_sealed.TestParseLine.test_split_at_firs | 01a15283-eeff-7516-ae8d-24ab551866d4 |
| m09-6194690cfd | kvparse/parser.py | 19 | 1 -> 2 | killed | test_sealed.TestParseLine.test_matching_outer_quotes, test_sealed.TestParseLine.test_quote_removal_happens_once_without_ | 01a15284-29b2-75b9-9331-09fbe413ca99 |
| m10-1c577edb31 | kvparse/parser.py | 26 | remove `not` | killed | test_sealed.TestParse.test_single_assignment, test_sealed.TestParse.test_blank_and_whitespace_only_lines_are_ignored, te | 01a15284-2a46-77ec-ad3b-55bcea64704a |
| m11-b710a0161f | kvparse/parser.py | 26 | 0 -> 1 | killed | test_sealed.TestParse.test_whitespace_prefixed_comments_are_ignored_even_with_equals | 01a15284-2ae0-73fe-97e5-60691d6cb330 |
| m12-06274de156 | kvparse/parser.py | 26 | In -> NotIn | killed | test_sealed.TestParse.test_single_assignment, test_sealed.TestParse.test_blank_and_whitespace_only_lines_are_ignored, te | 01a15284-2c71-75b9-ab98-36229f7ba4cc |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `e56434025cbb0c779368ae38f7b1867ab52c559c0b727d2be78a90bbeedfa1a0`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a15285-9d07-73ab-8c89-de254a6b6993`. Notes: Targets nested quotes, Unicode strip boundaries, literal delimiters, comment handling, and duplicate keys across line separators.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fulfills both changes: `line.partition("=")` replaces index loops, preserves stripping and validation, and removes one matching quote pair using `value[1:-1]`; module-level `_is_ignorable(line) -> bool` implements the required rule and is called by parse. Input validation, splitlines iteration, duplicate assignment, public exports, and tests remain unchanged, and the observed test run supports the claim that all four existing tests passed.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 11094 | 1645 | 0 | - | 86.9s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12469 | 130 | 0 | - | 88.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11579 | 4688 | 0 | - | 154.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11132 | 123 | 7168 | - | 86.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11675 | 540 | 0 | - | 65.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11798 | 192 | 7168 | - | 50.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 11975 | 130 | 7168 | - | 41.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12432 | 136 | 7168 | - | 47.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11685 | 1788 | 7040 | - | 80.3s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12287 | 135 | 0 | - | 35.0s | ok |

Model calls: 10 (0 failed, 0 malformed); tokens in/out/cached 118126/9507/35712; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15279-b994-7351-beb4-2c10759bfac2 | SUCCESS | 0 | 0.839s | retained | off | 0.0028283600000000002 |
| red-1 | 01a1527e-e5d2-73d0-9af9-25c8d12c49b3 | SUCCESS | 0 | 10.088s | disposable | off | 0.09066054999999999 |
| impl-tests-3 | 01a15282-38c9-74b8-a223-8d56f2c040c9 | SUCCESS | 0 | 0.779s | disposable | off | 0.00285534 |
| verify | 01a15283-a45d-7456-b46d-d4fb86b5fb74 | SUCCESS | 0 | 10.108s | disposable | off | 0.09129872 |
| existing | 01a15283-d591-71bf-a861-e3dc970b9c9d | SUCCESS | 0 | 1.754s | disposable | off | 0.01201457 |
| mutant-m01-55ec49488a | 01a15283-ef19-7166-bdda-833e3fbd5aac | SUCCESS | 0 | 9.731s | disposable | off | 0.08556285000000001 |
| mutant-m02-cab0e00a17 | 01a15283-ef19-7535-80b1-a4c5624a767a | SUCCESS | 0 | 9.555s | disposable | off | 0.08502741999999999 |
| mutant-m03-d027657631 | 01a15283-fb0e-7734-8725-5ec66ca1acb2 | SUCCESS | 0 | 9.599s | disposable | off | 0.08523560999999999 |
| mutant-m04-d9740fe1dc | 01a15283-ef1b-71cf-bd6c-8d11edb355a0 | SUCCESS | 0 | 9.731s | disposable | off | 0.08559320999999999 |
| mutant-m05-a52b340800 | 01a15283-eea2-715d-bc9d-4849e898690a | SUCCESS | 0 | 9.655s | disposable | off | 0.08623731 |
| mutant-m06-41efa47fe4 | 01a15283-eefd-7529-9eca-c710af1caf0b | SUCCESS | 0 | 9.843s | disposable | off | 0.08677847 |
| mutant-m07-13cc78ffe9 | 01a15283-ef69-70f1-8cdc-b01bf732e16a | SUCCESS | 0 | 9.731s | disposable | off | 0.08605525 |
| mutant-m08-f427053313 | 01a15283-eeff-7516-ae8d-24ab551866d4 | SUCCESS | 0 | 9.731s | disposable | off | 0.08616761 |
| mutant-m09-6194690cfd | 01a15284-29b2-75b9-9331-09fbe413ca99 | SUCCESS | 0 | 9.626s | disposable | off | 0.08559858 |
| mutant-m10-1c577edb31 | 01a15284-2a46-77ec-ad3b-55bcea64704a | SUCCESS | 0 | 9.737s | disposable | off | 0.08677915 |
| mutant-m11-b710a0161f | 01a15284-2ae0-73fe-97e5-60691d6cb330 | SUCCESS | 0 | 9.525s | disposable | off | 0.08498748 |
| mutant-m12-06274de156 | 01a15284-2c71-75b9-ab98-36229f7ba4cc | SUCCESS | 0 | 9.555s | disposable | off | 0.08504653000000001 |
| breaker-tests | 01a15285-9d07-73ab-8c89-de254a6b6993 | SUCCESS | 0 | 2.822s | disposable | off | 0.02170002 |

Sandbox operations: 18, total guest duration 142.409s, retained images ['5997b19f-5f1b-4642-b7bb-e0b176ee7a16'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion is never overridden. The classification itself remains a model judgement.
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
