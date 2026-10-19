# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: ERROR**  
Run `kvparse-refactor-001-attest-a1-20261019T144354722873Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T14:43:54.725064+00:00, finished 2026-10-19T14:51:36.928194+00:00.

**This run did not complete.** The sandbox executor failed at stage implement. The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): sandbox executor error after 6 model call(s): a sandbox operation's outcome is uncertain; it was not replayed [ref 5b49d539]



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: a sandbox operation's outcome is uncertain; it was not replayed [ref 5b49d539]


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 3 of 20 sealed tests fail on the unmodified base; the candidate was never run against them (E1).
- The run failed in the sandbox executor at stage implement; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | 3 of 20 failed on the base; the candidate was never verified |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | sandbox executor failed at stage implement: a sandbox operation's outcome is uncertain; it was not replayed [ref 5b49d539] |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `344ed4d5-fee4-4482-b6ad-214165157a9f`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.7.0 revision `f836cfd0154faa87` (37 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision6-repairs-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its string-input parsing behavior: replace parse_line's manual index loops with splitting at the first '=' using str.partition, retain whitespace stripping and removal of exactly one matching surrounding quote pair, and extract blank/comment-line detection into a module-level _is_ignorable helper used by parse. Preserve public exports, duplicate-key handling, input validation, and the existing tests without modification.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a str input, partition at the first '='. Strip surrounding whitespace from the key and value using Python str.strip semantics. If the stripped value has len | ValueError: the input string contains no '='.; ValueError: the portion before the first '=' is empty after stripping.; Behavior for non-string arguments is unsp |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Validate input with isinstance(text, str), then process lines in text.splitlines() order. Use _is_ignorable to skip blank and comment lines. Pass each remaining | TypeError: text is not an instance of str, including None, integers, lists, mappings, and bytes.; ValueError: any non-ignorable line lacks '=' or has an empty s |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper for string lines. Return True exactly when line.strip() is empty or begins with '#' or ';'; otherwise return False. Return a bool. parse mus | Behavior for non-string arguments is unspecified and must not be tested. |

Acceptance criteria:
AC1. 1. parse_line returns the exact tuples for these inputs: 'a=b' → ('a', 'b'); ' a = b ' → ('a', 'b'); 'a==b' → ('a', '=b'); 'a = b = c' → ('a', 'b = c'); 'a=' → ('a', ''); 'k e y = v' → ('k e y', 'v').
AC2. 2. parse_line removes exactly one matching outer quote pair: "q = \"x\"" → ('q', 'x'); "q = 'x'" → ('q', 'x'); "q = ''" → ('q', ''); 'q = ""' → ('q', ''); 'q = " spaced "' → ('q', ' spaced '); 'u = "a" "b"' → ('u', 'a" "b').
AC3. 3. parse_line preserves unmatched, mismatched, and lone quotes: a value consisting of double quote, x, single quote remains those exact three characters; a value consisting of a lone double quote or lone single quote remains unchanged. Nested matching quote pairs lose only the outermost pair.
AC4. 4. parse_line strips whitespace according to str.strip, including tabs and Unicode whitespace, while preserving all interior key/value characters, additional '=' characters, backslashes, and quote contents. It performs no escape decoding or inline-comment removal.
AC5. 5. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1', and generally for every string with no '=' or an empty stripped key.
AC6. 6. parse_line treats '#' and ';' as ordinary characters: '#k=v' and ';k=v' produce key/value tuples, while '# comment' without '=' raises ValueError.
AC7. 7. _is_ignorable returns True for '', whitespace-only strings, '   # c', and '\t; c'; it returns False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'. Its result follows the stated strip-and-prefix rule for all string inputs.
AC8. 8. parse('') == {} and parse('k = v') == {'k': 'v'}. Text containing only blank lines and full-line comments returns {}. Comment lines are ignored even when they contain no '='.
AC9. 9. parse retains text.splitlines() semantics for all supported line boundaries, including LF, CRLF, CR, and Unicode line separators. Leading/trailing blank lines and trailing line endings do not create malformed lines.
AC10. 10. parse processes non-ignorable lines in order, preserves inline '#' and ';' in values, and lets later duplicate keys win. For 'a=1\nb=2\na=3', the result is {'a': '3', 'b': '2'} with key iteration order ['a', 'b'].
AC11. 11. parse raises ValueError for a malformed non-ignorable line at the beginning, middle, or end of otherwise valid text, including lines without '=' and lines with an empty stripped key.
AC12. 12. parse raises TypeError for None, 3, a list, a mapping, and bytes, retaining its isinstance(text, str) input validation.
AC13. 13. Structural inspection confirms that parse_line uses str.partition with '=' to split at the first separator, replaces the manual index loops, and contains no while loop.
AC14. 14. Structural inspection confirms that _is_ignorable is defined at module scope in kvparse/parser.py and that parse calls it to decide which lines to skip.
AC15. 15. Both 'from kvparse import parse, parse_line' and imports from kvparse.parser continue to work with the existing public signatures.
AC16. 16. The existing tests under tests/ remain unchanged and pass. Added verification must not assert behavior for non-string arguments to parse_line or assert exception-message text.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. For plain string inputs, partitioning at the first '=' preserves the existing parser's behavior, including whitespace stripping, quote handling, and malformed-line errors. Extracting the ignorable-line check is compatible with all criteria, unchanged exports, existing tests, and the write scope. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `83ead5a8a03a1a9fa35e00d05e61e537f2597fa1fc2ffad3b4371e16dad05e36`, 20 test methods, sealed at 2026-10-19T14:48:41.821014+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (3 of 20 methods: FAIL 3): 3 of 20 methods failing, 17 passing; operation `01a154a2-c638-775b-b126-9d20ac47bb5d`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestParse.test_all_splitlines_boundaries_are_processed | ok (1 ev) | - |
| test_sealed.TestParse.test_blank_and_full_line_comments_are_ignored | ok (1 ev) | - |
| test_sealed.TestParse.test_duplicate_key_overwrites_without_moving_its_position | ok (1 ev) | - |
| test_sealed.TestParse.test_empty_and_single_line_text | ok (1 ev) | - |
| test_sealed.TestParse.test_inline_comment_markers_remain_in_values | ok (1 ev) | - |
| test_sealed.TestParse.test_malformed_non_ignorable_lines_raise_at_every_position | ok (1 ev) | - |
| test_sealed.TestParse.test_module_level_helper_follows_strip_and_prefix_rule | FAIL (1 ev) | - |
| test_sealed.TestParse.test_non_string_text_raises_type_error | ok (1 ev) | - |
| test_sealed.TestParse.test_package_and_parser_module_exports_match | ok (1 ev) | - |
| test_sealed.TestParse.test_parse_calls_helper_for_each_input_line | FAIL (1 ev) | - |
| test_sealed.TestParse.test_str_subclass_is_accepted | ok (1 ev) | - |
| test_sealed.TestParseLine.test_comment_markers_are_ordinary_line_characters | ok (1 ev) | - |
| test_sealed.TestParseLine.test_empty_stripped_key_raises_value_error | ok (1 ev) | - |
| test_sealed.TestParseLine.test_first_separator_and_surrounding_spaces | ok (1 ev) | - |
| test_sealed.TestParseLine.test_literal_value_content_is_preserved | ok (1 ev) | - |
| test_sealed.TestParseLine.test_missing_separator_raises_value_error | ok (1 ev) | - |
| test_sealed.TestParseLine.test_one_matching_outer_quote_pair_is_removed | ok (1 ev) | - |
| test_sealed.TestParseLine.test_partition_is_used_without_index_loops | FAIL (1 ev) | - |
| test_sealed.TestParseLine.test_strip_uses_python_whitespace_semantics | ok (1 ev) | - |
| test_sealed.TestParseLine.test_unmatched_mismatched_and_nested_quotes | ok (1 ev) | - |


## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11113 | 1548 | 0 | - | 61.8s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 13497 | 103 | 0 | - | 69.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 11485 | 5135 | 7168 | - | 135.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 11087 | 115 | 7168 | - | 60.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 11633 | 559 | 0 | - | 31.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11760 | 144 | 7168 | - | 23.6s | ok |

Model calls: 6 (0 failed, 0 malformed); tokens in/out/cached 70575/7604/21504; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1549e-9c03-749a-bdef-fb5c6943bde5 | SUCCESS | 0 | 0.763s | retained | off | 0.00295559 |
| red-1 | 01a154a2-c638-775b-b126-9d20ac47bb5d | SUCCESS | 0 | 7.793s | disposable | off | 0.0677284 |
| impl-tests-3 | None | UNCERTAIN | None | - | disposable | off | None |

Sandbox operations: 3, total guest duration 8.556s, retained images ['344ed4d5-fee4-4482-b6ad-214165157a9f'].

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

## 12. E7 Failure record
Component: sandbox executor; stage: implement; model calls 6 (0 failed); sandbox operations 3; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: yes.

- a sandbox operation's outcome is uncertain; it was not replayed [ref 5b49d539]

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
