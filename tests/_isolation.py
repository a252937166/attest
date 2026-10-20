"""Offline test isolation (revision 9, 20 Oct 2026), imported by tests/__init__.py before any test module, whichever way the suite is
run from this package (`python -m unittest discover -s tests -t .`, or a single module).

- Provider credentials and the private configuration are removed from this process: the API key variables, the development
  gateway's URL, the Token Factory project and the export's private host list are unset, and ATTEST_SECRETS_NOTES points at a file
  that does not exist, so ~/.config/attest/notes.json is never read. A test that needs such a value sets its own synthetic one.
- Proxies: the environment's proxy variables are removed and `no_proxy=*` is set, so urllib never sends a request through this
  machine's proxy (on macOS it would otherwise read the system proxy configuration, and a loopback proxy forwards anywhere).
- Network: a connection or a name lookup outside the loopback interface raises `NetworkForbidden` (an AssertionError, which no
  transport handler catches, so the test that caused it fails where it happened) and is recorded in ATTEMPTS;
  tests/test_zz_isolation.py, the last module of a discovery run, fails when any attempt was recorded. A connection to the loopback
  port of a proxy this machine is configured to use (read from the environment and the system settings before they are removed) is
  refused the same way: through it a request would leave the machine. So is a connection to any loopback port that something was
  already listening on when the suite started (a local proxy, a resolver, another service could forward it); a test's own servers
  open new ports, and every port this process binds itself stays allowed.
- Home directory: HOME points at a new empty directory for the run, and the XDG base-directory variables are removed, so no test
  reads or writes the developer's home (the Codex pacing state under ~/.cache/attest, ~/.config/attest) and no run sees what an
  earlier one left there; subprocesses inherit it. tests/test_zz_isolation.py fails when the suite left anything in it. The
  directory is removed when the process exits.
"""

from __future__ import annotations

import atexit
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import traceback

PRIVATE_VARIABLES = ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY", "ATTEST_CODEX_BASE_URL", "ATTEST_EXPORT_PRIVATE_HOSTS", "NEBIUS_PROJECT_ID",
                     "NEBIUS_AI_PROJECT", "ATTEST_CODEX_KEY_LABEL", "ATTEST_NEBIUS_NOTE", "ATTEST_CODEX_NOTE", "ATTEST_TAVILY_NOTE")
PROXY_VARIABLES = ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy")
HOME_VARIABLES = ("XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME")
LOOPBACK = {"127.0.0.1", "::1", "localhost", "0.0.0.0", ""}
ATTEMPTS: list[str] = []
SUITE_HOME = ""  # the run's own home directory (install)
_lock = threading.Lock()


def _configured_proxy_ports() -> set[int]:
    """Loopback ports of the proxies this machine is configured to use (environment variables and, on macOS, the system settings)."""
    import urllib.request
    from urllib.parse import urlsplit
    try:
        configured = dict(urllib.request.getproxies())
    except Exception:  # noqa: BLE001 - no readable proxy configuration: nothing to refuse
        return set()
    ports = set()
    for scheme, value in configured.items():
        if scheme == "no" or not value:
            continue
        try:
            parts = urlsplit(value if "://" in value else "http://" + value)
            if parts.hostname in LOOPBACK and parts.port:
                ports.add(parts.port)
        except ValueError:
            continue
    return ports


PROXY_PORTS: set[int] = set()
PREEXISTING: dict[str, set[int]] = {"tcp": set(), "udp": set()}  # loopback-reachable ports listened on before the suite started
OWN_PORTS: set[tuple[str, int]] = set()                          # ports this process bound itself (a test's own servers)


