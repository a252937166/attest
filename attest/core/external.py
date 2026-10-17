"""Bounded import of an external repository as an Attest task (milestone M4, 17 Oct 2026).

Scope, from the design brief (section 2.4): a public GitHub repository at a pinned commit, or a local directory; Python
with unittest or pytest; dependencies installed once at checkpoint time from pinned requirements (the only networked
operation); write scope limited to named globs; tests and packaging files protected; at most 2,000 files and 25 MB; a
test suite that finishes on the base within the task's timeout (at most 300 s); at most 12 implementer turns.

Every limit is enforced here, before any sandbox operation, and every refusal names the limit it hit. The import writes
`SOURCE.json` next to the repository copy (URL, commit, tarball digest, counts, anything skipped) and a `task.json`
skeleton whose statement and acceptance criteria the requester fills in; `upstream` carries the URL and commit into the
frozen task and the Proof Bundle.
"""

from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import io
import json
import re
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

from ..http import tls_context
from .workspace import SKIP_DIRS, snapshot_repo

LIMITS = {
    "max_files": 2000,
    "max_total_bytes": 25_000_000,
    "max_file_bytes": 200_000,          # per file; see MAX_FILE_BYTES in workspace.py (raise per task up to the hard cap)
    "hard_max_file_bytes": 1_000_000,
    "max_test_timeout_s": 300,
    "max_checkpoint_timeout_s": 600,
    "max_turns": 12,
    "max_tarball_bytes": 80_000_000,    # compressed download cap
}
ALLOWED_RUNNERS = ("unittest", "pytest")
PROTECTED_DEFAULT = ["tests/**", "test/**", "setup.py", "setup.cfg", "pyproject.toml", "requirements*.txt", "requirements/**",
                     "*.lock", "poetry.lock", "Pipfile", "Pipfile.lock", "tox.ini", "noxfile.py", "MANIFEST.in", "Makefile", ".github/**"]
