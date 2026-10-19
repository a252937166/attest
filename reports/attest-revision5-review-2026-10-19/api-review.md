# Revision 5 console/API closure review — 19 October 2026

**Verdict: ten of the eleven API findings are closed in the reviewed local source and offline acceptance tests. API-09 is partially repaired. Team visibility is implemented and verified offline. The known master-token-in-download-URL design remains a P2 residual with full administrative scope, rather than a read-only download credential. No actual credential disclosure or security incident was observed.**

This bounded follow-up read the supplied completion attachment, current source, acceptance tests and console repair notes. Application sources and the original audit folder were left untouched. The coordinating review owns deployment/export verification, production GET checks and the complete regression suite.

## Validation

`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest tests.test_audit_console -q` passed **36 tests** in 0.633 seconds. The tests idle or stop the worker, block runtime construction and socket connections, and use temporary data. This includes the Node checks of the actual extracted client functions.

`api-review-repro.py` adds three bounded synthetic scenarios. All current-behavior assertions passed; retained evidence is `api-review-repro-results.json`. It verifies sanitized row-only errors, remaining diagnostics in public bundle/reason/event paths, and the full privileges of the URL token. Only the harness's synthetic token is used; its value is not retained in the result file. No inference, Sandbox operation, production POST, live credential or external network call was used.

## API-01–11 closure matrix

| ID | Verdict | Reviewed mechanism and source lines | Evidence |
|---|---|---|---|
| API-01 | Closed for the supplied single-edge topology | `server.py:140-157` trusts only configured peers and validates the last IP; nginx overwrites inbound XFF with `$remote_addr` at `deploy/yungou/attest.axiqo.xyz.conf:25-26,33`. | TrustedProxyIdentity tests cover trusted/untrusted peers and rotation. Deployment configuration is checked by the coordinating review. |
| API-02 | Closed for the deployed single-process design | `db.py:198-223` checks quota and inserts under one store lock; `worker.py:163-174` serializes capacity/admission. | Four simultaneous same-visitor requests return three 200s and one 429 with exactly three rows/reservations. |
| API-03 | Closed | `db.py:158-172` materializes fetches inside the lock; get/list/event methods use those helpers. | MaterialisedReads exercises four readers plus a writer against the shared connection; no failures. |
| API-04 | Closed for the identified row/path fields | `server.py:90-94,237-246` uses an allowlist; tasks drop `path` at 390; health publishes startup counts at 367. | PublicProjection tests pass. Diagnostic content inside permitted `reasons`/events is the remaining API-09 gap below. |
| API-05 | Closed | `server.py:278-344,479-513` checks containment, enumerates artifacts, returns explicit 413/409 and spools the archive. | Exact 5 MB fixture included and verified; oversized exports explicitly refused; containment tests pass. |
| API-06 | Closed | `db.py:342-369` includes error retention; `worker.py:183-215,230-242` runs housekeeping after failure and while idle. | ErrorRetention tests cover failed, active, protected and imported directories. |
| API-07 | Closed | `server.py:409-419`, `worker.py:75-101,151-159` require/recover a live worker before admission. | WorkerReadiness and WorkerSupervision tests pass, including stopped worker/no reservation and restart. |
| API-08 | Closed | `app.js:703-752` retries final detail five times, then offers Retry; `server.py:428-447` returns retryable 503; `core/proof.py:352-362` publishes atomically. | BundleIncomplete and original-client-function retry tests pass. |
| API-09 | **Partial** | `server.py:227-246,522-527` sanitizes row/global errors; raw reasons, events and bundle bytes remain exposed via `92-94,450-463,466-513`. | Existing SanitizedErrors tests pass, but added synthetic repro confirms the uncovered public paths. |
| API-10 | Closed | `app.js:898-908` checks `res.ok` before clipboard write. | 404/503 preserve clipboard; 200 copies exact patch. |
| API-11 | Closed | `worker.py:141-149` reports the ordered position; `server.py:463` returns it; `app.js:674-680` uses it. | QueuePosition plus client test covers A/B/C and appending D. |

All source paths in this matrix are under `attest/app/` unless another path is stated. Closures are bounded to these findings and reviewed mechanisms; they do not certify every possible API or deployment behavior.

## API-09 remains partial: row sanitization does not cover published diagnostics

The row-only case is repaired: `record_failure()` stores private diagnostic fields (`db.py:281-289`); public row/error projection omits them, and the global handler returns a correlation ID instead of exception text.

The pipeline still creates other public diagnostic carriers:

