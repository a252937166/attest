"""Minimal HTTPS JSON client shared by the model and sandbox adapters.

TLS verification is always on. Transport failures on POST are reported as
"uncertain" so callers never replay them blindly.
"""

from __future__ import annotations

import http.client
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path


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


_OPENER = None


def opener():
    global _OPENER
    if _OPENER is None:
        _OPENER = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=tls_context()))
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
    """The request outcome is uncertain (timeout, reset). Never auto-replay a POST after this."""


def request_json(method: str, url: str, headers: dict, payload=None, timeout: float = 60,
                 max_bytes: int = 20_000_000):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    merged = dict(headers)
    merged.setdefault("Accept", "application/json")
    if data is not None:
        merged["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=merged, method=method)
    try:
        with opener().open(req, timeout=timeout) as resp:
            raw = resp.read(max_bytes)
            try:
                body = json.loads(raw) if raw.strip() else None
            except json.JSONDecodeError as error:
                snippet = raw[:160].decode("utf-8", "replace").replace("\n", " ")
                raise TransportError(f"JSONDecodeError after HTTP {resp.status}: {error.msg} at char {error.pos}; "
                                     f"{len(raw)} bytes received, starts with: {snippet!r}") from None
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
        raise TransportError(f"{type(error).__name__}: {str(error)[:200]}") from None
