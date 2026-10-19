# Transport failures of the development batches: investigation and repair (revision 8, 19 October 2026)

The revision-7 development batches (`reports/attest-revision6-repairs-2026-10-19/evaluation-codex*/`) ended six cells with
transport failures: four calls to the development gateway and two Token Factory Sandboxes spawns. Each was handled as uncertain
and never replayed. This folder records what happened to each request, why it failed, what may be retried safely, and the
repair.

## The path

The batches run on the project owner's machine. Every request leaves through a local proxy (the system HTTPS proxy on the
loopback interface, with a TUN device and fake-IP DNS); the development gateway is reached through its public host name, served by
nginx on a team host, which relays to the gateway's backend; Token Factory Sandboxes is reached at `api.tokenfactory.nebius.com`.
Python's `urllib` sends an HTTPS request through the proxy in three steps: a TCP connection to the proxy and a `CONNECT` tunnel,
the TLS handshake with the destination through the tunnel, then the HTTP request; `urllib` wraps an exception raised during the
first two steps or while writing the request in `URLError`, and lets an exception raised while waiting for the answer (for example
`RemoteDisconnected`) through unwrapped.

## The six failures, one by one

Client times are the harness's (UTC); gateway times are from the gateway's nginx ingress log (`gateway-ingress-2026-10-19.txt`,
client addresses removed, converted to UTC; nginx writes an entry when a request ends). Sandboxes operations are from the account's
operation list (`sandboxes-operations-2026-10-19-r7.json`, read with `GET /operations` and matched to the ledgers and judge records).

| Batch, cell, stage | Client | Error (private diagnostics) | Where it failed | What the server side shows | Executed? |
| --- | --- | --- | --- | --- | --- |
| 1, durationkit, spawn impl-tests-3 | 14:31:38, spawn | `URLError: [SSL: UNEXPECTED_EOF_WHILE_READING]` | TLS handshake through the proxy (wrapped: before or while writing) | no operation exists on the run's checkpoint image (`6df49ea6`) in the window; the 13 operations of that minute all belong to the concurrent balanced-brackets run | no |
| 2, durationkit, seal-1 | 14:36:49 to 14:36:54 (5.0 s) | `URLError: [SSL: UNEXPECTED_EOF_WHILE_READING]` | TLS handshake | no ingress entry for it (the entries of that minute are the other requests of both runs) | no |
| 2, kvparse, implement-1 | 14:38:25 to 14:39:26 (61.0 s) | `URLError: [SSL: UNEXPECTED_EOF_WHILE_READING]` | TLS handshake (the proxy held the tunnel open for 60 s, then closed it) | no `POST /v1/run` entry between 14:38:25 and 14:45:10 | no |
| 3, durationkit, implement-1 | 14:49:27 to 14:50:54 (87.3 s) | `RemoteDisconnected` | after the request was written | `POST /v1/run` 408, 0 bytes, 61.1 s (14:49:56 to 14:50:57): nginx received the headers and part of the body, waited its 60 s `client_body_timeout` for the rest and closed; with request buffering nothing reaches the gateway's backend before the whole body has | no |
| 3, kvparse, spawn impl-tests-3 | 14:50:36, spawn, 60 s | `URLError: _ssl.c:983: The handshake operation timed out` | TLS handshake | no operation on the run's checkpoint image (`344ed4d5`) in the window; the one operation of that minute (`01a154a4`) is the held-out judge of the durationkit cell of the same batch (`judge_operation_uuid` in its `evaluation.json`) | no |
| 4, durationkit, contract-audit | 14:54:06 to 14:55:51 (105.5 s) | `RemoteDisconnected` | after the request was written | `POST /v1/run` 408, 0 bytes, 91.4 s (14:54:24 to 14:55:55): the body stalled in transit | no |

