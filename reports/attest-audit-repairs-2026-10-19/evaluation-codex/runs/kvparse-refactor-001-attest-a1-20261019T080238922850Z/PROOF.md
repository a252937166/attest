# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: ERROR**  
Run `kvparse-refactor-001-attest-a1-20261019T080238922850Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T08:02:38.937910+00:00, finished 2026-10-19T08:07:19.605356+00:00.

**This run did not complete.** The inference provider failed at stage error. Attest did not retry it and certified nothing. The repository was not changed by this run.

Key evidence (E7): inference provider error after 3 model call(s): model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model.



What to do: Start a new run. This failure is infrastructure, not a judgement about the task.

Reasons: model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model.


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The run failed in the inference provider at stage error; nothing was retried (E7).

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- Anything about the patch or the task: no verdict about the candidate was reached (E7).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |
| E7 | Failure record | FAIL | bound | inference provider failed at stage error: model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model. |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c624913c-2ef7-40af-abe6-58d0e8c61b74`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.5.0 revision `722cd6dd1a217c6d` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-audit-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse/parser.py to implement parse_line using str.partition at the first '=' without hand-written index loops or any while loop, and extract blank/comment-line detection into module-level _is_ignorable(line) -> bool used by parse. Preserve all specified string-input behavior, including whitespace handling, matching outer quote removal, malformed-line errors, line splitting, duplicate-key precedence, and public exports. Keep the existing tests unchanged and passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| kvparse.parser.parse_line | parse_line(line) | For string input, partition at the first '=' and apply str.strip() independently to the key and value. Return a two-element (key, value) tuple of strings. If th | ValueError when the input string contains no '='.; ValueError when the portion before the first '=' is empty after str.strip().; Non-string arguments are unspec |
| kvparse.parser.parse | parse(text) | Accept text satisfying isinstance(text, str). Iterate over text.splitlines() in order, use _is_ignorable to skip blank and full-line comments, and pass each rem | TypeError for any argument that does not satisfy isinstance(text, str), including None, integers, lists, and bytes.; ValueError when any non-ignorable line lack |
| kvparse.parser._is_ignorable | _is_ignorable(line) -> bool | Module-level helper for string lines. Return True exactly when line.strip() is empty or begins with '#' or ';'; otherwise return False. Only a leading marker af | Non-string arguments are outside the specified contract and must not be tested. |

Acceptance criteria:
AC1. 1. parse_line uses str.partition with '=' to split at the first separator, contains no while statement, and replaces the hand-written index loops rather than retaining them in another form.
AC2. 2. parse_line('a=b') == ('a', 'b'); parse_line(' a = b ') == ('a', 'b'); parse_line('a==b') == ('a', '=b'); parse_line('a = b = c') == ('a', 'b = c'); parse_line('a=') == ('a', '').
AC3. 3. Keys and values use Python str.strip() whitespace semantics, including tabs and Unicode whitespace. Interior key whitespace is preserved: parse_line('k e y = v') == ('k e y', 'v'). Direct parse_line calls do not split lines or interpret comment markers.
AC4. 4. Matching single or double outer quotes are removed exactly once: parse_line('q = "x"') == ('q', 'x'); parse_line("q = 'x'") == ('q', 'x'); parse_line("q = ''") == ('q', ''); parse_line('q = ""') == ('q', '').
AC5. 5. Mismatched or lone quotes are preserved: parse_line("q = \"x'") == ('q', "\"x'"); parse_line('q = "') == ('q', '"'); parse_line("q = '") == ('q', "'").
AC6. 6. Quote interiors remain unchanged: parse_line('q = " spaced "') == ('q', ' spaced '); parse_line('u = "a" "b"') == ('u', 'a" "b'). Nested quote pairs are not recursively removed and backslash escapes are not interpreted.
AC7. 7. parse_line raises ValueError for each of '', 'novalue', ' = v', '   ', '=', and '\t= 1'. More generally, every string without '=' or with an empty stripped prefix before its first '=' raises ValueError.
AC8. 8. _is_ignorable exists at module scope and returns bool values: True for '', '   ', '   # c', and '\t; c'; False for 'a = 1', 'a = # not a comment', and 'a = ; not a comment'. Its result follows the stated strip-and-prefix rule for every string.
AC9. 9. parse calls _is_ignorable to decide whether each line yielded by text.splitlines() is skipped, and passes retained lines unchanged to parse_line.
AC10. 10. parse('') == {}; parse('k = v') == {'k': 'v'}; parse('# comment\n\n; other\nname = x\n') == {'name': 'x'}. Whitespace-only and indented comment lines are ignored even when they contain no '='.
AC11. 11. parse preserves text.splitlines() behavior for LF, CRLF, CR, and other separators recognized by that method, including trailing line endings. For example, parse('a=1\r\nb=2\r\n') == {'a': '1', 'b': '2'}.
AC12. 12. Later duplicate stripped keys win, with original dict insertion order preserved: parse('a=1\nb=2\n a =3') equals {'a': '3', 'b': '2'} and its keys iterate as ['a', 'b'].
AC13. 13. Inline comment characters remain ordinary data: parse('a = # not a comment\nb = ; not a comment') == {'a': '# not a comment', 'b': '; not a comment'}. Quotes do not make multiline values; parse continues to split text before parsing lines.
AC14. 14. parse raises ValueError for a malformed non-ignorable line at the beginning, middle, or end of otherwise valid input, including an empty-key line.
AC15. 15. parse raises TypeError for None, 3, [], and b'a=b', retaining its isinstance(text, str) input guard.
AC16. 16. For string inputs, parse and parse_line retain the original return values and exception types under the specified rules; exception messages need not match. No tests assert parse_line behavior for non-string arguments.
AC17. 17. Both 'from kvparse import parse, parse_line' and access through kvparse.parser continue to work. The existing tests/ files remain unchanged and their suite passes.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The required partition, stripping, and quote removal match the original string parsing rules. Extracting the ignorable-line check preserves parse behavior, and both changes fit within the write scope without changing exports or existing tests. Rule: a conflict is demonstrated only when it names existing acceptance criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

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
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 11094 | 1651 | 0 | - | 127.2s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 12474 | 119 | 0 | - | 54.2s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | - | - | - | - | 80.4s | error |

Model calls: 3 (1 failed, 0 malformed); tokens in/out/cached 23568/1770/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a1532f-4f56-74a8-9189-bdf9f912eaca | SUCCESS | 0 | 0.791s | retained | off | 0.00294744 |

Sandbox operations: 1, total guest duration 0.791s, retained images ['c624913c-2ef7-40af-abe6-58d0e8c61b74'].

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
Component: inference provider; stage: error; model calls 3 (1 failed); sandbox operations 1; committed cost USD 0.0; uncertain unpriced calls 0; retried: no; outcome uncertain: no.

- model provider: HTTP 502 from development-gateway/run: Selected model is at capacity. Please try a different model.

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
