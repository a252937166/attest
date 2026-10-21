# Evaluation results: r10-final (nebius)

Registered 2026-10-21T01:54:13.728156+00:00; finished 2026-10-21T03:28:55.956223+00:00; complete: True; stopped: no.
Systems ['baseline', 'attest'], 8 tasks, 2 attempt(s) per cell, 32 cells scheduled, 32 completed, 0 not run.
Provenance: commit `953ae59b8c8ef5e54bbadbf2fb2b940b8851fa3a`, package `7e72364f135c45c8`, harness `243ab12f3879ffc6`, examples `e95a28aa36336616`; snapshot intact at end: True; invalid comparisons: none; provider profile: provider=nebius_tokenfactory; roles arbitrate=nvidia/Nemotron-3-Ultra-550b-a55b audit=nvidia/Nemotron-3-Ultra-550b-a55b break=nvidia/nemotron-3-super-120b-a12b implement=nvidia/nemotron-3-super-120b-a12b seal=nvidia/nemotron-3-super-120b-a12b spec=nvidia/Nemotron-3-Ultra-550b-a55b summary=nvidia/Nemotron-3_5-Lightning; reasoning_effort seal=low implement=medium break=low summary=low; temperature=0.2; max_tokens=16000; usd_cap=0.5; max_calls=22; thinking_roles=[]; send_thinking_flag=False.
Budget: committed $1.3871 of an approved 9.0 (per-run cap $0.5).
Services, kept apart: inference on the Nebius Token Factory (USD, public price table): 303 model call records (1 never sent), committed USD 1.387089; Nebius Token Factory Sandboxes (beta): 163 operations in the run ledgers and 22 judge operations, 342.971 s, 0 spawn resend(s), billing not visible to this harness: the Sandboxes console wording says beta runs are free; no invoice-level reconciliation has been done; Tavily: 0 calls (the harness runs the pipeline without Tavily (tavily=None)); 12 item(s) to reconcile. Harness peak resident memory 45.5 MiB.

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | roman-to-numeral | baseline | 1 | completed | ERROR | not judged | infra_error | 7 | 0.008825 | 82.4 s | 7e72364f |
| 1 | roman-to-numeral | baseline | 2 | completed | ERROR | not judged | infra_error | 6 | 0.007908 | 67.1 s | 7e72364f |
| 2 | roman-to-numeral | attest | 1 | completed | ERROR | not judged | infra_error | 10 | 0.038436 | 117.5 s | 7e72364f |
| 3 | roman-to-numeral | attest | 2 | completed | ERROR | not judged | infra_error | 11 | 0.034474 | 120.3 s | 7e72364f |
| 4 | rle-encode | baseline | 1 | completed | BASELINE | not correct | false_accept | 13 | 0.05405 | 473.2 s | 7e72364f |
| 5 | rle-encode | baseline | 2 | completed | BASELINE | not correct | false_accept | 8 | 0.00667 | 54.4 s | 7e72364f |
| 6 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.028404 | 43.2 s | 7e72364f |
| 7 | rle-encode | attest | 2 | completed | NEEDS HUMAN | not correct | true_reject | 13 | 0.070303 | 149.2 s | 7e72364f |
| 8 | balanced-brackets | baseline | 1 | completed | BASELINE | correct | true_accept | 7 | 0.005907 | 55.4 s | 7e72364f |
| 9 | balanced-brackets | baseline | 2 | completed | BASELINE | correct | true_accept | 8 | 0.007284 | 61.3 s | 7e72364f |
| 10 | balanced-brackets | attest | 1 | completed | NEEDS HUMAN | correct | false_reject | 19 | 0.048372 | 253.9 s | 7e72364f |
| 11 | balanced-brackets | attest | 2 | completed | NEEDS HUMAN | correct | false_reject | 12 | 0.031538 | 129.6 s | 7e72364f |
| 12 | durationkit-units-001 | baseline | 1 | completed | ERROR | not judged | infra_error | 6 | 0.015307 | 135.5 s | 7e72364f |
| 13 | durationkit-units-001 | baseline | 2 | completed | ERROR | not judged | infra_error | 6 | 0.013586 | 118.2 s | 7e72364f |
| 14 | durationkit-units-001 | attest | 1 | completed | ERROR | not judged | infra_error | 7 | 0.032107 | 83.5 s | 7e72364f |
| 15 | durationkit-units-001 | attest | 2 | completed | ERROR | not judged | infra_error | 3 | 0.057317 | 75.5 s | 7e72364f |
| 16 | semver-is-compatible-pr368-v2 | baseline | 1 | completed | BASELINE | correct | false_reject | 12 | 0.041002 | 322.4 s | 7e72364f |
| 17 | semver-is-compatible-pr368-v2 | baseline | 2 | completed | BASELINE | correct | true_accept | 13 | 0.055577 | 454.8 s | 7e72364f |
| 18 | semver-is-compatible-pr368-v2 | attest | 1 | completed | NO CHANGE | not correct | no_patch | 16 | 0.124223 | 464.2 s | 7e72364f |
| 19 | semver-is-compatible-pr368-v2 | attest | 2 | completed | NEEDS HUMAN | not correct | false_refusal | 5 | 0.080092 | 105.2 s | 7e72364f |
| 20 | slugkit-regression-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 13 | 0.023107 | 130.3 s | 7e72364f |
| 21 | slugkit-regression-001 | baseline | 2 | completed | BASELINE | correct | true_accept | 6 | 0.00588 | 39.0 s | 7e72364f |
| 22 | slugkit-regression-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 15 | 0.054238 | 171.5 s | 7e72364f |
| 23 | slugkit-regression-001 | attest | 2 | completed | VERIFIED | correct | true_accept | 14 | 0.05651 | 188.2 s | 7e72364f |
| 24 | kvparse-refactor-001 | baseline | 1 | completed | BASELINE | correct | true_accept | 6 | 0.008044 | 40.3 s | 7e72364f |
| 25 | kvparse-refactor-001 | baseline | 2 | completed | BASELINE | correct | true_accept | 9 | 0.013116 | 64.2 s | 7e72364f |
| 26 | kvparse-refactor-001 | attest | 1 | completed | NEEDS HUMAN | not correct | false_refusal | 5 | 0.034374 | 64.1 s | 7e72364f |
| 27 | kvparse-refactor-001 | attest | 2 | completed | NEEDS HUMAN | not correct | false_refusal | 6 | 0.053763 | 88.7 s | 7e72364f |
| 28 | semver-long-prerelease-pr488 | baseline | 1 | completed | BASELINE | not correct | no_patch | 12 | 0.041821 | 171.5 s | 7e72364f |
| 29 | semver-long-prerelease-pr488 | baseline | 2 | completed | BASELINE | correct | true_accept | 9 | 0.036672 | 172.7 s | 7e72364f |
| 30 | semver-long-prerelease-pr488 | attest | 1 | completed | ERROR | not judged | infra_error | 14 | 0.158574 | 316.6 s | 7e72364f |
| 31 | semver-long-prerelease-pr488 | attest | 2 | completed | ERROR | not judged | infra_error | 10 | 0.139608 | 237.0 s | 7e72364f |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (hold without a patch on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 16 | 16 | 8 | 2 | 1 | 0 | 0 | 1 | 4 | 0 | 0 | 0.3448 | 152.7 s |
| attest | 16 | 16 | 2 | 0 | 2 | 2 | 3 | 1 | 6 | 0 | 7 | 1.0423 | 163.0 s |
Starting committed total of this process: $1.387089 = $1.387089 from 32 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-21T03:28:55.956065+00:00).


