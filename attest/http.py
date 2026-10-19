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
    def __init__(self, status: int, body, url: str, headers: dict | None = None):
        self.status = status
        self.body = body
        self.url = url
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}  # Retry-After and rate-limit headers, when sent
        message = ""
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict):
                message = str(err.get("message") or err.get("type") or "")
            elif err:
                message = str(err)
            else:
                message = str(body.get("message") or body.get("detail") or "")[:300]
        super().__init__(f"HTTP {status} from {url.split('?')[0]}: {message[:300]}")


class TransportError(Exception):
    """The request failed in transit. `request_sent` is False only when the failure happened while the connection was being set
    up, before any byte of the request was written: the server cannot have received it, and it may be sent again. Otherwise the
    outcome is uncertain (timeout, reset, a cut response): never auto-replay a POST after this."""

    def __init__(self, message: str, request_sent: bool = True, phase: str = "unknown"):
        super().__init__(message)
        self.request_sent = request_sent
        self.phase = phase


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
            raw = resp.read(max_bytes)
            try:
                body = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError as error:
                snippet = raw[:160].decode("utf-8", "replace").replace("\n", " ")
                raise TransportError(f"JSONDecodeError after HTTP {resp.status}: {error.msg} at char {error.pos}; "
                                     f"{len(raw)} bytes received, starts with: {snippet!r}", request_sent=True, phase="response") from None
            return resp.status, body, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as error:
        raw = error.read(200_000)
        try:
            body = json.loads(raw)
        except Exception:
            body = {"raw": raw.decode("utf-8", "replace")[:2000]}
        raise HttpError(error.code, body, url, dict(error.headers.items()) if error.headers else None) from None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, http.client.HTTPException) as error:
        # http.client.IncompleteRead (a chunked body cut short while reading) is an HTTPException, not an OSError: it is
        # a transport failure like any other, so GET polls retry it and a POST after it stays uncertain
        sent = progress.phase != "connect"
        detail = f"{type(error).__name__}: {str(error)[:200]}"
        if not sent:
            detail += " (while the connection was being set up; no byte of the request was sent)"
        raise TransportError(detail, request_sent=sent, phase=progress.phase) from None
