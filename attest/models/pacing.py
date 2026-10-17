"""Pacing for the Codex gateway key: every role and every worker in this process (and, through a small state file, every
process on this machine) draws from one hourly budget.

What is known about the limit (recorded in reports/attest-reliability-2026-10-17/README.md): on 16 Oct 2026 and again on
17 Oct 2026 the gateway accepted exactly 60 requests for this key within an hour and answered `HTTP 429 hourly limit reached
for this key` to the next ones, independent of the token volume (628k and 718k tokens; 1.17M tokens in one hour had passed on
15 Oct). The gateway operator removed the hourly counter on 17 Oct 2026 at 09:37 UTC; `GET /v1/status` now declares the
policy under `limits` (`hourly_requests`, `hourly_requests_enforced`, `max_concurrent_requests`, `max_waiting_requests`,
`daily_token_cap`). The governor therefore takes its budget from the declared policy when the client can read it
(`configure_from_status`): no hourly window when enforcement is off, otherwise the declared count times a safety fraction
(default 90%). Without a readable policy it falls back to the observed 60 per rolling hour. A rolling window with a margin is
conservative whether a gateway counts per rolling hour or per clock hour.

Rules:
* Before every request the caller takes a slot: a concurrency permit (the gateway executes one request at a time and
  queues the rest, so more than a couple in flight only lengthens its queue) and a window entry. Attempts count, not
  successes, so a rejected request also consumes budget here.
* When the window is full the caller waits until the oldest entry ages out, in bounded steps that are reported through
  `notify`; past `max_wait_s` the wait fails visibly (PacingError) instead of blocking forever.
* An HTTP 429 from the gateway marks the key blocked (Retry-After when the gateway sends one, otherwise until the window
  reopens, at least 60 s); the next acquire waits for that. A 429 is a definite rejection (nothing executed), so the caller
  may retry the same request after the wait; transport-uncertain failures are never retried.
* Nothing here ever selects another provider. Exhaustion is reported, not worked around.

The state file (`ATTEST_CODEX_PACING_STATE`, default ~/.cache/attest/codex-pacing-<key id>.json, `off` to disable) is
shared between processes with an advisory lock; when it is unusable the governor falls back to process memory and says so.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import threading
import time
from pathlib import Path

WINDOW_S = 3600.0
DEFAULT_HOURLY_LIMIT = 60
DEFAULT_SAFETY = 0.9
DEFAULT_CONCURRENCY = 2
DEFAULT_MAX_WAIT_S = 3900.0  # a full window plus margin; beyond this the wait is reported as a failure
MIN_BLOCK_S = 60.0
MAX_429_RETRIES = 2
STEP_S = 30.0


class PacingError(RuntimeError):
    """The bounded wait for budget was exceeded; the request was NOT sent."""


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, "") or default)
    except ValueError:
        return default


def key_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:12]


def default_state_path(key: str) -> Path | None:
    configured = os.environ.get("ATTEST_CODEX_PACING_STATE", "")
    if configured.lower() == "off":
        return None
    if configured:
        return Path(configured)
    cache = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return cache / "attest" / f"codex-pacing-{key}.json"


class RateGovernor:
    def __init__(self, key: str, hourly_limit: int = DEFAULT_HOURLY_LIMIT, safety: float = DEFAULT_SAFETY,
                 max_concurrency: int = DEFAULT_CONCURRENCY, max_wait_s: float = DEFAULT_MAX_WAIT_S,
                 state_path: Path | None = None, time_fn=time.time, sleep_fn=time.sleep):
        self.key = key
        self.safety = float(safety)
        self.hourly_limit: int | None = int(hourly_limit) if hourly_limit else None
        self.budget: int | None = max(1, int(self.hourly_limit * self.safety)) if self.hourly_limit else None
        self.policy_source = "default (observed limit of 60 requests per hour, 16 and 17 Oct 2026)"
        self.policy_checked_at: float | None = None
        self.max_concurrency = max(1, int(max_concurrency))
        self.max_wait_s = float(max_wait_s)
        self.state_path = state_path
        self.state_error: str | None = None
        self._time = time_fn
        self._sleep = sleep_fn
        self._permits = threading.BoundedSemaphore(self.max_concurrency)
        self._lock = threading.Lock()
        self._calls: list[float] = []
        self._blocked_until = 0.0
        self.waits: list[dict] = []
        self.rejections = 0
        self.in_flight = 0

    # ------------------------------------------------------------------ shared state
    def _read_state(self) -> dict:
        if not self.state_path:
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_state(self, calls: list[float], blocked_until: float) -> None:
        if not self.state_path:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"calls": calls, "blocked_until": blocked_until, "updated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat()}),
                           encoding="utf-8")
            os.replace(tmp, self.state_path)
            self.state_error = None
        except OSError as error:
            self.state_error = f"{type(error).__name__}: {error}"  # memory-only from here; recorded in snapshot()

    def _locked_file(self):
        """Advisory lock around read-modify-write of the state file (no-op without a file)."""
        governor = self

        class _Lock:
            def __enter__(self):
                self.handle = None
                if governor.state_path:
                    try:
                        governor.state_path.parent.mkdir(parents=True, exist_ok=True)
                        self.handle = open(governor.state_path.with_suffix(".lock"), "a+")
                        import fcntl
                        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
                    except (OSError, ImportError) as error:
                        governor.state_error = f"{type(error).__name__}: {error}"
                        self.handle = None
                return self

            def __exit__(self, *exc):
                if self.handle:
                    try:
                        import fcntl
                        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
                    except (OSError, ImportError):
                        pass
                    self.handle.close()
                return False

        return _Lock()

    def _merged(self, now: float) -> tuple[list[float], float]:
        """The window: the shared state file when it is usable (it already contains this process's attempts), otherwise
        process memory. Attempts are kept as a list, never a set: two attempts in the same instant are two attempts."""
        state = self._read_state() if self.state_path and not self.state_error else {}
        if state:
            calls = [float(t) for t in (state.get("calls") or []) if isinstance(t, (int, float))]
            blocked = max(float(state.get("blocked_until") or 0.0), self._blocked_until)
        else:
            calls, blocked = list(self._calls), self._blocked_until
        calls = sorted(t for t in calls if now - t < WINDOW_S)
        return calls, blocked

    # ------------------------------------------------------------------ policy
    def configure_from_status(self, status: dict | None, source: str = "gateway status") -> None:
        """Adopt the gateway's declared policy: `limits.hourly_requests_enforced` false disables the hourly window; a declared
        `hourly_requests` count sets the budget (times the safety fraction); the declared concurrency never raises ours."""
        limits = (status or {}).get("limits") if isinstance(status, dict) else None
        self.policy_checked_at = self._time()
        if not isinstance(limits, dict):
            self.policy_source = f"{source}: no limits declared; keeping {self.policy_source}"
            return
        with self._lock:
            if limits.get("hourly_requests_enforced") is False or (limits.get("hourly_requests") is None and "hourly_requests_enforced" in limits):
                self.hourly_limit, self.budget = None, None
                self.policy_source = f"{source}: hourly request counting not enforced"
            elif isinstance(limits.get("hourly_requests"), (int, float)) and limits["hourly_requests"] > 0:
                self.hourly_limit = int(limits["hourly_requests"])
                self.budget = max(1, int(self.hourly_limit * self.safety))
                self.policy_source = f"{source}: {self.hourly_limit} requests per hour declared"
            declared = limits.get("max_concurrent_requests")
            if isinstance(declared, int) and declared > 0 and declared + 1 < self.max_concurrency:
                self.max_concurrency = declared + 1  # one executing, one waiting in the gateway queue

    # ------------------------------------------------------------------ planning
    def next_slot(self, now: float | None = None, needed: int = 1) -> tuple[float, dict]:
        """Earliest time at which `needed` more requests fit in the window, and the window state used to decide."""
        now = self._time() if now is None else now
        with self._lock, self._locked_file():
            calls, blocked = self._merged(now)
        used = len(calls)
        if self.budget is None:
            return max(now, blocked), {"used": used, "budget": None, "blocked_until": blocked, "now": now}
        free = self.budget - used
        slot = now
        if free < needed:
            # the (needed - free)-th oldest entry must age out first
            index = min(len(calls) - 1, max(0, needed - free - 1))
            slot = max(slot, calls[index] + WINDOW_S)
        slot = max(slot, blocked)
        return slot, {"used": used, "budget": self.budget, "blocked_until": blocked, "now": now}

    def headroom(self, now: float | None = None) -> int | None:
        """Requests that still fit in the window; None when no hourly budget is enforced."""
        _, state = self.next_slot(now)
        return None if state["budget"] is None else max(0, state["budget"] - state["used"])

    def _wait_until(self, slot: float, notify, what: str) -> float:
        waited = 0.0
        announced = False
        while True:
            now = self._time()
            remaining = slot - now
            if remaining <= 0:
                return waited
            if waited + remaining > self.max_wait_s:
                raise PacingError(f"codex pacing: {what} needs {remaining:.0f} s more but the bounded wait is {self.max_wait_s:.0f} s "
                                  f"(waited {waited:.0f} s); the request was not sent and nothing fell back to another provider")
            if notify and not announced:
                budget = f"hourly budget {self.budget} of {self.hourly_limit} requests per key" if self.budget else "no hourly budget enforced"
                notify(f"pacing: {what}; waiting {remaining:.0f} s ({budget})")
                announced = True
            step = min(STEP_S, remaining)
            self._sleep(step)
            waited += step

    # ------------------------------------------------------------------ slots
    def acquire(self, notify=None) -> dict:
        """Take a concurrency permit and a window entry; wait (bounded) when the budget is used up or the key is blocked."""
        if not self._permits.acquire(timeout=self.max_wait_s):
            raise PacingError(f"codex pacing: no concurrency permit within {self.max_wait_s:.0f} s ({self.max_concurrency} in flight)")
        try:
            waited_total = 0.0
            while True:
                slot, state = self.next_slot()
                if slot <= state["now"]:
                    with self._lock, self._locked_file():
                        calls, blocked = self._merged(state["now"])
                        calls.append(state["now"])
                        self._calls = calls  # memory mirrors the shared window so a later file failure loses nothing
                        self._write_state(calls, blocked)
                        self.in_flight += 1
                    if waited_total:
                        self.waits.append({"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "waited_s": round(waited_total, 1),
                                           "reason": "hourly budget" if state["blocked_until"] <= state["now"] else "key blocked after HTTP 429"})
                    return {"waited_s": round(waited_total, 1), "used": len(calls), "budget": self.budget}
                reason = ("key blocked after HTTP 429" if state["blocked_until"] > state["now"]
                          else f"hourly budget used ({state['used']} of {self.budget} requests in the last hour)")
                waited_total += self._wait_until(slot, notify, reason)
        except BaseException:
            self._permits.release()
            raise

    def release(self) -> None:
        with self._lock:
            self.in_flight = max(0, self.in_flight - 1)
        self._permits.release()

    def record_rejection(self, retry_after_s: float | None = None, now: float | None = None) -> float:
        """The gateway answered 429. Block the key until Retry-After, else until the window reopens (at least MIN_BLOCK_S)."""
        now = self._time() if now is None else now
        with self._lock, self._locked_file():
            calls, blocked = self._merged(now)
            if retry_after_s is not None:
                until = now + max(MIN_BLOCK_S, float(retry_after_s))
            elif calls:
                until = max(now + MIN_BLOCK_S, calls[0] + WINDOW_S + 30.0)
            else:
                # our window is empty, so another process or machine used the budget: wait for the next clock hour (covers a
                # per-clock-hour gateway) with a one-minute margin
                until = (now // 3600 + 1) * 3600 + 60.0
            self._blocked_until = max(blocked, until)
            self.rejections += 1
            self._write_state(calls, self._blocked_until)
            return self._blocked_until

    def wait_for_headroom(self, needed: int, notify=None) -> float:
        """Harness use: before starting a cell, wait (bounded) until `needed` requests fit in the window."""
        slot, _ = self.next_slot(needed=max(1, needed))
        return self._wait_until(slot, notify, f"a run needs about {needed} requests of headroom")

    def snapshot(self) -> dict:
        _, state = self.next_slot()
        return {"model": ("rolling window of 3600 s per key; attempts counted; safety fraction applied" if self.budget
                          else "no hourly window (the gateway declares hourly counting not enforced); concurrency and 429 handling only"),
                "policy_source": self.policy_source, "policy_checked_at_epoch": self.policy_checked_at,
                "hourly_limit_assumed": self.hourly_limit, "budget": self.budget, "max_concurrency": self.max_concurrency,
                "max_wait_s": self.max_wait_s, "used_in_window": state["used"], "blocked_until_epoch": state["blocked_until"] or None,
                "rejections_seen": self.rejections, "waits": list(self.waits), "state_file": str(self.state_path) if self.state_path else None,
                "state_shared_across_processes": bool(self.state_path) and not self.state_error, "state_error": self.state_error}


_GOVERNORS: dict[str, RateGovernor] = {}
_REGISTRY_LOCK = threading.Lock()


def governor_for(api_key: str) -> RateGovernor:
    """One governor per key for the whole process (every role, every worker thread), configured from the environment:
    ATTEST_CODEX_HOURLY_LIMIT (60), ATTEST_CODEX_SAFETY (0.9), ATTEST_CODEX_MAX_CONCURRENCY (2), ATTEST_CODEX_MAX_WAIT_S (3900),
    ATTEST_CODEX_PACING_STATE (path, or `off`)."""
    key = key_id(api_key)
    with _REGISTRY_LOCK:
        if key not in _GOVERNORS:
            _GOVERNORS[key] = RateGovernor(key, hourly_limit=int(_env_float("ATTEST_CODEX_HOURLY_LIMIT", DEFAULT_HOURLY_LIMIT)),
                                           safety=_env_float("ATTEST_CODEX_SAFETY", DEFAULT_SAFETY),
                                           max_concurrency=int(_env_float("ATTEST_CODEX_MAX_CONCURRENCY", DEFAULT_CONCURRENCY)),
                                           max_wait_s=_env_float("ATTEST_CODEX_MAX_WAIT_S", DEFAULT_MAX_WAIT_S),
                                           state_path=default_state_path(key))
        return _GOVERNORS[key]