## Reasons recorded for every non-accepted cell

- cell 0 (roman-to-numeral, baseline): stopped for reconciliation at impl-python-6: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every oper
- cell 1 (roman-to-numeral, baseline): stopped for reconciliation at impl-python-6: the outcome of the impl-python-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref b6ca
- cell 2 (roman-to-numeral, attest): stopped for reconciliation at mutant-m07-ade8d4d4b3: the outcome of the mutant-m07-ade8d4d4b3 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not re
- cell 3 (roman-to-numeral, attest): stopped for reconciliation at implement-9: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operat
- cell 6 (rle-encode, attest): contract contradiction demonstrated by an executed witness in attest-witness/1 on the task's own criteria (requirements TC5): The round-trip property decode(encode(x)) == x for every string x (TC5) conflicts with the fix
- cell 7 (rle-encode, attest): child process nonzero exit: test_encode_roundtrip_property exit 1
- cell 10 (balanced-brackets, attest): implementer did not finish within 14 turns
- cell 11 (balanced-brackets, attest): adversarial suite binding failed: child process nonzero exit: test_bracket_like_characters_not_brackets exit 1; model-written adversarial tests failed: 1 of 10 (test_breaker.TestIsBalancedBreaker.test_bracket_like_characters_not_brackets); each failure is a bug or a contract disagreement to resolve
- cell 12 (durationkit-units-001, baseline): stopped for reconciliation at impl-tests-6: the outcome of the impl-tests-6 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref 8623e6
- cell 13 (durationkit-units-001, baseline): stopped for reconciliation at implement-7: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operat
- cell 14 (durationkit-units-001, attest): stopped for reconciliation at implement-5: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operat
- cell 15 (durationkit-units-001, attest): stopped for reconciliation at red-1: the outcome of the red-1 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref d20a6d56]; it was no
- cell 18 (semver-is-compatible-pr368-v2, attest): unfinished: the turn budget (12 turns) was exhausted without a patch; the implementer neither finished nor changed a file
- cell 19 (semver-is-compatible-pr368-v2, attest): could not seal a valid acceptance-test suite: your coverage map leaves acceptance criteria without any existing test method: AC17; add tests for them and map every cr; your coverage map leaves acceptance criteria without
- cell 26 (kvparse-refactor-001, attest): could not seal a valid acceptance-test suite: the module has a syntax error: unexpected character after line continuation character (test_sealed.py, line 1); the module has a syntax error: unterminated string literal (de
- cell 27 (kvparse-refactor-001, attest): could not seal a valid acceptance-test suite: the module has a syntax error: unexpected character after line continuation character (test_sealed.py, line 1); the module has a syntax error: unterminated string literal (de
- cell 30 (semver-long-prerelease-pr488, attest): stopped for reconciliation at impl-tests-11: the outcome of the impl-tests-11 spawn is uncertain: the sandbox service answered HTTP 500 after the spawn was sent, so its outcome is uncertain; it was not replayed [ref cf62
- cell 31 (semver-long-prerelease-pr488, attest): stopped for reconciliation at implement-8: another run of this batch stopped for reconciliation; this run sent nothing further (another run of the batch stopped for reconciliation; nothing further was sent); every operat

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks a hold that produced no patch (an INFEASIBLE verdict, or a NEEDS HUMAN hold with no patch) on a task whose held-out suite is satisfiable (a wrong refusal); the same hold on a task marked `unsatisfiable` is a `true_reject`. A NEEDS HUMAN hold that did produce a patch is judged on that patch. A task is an invalid comparison when any of its cells ran another revision, provider, limit or effective provider profile (models per role, reasoning effort, sampling) than the registered one. Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