- `core/pipeline.py:563-565` streams `MODEL ERROR: {error}` into progress and writes the error into `bundle.verdict.reasons`.
- `core/pipeline.py:566-569` writes generic exception type/text into the bundle before persisting and re-raising.
- `worker.py:320-325` persists a completed error bundle's reasons into the row; `server.py:92-94` publicly allows `reasons` unchanged.
- `server.py:450-451` returns the original bundle and events; `458` returns event messages unchanged. Artifact and ZIP routes return the recorded file bytes.

**Observed synthetic comparison:** a row-only `record_failure` marker was absent from list/detail/events. A synthetic pipeline-shaped public ERROR bundle with the same diagnostic marker in its reasons and progress event returned it through list, detail, events, `proof_bundle.json`, `PROOF.md` and a ZIP member, all HTTP 200. The fixture seeds the public records rather than issuing a real failing provider call; the source paths above establish how runtime exceptions reach those records. The PROOF fixture is synthetic text; the original pipeline writer is not executed by this focused check.

**Remaining repair:** make public pipeline events/reasons use stable error codes and correlation IDs while retaining detailed diagnostics privately. Apply a deliberate publication policy to recorded error bundles/artifacts. Preserve original manifests by using clearly labelled derived/redacted exports when rewriting historical evidence, rather than silently mutating sealed originals.

**Acceptance gap:** inject a fake ModelError or local exception containing a private marker through the fake pipeline, then verify absence across list/detail/events, rendered proof and downloads. The existing tests inject row/worker-handler failures without a diagnostic-bearing bundle, so their passing result does not establish this case's closure.

## Team visibility: implemented, with a credential-delivery residual

The product decision changed from all-public runs to team-only development runs (`static/index.html:300`). Provider-to-visibility assignment is in `db.py:112-113`; new rows get visibility and old development rows are backfilled at `154-156`. Public store lists and estimates filter team rows. `server.py:173-194` gates direct reads and current references; list/tasks/detail/events/artifact/ZIP routes call the corresponding filtering helpers at `383-398,433-481`.

TeamVisibility tests pass for anonymous 404s, token-authorized reads, public current/estimate hiding, imported rows and migration. Anonymous `queue`/`busy` values still reveal aggregate activity without a run identifier; this is the disclosed operating policy, not an outstanding private-record access finding.

### Known residual: a download URL contains the full team/admin token

`app.js:70-73` appends the accepted in-memory token to artifact/ZIP URLs. It does this for downloads from both public and team runs whenever the viewer is signed in. Those URLs appear in anchor/data attributes (`364-375,465,511,575`), and the copy-patch fetch uses the token-bearing URL (`898-908`).

`server.py:164-170` accepts `?token=` globally, and `start_run()` treats that caller as admin at `404`. This token is a static shared secret read from the environment (`49`), with no expiry or run/artifact scope in the checked code.

**Observed with the synthetic token:** a team enqueue without a token returned 403; the same POST with only the query token returned 200. After seeding three current public runs, an anonymous public enqueue returned 429 while the query-token request returned 200. The token also reveals team lists. Thus leakage of a download URL gives the holder team reads, team-run creation and exemption from the visitor quota, while the separate Nebius daily budget still applies.

**Leak avenues to account for:** browser download history/URL records, copied links or page DOM/snapshots, and reverse-proxy/access/observability logging of request URIs. The supplied vhost has no token-query redaction rule; its actual active access-log format was not inspected here. Uvicorn access logs are disabled (`attest.service:20`), and the app's exception logger uses `request.url.path` (`server.py:525`), which reduces those particular logging paths. `strict-origin-when-cross-origin` (`nginx:16`) normally strips the query from cross-origin referrers but allows full same-origin referrers; it is not a general guarantee that a URL credential stays private. `no-cache` (`nginx:19`) permits storage with revalidation, unlike `no-store`. No actual token-bearing production log/history record was accessed.

**Recommended improvement:** use header-authenticated fetches with a Blob download, an appropriately protected session cookie, or short-lived signed download/read tickets restricted to one run/artifact and unable to authorize POSTs. Remove global master-token query acceptance. Query/log redaction and restrictive referrer/cache headers are useful interim controls, but do not narrow a copied master token's authority.

**Release assessment:** this is a manageable P2 pre-publication/team-use improvement, and not evidence of an existing compromise. It does not alone block publishing source or an anonymous public-evidence demo where the team token is never entered. It should block an unqualified claim that the team privacy/security work is complete, and should be addressed before routine authenticated downloads or distribution of private team evidence. API-09 likewise prevents an “all API findings fully closed” sign-off. No emergency rotation is inferred without evidence that a real credential-bearing URL was exposed; if such exposure is confirmed, revoke/rotate that token after fixing its delivery path.
