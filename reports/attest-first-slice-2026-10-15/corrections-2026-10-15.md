# Corrections to the first-slice reporting (recorded 2026-10-15, historical artifacts unchanged)

The run directories and the evidence copies under `codex-development-run/`, `nebius-pilot-run/` and
`nebius-pilot-attempt1-http422/` are preserved exactly as produced. The statements below correct how they were
described in `attest-first-slice.md` and `attest-product-design.md`; the corrected documents cite this file.

## 1. Red-check accounting (unittest subtests)

The first parser recorded one entry per outcome line, so subtest error lines repeated a method's ID. Recomputed from
the stored `red.attempt1.json` events of the Codex development run:

| Measure | Reported before | Corrected |
| --- | --- | --- |
| Test methods in the sealed suite | 27 | 27 |
| Methods failing on the unmodified checkpoint | "24 failing of 27" | 9 methods failing, 18 passing |
| Error events behind those failures | not separated | 24 subtest error events (`FAILED (errors=24)`) |

The Nemotron pilot's red check had no subtests: 28 methods, 13 failing, 15 passing, unchanged. The parser now
aggregates per method and reports events separately (`tests/test_verification.py::SubtestAccounting`); the sealed
suite is additionally executed by a `TestResult` recorder inside the sandbox, so method and event counts no longer
depend on console text.

## 2. Cached-token reporting (claim withdrawn)

All 12 Nemotron responses in the pilot ledger contain `usage.prompt_tokens_details.cached_tokens` with value `0`,
alongside `prompt_cache_hit_tokens` (0) and `prompt_cache_miss_tokens` (equal to the prompt size), plus
`created_cache_tokens` and `completion_tokens_details`. The earlier statement that the API "reports no cached-token
field" was wrong: the field is present and zero. Zero and missing are different states, and the ledger now stores the
raw usage object for every call. The Codex gateway reports `cached_input_tokens`, `cache_write_input_tokens` and
`reasoning_output_tokens`.

## 3. Structured-output documentation (scope of the claim)

Evidence: the retained HTTP 422 body of the first native attempt names exactly one missing field,
`body.response_format.json_schema.name`; the subsequent request wrapped as `{"name", "schema", "strict": true}`
succeeded 12 times. The Token Factory docs' Python and cURL examples pass the raw schema under `json_schema`, which the
live API rejected. What is established: `name` is required and the wrapped form is accepted. Not established: that
`schema` or `strict` were individually validated as mandatory.

## 4. Sandbox capability statements (narrowed)

- File upload: documented by the service (operation tag "file uploads"); not implemented or exercised by the Attest
  adapter, which ships inputs as a base64 stdin job.
- Image deletion and configurable VM CPU/RAM quotas: no corresponding controls were found in the current public REST API
  (`InstanceResourcesLimits` exposes `max_layer_bytes`); behaviour of the CLI 0.9.4 / SDK 0.3.6 surfaces was not
  checked for these two items.
- Outbound networking: verified on 2026-10-15 (operation `01a13fab-fefc-714d-8ef6-8f57ef23b4d4`): with
  `networking.enabled=true` a sandbox resolved and reached pypi.org and installed `pytest==8.3.3` in 1.9 s.

## 5. Specification drift (separated)

The original `parse_duration` already accepted leading zeros and Unicode decimal digits for plain numeric input, because
it used `str.isdigit()` and `float()`. The Codex specification therefore preserved that compatibility for plain input;
the additional assumption it introduced was extending the same acceptance to unit-bearing input ("١h٣٠m"), which the
request did not ask for. The Nemotron specification reproduced the request as given. The Nemotron implementer's turn-7
self-check wrongly expected `"1h 30m"` to raise; the trajectory shows the check being corrected at turn 8, with the
code unchanged.

## 6. Billing reconciliation (official usage view, not an invoice)

The official Token Factory Usage view, read by the account owner after the pilot, lists four Nemotron entries totaling
**$0.0254671**, consistent with the pilot's token counts; the ledger's price-table figure is **$0.025468** (rounding
difference 0.0000009). The console showed **$25.00 main balance and $0.97 trial credit**, i.e. about $0.03 of
consumption offset by trial credit. This is a usage-view reconciliation; final invoices may differ by rounding and lag.
