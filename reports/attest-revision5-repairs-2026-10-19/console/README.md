# R5-07 repair: the team token leaves every URL; downloads use run-scoped tickets (19 October 2026)

Finding R5-07 of the revision-5 follow-up review (`reports/attest-revision5-review-2026-10-19/README.md`, section R5-07;
`api-review.md`, "Team visibility: implemented, with a credential-delivery residual"): the console put the master team token
into download links as `?token=`, and the server accepted that query token as full administrative authority everywhere, so a
copied or logged download URL gave its holder team listings, team enqueue and an exemption from the public visitor quota.
The review observed this with a synthetic token; no real exposure was found.

Offline work only: no live run, no network, no deployment, no git commit. Every credential in the tests is synthetic and
assembled at run time.

## What changed

| File | Change |
|---|---|
| `attest/app/server.py` | The team token is read from the `X-Attest-Token` header only (`_team_caller`); `_caller_token` and the `token` query parameter are gone. New: a per-process signing secret (`secrets.token_bytes(32)` at import), `DOWNLOAD_TICKET_SECONDS` (`ATTEST_DOWNLOAD_TICKET_SECONDS`, default 600), `_now()` (the ticket clock), `mint_download_ticket()`, `ticket_run_id()`, `_download_run()`, `_download_headers()`; route `POST /api/runs/{run_id}/download-ticket`; the artifact and zip routes resolve their row through `_download_run`, which honours `?ticket=` for the embedded run id alone, and send `Cache-Control: no-store` on team downloads. Module docstring updated. |
| `attest/app/static/app.js` | `tokenQuery` removed; `ticketQuery(runId)`, `ensureTicket(run)`, `clearTicket()`, `renewTicket(runId)`, `refreshDownloadLinks()`. A finished team run's case file requests one ticket before it renders (`openRun`, `finishLive`), reuses it for that run view and renews it a minute before expiry, rewriting the rendered links in place. `artUrl`/`zipUrl` append `?ticket=` only for the ticketed run; public runs' links carry nothing. `copyPatch` fetches the plain artifact path with the header (the `data-patch-url` attribute is gone); its no-clipboard fallback navigates to the ticketed link. `showHome`, `openRun` and a sign-in change drop the ticket. The token stays in memory only. |
| `attest/app/static/index.html` | One sentence in the publication paragraph: a team run's download links carry a short-lived ticket; the team token never appears in a link. Asset stamps untouched (`?v=20261019b`; the orchestrator bumps them). |
| `tests/test_audit_console.py` | `TeamVisibility` extended, new `DownloadTickets` class, `ConsoleClient` assertions inverted (see below). `TOKEN`, `_bundle`, `_row` and `ConsoleHarness` keep their names so the review's reproduction still imports them. |
| `tests/test_console.py` | The imported development-profile fixture: `?token=` is refused on every route, a header-minted ticket opens its zip and artifact, not its detail. |
| `tests/console_client_test.mjs` | `copyPatch` is checked for header use and a credential-free URL; new block checks `artUrl`/`zipUrl`/`ensureTicket`. |

`attest/app/db.py` was not needed.

## Mechanism

