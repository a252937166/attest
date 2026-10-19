# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: INFEASIBLE**  
Run `kvparse-refactor-001-attest-a1-20261019T082112441408Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T08:21:12.441942+00:00, finished 2026-10-19T08:26:07.442967+00:00.

**This task cannot be implemented as stated.** The contract auditor claimed that requirements AC1, AC2, AC16 cannot both hold, and its witness program demonstrated the conflict when Attest ran it on the unmodified repository in a sandbox (exit code 3, operation 01a15344-a27e-74c9-b84f-2000ed6798d7). No sealed tests were written and no implementation was attempted. The witness's reasoning is the model's; its execution and output are recorded.

Key evidence (contract_audit): CONTRADICTION AC1 AC2 AC16: For ZeroLengthString('a=b') with __len__ returning 0, the original outcome is ('exception', 'ValueError') while the required partition-and-strip outcome is ('return', ('a', 'b')).



What to do: Read the witness program and its output in contract_audit/; it names the input on which the requirements conflict. Revise the task statement or the contract so the conflict disappears, then run again.

Reasons: contract contradiction demonstrated by an executed witness (requirements AC1, AC2, AC16): The universal string-input preservation requirement includes str subclasses. A subclass containing 'a=b' but overriding __len__ to return zero makes the original parse_line raise ValueError, whereas t; witness output: CONTRADICTION AC1 AC2 AC16: For ZeroLengthString('a=b') with __len__ returning 0, the original outcome is ('exception', 'ValueError') while the required partition-and-strip outcome is ('return', ('a',


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- A witness program written by the contract auditor demonstrated the contract's contradiction when executed on the unmodified repository (contract_audit).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the witness's reasoning is sound beyond what its recorded output shows: the program is the model's, only its execution is Attest's.
- Anything about a candidate patch: none was verified in this run.

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `5178fdb4-682f-40f6-b335-6f93ec9546d8`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.5.0 revision `1e12d46217fb6b8a` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-audit-repairs-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py while preserving its string-input behavior: replace parse_line's index loops with partitioning at the first '=', retain whitespace stripping and removal of exactly one matching outer quote pair, and extract blank/comment-line detection into a module-level _is_ignorable helper used by parse. Preserve parsing results, error types, duplicate-key handling, public exports, and the existing tests; exception messages and parse_line behavior for non-string arguments are outside the contract.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line (also exported as kvparse.parse_line) | parse_line(line) | For a string argument, use str.partition with '=' to separate the key from the value at the first occurrence. Strip both parts using default str.strip semantics | ValueError: the string contains no '='.; ValueError: the portion preceding the first '=' is empty after stripping.; Non-string arguments: unspecified; no tests  |
| kvparse.parser.parse (also exported as kvparse.parse) | parse(text) | Retain the isinstance(text, str) input check. Iterate over text.splitlines() in order, use _is_ignorable to skip blank and whole-line comments, and parse each r | TypeError: text is not an instance of str, including None, integers, lists, and bytes.; ValueError: any non-ignorable line lacks '=' or has an empty stripped ke |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper returning a bool. For a string argument, return True exactly when line.strip() is empty or starts with '#' or ';'; return False otherwise. p | Non-string arguments: outside the specified contract. |

Acceptance criteria:
AC1. 1. parse_line uses str.partition with '=' to split at the first separator, contains no while loop, and replaces the hand-rolled index loops rather than reproducing them with another character-collection loop.
AC2. 2. parse_line('a=b') == ('a', 'b'); parse_line(' a = b ') == ('a', 'b'); parse_line('a==b') == ('a', '=b'); parse_line('a = b = c') == ('a', 'b = c'); parse_line('a=') == ('a', ''); parse_line('k e y = v') == ('k e y', 'v').
AC3. 3. Both matching single and double outer quotes are removed exactly once: parse_line('q = "x"') == ('q', 'x'); parse_line("q = 'x'") == ('q', 'x'); parse_line("q = ''") == ('q', ''); parse_line('q = ""') == ('q', '').
AC4. 4. Mismatched quotes and lone quotes are retained: parse_line('q = "x\'') == ('q', '"x\''); parse_line('q = "') == ('q', '"'); parse_line("q = '") == ('q', "'").
AC5. 5. Quote removal preserves all interior characters and whitespace: parse_line('q = " spaced "') == ('q', ' spaced ''); parse_line('u = "a" "b"') == ('u', 'a" "b'). Nested matching quote pairs are not recursively removed, and backslashes are not interpreted.
AC6. 6. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1'. Exception-message text is unrestricted.
AC7. 7. Default Python str.strip whitespace semantics are preserved for keys, values, and ignorable-line detection, including Unicode whitespace. parse_line itself does not split on line breaks or treat comment markers specially.
AC8. 8. _is_ignorable exists at module scope, has a bool return annotation, and returns True for '', whitespace-only strings, '   # c', and '\t; c'; it returns False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'. Its predicate is exactly the specified stripped-line rule.
AC9. 9. parse uses _is_ignorable to decide whether to skip each line and passes non-ignored original lines to parse_line.
AC10. 10. parse('') == {}; parse('k = v') == {'k': 'v'}; parse('# comment\n\n; other\nname = x\n') == {'name': 'x'}. Leading whitespace before comment markers is accepted, including for comments without '='.
AC11. 11. parse retains text.splitlines() semantics, including Windows CRLF, lone CR, other Python-recognized line boundaries, and trailing line endings. For example, parse('a=1\r\nb=2\r\n') == {'a': '1', 'b': '2'}.
AC12. 12. Later duplicate keys win after stripping: parse(' a = 1\nb=2\na=3') == {'a': '3', 'b': '2'}, with key iteration order ['a', 'b'].
AC13. 13. Inline comment characters remain part of values: parse('a = # text\nb = ; text') == {'a': '# text', 'b': '; text'}.
AC14. 14. parse raises ValueError for a malformed non-ignorable line at the beginning, middle, or end of input, including malformed lines following valid assignments or duplicate keys.
AC15. 15. parse raises TypeError for None, 3, a list, and bytes, and retains its isinstance-based string validation.
AC16. 16. For every string input, parse and parse_line preserve the supplied implementation's exact returned string contents and results or exception types; no normalization beyond the specified existing operations is introduced. Tests must not prescribe parse_line behavior for non-string arguments.
AC17. 17. from kvparse import parse, parse_line remains valid and exposes the corresponding functions from kvparse.parser.
AC18. 18. All existing tests in tests/ pass without modifying any test files.

## 2b. Contract audit (executed witnesses)
Outcome: contradiction demonstrated. Auditor `gpt-6-astra`; consistent=False. For ordinary built-in strings, the requested refactor is consistent with the supplied implementation and tests. Restricting behavioral preservation to inputs with type(line) is str would remove this subclass conflict. Rule: a conflict is demonstrated only when it names existing acceptance criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

| Requirements | Claimed conflict | Witness result | Exit | First output line | Operation |
| --- | --- | --- | --- | --- | --- |
| AC1, AC2, AC16 | The universal string-input preservation requirement includes str subclasses. A subclass containing 'a=b' but overriding __len__ to return zero makes the origina | demonstrated | 3 | CONTRADICTION AC1 AC2 AC16: For ZeroLengthString('a=b') with __len__ returning 0, the original outcome is ('exception', 'ValueError') while the required partiti | 01a15344-a27e-74c9-b84f-2000ed6798d7 |

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.


(none)


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
Grounding not configured.



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11096 | 1631 | 0 | - | 107.9s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12451 | 719 | 7552 | - | 164.9s | ok |

Model calls: 2 (0 failed, 0 malformed); tokens in/out/cached 23547/2350/7552; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15340-505b-72e5-bd25-08dd58dcab68 | SUCCESS | 0 | 0.848s | retained | off | 0.00284534 |
| witness-1 | 01a15344-a27e-74c9-b84f-2000ed6798d7 | SUCCESS | 0 | 0.633s | disposable | off | 0.00122222 |

Sandbox operations: 2, total guest duration 1.481s, retained images ['5178fdb4-682f-40f6-b335-6f93ec9546d8'].

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
