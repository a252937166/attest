"""Minimal HTTPS JSON client shared by the model and sandbox adapters.

TLS verification is always on. Transport failures on POST are reported as "uncertain" so callers never replay them blindly.

Request phases (transport investigation, revision 8, 19 Oct 2026): every request records how far it got. `connect` covers the TCP
connection to the server or to the proxy, the proxy's CONNECT tunnel and the TLS handshake; `send` starts when the first byte of
the HTTP request is handed to the connection; `response` starts once the request is written. A failure in the connect phase is a
TransportError with `request_sent=False`: no byte of the request was written, so the server cannot have received it and sending it
again is safe for any method. Every later failure keeps `request_sent=True`: the request may have been received and executed, the
outcome is uncertain, and a POST is never sent again automatically. A TransportError that carries no recorded phase (an error
raised before the connection classes ran, or by a test double) is treated as sent, the conservative reading.

The investigation behind this (reports/attest-revision7-repairs-2026-10-19/transport/): of the six transport failures of the
revision-7 development batches, four happened while the connection was being set up (TLS end-of-file or handshake timeout through
this machine's proxy) and the two others after the request had been written; the gateway's ingress log shows that neither of the
two gateway requests that failed during setup reached it.

Error bodies and answer classes (revision 9, 20 Oct 2026): an HTTP error status arrives before its body, so the server's answer is
known even when the body is cut. Reading the error body used to run inside the `except HTTPError` handler, where a chunked body cut
short raised a raw `http.client.IncompleteRead` (and a stalled one a raw timeout) past the transport wrapper. Both bodies, the error's
and the success's, are now read under their own guard: an error answer is always an `HttpError` that keeps its status, says that the
request was sent and the phase it reached (`response`), and whether its body arrived complete (`body_complete`); a success whose body
is cut is a `TransportError` that keeps the status. `post_outcome` is the one classification of a failed POST that every adapter uses:
`not_sent` (no byte left this machine: safe to send again), `rejected` (an HTTP 4xx answer: the server refused the request, so it did
not execute it) or `uncertain` (an HTTP 5xx or any other answer, or a failure after the request was written: it may have executed, so
it is never sent again and the run stops for reconciliation). `read_retryable` says which failures of an idempotent read are retried.
"""

from __future__ import annotations

import http.client
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

# Bounded retries, used by the adapters (they keep their own loops so every attempt is recorded where it belongs):
NOT_SENT_RETRIES = 2              # a request that never left this machine is sent again at most twice
NOT_SENT_BACKOFF_S = (2.0, 6.0)   # waits before the second and the third attempt
READ_RETRIES = 4                  # idempotent reads (status, catalog, operation polls) are retried on any transport failure
READ_BACKOFF_S = (1.0, 2.0, 4.0, 8.0)


def backoff(schedule: tuple[float, ...], retry_index: int) -> float:
    return schedule[min(max(retry_index, 0), len(schedule) - 1)]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):  # noqa: D401
        return None


def tls_context() -> ssl.SSLContext:
    configured = os.environ.get("SSL_CERT_FILE")
    if configured:
        return ssl.create_default_context(cafile=configured)
    paths = ssl.get_default_verify_paths()
    if paths.cafile or paths.capath:
        return ssl.create_default_context()
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        if Path("/etc/ssl/cert.pem").is_file():
            return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
        return ssl.create_default_context()


class _Progress:
    """How far one request got. Written by the connection classes below, read by request_json when the request fails."""

    __slots__ = ("phase", "bytes_written")

    def __init__(self):
        self.phase = "unknown"  # unknown -> connect -> connected -> send -> response
        self.bytes_written = 0


def _tracked(base):
    class Tracked(base):
        def __init__(self, *args, progress: _Progress | None = None, **kwargs):
            super().__init__(*args, **kwargs)
            self._progress = progress
            self._connecting = False

        def connect(self):
            # the TCP connection, the proxy's CONNECT tunnel (written through send() below) and, for HTTPS, the TLS handshake
            self._connecting = True
            if self._progress is not None:
                self._progress.phase = "connect"
            try:
                super().connect()
            finally:
                self._connecting = False
            if self._progress is not None:
                self._progress.phase = "connected"

        def send(self, data):
            if self._connecting:
                return super().send(data)  # the CONNECT line to the proxy is part of setting up the connection, not the request
            if self.sock is None and self.auto_open:
                self.connect()
            if self._progress is not None:
                self._progress.phase = "send"
            super().send(data)
            if self._progress is not None:
                try:
                    self._progress.bytes_written += len(data)
                except TypeError:
                    pass

        def getresponse(self):
            if self._progress is not None:
                self._progress.phase = "response"
            return super().getresponse()

    Tracked.__name__ = Tracked.__qualname__ = "Tracked" + base.__name__
    return Tracked