- **Header only.** `_team_caller(request)` is `_is_admin(request.headers.get("x-attest-token"))`. Every read route (list, detail,
  events, estimates, current-run references, health's `team`/`current`) and `start_run`'s admin decision go through it or
  through the request body's `admin_token`; nothing reads `request.query_params["token"]` any more. A `?token=` caller is an
  anonymous caller: team rows are omitted or 404, the development profile is refused (403), the visitor quota applies (429).
- **Ticket.** `<run_id>.<expiry unix seconds>.<hmac-sha256 hex>`: HMAC-SHA256 over `run_id` and the expiry with a 32-byte secret
  drawn at import. `POST /api/runs/{run_id}/download-ticket` requires the header token (403 otherwise; a body `admin_token`,
  a `?token=` or a ticket do not count) and a run visible to the caller (404 otherwise); it returns
  `{"run_id", "ticket", "expires_at" (ISO 8601 UTC), "expires_in_s"}`. `ticket_run_id()` splits from the right (run ids may
  contain dots), requires a decimal expiry and 64 lower-case hex digits, compares the signature with `hmac.compare_digest`
  and refuses the ticket once `_now() >= expiry`.
- **Scope.** Only the artifact and zip routes consult `?ticket=` (`_download_run`): a row is served when it is public, when the
  caller has the header token, or when the ticket's run id equals the route's run id. The artifact allowlist and containment
  checks are unchanged for ticketed downloads. No other route reads the parameter, so a ticket opens nothing else and never
  authorises admission or a quota exemption; presented as a header or body token it is simply a wrong token.
- **Public runs** download exactly as before, with no credential; a stray `?ticket=` or `?token=` on them is ignored.

## API shape changes

- Removed: acceptance of `?token=<team token>` on any route (reads and POST admission alike).
- Added: `POST /api/runs/{run_id}/download-ticket` (header token required) returning `run_id`, `ticket`, `expires_at`, `expires_in_s`.
- Added: `?ticket=<ticket>` on `GET /api/runs/{run_id}/artifacts/{name}` and `GET /api/runs/{run_id}/bundle.zip`, valid for the embedded run id only, while unexpired.
- Added: `Cache-Control: no-store` on team-run downloads (public downloads unchanged).
- Added: environment variable `ATTEST_DOWNLOAD_TICKET_SECONDS` (default 600).

## Acceptance tests (all offline, `ConsoleHarness`)

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest tests.test_console tests.test_audit_console -v`: **60 tests, OK**
(`unittest-console.txt`; 52 before this repair). `node tests/console_client_test.mjs`: ok, four checks (`node-console-client.txt`).

| Case | Test |
|---|---|
| (a) `?token=` is an anonymous caller on list, detail, events, artifact, zip, tasks, profiles, health; POST with `?token=` gives 403 for the development profile and 429 for a visitor at quota | `TeamVisibility.test_a_query_token_is_ignored_on_every_route`; `DownloadTickets.test_a_ticket_grants_nothing_but_downloads`; `test_console.ConsoleApi.test_team_rows_are_hidden_from_anonymous_readers_and_shown_with_the_token` |
| (b) a ticket for run A does not open run B's artifacts or zip | `DownloadTickets.test_a_ticket_opens_only_its_own_runs_downloads` |
| (c) an expired ticket is refused (frozen clock: valid at expiry-1 s, refused at expiry; negative lifetime refused at once) | `DownloadTickets.test_an_expired_ticket_is_refused` |
| (d) a ticket on POST /api/runs, /api/runs, /api/runs/{id}, /events, /api/tasks, /api/profiles, /api/health, as a header or body token, or on the ticket route itself, grants nothing | `DownloadTickets.test_a_ticket_grants_nothing_but_downloads`; `TeamVisibility.test_a_download_ticket_opens_the_team_runs_downloads_and_nothing_else` |
| (e) forged tickets (flipped signature, other run, extended expiry, other secret, non-canonical hex, malformed shapes, another process's secret) are refused | `DownloadTickets.test_forged_and_malformed_tickets_are_refused` |
| (f) the header token lists team runs, opens detail and events, mints a ticket; minting needs the header (not body, not query) and a visible run | `TeamVisibility.test_the_team_token_reveals_the_team_run_on_every_route`; `DownloadTickets.test_minting_needs_the_header_token_and_a_visible_run` |
| (g) the ticket opens that team run's artifact and zip within its lifetime | `TeamVisibility.test_a_download_ticket_opens_the_team_runs_downloads_and_nothing_else`; `DownloadTickets.test_a_ticket_opens_only_its_own_runs_downloads`; `test_console` as above |
| (h) public runs download without any credential | `DownloadTickets.test_public_runs_download_without_any_credential` |
| (i) client: `artUrl`/`zipUrl` never contain the token value, carry the ticket only for the ticketed run; one ticket per run view; none for public runs or signed-out viewers; `copyPatch` fetches with the header and no credential in the URL | `console_client_test.mjs` checks `download_urls_carry_tickets_never_the_token` and `copy_patch_requires_ok`, run by `ConsoleClient.test_client_functions_behave_as_repaired`; `ConsoleClient.test_client_sends_the_token_in_the_header_only_and_tickets_on_team_download_links` (source assertions: no `?token=`, no `tokenQuery`, no `data-patch-url`, no storage of token or ticket) |

Unchanged regression coverage still passing: `TeamVisibility.test_anonymous_reads_never_see_the_team_run`,
`TeamVisibility.test_imported_development_bundles_become_team_rows_and_old_rows_are_backfilled`, `ZipExportAndContainment`,
`SanitizedErrors`, `PublicProjection` and the rest of both modules.

## The review's reproduction, re-run

`review-repro/api-review-repro.py` is a byte-identical copy of `reports/attest-revision5-review-2026-10-19/api-review-repro.py`
(`review-repro/sha256.txt`, both `57b4b2dd…6bab4`); the original was not edited or run. Because the copy sits two directories
deeper than the original, its own root computation points at `reports/`, so it was run from the repository root with
`PYTHONPATH=<repository root> PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B review-repro/api-review-repro.py`.

Result (`review-repro/api-review-repro-rerun.txt`): its first two blocks (row-only sanitization; bundle reasons and events
still public, which is finding R5-04, outside this repair) pass as before, then the `query_token_has_full_team_privileges`
block fails at line 59, `assert denied.status_code == 403 and query_team.status_code == 200`: the development-profile POST
with only `?token=` is now 403. Exit code 1. This is the expected outcome; the script asserts the faulty behaviour, so its
results JSON is not written on this run.

## Residual limitations

- A ticket travels in a URL. For its lifetime (default ten minutes) it can appear in the reverse proxy's access log, browser
  history, a copied link or a same-origin referrer. What such a copy grants is bounded: the artifact and zip downloads of
  that one run, nothing else, and never a POST. The server sends `Cache-Control: no-store` on team downloads; the vhost's
  access-log format was not changed here (see below).
- There is no revocation before expiry other than a restart: a leaked ticket stays valid for the remainder of its lifetime.
- The signing secret lives in the process. A restart (or a second worker process) invalidates outstanding tickets; the
  console requests a new one when a case file renders or the renewal timer fires. The deployed service is a single
  process, so this is acceptable and documented in the server module docstring. A multi-process deployment would need a
  shared secret.
- A ticket is run-scoped, not artifact-scoped: it opens every allowlisted artifact and the zip of its run.
- Two tickets minted for the same run in the same second are identical (deterministic HMAC over run id and expiry).
- The team token itself is unchanged: a static shared secret in the header, with no expiry; rotation stays an operational
  step. The `admin_token` body field of `POST /api/runs` and `POST /api/profiles` is unchanged.
- Between a ticket's expiry and its renewal (for example a suspended tab), a click on a team download link answers 404 JSON
  until the page renews the ticket; a reload or sign-in renews it too.
- `ATTEST_DOWNLOAD_TICKET_SECONDS` of zero or less issues tickets that are already dead; the server does not refuse the
  setting.
- Not verified here (offline): that the deployed nginx access log and the systemd unit behave as the review describes
  (uvicorn access logging disabled; the application logs `request.url.path` only).

## Changes needed in files outside this repair's scope

- `attest-console.md` line 265: "(or `?token=` on downloads)" is no longer true; describe the header-only token, the
  `POST /api/runs/{run_id}/download-ticket` route, `?ticket=` on artifact and zip links, and `ATTEST_DOWNLOAD_TICKET_SECONDS`.
- `attest/app/static/index.html`: bump the asset stamps (`?v=20261019b`) because `app.js` changed (orchestrator).
- `deploy/yungou/attest.axiqo.xyz.conf`: consider an access-log format that drops the query string for
  `/api/runs/*/artifacts/*` and `/api/runs/*/bundle.zip` (or a `map` that redacts `ticket=`), so a ticket never reaches the
  log for its ten minutes. Note that `add_header Cache-Control "no-cache" always` now coexists with the application's
  `Cache-Control: no-store` on team downloads (two headers; browsers apply the stricter one); `proxy_hide_header` on the
  API location would avoid the duplicate.
- `deploy/yungou/attest.env.example`: optionally document `ATTEST_DOWNLOAD_TICKET_SECONDS` (default 600).
- `reports/attest-audit-repairs-2026-10-19/console/README.md` line 214 describes the earlier `?token=` design; it is a
  historical record and was left as written.
- A version bump and a new pin are the orchestrator's decisions; nothing was committed or deployed.
