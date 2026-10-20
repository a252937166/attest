"""Offline test isolation (revision 9, 20 Oct 2026), imported by tests/__init__.py before any test module, whichever way the suite is
run from this package (`python -m unittest discover -s tests -t .`, or a single module).

- Provider credentials and the private configuration are removed from this process: the API key variables, the development
  gateway's URL, the Token Factory project and the export's private host list are unset, and ATTEST_SECRETS_NOTES points at a file
  that does not exist, so ~/.config/attest/notes.json is never read. A test that needs such a value sets its own synthetic one.
- Proxies: the environment's proxy variables are removed and `no_proxy=*` is set, so urllib never sends a request through this
  machine's proxy (on macOS it would otherwise read the system proxy configuration, and a loopback proxy forwards anywhere).
- Network: a connection or a name lookup outside the loopback interface raises `NetworkForbidden` (an AssertionError, which no
  transport handler catches, so the test that caused it fails where it happened) and is recorded in ATTEMPTS;
  tests/test_zz_isolation.py, the last module of a discovery run, fails when any attempt was recorded.
"""

from __future__ import annotations

import os
import socket
import tempfile
import threading
import traceback

PRIVATE_VARIABLES = ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY", "ATTEST_CODEX_BASE_URL", "ATTEST_EXPORT_PRIVATE_HOSTS", "NEBIUS_PROJECT_ID",
                     "NEBIUS_AI_PROJECT", "ATTEST_CODEX_KEY_LABEL", "ATTEST_NEBIUS_NOTE", "ATTEST_CODEX_NOTE", "ATTEST_TAVILY_NOTE")
PROXY_VARIABLES = ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy")
LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0", ""}
ATTEMPTS: list[str] = []
_lock = threading.Lock()


class NetworkForbidden(AssertionError):
    """A test tried to reach something outside the loopback interface."""


def _forbid(what: str, target) -> None:
    where = "".join(traceback.format_stack(limit=8)[:-2])
    with _lock:
        ATTEMPTS.append(f"{what} {target!r}\n{where}")
    raise NetworkForbidden(f"the offline suite reached outside the loopback interface ({what} {target!r})")


def _host(address):
    return address[0] if isinstance(address, tuple) and address else None


_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_create_connection = socket.create_connection
_real_getaddrinfo = socket.getaddrinfo


def _connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and _host(address) not in LOOPBACK:
        _forbid("connection to", _host(address))
    return _real_connect(self, address)


def _connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6) and _host(address) not in LOOPBACK:
        _forbid("connection to", _host(address))
    return _real_connect_ex(self, address)


def _create_connection(address, *args, **kwargs):
    if _host(address) not in LOOPBACK:
        _forbid("connection to", _host(address))
    return _real_create_connection(address, *args, **kwargs)


def _getaddrinfo(host, *args, **kwargs):
    name = host.decode() if isinstance(host, bytes) else host
    if name is not None and name not in LOOPBACK:
        _forbid("name lookup of", name)
    return _real_getaddrinfo(host, *args, **kwargs)


def install() -> None:
    for name in PRIVATE_VARIABLES + PROXY_VARIABLES:
        os.environ.pop(name, None)
    os.environ["ATTEST_SECRETS_NOTES"] = os.path.join(tempfile.gettempdir(), "attest-tests-no-private-notes", "notes.json")
    os.environ["no_proxy"] = os.environ["NO_PROXY"] = "*"
    socket.socket.connect = _connect
    socket.socket.connect_ex = _connect_ex
    socket.create_connection = _create_connection
    socket.getaddrinfo = _getaddrinfo


install()