TrackedHTTPConnection = _tracked(http.client.HTTPConnection)
TrackedHTTPSConnection = _tracked(http.client.HTTPSConnection)


class _TrackedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        progress = getattr(req, "attest_progress", None)
        return self.do_open(lambda host, **kwargs: TrackedHTTPConnection(host, progress=progress, **kwargs), req)


class _TrackedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        progress = getattr(req, "attest_progress", None)
        return self.do_open(lambda host, **kwargs: TrackedHTTPSConnection(host, progress=progress, **kwargs), req, context=self._context)


def build_opener(proxies: dict | None = None, context: ssl.SSLContext | None = None):
    """The opener every request uses: no redirects, phase-tracked connections, and the proxies of the environment (the system
    configuration on macOS) unless `proxies` is given (tests pass an explicit proxy)."""
    handlers = [NoRedirect, _TrackedHTTPHandler(), _TrackedHTTPSHandler(context=context or tls_context())]
    if proxies is not None:
        handlers.insert(0, urllib.request.ProxyHandler(proxies))
    return urllib.request.build_opener(*handlers)


_OPENER = None


def opener():
    global _OPENER
    if _OPENER is None:
        _OPENER = build_opener()
    return _OPENER


class HttpError(Exception):
    """The server answered with an HTTP error status. The request was sent and answered (`request_sent`, `phase` "response");
    `body_complete` is False when the error body was cut or stalled while being read (`body_error` says how), which leaves the status
    itself, and so the classification of the answer, intact."""

    request_sent = True
    phase = "response"

    def __init__(self, status: int, body, url: str, headers: dict | None = None, body_complete: bool = True, body_error: str | None = None):
        self.status = status
        self.body = body
        self.url = url
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}  # Retry-After and rate-limit headers, when sent
        self.body_complete = body_complete
        self.body_error = body_error
        message = ""
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                message = str(err.get("message") or err.get("type") or "")
            elif err:
                message = str(err)
            else:
                message = str(body.get("message") or body.get("detail") or "")[:300]
        suffix = "" if body_complete else f" (error body incomplete: {body_error or 'cut short'})"
        super().__init__(f"HTTP {status} from {url.split('?')[0]}: {message[:300]}{suffix}")


class TransportError(Exception):
    """The request failed in transit. `request_sent` is False only when the failure happened while the connection was being set
    up, before any byte of the request was written: the server cannot have received it, and it may be sent again. Otherwise the
    outcome is uncertain (timeout, reset, a cut response): never auto-replay a POST after this. `status` is the HTTP status when an
    answer had started to arrive (a success whose body was cut), None otherwise."""

    def __init__(self, message: str, request_sent: bool = True, phase: str = "unknown", status: int | None = None):
        super().__init__(message)
        self.request_sent = request_sent
        self.phase = phase
        self.status = status


def post_outcome(error: BaseException) -> str:
    """The outcome of a POST that failed: `not_sent` (a transport failure before any byte was written), `rejected` (an HTTP 4xx
    answer: the server refused the request and did not execute it) or `uncertain` (an HTTP 5xx or any other non-success answer, a
    transport failure after the request was written, or anything unrecognised). Only `not_sent` may be sent again automatically; an
    `uncertain` request is never replayed and stops the run for reconciliation. A 5xx is uncertain because a proxy or the server may
    answer it after the request was executed (a gateway timeout, a crash while answering)."""
    if isinstance(error, TransportError):
        return "uncertain" if getattr(error, "request_sent", True) else "not_sent"
    if isinstance(error, HttpError) and isinstance(error.status, int) and 400 <= error.status < 500:
        return "rejected"
    return "uncertain"


