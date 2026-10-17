# Attest Proof Bundle: Accept unit suffixes in parse_duration

**Verdict: ERROR**  
Run `durationkit-units-001-20261015T092047Z` · profile `submission-pilot` · provider `nebius_tokenfactory` · executor `tf_sandboxes`  
Started 2026-10-15T09:20:47.219360+00:00, finished 2026-10-15T09:20:54.139130+00:00.

Reasons: model provider: HTTP 422 from https://api.tokenfactory.nebius.com/v1/chat/completions: [{'type': 'missing', 'loc': ['body', 'response_format', 'json_schema', 'name'], 'msg': 'Field required', 'input': {'type': 'object', 'additionalProperties': False, 'properties': {'feasible': {'type': 'boolean'}, 'infeasibility_reason': {'type': ['string', 'null']}, 'restated_task': {'type': 'string'

## 1. Frozen task
Task `durationkit-units-001`, spec digest `e51653cf1b317948395923522095ddf1b6d11db0574120e38c3472448f457b8c`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `532a8fa2-ec1a-4fd5-99c2-2f21b1d07dc7`.

Users want to write durations such as '1h30m' instead of counting seconds. Extend parse_duration(text) so that, in addition to the existing plain-integer-seconds form, it accepts one or more components made of a non-negative integer followed by a unit: d (days), h (hours), m (minutes), s (seconds) or ms (milliseconds). Components must appear in descending unit order (for example '2d4h', '1h30m', '45m10s', '1s500ms'), each unit may appear at most once, and whitespace is allowed around the whole string and between components (but not between a number and its unit). The function keeps returning the total number of seconds as a float (so '500ms' is 0.5 and '1h30m' is 5400.0). Reject with ValueError: empty or whitespace-only input, negative numbers, fractional numbers, unknown units, repeated units, components out of descending order, a unit without a number, and any other malformed text. Keep raising TypeError for non-string input. The existing tests in tests/ must keep passing and must not be modified.

## 2. Specification and contract
Feasible: None. (specification stage did not complete)

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |

Acceptance criteria:
(none)

## 3. Sealed tests (written before implementation by an independent model instance)
`None` sha256 `None`, 0 tests, sealed at None by `None`; attempts: 0.

Red check on the unmodified checkpoint: n/a (0 failing of 0 ran; operation `None`).

| Sealed test | Base (red) | Candidate |
| --- | --- | --- |

## 4. Candidate patch
0 changed path(s); scope check not run; 0 implementer turn(s).

```diff
(no changes)
```

## 5. Fresh-branch verification
Existing suite: n/a (0 passed of 0). Sealed suite: n/a (0 passed of 0). Operation `None`, networking disabled, disposable branch from the checkpoint.

## 6. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nebius_tokenfactory:nvidia/Nemotron-3-Ultra-550b-a55b | spec | spec | default | - | - | - | 1.7s | error |

Model calls: 1 (1 failed, 0 malformed); tokens in/out/cached 0/0/0; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a13edd-4ecb-7638-b26b-ca0dc70586b7 | SUCCESS | 0 | 0.799s | retained | 0.0028060900000000002 |

Sandbox operations: 1, total guest duration 0.799s, retained images ['532a8fa2-ec1a-4fd5-99c2-2f21b1d07dc7'].

## 7. Limitations of this bundle
- Profile 'submission-pilot': inference provider nebius_tokenfactory; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- First slice: single candidate, no breaker/mutation pass, no drift audit, no Tavily grounding, no arbitration of disputed sealed failures.
- Sealed tests are authored by a separate request with no access to the implementation; they share the provider account but not the context.
- Sandbox CPU/RAM quotas are not configurable through the public REST schema; only max_layer_bytes, a timeout and networking=off are enforced per operation.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge.
- The retained checkpoint image stays on the service (no documented delete endpoint) and is listed in the ledger.
