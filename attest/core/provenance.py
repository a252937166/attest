"""Provenance of a run: which Attest code, which guest programs, which sampling parameters and limits produced a bundle.

There is no git repository yet, so the Attest revision is the sha256 over the package sources (relative path and content
of every `attest/**/*.py`, sorted). The guest programs that decide test outcomes (supervisor, per-test child, canary module
and the sandbox runner) are digested from the exact source strings sent to the sandbox. Everything here is recorded once
per run under `bundle["provenance"]` and shown in PROOF.md section 1.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path

from .. import __version__
from .sealed import CANARY_SRC, CHILD_SRC, SUPERVISOR_SRC, SUPERVISOR_VERSION

PACKAGE_DIR = Path(__file__).resolve().parent.parent  # attest/


def attest_revision(package_dir: Path = PACKAGE_DIR) -> dict:
    """sha256 over every Python source of the package, plus the git commit when the tree is a repository."""
    digest = hashlib.sha256()
    count = 0
    for path in sorted(p for p in Path(package_dir).rglob("*.py") if "__pycache__" not in p.parts):
        rel = path.relative_to(package_dir).as_posix()
        digest.update(rel.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
        count += 1
    commit = None
    try:
        proc = subprocess.run(["git", "-C", str(package_dir), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            commit = proc.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {"method": "sha256 over the relative path and content of every attest/**/*.py, sorted", "digest": digest.hexdigest(),
            "files": count, "git_commit": commit, "version": __version__}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def guest_digests() -> dict:
    """Digests of the programs that run inside the sandbox and decide test outcomes."""
    try:
        from ..sandbox.tf_sandboxes import GUEST_RUNNER
        runner = _sha(GUEST_RUNNER)
    except Exception:  # noqa: BLE001 - the executor module is optional for offline tools
        runner = None
    return {"supervisor": {"version": SUPERVISOR_VERSION, "sha256": _sha(SUPERVISOR_SRC)}, "child_sha256": _sha(CHILD_SRC),
            "canary_sha256": _sha(CANARY_SRC), "guest_runner_sha256": runner}


def sampling_from(provider_description: dict) -> dict:
    """Sampling parameters in one place. The Codex gateway controls sampling itself and exposes a reasoning effort per
    role; the Token Factory provider sends an explicit temperature and max_tokens."""
    desc = provider_description or {}
    provider = desc.get("provider")
    roles = desc.get("roles") or {}
    if provider == "codex_gateway":
        return {"provider": provider, "temperature": None, "max_tokens": None,
                "note": "sampling is controlled by the gateway; the reasoning effort requested per role is recorded",
                "roles": {role: {"model": (sel[0] if isinstance(sel, (list, tuple)) else sel), "effort": (sel[1] if isinstance(sel, (list, tuple)) and len(sel) > 1 else None)}
                          for role, sel in roles.items()}}
    return {"provider": provider, "temperature": desc.get("temperature"), "max_tokens": desc.get("max_tokens"),
            "thinking_roles": desc.get("thinking_roles"), "send_thinking_flag": desc.get("send_thinking_flag"),
            "reasoning_effort": desc.get("reasoning_effort"),
            "note": "temperature and max_tokens are sent with every request; roles map to model ids",
            "roles": {role: ({"model": sel[0], "effort": sel[1] if len(sel) > 1 else None} if isinstance(sel, (list, tuple)) else {"model": sel, "effort": None})
                      for role, sel in roles.items()}}


def runtime() -> dict:
    """The interpreter and the package location this process executes (a batch snapshot or a deployed tree)."""
    return {"python": sys.version.split()[0], "platform": platform.platform(), "package_dir": str(PACKAGE_DIR)}


def build_provenance(provider_description: dict, limits: dict, upstream: dict | None) -> dict:
    guest = guest_digests()
    desc = provider_description or {}
    return {"attest_version": __version__, "attest_revision": attest_revision(), **guest, "runtime": runtime(),
            "sampling": sampling_from(desc), "limits": dict(limits), "pacing": desc.get("pacing"),
            "retry_policy": desc.get("retry_policy"), "upstream": dict(upstream) if upstream else None}
