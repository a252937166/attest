"""Implementer workspace: an in-memory copy of the repository with a write policy and diff."""

from __future__ import annotations

import difflib
import fnmatch
import hashlib
from pathlib import Path, PurePosixPath

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv"}
MAX_FILE_BYTES = 200_000


class PolicyViolation(ValueError):
    pass


def snapshot_repo(repo_dir: Path, max_file_bytes: int = MAX_FILE_BYTES) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(repo_dir.rglob("*")):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(repo_dir).parts):
            continue
        rel = path.relative_to(repo_dir).as_posix()
        data = path.read_bytes()
        if len(data) > max_file_bytes:
            raise ValueError(f"{rel} exceeds the per-file limit of {max_file_bytes} bytes")
        files[rel] = data
    return files


def _glob_match(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        if pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(pattern[:-3] + "/")):
            return True
    return False


class Workspace:
    def __init__(self, base: dict[str, bytes], allowed: list[str], protected: list[str]):
        self.base = dict(base)
        self.files = dict(base)
        self.allowed = allowed
        self.protected = protected
        self.writes: list[str] = []
        self.history: list[tuple[str, bytes | None]] = []  # (path, previous content) for undo of the last edit

    @staticmethod
    def normalize(path: str) -> str:
        pure = PurePosixPath(path.strip())
        if pure.is_absolute() or any(part in ("..", "") for part in pure.parts) or not pure.parts:
            raise PolicyViolation(f"path must be relative and inside the repository: {path!r}")
        return pure.as_posix()

    def check_writable(self, path: str) -> str:
        rel = self.normalize(path)
        if _glob_match(rel, self.protected):
            raise PolicyViolation(f"{rel} is protected (tests and infrastructure are off limits)")
        if not _glob_match(rel, self.allowed):
            raise PolicyViolation(f"{rel} is outside the allowed write scope {self.allowed}")
        return rel

    def list_files(self) -> list[str]:
        return sorted(self.files)

    def read(self, path: str, limit: int = 60_000, start_line: int | None = None, end_line: int | None = None) -> str:
        rel = self.normalize(path)
        if rel not in self.files:
            raise FileNotFoundError(rel)
        text = self.files[rel].decode("utf-8", "replace")
        lines = text.splitlines(keepends=True)
        if start_line or end_line:
            first = max(1, int(start_line or 1))
            last = min(len(lines), int(end_line or len(lines)))
            text = f"[lines {first}-{last} of {len(lines)}]\n" + "".join(lines[first - 1:last])
        else:
            text = f"[{len(lines)} lines]\n" + text
        return text if len(text) <= limit else text[:limit] + f"\n...[truncated at {limit} chars; use start_line/end_line to read the rest]..."

    def replace(self, path: str, find: str, replacement: str) -> str:
        """Replace exactly one occurrence of `find`; refuse when the snippet is absent or ambiguous."""
        rel = self.check_writable(path)
        if rel not in self.files:
            raise FileNotFoundError(rel)
        if not find:
            raise PolicyViolation("replace_in_file needs a non-empty find snippet")
        text = self.files[rel].decode("utf-8", "replace")
        count = text.count(find)
        if count != 1:
            raise PolicyViolation(f"find snippet occurs {count} times in {rel}; it must occur exactly once")
        new_text = text.replace(find, replacement, 1)
        data = new_text.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise PolicyViolation(f"{rel}: file exceeds {MAX_FILE_BYTES} bytes")
        self.history.append((rel, self.files.get(rel)))
        self.files[rel] = data
        self.writes.append(rel)
        return rel

    def write(self, path: str, content: str) -> str:
        rel = self.check_writable(path)
        data = content.encode("utf-8")
        if len(data) > MAX_FILE_BYTES:
            raise PolicyViolation(f"{rel}: file exceeds {MAX_FILE_BYTES} bytes")
        self.history.append((rel, self.files.get(rel)))
        self.files[rel] = data
        self.writes.append(rel)
        return rel

    def undo(self) -> str | None:
        """Revert the most recent write or replace. Returns the path reverted, or None when there is nothing to undo."""
        if not self.history:
            return None
        rel, previous = self.history.pop()
        if previous is None:
            self.files.pop(rel, None)
        else:
            self.files[rel] = previous
        return rel

    def changed(self) -> dict[str, bytes]:
        return {p: d for p, d in self.files.items() if self.base.get(p) != d}

    def deleted(self) -> list[str]:
        return sorted(p for p in self.base if p not in self.files)

    def unified_diff(self) -> str:
        chunks = []
        for path in sorted(set(self.base) | set(self.files)):
            before, after = self.base.get(path), self.files.get(path)
            if before == after:
                continue
            a = before.decode("utf-8", "replace").splitlines(keepends=True) if before is not None else []
            b = after.decode("utf-8", "replace").splitlines(keepends=True) if after is not None else []
            chunks.append("".join(difflib.unified_diff(
                a, b, fromfile=f"a/{path}" if before is not None else "/dev/null",
                tofile=f"b/{path}" if after is not None else "/dev/null")))
        return "".join(chunks)

    def scope_report(self) -> dict:
        changed = sorted(set(self.changed()) | set(self.deleted()))
        violations = []
        for path in changed:
            try:
                self.check_writable(path)
            except PolicyViolation as error:
                violations.append(str(error))
        return {"changed_paths": changed, "violations": violations, "ok": not violations,
                "sha256": {p: hashlib.sha256(d).hexdigest() for p, d in self.changed().items()}}
