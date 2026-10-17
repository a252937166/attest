"""Private credential loading.

Order: process environment, then (optionally) a private credential note on this machine. Secrets are only placed into
os.environ for this process and are never written to run artifacts.

Note locations are personal and live outside the repository: `~/.config/attest/notes.json` maps a secret name to the
path of the note that contains it (`ATTEST_SECRETS_NOTES` overrides the config path; `ATTEST_<NAME>_NOTE` overrides one
entry). Deployments and pilot users set the environment variables and never need notes.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

KNOWN = ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY")
DEFAULT_PROJECT_ID = "aiproject-e00p460g3mgey447tt"


class SecretError(RuntimeError):
    pass


def _notes_config() -> dict:
    path = Path(os.environ.get("ATTEST_SECRETS_NOTES") or (Path.home() / ".config" / "attest" / "notes.json"))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _note_path(name: str) -> Path | None:
    override = os.environ.get(f"ATTEST_{name}_NOTE")
    if override:
        return Path(override)
    configured = _notes_config().get(name)
    return Path(configured) if configured else None


def _extract(name: str, text: str) -> str | None:
    if name == "NEBIUS_API_KEY":
        match = re.search(r"(?m)^\s*(?:export\s+)?NEBIUS_API_KEY\s*=\s*([^\r\n]+)", text)
        return match.group(1).strip().strip("\"'`") if match else None
    if name == "CODEX_API_KEY":
        label = os.environ.get("ATTEST_CODEX_KEY_LABEL", "mac")
        for match in re.finditer(r"\|\s*API Key[：:]\s*([^|]+?)\s*\|\s*`(cxk_[A-Za-z0-9_\-]+)`", text):
            if match.group(1).strip() == label:
                return match.group(2)
        return None
    if name == "TAVILY_API_KEY":
        match = re.search(r"(tvly-[A-Za-z0-9_\-]+)", text)
        return match.group(1) if match else None
    raise SecretError(f"unknown secret {name}")


def load_secret(name: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    if name not in KNOWN:
        raise SecretError(f"unknown secret {name}")
    path = _note_path(name)
    if path is None:
        raise SecretError(f"{name} is not set. Export it in your shell (export {name}=...) before running; it is never written to artifacts.")
    if not path.is_file():
        raise SecretError(f"{name} not in environment and note not found: {path}")
    value = _extract(name, path.read_text(encoding="utf-8"))
    if not value:
        raise SecretError(f"{name} not found in {path.name}")
    os.environ[name] = value
    return value


def project_id() -> str:
    """The Token Factory project id. Pilot users must set NEBIUS_PROJECT_ID; the team's default applies only on a machine that
    has the team's credential-note config, so nobody runs against the team's project by accident."""
    value = os.environ.get("NEBIUS_PROJECT_ID") or os.environ.get("NEBIUS_AI_PROJECT")
    if value:
        return value
    if _notes_config():
        return DEFAULT_PROJECT_ID
    raise SecretError("NEBIUS_PROJECT_ID is not set (export NEBIUS_PROJECT_ID=aiproject-...; it is the project id shown in the Token Factory console, not a key)")


def redact(text: str, *names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value and value in text:
            text = text.replace(value, f"[{name} REDACTED]")
    return text
