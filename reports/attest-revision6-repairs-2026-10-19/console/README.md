# Item 2: malformed admission requests can no longer start paid runs (19 October 2026)

Finding (revision-6 review, item 2): `attest/app/server.py` declared `RunRequest.provider: str = "nebius"` and accepted unknown
fields. The post-deployment verification of 19 Oct 2026 sent `POST /api/runs?token=junk` with
`{"task_id": "durationkit-units-001", "profile": "development"}`; `profile` was ignored, the provider defaulted to Nebius, and the
console admitted an ordinary public Nemotron run. It made 16 model calls before it was stopped by a service restart; its
journal-accounted cost is $0.055226 (computed by the console from the returned usage and the public price table; not a provider
invoice, billing-page reading or card charge). It was not an approved smoke test. The incident record stays as written in
`reports/attest-deployment-2026-10-19c/README.md`, with a dated clarification of its accounting appended there.

## What changed

- `RunRequest` (`attest/app/server.py`): `model_config = ConfigDict(extra="forbid")`; `task_id` required (1 to 200 characters);
  `provider` required with no default (1 to 40 characters) and validated against `SUPPORTED_PROVIDERS` in code, so the public
  OpenAPI schema names no gateway; `admin_token` optional (at most 512 characters). The handler's own provider check stays as a
  guard and answers 422 as well.
- A `RequestValidationError` handler answers every malformed request with 422 and
  `{"error": "invalid_request", "detail": "invalid request: <field>: <rule>; ...", "errors": [{"field", "problem", "type"}]}`.
  The submitted values are never echoed (FastAPI's default handler returns them as `input`, which would echo an admin token
  sent in a malformed body).
- Validation runs before the handler, so a refused request never reaches `Worker.enqueue`: no row, no queue entry, no budget
  reservation (a queued or running row is the reservation) and no provider.
- The console client already sends `provider` explicitly (`attest/app/static/app.js`); unchanged. Asset stamp unchanged.

## Local verification (idle worker, blocked runtime builder, blocked sockets)

`tests/test_audit_console.py::StrictRunRequests`, with the existing `DownloadTickets`, `TeamVisibility` and `tests/test_console.py`;
output in `unittest-strict-requests.txt` (32 tests, all passing). The harness gives every test class a fresh application with an
idle worker loop, `Worker.build_runtime` replaced by a recorder that raises, and `socket.connect`, `connect_ex` and
`create_connection` blocked; `Worker.enqueue` is wrapped by a recorder.

| Requirement | Test | Result |
| --- | --- | --- |
| `profile` supplied instead of `provider` returns 422 | `test_the_incident_request_is_refused_and_leaves_no_trace` (the incident's exact body, with and without the junk query token) | 422, `provider: Field required; profile: Extra inputs are not permitted` |
| missing or invalid `provider` returns 422 | `test_missing_invalid_and_extra_fields_are_refused_before_admission` | 422 for a missing, empty, unknown (`openai`), wrongly cased (`Nebius`), null, numeric and list provider, an extra field next to a valid provider, a missing task, a non-object body, an empty body, a form-encoded body and malformed JSON, each as a visitor and with the team token in the header; a synthetic admin token sent in a malformed body never appears in the response |
| rejected requests create no row, queue entry, reservation or provider call | the same two tests (`assert_refused_without_trace`) | after every refusal: the row list, the worker's queue size and queued ids, the public budget's `reserved_usd` and `active_runs` are unchanged; `Worker.enqueue` was never called; the runtime builder was never called |
| valid public and team requests still enforce their authorization rules | `test_valid_requests_keep_their_authorization_rules` | the development profile without the team token: 403 and no row; a public Nemotron request: 200, visibility public; the development profile with the token in the body or in the header: 200, visibility team; an unknown task: 404; the hourly visitor quota still answers 429 |
| download tickets cannot authorize task creation | `test_a_download_ticket_never_authorizes_admission` and the existing `DownloadTickets` tests | a valid ticket in the query, the token header or the body never opens the development profile (403); a malformed body with a ticket is still 422 without trace; a ticket-carrying public request is admitted only as an ordinary visitor (quota applied, judge profile) and refused at the quota (429) without a row |
| the published contract | `test_the_public_schema_declares_the_strict_body_without_naming_the_gateway` | `/api/openapi.json`: `RunRequest.additionalProperties` false, `required` [`provider`, `task_id`], no default and no enum for `provider`, no gateway name in the document |

Earlier admission tests that relied on the removed default now name `"provider": "nebius"` explicitly; the unknown-provider
case in `tests/test_console.py` expects 422 instead of 400.

## Production verification

Read-only GET requests only, after the deployment (`reports/attest-deployment-2026-10-19d/README.md`): `/api/health`,
`/api/profiles`, `/api/runs`, the assets and `/api/openapi.json`, whose `RunRequest` schema shows the strict body. No production
POST was sent to test rejection behaviour; the rejection behaviour is verified by the local tests above.

## Remaining limitations

Schema hardening prevents this particular mistake (a body that does not name its provider); it does not make a valid production
POST free. A well-formed request for the public profile is still a paid Nemotron run by design, so admission must not be probed on
the live host without the owner's approval.