PACKAGING_FILES = ("setup.py", "setup.cfg", "pyproject.toml", "tox.ini", "noxfile.py", "MANIFEST.in")
GITHUB_RE = re.compile(r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class ImportRefused(ValueError):
    """The repository or the task violates a bound; the message names the limit. Nothing was run."""


def parse_github(url: str) -> tuple[str, str]:
    match = GITHUB_RE.match(url.strip())
    if not match:
        raise ImportRefused(f"source must be a public GitHub repository URL of the form https://github.com/<owner>/<repo>, got {url!r}")
    return match.group("owner"), match.group("repo")


def require_commit(commit: str) -> str:
    commit = (commit or "").strip().lower()
    if not COMMIT_RE.match(commit):
        raise ImportRefused("the commit must be pinned as a full 40-character hexadecimal sha (branches and tags are not accepted)")
    return commit


def _safe_member(member: tarfile.TarInfo, top: str) -> str | None:
    """Relative path inside the repository for a regular file member, or None to skip (dirs, links, unsafe names)."""
    name = member.name
    if not name.startswith(top + "/"):
        return None
    rel = name[len(top) + 1:]
    if not rel:
        return None
    pure = PurePosixPath(rel)
    if pure.is_absolute() or any(part in ("..", "") for part in pure.parts):
        raise ImportRefused(f"tarball member with an unsafe path: {name!r}")
    if not member.isfile():
        return None
    return pure.as_posix()


def _check_tree(files: dict[str, int], max_file_bytes: int) -> list[str]:
    problems = []
    if len(files) > LIMITS["max_files"]:
        problems.append(f"{len(files)} files exceed the limit of {LIMITS['max_files']} files")
    total = sum(files.values())
    if total > LIMITS["max_total_bytes"]:
        problems.append(f"{total} bytes exceed the limit of {LIMITS['max_total_bytes']} bytes (25 MB)")
    big = sorted((rel for rel, size in files.items() if size > max_file_bytes), key=lambda r: -files[r])
    if big:
        problems.append(f"{len(big)} file(s) exceed the per-file limit of {max_file_bytes} bytes, for example {big[0]} ({files[big[0]]} bytes)")
    return problems


def fetch_github(url: str, commit: str, dest: Path, max_file_bytes: int = LIMITS["max_file_bytes"]) -> dict:
    """Download the pinned commit as a tarball from codeload.github.com and extract regular files into `dest/repo`.
    Refuses (without writing the repository) when any bound is exceeded."""
    owner, repo = parse_github(url)
    commit = require_commit(commit)
    tarball_url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/{commit}"
    request = urllib.request.Request(tarball_url, headers={"User-Agent": "attest-import/0.4", "Accept": "application/x-gzip"})
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=tls_context()))
    buffer = io.BytesIO()
    with opener.open(request, timeout=120) as response:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            buffer.write(chunk)
            if buffer.tell() > LIMITS["max_tarball_bytes"]:
                raise ImportRefused(f"the tarball exceeds the download cap of {LIMITS['max_tarball_bytes']} bytes")
    data = buffer.getvalue()
    if not data:
        raise ImportRefused(f"empty tarball from {tarball_url}")
    record = {"url": url, "owner": owner, "repo": repo, "commit": commit, "tarball_url": tarball_url,
              "tarball_sha256": hashlib.sha256(data).hexdigest(), "tarball_bytes": len(data), "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    record.update(extract_tarball(data, dest, max_file_bytes))
    return record


def extract_tarball(data: bytes, dest: Path, max_file_bytes: int = LIMITS["max_file_bytes"]) -> dict:
    """Extract the regular files of a GitHub-style tarball (single top-level directory) into `dest/repo` under the bounds.
    Links, caches and VCS directories are skipped and listed; unsafe member names and any exceeded bound refuse the import
    before anything is written."""
    record = {"skipped": [], "limits": {k: LIMITS[k] for k in ("max_files", "max_total_bytes")} | {"max_file_bytes": max_file_bytes}}
    files: dict[str, bytes] = {}
    links: list[tuple[str, str]] = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise ImportRefused("the tarball is empty")
        top = members[0].name.split("/")[0]
        for member in members:
            if member.issym() or member.islnk():
                name = member.name[len(top) + 1:] if member.name.startswith(top + "/") else member.name
                links.append((name, member.linkname))
                continue
            rel = _safe_member(member, top)
            if rel is None:
                continue
            if any(part in SKIP_DIRS for part in PurePosixPath(rel).parts):
                record["skipped"].append({"path": rel, "reason": "cache or VCS directory"})
                continue
            if len(files) >= LIMITS["max_files"]:
                raise ImportRefused(f"more than {LIMITS['max_files']} files in the repository; the limit is {LIMITS['max_files']} files")
            handle = archive.extractfile(member)
            files[rel] = handle.read() if handle else b""
    # Links are never extracted as links. A symbolic link whose target is a regular file inside the repository becomes a
    # copy of that file (python-semver's tests import two modules this way); anything else is skipped and listed.
    record["materialized_links"] = []
    for rel, target in links:
        resolved = None
        if target and not target.startswith("/"):
            candidate = PurePosixPath(rel).parent.joinpath(target)
            parts: list[str] = []
            for part in candidate.parts:
                if part == "..":
                    if not parts:
                        parts = None
                        break
                    parts.pop()
                elif part not in (".", ""):
                    parts.append(part)
            resolved = "/".join(parts) if parts else None
        if resolved and resolved in files and rel not in files:
            files[rel] = files[resolved]
            record["materialized_links"].append({"path": rel, "copied_from": resolved})
        else:
            record["skipped"].append({"path": rel, "reason": f"link to {target!r} (outside the repository, missing, or not a regular file)"})
    problems = _check_tree({rel: len(content) for rel, content in files.items()}, max_file_bytes)
    if problems:
        raise ImportRefused("; ".join(problems))
    repo_dir = dest / "repo"
    if repo_dir.exists():
        raise ImportRefused(f"{repo_dir} already exists; refusing to overwrite an imported repository")
    for rel, content in files.items():
        path = repo_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    record.update({"files": len(files), "total_bytes": sum(len(c) for c in files.values()),
                   "tree_sha256": tree_sha256(files)})
    return record


def import_local(source: Path, dest: Path, max_file_bytes: int = LIMITS["max_file_bytes"]) -> dict:
    """Copy a local directory (regular files only, caches and VCS metadata skipped) under the same bounds."""
    source = Path(source).resolve()
    if not source.is_dir():
        raise ImportRefused(f"{source} is not a directory")
    files: dict[str, int] = {}
    skipped = []
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(source).parts):
            continue
        if path.is_symlink():
            skipped.append({"path": rel, "reason": "symbolic link"})
            continue
        if path.is_file():
            files[rel] = path.stat().st_size
            if len(files) > LIMITS["max_files"]:
                raise ImportRefused(f"more than {LIMITS['max_files']} files under {source}; the limit is {LIMITS['max_files']} files")
    problems = _check_tree(files, max_file_bytes)
    if problems:
        raise ImportRefused("; ".join(problems))
    repo_dir = dest / "repo"
    if repo_dir.exists():
        raise ImportRefused(f"{repo_dir} already exists; refusing to overwrite an imported repository")
    for rel in files:
        target = repo_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target)
    snapshot = snapshot_repo(repo_dir)
    return {"url": None, "local_source": str(source), "commit": None, "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "files": len(files), "total_bytes": sum(files.values()), "tree_sha256": tree_sha256(snapshot), "skipped": skipped,
            "limits": {k: LIMITS[k] for k in ("max_files", "max_total_bytes")} | {"max_file_bytes": max_file_bytes}}


def tree_sha256(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(files[rel]).digest())
    return digest.hexdigest()


def _glob_hits(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or (pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(pattern[:-3] + "/"))):
            return True
    return False