def _listening_ports() -> dict[str, set[int]]:
    """TCP ports in LISTEN state and bound UDP ports on this machine (Linux: /proc/net; elsewhere: netstat)."""
    found: dict[str, set[int]] = {"tcp": set(), "udp": set()}
    proc = [("tcp", "/proc/net/tcp"), ("tcp", "/proc/net/tcp6"), ("udp", "/proc/net/udp"), ("udp", "/proc/net/udp6")]
    if any(os.path.exists(path) for _, path in proc):
        for kind, path in proc:
            try:
                with open(path, encoding="ascii", errors="replace") as handle:
                    lines = handle.read().splitlines()[1:]
            except OSError:
                continue
            for line in lines:
                cols = line.split()
                if len(cols) < 4 or (kind == "tcp" and cols[3] != "0A"):  # 0A: LISTEN
                    continue
                try:
                    found[kind].add(int(cols[1].rsplit(":", 1)[1], 16))
                except (IndexError, ValueError):
                    continue
        return found
    for kind in ("tcp", "udp"):
        try:
            out = subprocess.run(["netstat", "-an", "-p", kind], capture_output=True, text=True, timeout=15).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        for line in out.splitlines()[2:]:
            cols = line.split()
            if len(cols) < 4 or (kind == "tcp" and cols[-1] != "LISTEN"):
                continue
            match = re.search(r"[.:](\d+)$", cols[3])
            if match:
                found[kind].add(int(match.group(1)))
    return found


class NetworkForbidden(AssertionError):
    """A test tried to reach something outside the loopback interface."""


def _forbid(what: str, target) -> None:
    where = "".join(traceback.format_stack(limit=8)[:-2])
    with _lock:
        ATTEMPTS.append(f"{what} {target!r}\n{where}")
    raise NetworkForbidden(f"the offline suite reached outside the loopback interface ({what} {target!r})")


def _host(address):
    return address[0] if isinstance(address, tuple) and address else None


def _check(address, kind: str = "tcp") -> None:
    host = _host(address)
    if host not in LOOPBACK:
        _forbid("connection to", host)
    port = address[1] if isinstance(address, tuple) and len(address) > 1 else None
    if port in PROXY_PORTS and (kind, port) not in OWN_PORTS:
        _forbid("connection to this machine's proxy at", f"{host}:{port}")
    if port in PREEXISTING.get(kind, ()) and (kind, port) not in OWN_PORTS:
        _forbid(f"connection to a {kind} port that was listening before the suite started:", f"{host}:{port}")


def _kind(sock) -> str:
    return "udp" if sock.type == socket.SOCK_DGRAM else "tcp"


_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_bind = socket.socket.bind
_real_create_connection = socket.create_connection
_real_getaddrinfo = socket.getaddrinfo


def _connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(address, _kind(self))
    return _real_connect(self, address)


def _connect_ex(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _check(address, _kind(self))
    return _real_connect_ex(self, address)


def _bind(self, address):
    result = _real_bind(self, address)
    if self.family in (socket.AF_INET, socket.AF_INET6):
        try:
            with _lock:
                OWN_PORTS.add((_kind(self), self.getsockname()[1]))
        except OSError:
            pass
    return result


def _create_connection(address, *args, **kwargs):
    _check(address)
    return _real_create_connection(address, *args, **kwargs)


def _getaddrinfo(host, *args, **kwargs):
    name = host.decode() if isinstance(host, bytes) else host
    if name is not None and name not in LOOPBACK:
        _forbid("name lookup of", name)
    return _real_getaddrinfo(host, *args, **kwargs)


def home_contents() -> list[str]:
    """Everything under the run's home directory, relative to it (empty when no test wrote there)."""
    found = []
    for root, dirs, files in os.walk(SUITE_HOME):
        found.extend(os.path.relpath(os.path.join(root, name), SUITE_HOME) for name in dirs + files)
    return sorted(found)


def install() -> None:
    global SUITE_HOME
    PROXY_PORTS.update(_configured_proxy_ports())  # before the configuration is removed below
    for kind, ports in _listening_ports().items():
        PREEXISTING[kind].update(ports)
    for name in PRIVATE_VARIABLES + PROXY_VARIABLES + HOME_VARIABLES:
        os.environ.pop(name, None)
    SUITE_HOME = tempfile.mkdtemp(prefix="attest-tests-home-")
    os.environ["HOME"] = SUITE_HOME
    atexit.register(shutil.rmtree, SUITE_HOME, True)
    os.environ["ATTEST_SECRETS_NOTES"] = os.path.join(tempfile.gettempdir(), "attest-tests-no-private-notes", "notes.json")
    os.environ["no_proxy"] = os.environ["NO_PROXY"] = "*"
    socket.socket.connect = _connect
    socket.socket.connect_ex = _connect_ex
    socket.socket.bind = _bind
    socket.create_connection = _create_connection
    socket.getaddrinfo = _getaddrinfo


install()
