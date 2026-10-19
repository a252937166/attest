"""Implementer workspace: an in-memory copy of the repository with a write policy and diff."""

from __future__ import annotations

import difflib
import errno
import fnmatch
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv"}
MAX_FILE_BYTES = 200_000

# `search` is a literal substring search unless the pattern starts with this prefix; the rest is then a regular expression
# that runs in a separate interpreter under the deadline below (BOUND-01, audit of 19 Oct 2026: a model-controlled regex
# must never occupy the orchestrator's worker thread).
REGEX_PREFIX = "re:"
SEARCH_TIMEOUT_S = 2.0
SEARCH_INPUT_BYTES = 25_000_000   # text handed to the regex child at most (the import limit for a whole repository)
SEARCH_LINE_CHARS = 200

# Runs with `python -I -c` (isolated mode: no site, no cwd import) in a child process that receives the files on stdin
# and prints a bounded JSON result; the host kills it at the deadline. It is the only place a regular expression from the
# model is compiled or executed.
REGEX_WORKER = r'''
import json, re, sys
job = json.loads(sys.stdin.buffer.read().decode("utf-8"))
try:
    regex = re.compile(job["pattern"])
except re.error as error:
    sys.stdout.write(json.dumps({"error": "invalid regular expression: " + str(error)}))
    sys.exit(0)
hits, total, limit, width = [], 0, int(job["limit"]), int(job["width"])
for path, text in job["files"]:
    for number, line in enumerate(text.splitlines(), 1):
        if regex.search(line):
            total += 1
            if len(hits) < limit:
                hits.append([path, number, line.rstrip()[:width]])
sys.stdout.write(json.dumps({"total": total, "hits": hits}))
'''

_O_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
_O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_OPEN_DIR = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _O_NOFOLLOW | _O_CLOEXEC
_OPEN_FILE = os.O_RDONLY | _O_NOFOLLOW | _O_CLOEXEC | getattr(os, "O_NONBLOCK", 0)   # O_NONBLOCK: a FIFO swapped in never blocks
_FD_RELATIVE = os.open in os.supports_dir_fd and os.scandir in os.supports_fd


class PolicyViolation(ValueError):
    pass