The seventh failure of those batches was not a transport failure: the second sealing attempt of batch 2's durationkit cell got
`HTTP 502 "Selected model is at capacity"` after 82.7 s (ingress `POST /v1/run` 502, 172 bytes), a definite answer from the
gateway's upstream. From 14:23 to 14:56 UTC the gateway logged 36 `POST /v1/run` requests of the four batches: 33 answered 200, the
502 and the two 408s above. With the two requests that never reached it, these are all 38 call records of the batches.

The gateway backend's own audit records (`gateway-backend-audit-2026-10-19.json`: route, status, model, duration and tokens only)
confirm the ingress log: between 14:20 and 15:10 UTC the backend executed 34 `/v1/run` requests, 33 answered 200 and one ended
with the capacity error (8.7 s of execution after its wait in the gateway's queue). That is the 36 requests nginx logged minus
the two 408s, which nginx never forwarded; the two requests that failed during the TLS handshake appear in neither log.

The Sandboxes account lists exactly 34 operations between 14:15 and 15:15 UTC: 28 recorded in the run ledgers and 6 held-out
judge operations, all `SUCCESS`, 97.0 s of guest time and 72.7 CPU seconds in total. No operation is unrecorded and the two
uncertain spawns created none. The revision-7 report counted "36 recorded Sandboxes operations, and up to 2 more"; the 36 included
the two empty spawn records (correction appended to that report).

## Reading

All six failures were on this machine's outbound path, not in the gateway or the Sandboxes service: four broke while the
connection was being set up (the proxy accepted the tunnel and the TLS handshake then stalled or ended), two after the request
headers had left, while the body stalled in transit until nginx gave up. At 14:50 UTC both destinations failed within the same
minute. None of the six requests was executed. Four of them were demonstrably safe to send again at the moment they failed (no
byte of the request had been written); the client could not know that about the other two, because a written request may
have been received; only the server's log settles it afterwards.

## The revision-8 batch and the host's network outage (19:00 to 19:19 UTC)

The first development batch of this revision (`../evaluation-codex/`, started 19:00:02 UTC) met a different failure: the
network of the gateway's host went down.

| Time (UTC) | What happened | Source |
| --- | --- | --- |
| 19:00:02 to 19:00:16 | the batch read the gateway's status and catalog (200) and both cells sent their specification request; both requests reached nginx (19:00:20, 19:00:22) | harness log, ingress |
| 19:00:59, 19:01:30 | the gateway backend executed both (200 each; `gpt-6-astra:low`; 37.4 s and 31.2 s; 10,217 and 10,118 input tokens, 913 and 839 output tokens; the prompt lengths 3,322 and 3,094 characters match the two call records) | backend audit, bundles |
| about 19:01:30 to 19:02:08 | the host's network went down; nginx lost the relay to the backend and logged both requests as 502 after 105 s and 107 s; the answers never reached this machine | ingress |
| 19:03:38 | balanced-brackets: the client saw `RemoteDisconnected` after 202 s; uncertain, not retried, the run ended ERROR; its held-out judge spawn then timed out reading the answer (60 s) and was recorded as uncertain | diagnostics, ledger |
| 19:08:46 | rle-encode: the client's read timed out after 512 s; uncertain, not retried, the run ended ERROR | diagnostics |
| 19:08:46 | the batch stopped for reconciliation (3 items) and ran neither of its other two cells | `../evaluation-codex/evaluation.json` |
| 19:05 to 19:19 | the host was unreachable from this machine and from the team's second host in another network (no answer to ping, TCP 22, 80 or 443) | probes |
| 19:19:18 | reachable again; uptime 12 days (no reboot), `attest.service` the same process as since its 15:29 UTC start, no OOM or kernel event; no inbound request reached nginx on any of the host's sites between 19:00:23 and 19:18 UTC (the previous three days had requests in 11 to 25 minutes of that hour) | host |

Reconciled: both uncertain gateway requests were executed by the backend and spent the team's allowance (20,335 input tokens, 7,680
of them cached, and 1,752 output tokens); sending them again would have executed them twice. The judge spawn created no
Sandboxes operation (`sandboxes-operations-2026-10-19-r8-batch.json`: the batch's three operations are the two checkpoints and
the rle-encode judge). The outage's cause is not visible on the host; it looks like an interruption upstream of it. The console was
unreachable for about 17 minutes and no run was in progress.

