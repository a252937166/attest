# Attest console API and worker review — 19 October 2026

This slice found eleven reproducible defects: two independent hourly admission bypasses, a local runtime concurrency failure, excessive public metadata, an incomplete ZIP export, incomplete failed-run retention, admission without a live worker, a terminal-view retry failure, raw error disclosure, a false patch-copy success, and an inaccurate queue position. Team-run publication and artifact-directory trust are documented separately because their intended boundaries matter.

Only audit artifacts were written. Application sources and deployment files were read without modification. The checks used synthetic data beneath this audit directory, a disabled worker loop, blocked socket connections, and fake browser functions. They performed no inference, Sandbox operations, production requests, deployment, or live data mutations. Deployment impact is inferred from the supplied configuration unless explicitly identified as a local result.

## Evidence and reproduction

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B reports/attest-audit-2026-10-19/repro_api_offline.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B reports/attest-audit-2026-10-19/repro_sqlite_offline.py
node reports/attest-audit-2026-10-19/repro_console_offline.mjs
```

- `api-repro-results.json`: twelve API/control scenarios; all behavior assertions passed.
- `console-repro-results.json`: three client functions extracted unchanged from `app.js`, executed with fake DOM/API dependencies; all behavior assertions passed.
- `sqlite-concurrency-probe.json`: four threads and 120 synthetic reads in each of two arms. Retained result: Python 3.12.0, SQLite 3.42.0; three failures when fetching outside the lock, zero when execute and fetch share the lock. Counts vary with scheduling. An earlier independent run produced four failures versus zero.
- Local API dependencies: FastAPI 0.115.5, httpx 0.28.1. JavaScript checks: Node 22.23.1.

These checks assert the existing faulty behavior so the report can be independently reproduced. Repairs require acceptance tests that assert the desired behavior described below. The broad existing regression suite was owned by the coordinating review, rather than rerun by this slice.

## Confirmed defects

| ID | Priority | Finding | Primary location |
|---|---|---|---|
| API-01 | P2 | Forwarding-header rotation bypasses the visitor quota | `attest/app/server.py:80-82`; `deploy/yungou/attest.axiqo.xyz.conf:25` |
| API-02 | P2 | The visitor quota check and run creation are not atomic | `attest/app/server.py:199-205` |
| API-03 | P2 | Shared SQLite results are fetched after the store lock is released | `attest/app/db.py:65-67`, `249` |
| API-04 | P2 | Public responses disclose requester addresses and internal paths | `attest/app/server.py:185-188`, `225-227`; `attest/app/worker.py:62-64` |
| API-05 | P2 | ZIP download silently omits manifested files at 5 MB | `attest/app/server.py:263-265` |
| API-06 | P2 | Failed-run directories escape bounded retention | `attest/app/db.py:203`; `attest/app/worker.py:176-191` |
| API-07 | P2 | Run admission succeeds with no live worker | `attest/app/server.py:191-205`; `attest/app/worker.py:74-93` |
| API-08 | P2 | One failed final-detail request permanently stops live refresh | `attest/app/static/app.js:700-707` |
| API-09 | P3 | Public errors contain internal exception text and worker tracebacks | `attest/app/server.py:235-239`, `277-279`; `attest/app/worker.py:103` |
| API-10 | P3 | Copy patch reports success when the artifact request failed | `attest/app/static/app.js:855-861` |
| API-11 | P3 | Queue position counts runs behind the selected run | `attest/app/static/app.js:670-671` |

### API-01 — Caller-controlled forwarding address bypasses the hourly quota

`_requester()` trusts the first `X-Forwarded-For` item without checking its origin or syntax. The supplied nginx configuration uses `$proxy_add_x_forwarded_for`, preserving the caller's existing header before appending the real peer. nginx's separate 5 requests/second ingress guard does not enforce the application's 3 runs/hour rule.

**Observed:** after seeding three current synthetic rows for one visitor, the same TestClient received 429 with `198.51.100.20, 192.0.2.1` and 200 after changing only the first item to `198.51.100.21, 192.0.2.1`.

**Impact:** a caller can take more than its visitor allocation and consume the shared daily demo allowance. This does not establish a bypass of the separate daily USD reservation guard.

**Repair:** derive requester identity through an explicit trusted-proxy policy. At a directly exposed owned edge, overwrite the inbound forwarding header with the validated peer address; have the application use the normalized client address. Account for any real additional proxies explicitly.

**Acceptance:** through the configured proxy topology, changing an inbound `X-Forwarded-For` must not change the visitor identity or allow request four after three accepted runs.

### API-02 — Concurrent requests pass the same hourly count

`count_recent()` runs before `worker.enqueue()` with no shared admission transaction. FastAPI synchronous handlers can execute simultaneously even with the deployed single uvicorn process.

**Observed:** four same-visitor requests all returned 200 and created four rows under a quota of three. A scheduling barrier at the beginning of `enqueue()` ensured all four quota reads happened before insertion. The original `count_recent()` calls were serialized only to isolate API-03; the count/insert gap and all admission logic remained intact. The temporary daily cap was raised to keep this test independent of the separate budget guard.

**Impact:** bursts bypass the hourly quota without changing address. The global daily cap and queue bound still apply.

**Repair:** perform visitor-quota checking and successful run creation within the same store admission lock/transaction as budget reservation. Make queue rejection semantics explicit.

**Acceptance:** four simultaneous requests from a fresh visitor with quota three admit at most three; the rejected request returns 429, with no extra queued row or reservation.

### API-03 — Shared-connection reads fail under concurrency in the local supported runtime

`_exec()` locks only `Connection.execute()`, returns a live cursor, and releases the lock before callers invoke `fetchone()` or `fetchall()`. `count_recent()` is one example; listing/detail/event helpers use the same pattern.

**Observed:** on the local Python 3.12.0/SQLite 3.42.0 runtime, three of 120 four-thread `count_recent()` reads raised `TypeError: 'NoneType' object is not subscriptable` in the retained probe. The identical query with the store lock held through `fetchone()` produced zero failures. An API reproduction also intermittently returned 500 with `'>=' not supported between instances of 'NoneType' and 'int'` before enqueueing. This observation was isolated from the hourly race test rather than hidden by a retry.

**Impact:** a small number of concurrent local requests can cause incorrect/failed API reads. The deployed interpreter was not exercised by this slice; its exact susceptibility remains unverified. The results do not establish database corruption or the underlying interpreter defect.

**Repair:** materialize query results while holding the store lock, or use appropriately isolated connections. Avoid exposing active cursors after releasing connection synchronization. Verify the actual deployed Python/SQLite runtime as part of remediation.

**Acceptance:** concurrent count/list/detail reads produce correct results and no exceptions on every supported runtime; compare the deployed runtime as well. Use lock-through-fetch helpers rather than only serializing calls to `execute()`.

### API-04 — Public DTOs include requester IPs and server paths

`_with_summary()` copies the full store row. Anonymous list/detail responses include `requester`, `out_dir`, and raw `error`. `/api/tasks` includes absolute task-file `path`; `/api/health` includes the absolute data directory and startup reconciliation data.

**Observed:** an anonymous list request returned the exact seeded requester address `198.51.100.10`, the synthetic absolute run-directory path, and the task endpoint returned its filesystem path.

**Impact:** visitors can enumerate other visitors' requester addresses and operational filesystem details that the console does not need to render. The page's public-evidence notice does not provide a reason to publish visitor IPs.

**Repair:** define explicit public response models. Omit requester identity, host paths and internal diagnostic fields; use artifact URLs and public error codes. Keep operational diagnostics in an authenticated view/log.

**Acceptance:** seed a row with an IP, absolute output path and synthetic diagnostic marker; none appears in public list/detail/tasks/health responses, while the public UI still renders its evidence.

### API-05 — A successful ZIP download can contain an invalid manifest

The ZIP writer includes only individual files whose size is **strictly less than** 5,000,000 bytes, while including the existing manifest unchanged. The UI says “Everything below is in the downloadable zip” (`app.js:566`).

**Observed:** a seeded 5,000,000-byte `verify_raw.json` was correctly present in a source manifest that passed `verify_manifest()`. The API returned 200 for the ZIP, omitted that file, retained the manifest, and the downloaded copy failed manifest verification with `missing: ["verify_raw.json"]`. This is a boundary fixture; no claim is made that a current public run has reached this size or that the synthetic bundle passed the full proof checker.

**Impact:** sufficiently large evidence downloads are silently incomplete and cannot reproduce the source manifest's integrity result.

**Repair:** either stream every advertised artifact or reject oversized archives explicitly before returning success. If a bounded derivative export is a product feature, label it as partial and generate a corresponding derivative manifest rather than presenting the original manifest as complete.

**Acceptance:** a legitimate manifested artifact at the exact boundary and above it is either included in a verifiable download or produces an explicit export-size error; no 200 response silently loses advertised evidence.

### API-06 — Error output is never pruned

`prune_runs()` selects only `status = 'finished'`. Pipeline exceptions set status `error` and return before the only pruning call in `_execute()`. Failed runs that already created trajectory/ledger/test output therefore never enter bounded retention.

**Observed:** with one old finished directory and one old error directory, `keep=0` and no protected verdicts removed the finished directory but retained the error directory and its row's output path.

**Impact:** recurring provider, sandbox or pipeline failures accumulate partial output indefinitely. Eventually the disk guard can refuse otherwise usable new runs despite the configured retention count. This test proves the retention exclusion, rather than estimating production disk exhaustion.

**Repair:** apply a documented retention policy to terminal error runs, preserving recent diagnostic evidence and active/pinned directories. Invoke cleanup on failure paths or via independent housekeeping so an all-failure period still cleans up.

**Acceptance:** old error directories beyond the configured error-retention budget are reclaimed; running/queued directories, pinned evidence and imports outside the managed tree remain protected.

### API-07 — An unavailable worker still accepts queued work

Health exposes `worker_alive`, and the browser disables its run button when false (`app.js:186`), but the admission API performs no equivalent check. A dead background thread does not by itself terminate uvicorn or trigger the service's `Restart=on-failure` process policy.

**Observed:** with the worker loop disabled for the offline harness, health reported `worker_alive: false` and a real admin API request returned 200 and created a queued row. No consumer existed. The same enqueue path is used for public requests.

**Impact:** API clients receive apparent acceptance for work that will not progress; queued Nebius rows can retain daily reservations until recovery. No real production worker failure was induced.

**Repair:** make worker readiness a server admission requirement and return 503 before creating a row/reservation when no consumer is alive. Add appropriate worker supervision/recovery for an unexpected loop exit.

**Acceptance:** with a stopped worker, public and team submissions return 503, create no run/reservation, and readiness communicates the unavailable state; normal admission resumes after recovery.

### API-08 — Failed final-detail fetch leaves the page stale permanently

`pollLive()` calls `stopLive()` immediately on a terminal event, clears live status, then fetches detail with `.catch(() => null)`. A failed detail fetch schedules no retry. The periodic history/health refreshes do not reload the selected detail.

**Observed:** executing the original `pollLive()` with a finished event and one synthetic detail failure cleared its timer, retained a `running` detail, and never rendered the finished view.

**Related server trigger:** `server.py:221-224` parses `proof_bundle.json` without handling partial/corrupt content, while `core/proof.py:352` writes it non-atomically with `write_text()`. A seeded partial bundle returned 500/`JSONDecodeError`. The actual file-write timing race was not forced against production.

**Impact:** one transient network/API/read failure at completion can leave a completed run displayed as running until the viewer manually reloads or reopens it.

**Repair:** retry terminal-detail loading with a bounded visible recovery state; stop updates only after the terminal view is successfully installed or an explicit recoverable error is shown. Publish JSON artifacts using temporary files plus atomic replace, and handle unreadable artifact state deliberately.

**Acceptance:** make the first final-detail fetch fail and the second succeed; the selected run eventually renders its correct terminal verdict without navigation or manual reload. Readers must not observe half-written JSON.

### API-09 — Raw internal errors are public

The global exception handler returns `str(exc)[:300]`. Worker failures before/around `_execute()` can store the tail of `traceback.format_exc()`, and anonymous event/detail/list endpoints return it. Public pipeline errors also preserve exception text.

**Observed:** a synthetic internal path and diagnostic marker were returned verbatim from both a stored worker traceback and an unhandled API exception. No real credential leakage was observed or alleged.

**Impact:** expected infrastructure failures can disclose internal paths, implementation details, and potentially sensitive upstream diagnostic text.

**Repair:** map failures to stable public error codes/messages and retain full diagnostics server-side under a correlation ID. Apply the same projection to stored/imported failures and to artifact publication policy.

**Acceptance:** force an exception containing a synthetic private path/marker; public JSON and publicly rendered errors contain only the approved error message and correlation ID.

### API-10 — Failed patch download is copied as though it succeeded

`copyPatch()` reads the response body and writes the clipboard without checking `res.ok`.

**Observed:** the original function received a fake 404 with `{"detail":"artifact missing"}`, copied that JSON into the clipboard, and changed the button to `Copied`.

**Impact:** a user can paste an error document believing it is a candidate patch.

**Repair:** verify the response status before copying; keep a clear error message and enable retry.

**Acceptance:** 404/503 artifact responses leave the clipboard untouched and show a failure; a 200 patch copies its exact text and shows success.

### API-11 — Position includes jobs queued later

`queueAhead` is calculated from total queue length rather than the selected run's position. The events API exposes only total queue size and current ID, so the client cannot infer the true position.

**Observed:** with A running and B then C waiting, applying the original update for B reported two runs ahead. Only A was ahead; C was behind B.

**Impact:** the waiting UI overstates the selected run's place and changes its apparent position when later runs arrive.

**Repair:** expose an authoritative per-run queue position from the worker's ordered queue and use it in the client, or show total waiting work without claiming it is the selected run's position.

**Acceptance:** for A running and B/C queued in that order, B reports one ahead and C two; appending D does not increase B's position.

## Verified boundary observations and design decisions

### Team runs are intentionally public; the token is not a read-authorization boundary

`static/index.html:300` explicitly says: “Everything on this console is public. No account is needed; a team token only reveals a private inference profile.” Consequently, anonymous read access is **not reported as an unauthorized private-run access vulnerability**. No credential leak or promise of private run storage was demonstrated.

The offline test nevertheless establishes a practical publication behavior worth making explicit: after token-authenticated team enqueue, anonymous list/detail/events/patch/ZIP routes all return 200. Startup `ATTEST_IMPORT_PROVIDERS=nebius` filtering (`server.py:48-54`, `db.py:295-297`) only filters newly imported evidence. It does not filter live team rows or existing database rows. A team run's provider identifiers, evidence and errors become public, despite source comments about keeping development evidence private and public API responses free of development-provider naming (`server.py:39-50`).

Recommended product decision: keep the stated all-public model and explicitly confirm publication when starting a team run, coupled with safe public DTOs and artifact export policy; or introduce persistent run visibility and enforce it consistently on list, estimates, current-run references, detail, events, artifacts and ZIP. Merely filtering the profile dropdown or the importer cannot establish private run storage.

### Artifact roots are trusted; symlinks and extra files cross the download boundary

`artifact()` validates the lexical filename pattern, then calls `is_file()`/`FileResponse` without resolved-path containment. ZIP recursively includes every small file, independent of the individual artifact allowlist, and follows file symlinks. The closed lexical pattern blocks ordinary `../` names, but does not constrain symlink targets.

**Observed:** a synthetic `private-notes.env` received 404 from the individual artifact endpoint but was present in the ZIP. An allowlisted `ledger.json` symlink to a sentinel outside the run directory returned the external sentinel via both the individual endpoint and ZIP.

**Precondition and limit:** a local/imported run directory must already contain the extra file or symlink. The current public API exposes only fixed configured tasks; this review did not establish a remote file-creation primitive or a remote path-traversal chain. “The whole run directory” is also the documented ZIP contract, so including an extra regular file is an exposure characteristic rather than proof of a violated private-file promise.

If run directories are treated as an export trust boundary, reject symlinks and out-of-root resolved paths, enumerate an explicit public artifact set or a validated manifest, and apply an aggregate size/streaming policy. Acceptance should place a synthetic outside-root file symlink inside an imported run and verify its bytes are unavailable through either download route.

## Controls that held in the offline checks

- An unauthenticated development-provider submission returned 403; public profiles listed only Nebius.
- An unknown provider returned 400, a traversal-shaped task ID returned 404, and a non-string task ID returned 422.
- Public tasks are selected from configured sample files rather than accepting an arbitrary repository URL/path in the API.
- The ZIP size-boundary test used a small synthetic local fixture, and the concurrency tests used four local request/read workers only.
- No source repair, production load test, paid call, deployment or shared-service restart was performed by this review slice.