def snapshot_repo(repo_dir: Path, max_file_bytes: int = MAX_FILE_BYTES, skipped: list[dict] | None = None,
                  max_files: int | None = None, max_total_bytes: int | None = None) -> dict[str, bytes]:
    """The regular files of `repo_dir` as {posix relative path: bytes}.

    Symbolic links, sockets, devices and FIFOs are never followed or read: every entry is identified with lstat semantics
    before it is opened, directories and files are opened relative to their parent directory descriptor with O_NOFOLLOW (so a
    link swapped in after the listing is refused by the kernel as well), and the open descriptor is checked to be a regular
    file before anything is read. Nothing outside the chosen repository is opened. Skipped entries are appended to `skipped`
    (path and reason) when a list is given; SKIP_DIRS entries are left out silently, as before. A file above `max_file_bytes`
    raises ValueError naming the limit, as do `max_files` and `max_total_bytes` when given (the import uses them so that the
    direct run and the import see exactly the same files). A missing directory yields an empty snapshot, as before."""
    root = Path(repo_dir)
    records = skipped if skipped is not None else []
    files: dict[str, bytes] = {}
    if not root.is_dir():
        return files
    total = 0

    def read_regular(dir_fd: int | None, name: str, rel: str) -> bytes | None:
        try:
            fd = os.open(name, _OPEN_FILE, dir_fd=dir_fd) if dir_fd is not None else os.open(name, _OPEN_FILE)
        except OSError as error:
            reason = "symbolic link" if error.errno == errno.ELOOP else f"not readable without following links ({error.strerror})"
            records.append({"path": rel, "reason": reason})
            return None
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                records.append({"path": rel, "reason": "not a regular file"})
                return None
            if info.st_size > max_file_bytes:
                raise ValueError(f"{rel} exceeds the per-file limit of {max_file_bytes} bytes")
            chunks: list[bytes] = []
            remaining = max_file_bytes + 1          # read with a cap: a file that grows under us cannot exceed the limit unnoticed
            while remaining > 0:
                chunk = os.read(fd, min(remaining, 1 << 20))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
        finally:
            os.close(fd)
        if len(data) > max_file_bytes:
            raise ValueError(f"{rel} exceeds the per-file limit of {max_file_bytes} bytes")
        return data

    def walk(dir_fd: int | None, dir_path: Path, parts: tuple[str, ...]) -> None:
        nonlocal total
        with os.scandir(dir_fd if dir_fd is not None else str(dir_path)) as it:
            entries = sorted(it, key=lambda entry: entry.name)
        for entry in entries:
            if entry.name in SKIP_DIRS:
                continue
            rel = "/".join(parts + (entry.name,))
            if entry.is_symlink():
                records.append({"path": rel, "reason": "symbolic link"})
                continue
            if entry.is_dir(follow_symlinks=False):
                child_path = dir_path / entry.name
                if dir_fd is None:
                    child_fd = None
                    if os.path.realpath(child_path) != os.path.join(os.path.realpath(dir_path), entry.name):
                        records.append({"path": rel, "reason": "resolves outside its directory"})
                        continue
                else:
                    try:
                        child_fd = os.open(entry.name, _OPEN_DIR, dir_fd=dir_fd)
                    except OSError as error:
                        reason = "symbolic link" if error.errno == errno.ELOOP else f"directory not readable without following links ({error.strerror})"
                        records.append({"path": rel, "reason": reason})
                        continue
                try:
                    walk(child_fd, child_path, parts + (entry.name,))
                finally:
                    if child_fd is not None:
                        os.close(child_fd)
                continue
            if not entry.is_file(follow_symlinks=False):
                records.append({"path": rel, "reason": "not a regular file"})
                continue
            if max_files is not None and len(files) >= max_files:
                raise ValueError(f"more than {max_files} files in the repository; the limit is {max_files} files")
            data = read_regular(dir_fd, entry.name if dir_fd is not None else str(dir_path / entry.name), rel)
            if data is None:
                continue
            total += len(data)
            if max_total_bytes is not None and total > max_total_bytes:
                raise ValueError(f"the repository exceeds the total limit of {max_total_bytes} bytes")
            files[rel] = data

    if _FD_RELATIVE:
        root_fd = os.open(str(root), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | _O_CLOEXEC)   # the root the caller chose may itself be a link
        try:
            walk(root_fd, root, ())
        finally:
            os.close(root_fd)
    else:  # platforms without descriptor-relative opens: path-based with O_NOFOLLOW where it exists and a containment check
        walk(None, root, ())
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
        if len(text) <= limit:
            return text
        outline = self.outline(rel)
        where = ("\nOUTLINE (line: definition), so the next read can target a range:\n" + "\n".join(outline[:80])) if outline else ""
        return text[:limit] + f"\n...[truncated at {limit} chars; use start_line/end_line to read the rest]...{where}"

    def search(self, pattern: str, path: str | None = None, limit: int = 60) -> str:
        """Lines containing `pattern` in one file or in every text file of the workspace, as `path:line: text`.

        The pattern is a literal, case-sensitive substring (linear time, on the calling thread). A pattern that starts with
        `re:` is a regular expression instead: it runs in a separate interpreter with a 2 s deadline, a bounded input and a
        bounded output; past the deadline the action returns an error text and the worker thread is released, and an invalid
        expression is reported rather than searched literally. Output is bounded either way, so a broad pattern cannot
        flood the transcript."""
        if not pattern:
            return "INVALID ACTION: search needs a non-empty find pattern"
        targets = [self.normalize(path)] if path else sorted(self.files)
        if path and targets[0] not in self.files:
            raise FileNotFoundError(targets[0])
        limit = max(1, int(limit))
        if pattern.startswith(REGEX_PREFIX):
            return self._regex_search(pattern[len(REGEX_PREFIX):], targets, limit, bool(path))
        hits: list[str] = []
        total = 0
        for rel in targets:
            text = self._searchable_text(rel)
            if text is None or pattern not in text:
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if pattern in line:
                    total += 1
                    if len(hits) < limit:
                        hits.append(f"{rel}:{number}: {line.rstrip()[:SEARCH_LINE_CHARS]}")
        return self._format_hits(hits, total, limit, repr(pattern), targets[0] if path else None)

    def _searchable_text(self, rel: str) -> str | None:
        data = self.files[rel]
        if b"\0" in data[:4096]:
            return None  # binary
        return data.decode("utf-8", "replace")

    def _regex_search(self, expression: str, targets: list[str], limit: int, single: bool) -> str:
        if not expression:
            return f"INVALID ACTION: search needs a regular expression after the {REGEX_PREFIX} prefix"
        if not sys.executable:
            return "search failed: no interpreter is available for the regular expression worker; use a literal search"
        payload: list[list[str]] = []
        budget = SEARCH_INPUT_BYTES
        unsearched = 0
        for rel in targets:
            text = self._searchable_text(rel)
            if text is None:
                continue
            size = len(self.files[rel])
            if size > budget:
                unsearched += 1
                continue
            budget -= size
            payload.append([rel, text])
        job = json.dumps({"pattern": expression, "files": payload, "limit": limit, "width": SEARCH_LINE_CHARS}).encode("utf-8")
        try:
            proc = subprocess.run([sys.executable, "-I", "-c", REGEX_WORKER], input=job, capture_output=True,
                                  timeout=SEARCH_TIMEOUT_S)
        except subprocess.TimeoutExpired:   # the child was killed by run(); the worker thread continues immediately
            return f"search aborted: the regular expression exceeded {SEARCH_TIMEOUT_S:g} s; use a literal search"
        except OSError as error:
            return f"search failed: the regular expression worker could not start ({error}); use a literal search"
        if proc.returncode != 0:
            detail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
            return f"search failed: the regular expression worker exited with code {proc.returncode} ({detail[0][:200]}); use a literal search"
        try:
            result = json.loads(proc.stdout.decode("utf-8"))
        except ValueError:
            return "search failed: the regular expression worker returned no result; use a literal search"
        if result.get("error"):
            return f"INVALID ACTION: {result['error']} (without the {REGEX_PREFIX} prefix the text is searched literally)"
        hits = [f"{rel}:{number}: {line}" for rel, number, line in result.get("hits", [])[:limit]]
        text = self._format_hits(hits, int(result.get("total", 0)), limit, f"regular expression {expression!r}", targets[0] if single else None)
        if unsearched:
            text += f"\n({unsearched} file(s) were not searched: the input bound of {SEARCH_INPUT_BYTES} bytes was reached; give a path)"
        return text

    @staticmethod
    def _format_hits(hits: list[str], total: int, limit: int, what: str, only: str | None) -> str:
        if not hits:
            return f"no match for {what}" + (f" in {only}" if only else " in the workspace")
        head = f"{total} matching line(s)" + (f" (showing the first {limit})" if total > limit else "") + ":\n"
        return head + "\n".join(hits)

    def outline(self, path: str) -> list[str]:
        """`def`/`class` lines with line numbers of a Python file (empty for other files)."""
        rel = self.normalize(path)
        if rel not in self.files or not rel.endswith(".py"):
            return []
        out = []
        for number, raw in enumerate(self.files[rel].decode("utf-8", "replace").splitlines(), 1):
            if raw.lstrip().startswith(("def ", "class ", "async def ")):
                out.append(f"{number}: {raw.rstrip()[:110]}")
        return out

    def replace(self, path: str, find: str, replacement: str) -> str:
        """Replace exactly one occurrence of `find`; refuse when the snippet is absent or ambiguous. When it is absent the
        refusal names the closest lines of the file, so the next attempt can copy the real text."""
        rel = self.check_writable(path)
        if rel not in self.files:
            raise FileNotFoundError(rel)
        if not find:
            raise PolicyViolation("replace_in_file needs a non-empty find snippet")
        text = self.files[rel].decode("utf-8", "replace")
        count = text.count(find)
        if count == 0:
            first = next((line for line in find.splitlines() if line.strip()), find).strip()
            candidates = [line for line in text.splitlines() if line.strip()]
            close = difflib.get_close_matches(first, [c.strip() for c in candidates], n=3, cutoff=0.6)
            hint = ""
            if close:
                numbered = []
                for match in close:
                    for number, line in enumerate(text.splitlines(), 1):
                        if line.strip() == match:
                            numbered.append(f"line {number}: {line.rstrip()[:160]}")
                            break
                hint = "; closest lines in the file: " + " | ".join(numbered)
            raise PolicyViolation(f"find snippet occurs 0 times in {rel}; it must occur exactly once (copy the current text verbatim, including indentation{hint})")
        if count != 1:
            raise PolicyViolation(f"find snippet occurs {count} times in {rel}; it must occur exactly once (include more surrounding lines)")
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