## The second and third revision-8 batches

In the second batch (`../evaluation-codex-2/`, 19:25 UTC) the balanced-brackets cell's contract-audit request (10,722 prompt
characters, sent at 19:26:32) ended with `RemoteDisconnected` after 75 s. nginx had logged it as 408 after 62 s (the headers and
part of the body arrived, the rest never did) and the backend has no record of it: not executed. It is the same body stall as in
two revision-7 cases. The batch stopped with that one reconciliation item; the cell already running finished. The third batch
(`../evaluation-codex-3/`, kvparse alone) had no transport failure. The backend executed 28 of the three batches' 29 requests, all
with 200.

None of the three batches met a connection-setup failure, so the new resend of a never-sent request was not exercised by real
traffic in this pass; its behaviour is covered by the loopback and adapter tests.

## Repair (revision 8)

- `attest/http.py` records the phase each request reached: `connect` (TCP to the server or the proxy, the `CONNECT` tunnel, the
  TLS handshake; the tunnel's own `CONNECT` line does not count as the request), `send` (from the first byte of the request) and
  `response`. A failure in the connect phase is `TransportError(request_sent=False)`; every other failure, and any error raised
  without a recorded phase, keeps `request_sent=True`.
- The gateway and Token Factory adapters send a never-sent request again at most twice (after 2 s and 6 s); every attempt is its
  own call record with `request_sent` false. For Token Factory the attempt's reservation is closed at a known $0 (nothing reached
  the provider) and the resend takes a new reservation within the per-run USD and call caps. When every attempt failed before
  sending, the call fails definitely (`unreachable`, nothing executed), not as uncertain. A request whose bytes were written is
  never sent again: the run stops with an uncertain error, exactly as before.
- Reads (gateway status and catalog, Sandboxes image lookup and operation polls) and cancels are retried on any transport
  failure, at most four times. A spawn is sent again only when it was never sent. The operation id the Sandboxes service accepts
  is journaled before polling starts; an accepted operation whose outcome cannot be read is `ACCEPTED_UNREAD`, keeps its id and is
  never spawned again. Tavily searches follow the same rule (a never-sent search consumed no credit).
- The evaluation harness writes a reconciliation list per cell (each uncertain call with its stage, time, elapsed time and phase;
  each uncertain or unread operation with its source image or id and how to settle it) and stops the batch when any list is not
  empty. The console's restart recovery names accepted operations whose outcome a run never read.
- The pipeline stops at the first uncertain model call, wherever it happens. Until revision 8 the sealing stage took an uncertain
  call as an unusable attempt and sent its next attempt, which carried the same prompt (an uncertain request sent again in effect),
  and the adversarial-test authoring, the drift audit and arbitration recorded the failure and went on to further calls. All of them
  now end the run as ERROR (uncertain, not retried) with nothing further sent, as the specification, the contract audit and the
  implementation loop already did (`tests/test_transport.py`, `UncertainStopsTheRun`). Found during this pass's review of the
  transport paths, after the batches below had run; none of their failures was in those stages, so their outcomes are unaffected.
- `attest check` recomputes the new counters (`calls_not_sent`, `sandbox_spawn_retries`, `sandbox_uncertain`) and refuses a cost on
  an attempt recorded as never sent.

Tests: `tests/test_transport.py` (`unittest-transport.txt`) drives the real client against loopback servers that fail at each
point, including a proxy that accepts the tunnel and then drops it (never sent; the proxy never saw the request line or its
headers) and a server that reads the headers and part of the body and closes (uncertain), then the adapters' rules, the harness's
list, the restart recovery and the checker.

What this does not change: a request whose body stalls after its first bytes left (the two 408 cases) is still uncertain at the
client and still stops the run; the repair turns the setup failures into bounded resends, it does not make the path itself
reliable.
