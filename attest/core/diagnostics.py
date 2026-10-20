"""Public error text versus private diagnostics (follow-up review R5-04, 19 Oct 2026).

Everything a run records publicly (bundle reasons, stage records, progress events, trajectory observations, PROOF.md) must not
carry raw exception text: provider messages can echo request bodies, sandbox errors can carry API responses, generic exceptions
carry host paths. The pipeline therefore records every failure through `Diagnostics.record`, which returns a short public
sentence built from a fixed vocabulary (`code`), plus a correlation reference, and appends the full text to a PRIVATE sidecar
file outside the run directory (`<runs dir>/diagnostics/<run id>.jsonl`), which is never part of a bundle, a manifest, a
download or the public export. The CLI operator and the service owner can look the reference up there.
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from ..ledger import utcnow

SIDECAR_DIR = "diagnostics"

# code -> the public sentence (never interpolates the original text; a status code is the only variable part)
PUBLIC = {
    "provider_http": "the model provider returned HTTP {status}",
    "provider_transport_uncertain": "the inference outcome is uncertain (transport failure); the request was not retried",
    "provider_rate_limited": "the model provider refused the request (HTTP 429, rate limit)",
    "provider_schema": "the model's output violated the required schema",
    "provider_cap_usd": "the per-run USD cap would be exceeded; the request was not sent",
    "provider_cap_calls": "the per-run call cap was reached; the request was not sent",
    "provider_halted": "paid calls were halted (journal or metering failure); the request was not sent",
    "provider_error": "the model provider call failed",
    "sandbox_error": "a sandbox operation failed",
    "sandbox_uncertain": "a sandbox operation's outcome is uncertain; it was not replayed",
    # revision 8: failures that are known to have happened before any byte of the request was written, and an accepted operation
    # whose outcome could not be read
    "transport_not_sent": "the request was never sent (the connection could not be set up), so sending it again was safe",
    "provider_unreachable": "the model provider could not be reached: no attempt got as far as sending the request, so nothing was executed or billed",
    "sandbox_unreachable": "the sandbox service could not be reached: no attempt got as far as sending the request, so nothing was executed",
    "sandbox_accepted_unread": "a sandbox operation was accepted but its outcome could not be read; it was not replayed, and its operation id is recorded for reconciliation",
    # revision 9: answers whose execution is unknown, refusals, a stopped run and journal failures
    "provider_http_uncertain": "the model provider answered HTTP {status} after the request was sent, so its outcome is uncertain; the request was not retried",
    "sandbox_http_uncertain": "the sandbox service answered HTTP {status} after the spawn was sent, so its outcome is uncertain; it was not replayed",
    "sandbox_rejected": "the sandbox service refused the operation (HTTP {status}); nothing was executed",
    "run_halted": "not sent: the run had stopped for reconciliation after an operation whose outcome is uncertain",
    "journal_failure": "a record of this run could not be journaled durably, so nothing further was sent and the run stopped",
    "internal_error": "an internal error occurred ({type})",
}


def classify_error(error: BaseException | str) -> tuple[str, str]:
    """(code, public sentence) for an exception or an error text, from a fixed vocabulary; nothing of the original text
    survives except an HTTP status code or the exception type name."""
    text = str(error)
    name = type(error).__name__ if isinstance(error, BaseException) else "text"
    lower = text.lower()
    uncertain = bool(getattr(error, "uncertain", False)) or "uncertain" in lower
    rate_limited = bool(getattr(error, "rate_limited", False))
    status = getattr(error, "http_status", None)
    if name == "RunHalted" or (getattr(error, "halted", False) is True and not getattr(error, "journal_failed", False)
                               and "journal" not in lower and "metering" not in lower):
        return "run_halted", PUBLIC["run_halted"]
    if name == "LedgerError" or getattr(error, "journal_failed", False) is True:
        return "journal_failure", PUBLIC["journal_failure"]
    if name == "SandboxError" and getattr(error, "rejected", False) is True:
        return "sandbox_rejected", PUBLIC["sandbox_rejected"].format(status=status if isinstance(status, int) else "4xx")
    if isinstance(status, int) and status >= 500 and uncertain and name in ("ModelError", "SandboxError"):
        key = "provider_http_uncertain" if name == "ModelError" else "sandbox_http_uncertain"
        return key, PUBLIC[key].format(status=status)
    if name == "HttpError" and isinstance(getattr(error, "status", None), int):
        status = error.status
        if status == 429:
            return "provider_rate_limited", PUBLIC["provider_rate_limited"]
        return "provider_http", PUBLIC["provider_http"].format(status=status)
    if name == "TransportError":
        if getattr(error, "request_sent", True) is False:
            return "transport_not_sent", PUBLIC["transport_not_sent"]
        return "provider_transport_uncertain", PUBLIC["provider_transport_uncertain"]
    if getattr(error, "unreachable", False):
        return ("sandbox_unreachable", PUBLIC["sandbox_unreachable"]) if name == "SandboxError" else ("provider_unreachable", PUBLIC["provider_unreachable"])
    if name == "SandboxError" and getattr(error, "accepted_unread", False):
        return "sandbox_accepted_unread", PUBLIC["sandbox_accepted_unread"]
    if name == "ModelError" or name == "text" and any(k in lower for k in ("model provider", "schema", "http ", "transport", "cap")):
        if uncertain:
            return "provider_transport_uncertain", PUBLIC["provider_transport_uncertain"]
        if rate_limited:
            return "provider_rate_limited", PUBLIC["provider_rate_limited"]
        if "refusing the request" in lower or "halted" in lower or "metering" in lower or "journal" in lower:
            return "provider_halted", PUBLIC["provider_halted"]
        if "usd cap" in lower:
            return "provider_cap_usd", PUBLIC["provider_cap_usd"]
        if "call cap" in lower:
            return "provider_cap_calls", PUBLIC["provider_cap_calls"]
        match = re.search(r"\bHTTP (\d{3})\b", text)
        if match:
            return "provider_http", PUBLIC["provider_http"].format(status=match.group(1))
        if "schema" in lower or "no json output" in lower:
            return "provider_schema", PUBLIC["provider_schema"]
        return "provider_error", PUBLIC["provider_error"]
    if name == "SandboxError" or "sandbox" in lower or "operation status" in lower or "guest report" in lower:
        if uncertain or "do not replay" in lower:
            return "sandbox_uncertain", PUBLIC["sandbox_uncertain"]
        return "sandbox_error", PUBLIC["sandbox_error"]
    return "internal_error", PUBLIC["internal_error"].format(type=name if name != "text" else "error")


class Diagnostics:
    """Records failures privately and hands out public text with a correlation reference."""

    def __init__(self, run_id: str, sidecar_dir: Path | None):
        self.run_id = run_id
        self.path = (Path(sidecar_dir) / f"{run_id}.jsonl") if sidecar_dir is not None else None
        self.entries: list[dict] = []  # kept in memory too (the CLI prints them at the end for the operator)

    def record(self, stage: str, error: BaseException | str, context: dict | None = None) -> dict:
        code, public = classify_error(error)
        reference = secrets.token_hex(4)
        entry = {"reference": reference, "at_utc": utcnow(), "run_id": self.run_id, "stage": stage, "code": code,
                 "type": type(error).__name__ if isinstance(error, BaseException) else "text", "detail": str(error)[:4000],
                 "context": context or {}}
        self.entries.append(entry)
        if self.path is not None:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError:
                pass  # the private sidecar is best effort; the public text below is produced regardless
        return {"code": code, "public": public, "reference": reference}

    def public_text(self, stage: str, error: BaseException | str, context: dict | None = None) -> str:
        """`<public sentence> [ref <reference>]`: the only form in which a failure enters bundle reasons, stage records,
        progress events or trajectory observations."""
        record = self.record(stage, error, context)
        return f"{record['public']} [ref {record['reference']}]"