def read_retryable(error: BaseException) -> bool:
    """Whether an idempotent read (a GET or a DELETE) that failed this way is tried again (bounded): any transport failure, and the
    answers that say "try again" (408, 429, 5xx). Other 4xx answers are definite and are not retried."""
    if isinstance(error, TransportError):
        return True
    if isinstance(error, HttpError):
        return error.status in (408, 429) or (isinstance(error.status, int) and error.status >= 500)
    return False


def retry_after_s(error: BaseException, cap: float = 30.0) -> float | None:
    """A server's Retry-After (seconds) on an answer that carries one, bounded by `cap`."""
    value = (getattr(error, "headers", None) or {}).get("retry-after")
    try:
        return min(cap, max(0.0, float(value))) if value is not None else None
    except (TypeError, ValueError):
        return None


def _remaining_length(response) -> int | None:
    """Bytes of a Content-Length body that never arrived (http.client clips `read(n)` at the end of the stream without raising)."""
    length = getattr(response, "length", None)
    return length if isinstance(length, int) and length > 0 else None


def _read_body(response, limit: int) -> tuple[bytes, str | None]:
    """Read at most `limit` bytes of a response body. Returns (bytes, None) when the body arrived complete or reached the limit, and
    (the bytes that arrived, what went wrong) when it was cut (a chunked body ended early, a Content-Length body came up short) or the
    read failed (a timeout or a reset while reading)."""
    try:
        raw = response.read(limit)
    except http.client.IncompleteRead as error:
        partial = error.partial if isinstance(error.partial, bytes) else b""
        return partial[:limit], f"IncompleteRead after {len(partial)} bytes"
    except (http.client.HTTPException, OSError, ValueError) as error:
        return b"", f"{type(error).__name__}: {str(error)[:120]}"
    missing = _remaining_length(response)
    if missing and len(raw) < limit:
        return raw, f"Content-Length body cut short: {len(raw)} bytes arrived, {missing} missing"
    return raw, None


def request_json(method: str, url: str, headers: dict, payload=None, timeout: float = 60,
                 max_bytes: int = 20_000_000):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    merged = dict(headers)
    merged.setdefault("Accept", "application/json")
    if data is not None:
        merged["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=merged, method=method)
    progress = _Progress()
    req.attest_progress = progress
    try:
        with opener().open(req, timeout=timeout) as resp:
            progress.phase = "response"  # an answer exists, so the request was sent
            raw, cut = _read_body(resp, max_bytes)
            if cut:
                raise TransportError(f"the body of the HTTP {resp.status} answer was cut ({cut}); the request was sent and may have been executed",
                                     request_sent=True, phase="response", status=resp.status) from None
            try:
                body = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError as error:
                snippet = raw[:160].decode("utf-8", "replace").replace("\n", " ")
                raise TransportError(f"JSONDecodeError after HTTP {resp.status}: {error.msg} at char {error.pos}; "
                                     f"{len(raw)} bytes received, starts with: {snippet!r}", request_sent=True, phase="response",
                                     status=resp.status) from None
            return resp.status, body, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as error:
        # the status line and headers arrived: the answer is known whatever happens to its body, which is read under its own guard so
        # that a cut or stalled error body never escapes as a raw IncompleteRead or timeout (revision 9)
        progress.phase = "response"
        raw, cut = _read_body(error, 200_000)
        try:
            body = json.loads(raw)
        except Exception:
            body = {"raw": raw.decode("utf-8", "replace")[:2000]}
        try:
            headers = dict(error.headers.items()) if error.headers else None
        except Exception:  # noqa: BLE001 - headers that cannot be listed are not needed to classify the answer
            headers = None
        raise HttpError(error.code, body, url, headers, body_complete=cut is None, body_error=cut) from None
    except TransportError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, http.client.HTTPException) as error:
        # http.client.IncompleteRead (a chunked body cut short while reading) is an HTTPException, not an OSError: it is
        # a transport failure like any other, so GET polls retry it and a POST after it stays uncertain
        sent = progress.phase != "connect"
        detail = f"{type(error).__name__}: {str(error)[:200]}"
        if not sent:
            detail += " (while the connection was being set up; no byte of the request was sent)"
        raise TransportError(detail, request_sent=sent, phase=progress.phase) from None
