# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: VERIFIED**  
Run `kvparse-refactor-001-attest-a1-20261019T104242400822Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T10:42:42.402027+00:00, finished 2026-10-19T10:51:30.306312+00:00.

**Accept this patch.** All 19 sealed tests pass on the candidate in a fresh sandbox, and 3 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 19 of 19 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 19 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 3 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 16 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 3 of 19 failed on the unmodified base; 19 of 19 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d5973fe8-f643-4973-9708-8a56dda1b845`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.6.0 revision `b11ec0658845e54d` (36 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision5-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving the existing string-input behavior of parse_line and parse. Replace parse_line's manual index loops with partition at the first '='; strip the key and value and remove exactly one matching outer quote pair when present. Extract blank/comment-line detection into module-level _is_ignorable(line) -> bool and have parse use it. Preserve public exports, exception types, duplicate-key handling, and the existing tests without changing them.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a str input, partition at the first '=' using str.partition. Strip both resulting key and value using default str.strip whitespace semantics. Return a two-e | ValueError: the input string contains no '='.; ValueError: the portion before the first '=' is empty after stripping.; Non-string arguments are unspecified and  |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Accept strings using the existing isinstance(text, str) check. Iterate over text.splitlines() in order, preserving the full default splitlines semantics. Use _i | TypeError: text is not an instance of str, including None, integers, lists, mappings, and bytes.; ValueError: any non-ignored line has no '=' or has an empty st |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper accepting a string and returning an actual bool. Return True exactly when line.strip() is empty or starts with '#' or ';'; otherwise return  | Non-string arguments are unspecified and must not be tested. |

Acceptance criteria:
AC1. 1. parse_line('a=b') returns ('a', 'b'); parse_line(' a = b ') returns ('a', 'b'); parse_line('a=') returns ('a', ''); parse_line('k e y = v') returns ('k e y', 'v').
AC2. 2. Only the first '=' separates key and value: parse_line('a==b') returns ('a', '=b') and parse_line('a = b = c') returns ('a', 'b = c').
AC3. 3. Matching quotes are removed exactly once: parse_line('q = "x"') returns ('q', 'x'); parse_line("q = 'x'") returns ('q', 'x'); parse_line("q = ''") and parse_line('q = ""') both return ('q', ''); parse_line('u = "a" "b"') returns ('u', 'a" "b').
AC4. 4. Mismatched quotes and single quote characters remain unchanged: parse_line('q = "x\'') returns ('q', '"x\''); parse_line('q = "') returns ('q', '"'); a lone single quote is likewise preserved.
AC5. 5. Quoted contents remain exact: parse_line('q = " spaced "') returns ('q', ' spaced '); internal quotes, backslashes, whitespace, and '=' characters are neither interpreted nor normalized. Nested matching outer quotes lose only one pair.
AC6. 6. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1'. More generally, every string lacking '=' or having an empty stripped key raises ValueError.
AC7. 7. Default str.strip semantics apply to keys, values, and ignorable-line detection, including Unicode whitespace. For every valid string input, returned characters match the original implementation exactly.
AC8. 8. parse('') returns {}; parse('k = v') returns {'k': 'v'}; parse('a = 1\nb=2\n') returns {'a': '1', 'b': '2'}. Each call returns a new dict.
AC9. 9. parse ignores whitespace-only lines and lines whose first stripped character is '#' or ';', including comments without '='. It preserves text.splitlines() behavior for LF, CRLF, CR, and all other separators recognized by that method.
AC10. 10. Comment markers elsewhere are literal: parse('a = # not a comment') returns {'a': '# not a comment'} and parse('a = ; value') returns {'a': '; value'}. parse_line itself does not skip comments: parse_line('#k=v') returns ('#k', 'v'), while parse_line('# comment') raises ValueError.
AC11. 11. Later duplicate keys win after key stripping: parse('a=1\nb=2\n a =3') returns {'a': '3', 'b': '2'}, with key iteration order ['a', 'b'].
AC12. 12. parse raises ValueError for a malformed non-ignored line at the beginning, middle, or end of otherwise valid text. Ignorable malformed-looking comments do not raise.
AC13. 13. parse raises TypeError for non-string inputs, including None, 3, a list, a mapping, and bytes. Do not assert exception messages or test non-string arguments to parse_line.
AC14. 14. kvparse.parser._is_ignorable exists at module level with a bool return annotation. It returns True for '', '   ', '   # c', and '\t; c', and False for 'a = 1', 'a = # not a comment', and 'x; c'.
AC15. 15. Source inspection confirms parse delegates blank/comment detection to _is_ignorable and continues passing original non-ignored lines to parse_line.
AC16. 16. Source or AST inspection confirms parse_line uses str.partition with '=' as the separator, contains no while loop, and no longer manually accumulates key/value characters through index loops.
AC17. 17. Both 'from kvparse import parse, parse_line' and access through kvparse.parser continue to work with the existing public signatures.
AC18. 18. All existing tests in tests/ pass unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The partition-based rules preserve the existing implementation’s behavior for all plain string inputs, including whitespace, malformed lines, and quote handling. The helper extraction, public exports, and unchanged tests can all be satisfied within kvparse/**. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness is constrained (no function, class, lambda or dynamic type, no dynamic code; values of the input domain and the unchanged code only); a demonstrated conflict that involves a derived criterion (AC) or an unconstrained witness is held for a human; a claimed-only conflict never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `46758bd5cd62bb2fd290db7eb6b46cdfcb6cdf408c77203b9faa567c709a38fa`, 19 test methods, sealed at 2026-10-19T10:46:47.462010+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 19 methods: ERROR 2, FAIL 1): 3 of 19 methods failing, 16 passing; operation `01a153c5-548f-76f0-8c10-75386bda586f`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedParser.test_comment_markers_are_literal_after_key_or_in_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_default_strip_handles_unicode_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_duplicate_keys_replace_value_and_retain_order | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_existing_test_examples_remain_valid | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_module_helper_annotation_and_boolean_behavior | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_delegates_detection_and_passes_original_lines | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_empty_and_fresh_dict | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_basic_values_and_whitespace | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_keeps_quoted_contents_exact | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_partitions_only_first_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_preserves_mismatched_and_single_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_rejects_missing_separator_or_empty_key | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_uses_partition_without_index_loops | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_multiline_and_ignorable_lines | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_rejects_malformed_line_at_each_position | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_rejects_non_string_inputs | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_uses_default_splitlines_separators | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_public_exports_and_signatures | ok (1 ev) | ok (1 ev) |


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
+    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
+        value = value[1:-1]
     return key, value
+
+
+def _is_ignorable(line) -> bool:
+    """Return whether a line is blank or starts with a comment marker."""
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

Sealed suite: OK (19 of 19 methods, each in its own process). Operation `01a153c7-b9e0-70aa-af75-b464caca6bcb`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a153c7-ee6e-73e4-811f-084b4abb96ba`, bound through the supervisor: 1 module(s), binding ok.

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

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-938a846e35 | kvparse/parser.py | 12 | remove `not` | killed | test_sealed.TestSealedParser.test_parse_line_basic_values_and_whitespace, test_sealed.TestSealedParser.test_parse_line_p | 01a153c8-0c1f-768c-a5b0-0182922bcd82 |
| m02-d699b50f38 | kvparse/parser.py | 18 | 2 -> 3 | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair | 01a153c8-0c04-70ba-af0a-b03b0eefb961 |
| m03-4ef9b06237 | kvparse/parser.py | 18 | GtE -> Gt | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair | 01a153c8-0be8-7307-b51b-af455f8e31e2 |
| m04-ab7329a274 | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair, test_sealed.TestSealedParser.test_parse_li | 01a153c8-0bce-7356-af0f-bc2d4b4d0583 |
| m05-4e05d1c9c9 | kvparse/parser.py | 18 | Eq -> NotEq | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair, test_sealed.TestSealedParser.test_parse_li | 01a153c8-0c19-733d-9aec-e1fe383a5856 |
| m06-0c943d5796 | kvparse/parser.py | 18 | 0 -> 1 | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair, test_sealed.TestSealedParser.test_parse_li | 01a153c8-0bf5-77c2-852b-3c78a661d8c4 |
| m07-5ab0d32301 | kvparse/parser.py | 18 | In -> NotIn | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair, test_sealed.TestSealedParser.test_parse_li | 01a153c8-0c6f-7779-be9c-f8f59b1c15b8 |
| m08-971d1a14c9 | kvparse/parser.py | 18 | And -> Or | killed | test_sealed.TestSealedParser.test_parse_line_basic_values_and_whitespace, test_sealed.TestSealedParser.test_parse_line_p | 01a153c8-0c09-76a5-aba2-fc05550451f0 |
| m09-b9ba5be95a | kvparse/parser.py | 19 | 1 -> 2 | killed | test_sealed.TestSealedParser.test_parse_line_removes_one_matching_quote_pair, test_sealed.TestSealedParser.test_parse_li | 01a153c8-3ec7-7559-b8bb-a71f18ac2ab5 |
| m10-0ff551c7ef | kvparse/parser.py | 26 | remove `not` | killed | test_sealed.TestSealedParser.test_default_strip_handles_unicode_whitespace, test_sealed.TestSealedParser.test_parse_empt | 01a153c8-3f89-7293-84c6-e27bdd79a9a3 |
| m11-cfe476232a | kvparse/parser.py | 26 | 0 -> 1 | killed | test_sealed.TestSealedParser.test_default_strip_handles_unicode_whitespace, test_sealed.TestSealedParser.test_parse_mult | 01a153c8-3f98-73bd-b158-fb487696d3fb |
| m12-7c2c91e514 | kvparse/parser.py | 26 | In -> NotIn | killed | test_sealed.TestSealedParser.test_default_strip_handles_unicode_whitespace, test_sealed.TestSealedParser.test_parse_empt | 01a153c8-410f-72c7-afe9-9967062af93b |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `f299407f86b1e50a18ccc489a59cd19d01e61dd1e9dfd7109804dcb8b1997adc`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a153c9-4f5d-73a9-a3fe-5110e463e6d4`. Notes: Targets uncommon splitline separators, literal control characters, nested quotes, separator variants, and consistency between parse_line and parse.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff fulfills the requested refactor: `line.partition("=")` replaces both while loops, stripping and matching-quote removal remain equivalent, and `def _is_ignorable(line) -> bool` centralizes detection through `if _is_ignorable(raw):` while preserving original-line parsing. Public exports and tests are untouched, parse retains its type check and duplicate-key assignment, and the observed test result supports the implementer's claim that all four existing tests pass.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 11096 | 1656 | 7680 | - | 59.6s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13260 | 89 | 0 | - | 26.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11580 | 5682 | 0 | - | 138.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11159 | 134 | 7168 | - | 15.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11698 | 527 | 0 | - | 30.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 12132 | 119 | 0 | - | 34.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12376 | 492 | 7168 | - | 29.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12864 | 89 | 7168 | - | 15.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 13039 | 166 | 0 | - | 16.5s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11609 | 2029 | 0 | - | 55.4s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12374 | 139 | 0 | - | 23.0s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 133187/11122/29184; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a153c1-c937-75bb-a438-da90712565a8 | SUCCESS | 0 | 0.853s | retained | off | 0.0029018499999999997 |
| red-1 | 01a153c5-548f-76f0-8c10-75386bda586f | SUCCESS | 0 | 7.402s | disposable | off | 0.06441098 |
| impl-tests-5 | 01a153c7-6769-7266-9f95-d1aea1cb3c3d | SUCCESS | 0 | 0.871s | disposable | off | 0.00285056 |
| verify | 01a153c7-b9e0-70aa-af75-b464caca6bcb | SUCCESS | 0 | 7.725s | disposable | off | 0.06523282 |
| existing | 01a153c7-ee6e-73e4-811f-084b4abb96ba | SUCCESS | 0 | 1.794s | disposable | off | 0.011943939999999998 |
| mutant-m01-938a846e35 | 01a153c8-0c1f-768c-a5b0-0182922bcd82 | SUCCESS | 0 | 6.839s | disposable | off | 0.05846825 |
| mutant-m02-d699b50f38 | 01a153c8-0c04-70ba-af0a-b03b0eefb961 | SUCCESS | 0 | 6.911s | disposable | off | 0.059132130000000005 |
| mutant-m03-4ef9b06237 | 01a153c8-0be8-7307-b51b-af455f8e31e2 | SUCCESS | 0 | 6.86s | disposable | off | 0.05848054 |
| mutant-m04-ab7329a274 | 01a153c8-0bce-7356-af0f-bc2d4b4d0583 | SUCCESS | 0 | 6.89s | disposable | off | 0.05903146 |
| mutant-m05-4e05d1c9c9 | 01a153c8-0c19-733d-9aec-e1fe383a5856 | SUCCESS | 0 | 6.859s | disposable | off | 0.05874231 |
| mutant-m07-5ab0d32301 | 01a153c8-0c6f-7779-be9c-f8f59b1c15b8 | SUCCESS | 0 | 6.83s | disposable | off | 0.05878985 |
| mutant-m06-0c943d5796 | 01a153c8-0bf5-77c2-852b-3c78a661d8c4 | SUCCESS | 0 | 6.83s | disposable | off | 0.05817718 |
| mutant-m08-971d1a14c9 | 01a153c8-0c09-76a5-aba2-fc05550451f0 | SUCCESS | 0 | 6.828s | disposable | off | 0.05873715 |
| mutant-m09-b9ba5be95a | 01a153c8-3ec7-7559-b8bb-a71f18ac2ab5 | SUCCESS | 0 | 6.794s | disposable | off | 0.05841635 |
| mutant-m10-0ff551c7ef | 01a153c8-3f89-7293-84c6-e27bdd79a9a3 | SUCCESS | 0 | 6.788s | disposable | off | 0.05893095 |
| mutant-m11-cfe476232a | 01a153c8-3f98-73bd-b158-fb487696d3fb | SUCCESS | 0 | 6.754s | disposable | off | 0.058659869999999996 |
| mutant-m12-7c2c91e514 | 01a153c8-410f-72c7-afe9-9967062af93b | SUCCESS | 0 | 6.816s | disposable | off | 0.05861787 |
| breaker-tests | 01a153c9-4f5d-73a9-a3fe-5110e463e6d4 | SUCCESS | 0 | 2.877s | disposable | off | 0.02179605 |

Sandbox operations: 18, total guest duration 103.521s, retained images ['d5973fe8-f643-4973-9708-8a56dda1b845'].

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