def external_policy_problems(task) -> list[str]:
    """The task-level bounds for an externally sourced task (one with `upstream`): named write scope, protected tests and
    packaging, allowed runner, pinned install, bounded timeouts. Each problem names the limit."""
    problems = []
    if not task.upstream or not task.upstream.get("url"):
        problems.append("external tasks must record upstream.url")
    elif task.upstream.get("url", "").startswith("https://github.com/") and not COMMIT_RE.match(str(task.upstream.get("commit") or "")):
        problems.append("external tasks from GitHub must pin upstream.commit to a full 40-character sha")
    if task.language != "python":
        problems.append(f"language {task.language!r} is not supported; the external pilot supports Python only")
    if task.test_runner not in ALLOWED_RUNNERS:
        problems.append(f"test runner {task.test_runner!r} is not supported; allowed: {', '.join(ALLOWED_RUNNERS)}")
    globs = list(task.allowed_write_globs)
    if not globs or any(g.strip() in ("**", "*", "**/*", "/", ".") for g in globs):
        problems.append("allowed_write_globs must name the files the implementer may change (a whole-repository scope such as '**' is refused)")
    protected = list(task.protected_globs)
    for required in ("tests/**",):
        if not any(_glob_hits("tests/x.py", [p]) for p in protected):
            problems.append("protected_globs must protect the test directory (tests/**)")
            break
    for packaging in PACKAGING_FILES:
        if (Path(task.repo_dir) / packaging).is_file() and not _glob_hits(packaging, protected):
            problems.append(f"packaging file {packaging} exists and must be protected")
    if task.test_timeout > LIMITS["max_test_timeout_s"]:
        problems.append(f"test_timeout {task.test_timeout} s exceeds the limit of {LIMITS['max_test_timeout_s']} s")
    if task.checkpoint_timeout > LIMITS["max_checkpoint_timeout_s"]:
        problems.append(f"checkpoint_timeout {task.checkpoint_timeout} s exceeds the limit of {LIMITS['max_checkpoint_timeout_s']} s")
    if task.install_command:
        unpinned = [part for part in task.install_command[1:] if re.match(r"^[A-Za-z0-9_.\-\[\]]+$", part) and "==" not in part
                    and not part.startswith("-") and part not in ("pip", "install", "/tmp/deps") and not part.endswith(".txt")
                    and part not in ("python", "-m")]
        # tolerate `python -m pip install ... --target /tmp/deps name==ver`; anything that looks like a requirement without == is unpinned
        unpinned = [p for p in unpinned if not p.startswith("/") and p not in ("pip",)]
        if unpinned:
            problems.append(f"install_command must pin every requirement with ==; unpinned: {', '.join(unpinned[:5])}")
        if not task.requirements_lock:
            problems.append("external tasks with an install step must record requirements_lock (the exact pinned requirement set)")
    return problems


def repository_problems(snapshot: dict[str, bytes], max_file_bytes: int = LIMITS["max_file_bytes"]) -> list[str]:
    return _check_tree({rel: len(data) for rel, data in snapshot.items()}, max_file_bytes)


def task_skeleton(task_id: str, title: str, source: dict, runner: str, write_globs: list[str], protected: list[str] | None,
                  heldout: dict[str, str] | None, statement: str, criteria: list[str], python_paths: list[str],
                  install: list[str] | None, requirements_lock: str | None, test_command: list[str] | None,
                  test_timeout: int, reference: str | None, max_file_bytes: int = LIMITS["max_file_bytes"]) -> dict:
    body = {"id": task_id, "title": title, "repo_dir": "repo", "language": "python", "base_image": "python:3.12-slim",
            "test_runner": runner, "import_hint": "", "python_paths": python_paths,
            "test_command": test_command or (["/usr/local/bin/python", "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", "-o", "addopts=", "tests"]
                                             if runner == "pytest" else ["/usr/local/bin/python", "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]),
            "checkpoint_timeout": min(LIMITS["max_checkpoint_timeout_s"], 300), "test_timeout": min(test_timeout, LIMITS["max_test_timeout_s"]),
            "allowed_write_globs": write_globs, "protected_globs": protected or list(PROTECTED_DEFAULT),
            "max_file_bytes": min(max_file_bytes, LIMITS["hard_max_file_bytes"]),
            "heldout_tests": heldout or {}, "statement": statement, "acceptance_criteria": criteria,
            "external": {"imported_at_utc": source.get("fetched_at_utc"), "files": source.get("files"), "total_bytes": source.get("total_bytes"),
                         "tree_sha256": source.get("tree_sha256"), "limits": source.get("limits"), "max_turns": LIMITS["max_turns"]}}
    if install:
        body["install_command"] = install
        body["requirements_lock"] = requirements_lock
    if source.get("url"):
        body["upstream"] = {"url": source["url"], "commit": source["commit"], "reference": reference or f"imported from {source['url']} at {source['commit']}"}
    return body
