# Attest Proof Bundle: Behaviour-preserving refactor of kvparse.parser

**Verdict: NEEDS HUMAN**  
Run `kvparse-refactor-001-attest-a2-20261021T030957779881Z` · profile `eval-attest-a2` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-21T03:09:57.780589+00:00, finished 2026-10-21T03:11:26.584831+00:00.

**Hold this patch.** The gates did not all pass. The recorded reasons name what failed; nothing was certified.

Key evidence (gates): could not seal a valid acceptance-test suite: the module has a syntax error: unexpected character after line continuation character (test_sealed.py, line 1); the module has a syntax error: unterminate



What to do: Read the recorded reasons and the gates table; resolve each failure, then run again.

Reasons: could not seal a valid acceptance-test suite: the module has a syntax error: unexpected character after line continuation character (test_sealed.py, line 1); the module has a syntax error: unterminated string literal (detected at line 57) (test_sealed.py, line 57); the module has a syntax error: unterminated string literal (detected at line 61) (test_sealed.py, line 61)


## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- nothing: no gate was reached

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | not run | bound | not reached |
| E2 | Mutation check | not run | bound | not reached |
| E3 | Tests written after the patch | not run | bound | not reached |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | not run | model | not reached |

## 1. Frozen task and provenance
Task `kvparse-refactor-001`, spec digest `4c9587b9205c67694afee4df03fb99814ed1602348c1a6c53430347db6bfddd2`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `2882216e-eca3-40a6-8418-b3f1729e647e`; test runner `unittest`; install: `none` (checkpoint networking off).

