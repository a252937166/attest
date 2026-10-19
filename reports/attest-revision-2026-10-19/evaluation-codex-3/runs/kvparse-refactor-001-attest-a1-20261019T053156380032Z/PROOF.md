# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: VERIFIED**  
Run `kvparse-refactor-001-attest-a1-20261019T053156380032Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:31:56.381299+00:00, finished 2026-10-19T05:40:02.994758+00:00.

**Accept this patch.** All 22 sealed tests pass on the candidate in a fresh sandbox, and 3 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 22 of 22 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 22 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 3 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class bound).
- 8 of 8 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 19 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 3 of 22 failed on the unmodified base; 22 of 22 pass on the candidate |
| E2 | Mutation check | pass | bound | 8 of 8 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `036c442a-2527-47b5-a944-8b9bd501f476`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its string-input behavior: replace parse_line's index loops with partitioning at the first '=', retain whitespace stripping, validation and removal of exactly one matching outer quote pair, and extract blank/comment-line detection into a module-level _is_ignorable helper used by parse. Preserve public exports, parsing order, duplicate-key handling and specified exception types; leave existing tests unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a string argument, partition at the first '=' using str.partition. Strip the key and value using default str.strip whitespace semantics. Return a two-elemen | ValueError: the input string contains no '='.; ValueError: the key before the first '=' is empty after stripping.; Exception messages are unspecified.; Non-stri |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Require isinstance(text, str). Iterate over text.splitlines() in order, skipping lines identified by _is_ignorable. Parse each remaining original line with pars | TypeError: text is not an instance of str, including None, integers, lists and bytes.; ValueError: any non-ignored line lacks '=' or has an empty stripped key.; |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | For a string line, return a bool that is True exactly when line.strip() is empty or starts with '#' or ';'; otherwise return False. Define this helper at module | Non-string arguments are outside the helper's contract; no exception behavior is prescribed for them. |

Acceptance criteria:
AC1. 1. parse_line('a=b') == ('a', 'b'), parse_line(' a = b ') == ('a', 'b'), parse_line('a==b') == ('a', '=b'), parse_line('a = b = c') == ('a', 'b = c'), and parse_line('a=') == ('a', '').
AC2. 2. parse_line('q = "x"') == ('q', 'x'), parse_line("q = 'x'") == ('q', 'x'), parse_line("q = ''") == ('q', ''), and parse_line('q = ""') == ('q', '').
AC3. 3. parse_line('q = "x\'') == ('q', '"x\''), and parse_line('q = "') == ('q', '"'). Mismatched outer quotes and lone quote characters remain unchanged.
AC4. 4. parse_line('q = " spaced "') == ('q', ' spaced '), parse_line('k e y = v') == ('k e y', 'v'), and parse_line('u = "a" "b"') == ('u', 'a" "b'). Remove only one matching outer quote pair; do not strip again afterward or decode escapes.
AC5. 5. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=' and '\t= 1'. More generally, a string line is malformed exactly when it has no '=' or its prefix before the first '=' strips to an empty key.
AC6. 6. All string parsing retains default Python str.strip semantics, including Unicode whitespace. parse_line treats line-break characters as ordinary characters subject to boundary stripping, rather than splitting its argument into lines.
AC7. 7. _is_ignorable returns True for '', whitespace-only strings, '   # c' and '\t; c'; it returns False for 'a = 1' and 'a = # not a comment'. For every string line, its result equals whether the stripped line is empty or begins with '#' or ';'.
AC8. 8. parse('') == {}, parse('k = v') == {'k': 'v'}, and parse('# comment\n\n; other\nname = x\n') == {'name': 'x'}. Ignored comments need not contain '='.
AC9. 9. parse retains str.splitlines() line-boundary behavior, including LF, CRLF, lone CR and other boundaries supported by that method. For example, parse('a=1\r\nb=2\r\n') == {'a': '1', 'b': '2'}.
AC10. 10. parse('a=1\nb=2\na=3') returns {'a': '3', 'b': '2'} with iteration order ['a', 'b']; stripped keys determine duplicate identity.
AC11. 11. Comment markers inside a value remain literal: parse('a = # not a comment\nb = ; text') == {'a': '# not a comment', 'b': '; text'}. parse_line itself does not skip comment-looking inputs.
AC12. 12. parse raises ValueError for a malformed non-ignored line at the beginning, middle or end of the input, even if other lines are valid. It does not return a partial result.
AC13. 13. parse raises TypeError for None, 3, a list and bytes, preserving its isinstance(text, str) input check. Do not assert exception-message text.
AC14. 14. Source inspection verifies that parse_line uses str.partition with '=' to split at the first separator, replaces the hand-rolled index loops, and contains no while statement.
AC15. 15. Source inspection verifies that _is_ignorable is defined at module scope with the requested bool return annotation and that parse uses it for line-skipping decisions.
AC16. 16. from kvparse import parse, parse_line continues to expose the functions from kvparse.parser.
AC17. 17. The existing tests in tests/ remain unchanged and pass. Additional independent verification must not test parse_line with non-string arguments.
AC18. 18. For string inputs, return values and exception conditions remain equivalent to the supplied original implementation, including preservation of every character not removed by boundary stripping or the single matching outer quote-pair rule.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The partition-based implementation can preserve the original string parsing, validation, whitespace and quote handling exactly. Extracting the existing skip logic into _is_ignorable is compatible with all acceptance criteria, unchanged tests and public exports within the write scope. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `06d4393dd148fdd471056986b0ac82dd962a80f029558830e33158f865057e5b`, 22 test methods, sealed at 2026-10-19T05:35:46.795926+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 22 methods: ERROR 1, FAIL 2): 3 of 22 methods failing, 19 passing; operation `01a152a8-9d04-7330-96f9-9a64c633f877`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedParser.test_comment_markers_inside_values_are_literal | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_ignorable_helper_matches_stripped_line_rule | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_original_public_examples | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_duplicate_stripped_keys_keep_first_position | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_bytecode_calls_partition_without_a_backward_loop | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_does_not_split_line_breaks | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_preserves_internal_key_space_and_literal_escapes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_preserves_mismatched_and_lone_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_preserves_space_inside_outer_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_rejects_empty_stripped_key | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_rejects_missing_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_removes_matching_outer_quotes | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_removes_only_one_outer_pair | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_splits_at_first_equals | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_strips_key_and_value | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_line_uses_unicode_strip_boundaries | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_rejects_malformed_line_at_any_position | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_requires_string_instance | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_skips_blank_and_comment_lines | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_uses_module_scope_annotated_helper | FAIL (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_parse_uses_splitlines_boundaries | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedParser.test_public_exports_come_from_parser_module | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/kvparse/parser.py
+++ b/kvparse/parser.py
@@ -8,34 +8,24 @@
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
+    value = value.strip()
     if len(value) >= 2:
         first = value[0]
-        last = value[len(value) - 1]
+        last = value[-1]
         if (first == '"' and last == '"') or (first == "'" and last == "'"):
-            value = value[1:len(value) - 1]
+            value = value[1:-1]
     return key, value
+
+
+def _is_ignorable(line) -> bool:
+    stripped = line.strip()
+    return not stripped or stripped[0] in "#;"
 
 
 def parse(text):
@@ -45,12 +35,7 @@
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

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (22 of 22 methods, each in its own process). Operation `01a152ab-0a61-723c-9a97-eb1ffb6a332b`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `bound`): OK (4 of 4 methods, each in its own process) (4 passed of 4); operation `01a152ab-2cfb-73ef-b3c8-85980661ecf4`, bound through the supervisor: 1 module(s), binding ok.

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | bound | - | OK (4 of 4 methods, each in its own process) |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 8 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 8 generated, 8 evaluated: 8 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-c34fd3638b | kvparse/parser.py | 12 | remove `not` | killed | test_sealed.TestSealedParser.test_parse_line_strips_key_and_value, test_sealed.TestSealedParser.test_parse_line_splits_a | 01a152ab-45a8-7217-84de-48b0c0774e7f |
| m02-23b0ad94d8 | kvparse/parser.py | 20 | 1 -> 2 | killed | test_sealed.TestSealedParser.test_parse_line_removes_matching_outer_quotes, test_sealed.TestSealedParser.test_parse_line | 01a152ab-454c-7332-8b02-07befe79e80f |
| m03-163e0963c3 | kvparse/parser.py | 22 | 1 -> 2 | killed | test_sealed.TestSealedParser.test_parse_line_removes_matching_outer_quotes, test_sealed.TestSealedParser.test_parse_line | 01a152ab-455f-740b-97a8-a12dca120438 |
| m04-f56add5abd | kvparse/parser.py | 22 | 1 -> 2 | killed | test_sealed.TestSealedParser.test_parse_line_removes_matching_outer_quotes, test_sealed.TestSealedParser.test_parse_line | 01a152ab-4576-75f7-81fc-efae2401b5ca |
| m05-6ecc929e12 | kvparse/parser.py | 28 | remove `not` | killed | test_sealed.TestSealedParser.test_ignorable_helper_matches_stripped_line_rule, test_sealed.TestSealedParser.test_parse_s | 01a152ab-4522-7626-92ae-d7907f462b4a |
| m06-70b22ce10f | kvparse/parser.py | 28 | 0 -> 1 | killed | test_sealed.TestSealedParser.test_ignorable_helper_matches_stripped_line_rule, test_sealed.TestSealedParser.test_parse_s | 01a152ab-4564-713a-b0c6-8e9c9b5302d4 |
| m07-80608c3ecd | kvparse/parser.py | 28 | In -> NotIn | killed | test_sealed.TestSealedParser.test_ignorable_helper_matches_stripped_line_rule, test_sealed.TestSealedParser.test_parse_s | 01a152ab-4543-7149-b397-98b2d9589a20 |
| m08-57b85de02b | kvparse/parser.py | 28 | Or -> And | killed | test_sealed.TestSealedParser.test_ignorable_helper_matches_stripped_line_rule, test_sealed.TestSealedParser.test_parse_s | 01a152ab-4548-7764-9e0e-1b86362010bf |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `322d84cb13557dee7c23db734f8f1384f6c29c984ffde68e7b384e0836797b1e`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a152ac-4b51-7604-b0ca-c411be718e89`. Notes: Targets dense separators, layered quotes, Unicode whitespace, splitlines boundaries, comment placement, malformed lines, duplicate order, and parse/parse_line consistency.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff satisfies both requested changes: `line.partition("=")` replaces all index loops while preserving stripping, validation and matching quote removal, and module-level `_is_ignorable(line) -> bool` implements the required predicate and is used by parse. String-input behavior, public exports and tests remain unchanged; the observed test run supports the implementer's claim that all 4 existing tests passed.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 11096 | 1603 | 0 | - | 78.8s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12430 | 106 | 7552 | - | 35.5s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11567 | 4265 | 0 | - | 99.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11088 | 120 | 7168 | - | 18.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11197 | 83 | 7168 | - | 27.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11747 | 550 | 7168 | - | 30.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12203 | 121 | 7168 | - | 17.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12494 | 460 | 0 | - | 19.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 12950 | 80 | 7168 | - | 16.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 13126 | 140 | 7168 | - | 18.1s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11588 | 2411 | 0 | - | 57.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 12334 | 137 | 7552 | - | 17.5s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 143820/10076/58112; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a152a5-404b-7405-978d-04328a0b43ab | SUCCESS | 0 | 0.799s | retained | off | 0.00286682 |
| red-1 | 01a152a8-9d04-7330-96f9-9a64c633f877 | SUCCESS | 0 | 5.103s | disposable | off | 0.041369590000000005 |
| impl-tests-6 | 01a152aa-b674-769d-8729-b514b34ba1f7 | SUCCESS | 0 | 0.768s | disposable | off | 0.00285719 |
| verify | 01a152ab-0a61-723c-9a97-eb1ffb6a332b | SUCCESS | 0 | 4.802s | disposable | off | 0.04094911 |
| existing | 01a152ab-2cfb-73ef-b3c8-85980661ecf4 | SUCCESS | 0 | 1.781s | disposable | off | 0.012022419999999999 |
| mutant-m02-23b0ad94d8 | 01a152ab-454c-7332-8b02-07befe79e80f | SUCCESS | 0 | 4.656s | disposable | off | 0.03836333 |
| mutant-m01-c34fd3638b | 01a152ab-45a8-7217-84de-48b0c0774e7f | SUCCESS | 0 | 4.659s | disposable | off | 0.0384951 |
| mutant-m03-163e0963c3 | 01a152ab-455f-740b-97a8-a12dca120438 | SUCCESS | 0 | 4.638s | disposable | off | 0.038147049999999995 |
| mutant-m05-6ecc929e12 | 01a152ab-4522-7626-92ae-d7907f462b4a | SUCCESS | 0 | 4.584s | disposable | off | 0.03804005 |
| mutant-m04-f56add5abd | 01a152ab-4576-75f7-81fc-efae2401b5ca | SUCCESS | 0 | 4.637s | disposable | off | 0.03786158 |
| mutant-m06-70b22ce10f | 01a152ab-4564-713a-b0c6-8e9c9b5302d4 | SUCCESS | 0 | 4.64s | disposable | off | 0.03822393 |
| mutant-m07-80608c3ecd | 01a152ab-4543-7149-b397-98b2d9589a20 | SUCCESS | 0 | 4.616s | disposable | off | 0.038021559999999996 |
| mutant-m08-57b85de02b | 01a152ab-4548-7764-9e0e-1b86362010bf | SUCCESS | 0 | 4.713s | disposable | off | 0.038856919999999996 |
| breaker-tests | 01a152ac-4b51-7604-b0ca-c411be718e89 | SUCCESS | 0 | 2.831s | disposable | off | 0.02184904 |

Sandbox operations: 14, total guest duration 53.227s, retained images ['036c442a-2527-47b5-a944-8b9bd501f476'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
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
