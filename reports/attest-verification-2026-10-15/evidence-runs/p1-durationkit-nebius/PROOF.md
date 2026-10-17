# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: ERROR**  
Run `durationkit-units-001-20261015T151812Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T15:18:12.963182+00:00, finished 2026-10-15T15:21:15.556085+00:00.

Reasons: model provider: inference outcome uncertain (JSONDecodeError: Unterminated string starting at: line 1 column 241 (char 240)); not retried (outcome uncertain; not retried)


## 1. Frozen task
Task `durationkit-units-001`, spec digest `572a5c9489d23c03f83a38a8beb62ae99ee9e10e5b1d6fbdb161d892631311fe`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `df494740-3eb2-4f7f-a449-490cf910e669`; test runner `unittest`; install: `none` (checkpoint networking off).

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: True. Extend parse_duration to accept duration strings composed of one or more components (non-negative integer followed by unit d, h, m, s, ms) in descending unit order, with optional whitespace around the whole string and between components, while preserving the existing plain-integer-seconds behavior. Return total seconds as float. Reject malformed input with ValueError and non-string input with TypeError.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| parse_duration | parse_duration(text: str) -> float | Parses a duration string and returns the total number of seconds as a float. Accepted formats: (1) a plain non-negative integer (seconds) with optional surround | TypeError: if text is not a string; ValueError: if text is empty or whitespace-only; ValueError: if any component has a negative number; ValueError: if any comp |

Acceptance criteria:
1. 1. parse_duration('90') == 90.0 and surrounding whitespace is still ignored (existing behavior preserved).
2. 2. parse_duration('0') == 0.0 and parse_duration('0s') == 0.0.
3. 3. Single components work for every unit: '2d' -> 172800.0, '3h' -> 10800.0, '15m' -> 900.0, '45s' -> 45.0, '500ms' -> 0.5.
4. 4. Combined components in descending order work: '1h30m' -> 5400.0, '2d4h' -> 187200.0, '1m1s' -> 61.0, '1s500ms' -> 1.5, '1d1h1m1s1ms' -> 90061.001.
5. 5. Whitespace is accepted around the string and between components: ' 1h 30m ' -> 5400.0; '1 h' raises ValueError (no space between number and unit).
6. 6. ValueError for empty or whitespace-only input: '' and '   '.
7. 7. ValueError for negative numbers: '-1h'.
8. 8. ValueError for fractional numbers: '1.5h'.
9. 9. ValueError for unknown units: '1x'.
10. 10. ValueError for repeated units: '1h1h'.
11. 11. ValueError for components out of descending order: '30m1h'.
12. 12. ValueError for unit without a number: 'h'.
13. 13. ValueError for number without a unit (except plain integer): '1h30'.
14. 14. ValueError for completely malformed text: 'abc'.
15. 15. TypeError for non-string input such as 90 or None.
16. 16. The return type is float for every accepted input.
17. 17. Existing tests in tests/test_parse.py continue to pass without modification.

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 test methods, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint (one child process per test under the supervisor): n/a: 0 of 0 methods failing, 0 passing; operation `None`.

(none)

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification (bound to the sealed suite)
Existing suite: n/a (0 passed of 0). Sealed suite: n/a. Operation `None`, networking disabled, disposable branch from the checkpoint.

(none)

Held-out suite: none configured.

## 6. Gates
(none)

## 7. Breaker pass
Mutation pass not run (verification did not pass).

(none)

Model-written adversarial tests: not run.



## 8. Drift audit
Drift audit not run.



## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | 1622 | 1890 | 0 | 0.007292 | 6.9s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-1 | default | 1764 | 7786 | 0 | 0.007537 | 33.2s | ok |
| nebius_tokenfactory:nvidia/nemotron-3-super-120b-a12b | seal | seal-2 | default | - | - | - | - | 137.3s | error |

Model calls: 3 (1 failed, 0 malformed); tokens in/out/cached 3386/9676/0; USD: 0.014829.

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14024-8b2d-749e-81ea-39653c9c7926 | SUCCESS | 0 | 0.764s | retained | off | 0.00280033 |

Sandbox operations: 1, total guest duration 0.764s, retained images ['df494740-3eb2-4f7f-a449-490cf910e669'].

## 11. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code; a candidate can still tamper from inside a child after the nonce was read (the mutation gate and held-out tests are the structural detectors).
- Model-written adversarial tests can be wrong; their failures block VERIFIED and are listed for a human, not arbitrated automatically.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