Attest 0.10.0 revision `7e72364f135c45c8` (37 package sources; git commit 953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/scratchpad/r11-eval/attest-eval/reports/attest-evaluation-2026-10-21-nebius-r10/snapshot/attest`.

Sampling (nebius_tokenfactory): temperature 0.2, max_tokens 16000; spec: nvidia/Nemotron-3-Ultra-550b-a55b; seal: nvidia/nemotron-3-super-120b-a12b; implement: nvidia/nemotron-3-super-120b-a12b; break: nvidia/nemotron-3-super-120b-a12b; audit: nvidia/Nemotron-3-Ultra-550b-a55b; arbitrate: nvidia/Nemotron-3-Ultra-550b-a55b; summary: nvidia/Nemotron-3_5-Lightning.

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: none (task authored for this project, not taken from an external repository).

Refactor kvparse/parser.py without changing any behaviour. Two changes are requested. (1) parse_line(line) must be rewritten without the hand-rolled index loops: split the line at the first '=' with str.partition, strip the key and the value, raise ValueError when there is no '=' or the stripped key is empty, and remove one pair of matching surrounding quotes (both ends '"' or both ends "'") from a stripped value of length two or more; the function must not contain a 'while' loop. (2) Extract the detection of ignorable lines into a module-level function _is_ignorable(line) -> bool in kvparse/parser.py that returns True exactly when the stripped line is empty or starts with '#' or ';', and make parse use it. The observable behaviour of parse and parse_line must stay byte-for-byte identical for every str input: the same return values, the same exception types in the same situations (TypeError for non-string input to parse, ValueError for a malformed line), later duplicate keys still win, and quotes are removed only when the stripped value starts and ends with the same quote character (a value like '"x\'' keeps both characters; a lone '"' is kept). Exception messages are not prescribed. parse keeps raising TypeError for non-string input; what parse_line does with a non-string argument (for example a list or a mapping) is unspecified and must not be tested, because the required use of str.partition changes it. Keep the public names parse and parse_line exported from kvparse, do not modify the tests, and keep the existing suite passing.

## 2. Specification and contract
Feasible: True. Refactor kvparse.parser.parse_line to use str.partition instead of manual index loops, stripping key and value, raising ValueError for missing '=' or empty key, and removing matching surrounding quotes from values of length >=2; also extract the ignorable-line detection into a private module-level function _is_ignorable that returns True for lines that are empty or start with '#' or ';' after stripping, and update parse to use it. The observable behavior of parse and parse_line must remain identical for all string inputs, including exception types and duplicate-key handling; parse must still raise TypeError for non-string input. The existing test suite must pass unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_line | parse_line(line: str) -> tuple[str, str] | Split the input line at the first '=' using str.partition. Strip whitespace from the key part and the value part. If no '=' is found, raise ValueError. If the s | ValueError if line contains no '='; ValueError if stripped key is empty |
| parse | parse(text: str) -> dict[str, str] | If text is not a string, raise TypeError. Split text into lines with splitlines(). For each raw line, if _is_ignorable(raw) returns True, skip it. Otherwise, ca | TypeError if text is not a str; ValueError if any non-ignorable line causes parse_line to raise ValueError |
| _is_ignorable | _is_ignorable(line: str) -> bool | Strip the input line. Return True if the stripped line is empty or its first character is '#' or ';'. Otherwise return False. |  |

Acceptance criteria:
AC1. parse_line('a=b') returns ('a','b').
AC2. parse_line(' a = b ') returns ('a','b').
AC3. parse_line('a==b') returns ('a','=b').
AC4. parse_line('a = b = c') returns ('a','b = c').
AC5. parse_line('a=') returns ('a','').
AC6. parse_line('q = "x"') returns ('q','x').
AC7. parse_line("q = 'x'") returns ('q','x').
AC8. parse_line('q = "x\'') returns ('q','"x\'').
AC9. parse_line('q = "') returns ('q','"').
AC10. parse_line("q = ''") returns ('q','').
AC11. parse_line('q = " spaced "') returns ('q',' spaced ').
AC12. parse_line('k e y = v') returns ('k e y','v').
AC13. parse_line('u = "a" "b"') returns ('u','a" "b').
AC14. parse_line raises ValueError for ''.
AC15. parse_line raises ValueError for 'novalue'.
AC16. parse_line raises ValueError for ' = v'.
AC17. parse_line raises ValueError for '   '.
AC18. parse_line raises ValueError for '='.
AC19. parse_line raises ValueError for '\t= 1'.
AC20. parse_line contains no 'while' loop and uses str.partition.
AC21. parse('') returns {}.
AC22. parse('k = v') returns {'k': 'v'}.
AC23. parse handles comments: parse('# comment\n\n; other\nname = x\n') returns {'name': 'x'}.
AC24. parse handles blank lines and Windows line endings (e.g., '\r\n') as before.
AC25. parse later duplicate keys win: parse('a=1\na=2') returns {'a': '2'}.
AC26. parse raises ValueError for a malformed line anywhere in the text (e.g., parse('novalue\n') raises ValueError).
AC27. parse raises TypeError for non-string input (None, 3, a list, bytes).
AC28. _is_ignorable exists in kvparse.parser and returns True for '   # c', '', '\t; c'.
AC29. _is_ignorable returns False for 'a = 1' and 'a = # not a comment'.
AC30. The existing tests in tests/ pass unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `nvidia/Nemotron-3-Ultra-550b-a55b`; consistent=True. All authoritative criteria TC1-TC8 are mutually consistent and compatible with the existing test suite. The refactoring can be implemented using str.partition and a helper _is_ignorable without changing observable behavior. Rule: a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; it is GROUNDED, and may end the run as infeasible, only when every named requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language attest-witness/1 (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 3.

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
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 2046 | 3831 | 0 | 0.013539 | 11.1s | ok |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit | default | 4155 | 4695 | 0 | 0.018240 | 14.2s | malformed |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | audit | contract-audit-repair | default | 4216 | 3362 | 0 | 0.014302 | 11.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | low | 2533 | 1920 | 0 | 0.002488 | 16.6s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-2 | low | 2580 | 1963 | 0 | 0.002541 | 14.1s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-3 | low | 2589 | 2085 | 0 | 0.002653 | 14.7s | ok |

Model calls: 6 (1 failed, 1 malformed); tokens in/out/cached 18119/17856/0; Inference USD: 0.053763.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a15c70-01ab-74c4-859a-b814d0937d61 | SUCCESS | 0 | 0.885s | retained | off | 0.00290182 |

Sandbox operations: 1, total guest duration 0.885s, retained images ['2882216e-eca3-40a6-8418-b3f1729e647e'].

Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics with no confirmed currency, and Tavily used 0 search call(s) (section 9).

## 11. Limitations of this bundle
- Profile 'eval-attest-a2': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- Once an operation's outcome is uncertain, or a record of the run cannot be made durable, the run sends nothing further and ends ERROR with every unsettled operation listed under reconciliation; such operations are settled by a human against the providers' records, never by sending them again. Operations being polled in parallel when the run stops are not read further and are listed too.
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
