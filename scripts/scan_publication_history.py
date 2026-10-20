#!/usr/bin/env python3
"""Scan every object of a Git repository for private strings before it may be published (revision 9, 20 Oct 2026).

The export (`scripts/export_public.py`) scans the tree it writes; a repository publishes its whole history, so this scan reads
every object in the object database, reachable or not: each blob's content, each tree's entry names, each commit's message,
author and committer, each tag's message, plus the names of all refs. A blob that is gzip data, a ZIP archive, or that contains
base64 text decoding to gzip data is decompressed (bounded) and scanned as well.

What counts as private is the export's definition, imported from `scripts/export_public.py`: the private host names from the
exporter's private configuration (ATTEST_CODEX_BASE_URL or ~/.config/attest/notes.json, plus ATTEST_EXPORT_PRIVATE_HOSTS) and
the secret-like patterns of its final scan. Every host is looked for in these spellings, case-insensitively: plain; any number of
backslashes before each dot (regex- and JSON-escaped); the dot written as %2e, \\u002e, \\x2e, \\056, &#46;, &#x2e; or &period;;
and its base64 encodings at all three alignments (standard and URL-safe alphabet). A hit is reported by rule label, object and
path only; the private value itself is never printed.

Exit code 0 when nothing is found, 1 when anything is, 2 when the scan could not run (no private host configured: a scan without
the hosts proves nothing, so it refuses unless --allow-no-hosts is given).

Usage: scan_publication_history.py --repo DIR [--json OUT] [--allow-no-hosts]
"""

from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import importlib.util
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_INFLATED = 50_000_000      # bytes a decompressed blob or archive member may expand to before it is reported as unreadable
MAX_MEMBERS = 5_000
DOT_SPELLINGS = (r"\\*\.", r"%2e", r"\\+u002e", r"\\+x2e", r"\\+056", r"&#0*46;", r"&#x0*2e;", r"&period;")
BASE64_TOKEN = re.compile(rb"[A-Za-z0-9+/_\-]{40,}={0,2}")


def load_export_rules():
    spec = importlib.util.spec_from_file_location("attest_export_rules", ROOT / "scripts" / "export_public.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def host_spellings(host: str) -> re.Pattern:
    labels = [re.escape(label) for label in host.split(".")]
    dot = "(?:" + "|".join(DOT_SPELLINGS) + ")"
    return re.compile(dot.join(labels).encode(), re.I)


def base64_cores(value: bytes) -> list[bytes]:
    """The base64 characters that depend only on `value`'s bytes, for each of the three alignments it can have inside longer data."""
    cores = []
    for offset in range(3):
        encoded = base64.b64encode(b"\0" * offset + value + b"\0\0\0")
        first = -(-8 * offset // 6)
        last = (8 * (offset + len(value))) // 6
        core = encoded[first:last]
        cores.append(core)
        cores.append(core.replace(b"+", b"-").replace(b"/", b"_"))
    return sorted(set(cores))


class Scanner:
    def __init__(self, hosts: list[str], scan_patterns: list[re.Pattern], sentinels: tuple[str, ...]):
        self.rules: list[tuple[str, re.Pattern]] = []
        for host in hosts:
            self.rules.append(("a private host name (any spelling) from the exporter's private configuration", host_spellings(host)))
            for case in {host, host.lower(), host.upper()}:
                for core in base64_cores(case.encode()):
                    self.rules.append(("a private host name, base64-encoded", re.compile(re.escape(core))))
        self.secret_patterns = [re.compile(p.pattern.encode(), p.flags & ~re.U) for p in scan_patterns]
        self.sentinels = tuple(s.encode() for s in sentinels)

    def hits(self, data: bytes, depth: int = 0) -> list[str]:
        found = []
        for label, pattern in self.rules:
            if pattern.search(data):
                found.append(label)
        for pattern in self.secret_patterns:
            for match in pattern.finditer(data):
                if any(s in match.group(0) for s in self.sentinels):
                    continue
                found.append("a secret-like token (" + pattern.pattern.decode()[:40] + ")")
                break
        if depth < 2:
            found += [f"inside compressed data: {h}" for h in self.nested(data, depth)]
        return sorted(set(found))

    def nested(self, data: bytes, depth: int) -> list[str]:
        found = []
        if data[:2] == b"\x1f\x8b":
            found += self.hits(self.inflate(data), depth + 1)
        if data[:4] == b"PK\x03\x04":
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    total = 0
                    for info in archive.infolist()[:MAX_MEMBERS]:
                        total += info.file_size
                        if total > MAX_INFLATED:
                            found.append("an archive too large to inspect")
                            break
                        found += self.hits(archive.read(info), depth + 1)
            except (zipfile.BadZipFile, OSError, RuntimeError):
                found.append("an archive that could not be read")
        for token in BASE64_TOKEN.findall(data):
            if not token.startswith((b"H4sI", b"H4s")):  # base64 of gzip data starts with H4sI
                continue
            try:
                raw = base64.b64decode(token + b"=" * (-len(token) % 4), altchars=b"-_" if (b"-" in token or b"_" in token) else None)
            except (binascii.Error, ValueError):
                continue
            if raw[:2] == b"\x1f\x8b":
                found += self.hits(self.inflate(raw), depth + 1)
        return found

    @staticmethod
    def inflate(data: bytes) -> bytes:
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as handle:
                return handle.read(MAX_INFLATED)
        except (OSError, EOFError):
            return b""


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], input=data, capture_output=True, check=True).stdout


def all_objects(repo: Path):
    """(sha, type, content) of every object in the object database, through one `cat-file --batch` process."""
    listing = git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)").decode().split("\n")
    entries = [line.split() for line in listing if line.strip()]
    proc = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for sha, kind in entries:
            proc.stdin.write(sha.encode() + b"\n")
            proc.stdin.flush()
            header = proc.stdout.readline().split()
            size = int(header[2])
            content = proc.stdout.read(size)
            proc.stdout.read(1)
            yield sha, kind, content
    finally:
        proc.stdin.close()
        proc.wait()


def paths_of_blobs(repo: Path) -> dict[str, set[str]]:
    """blob sha -> the paths it has in reachable history (for reporting)."""
    paths: dict[str, set[str]] = {}
    for line in git(repo, "rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines():
        sha, _, path = line.partition(" ")
        if path:
            paths.setdefault(sha, set()).add(path)
    return paths


def tree_names(content: bytes) -> bytes:
    names, i = [], 0
    while i < len(content):
        space = content.index(b" ", i)
        nul = content.index(b"\0", space)
        names.append(content[space + 1:nul])
        i = nul + 21
    return b"\n".join(names)


def scan(repo: Path, scanner: Scanner) -> dict:
    blob_paths = paths_of_blobs(repo)
    reachable = set(git(repo, "rev-list", "--all").decode().split())
    report = {"repo": str(repo), "objects": 0, "by_type": {}, "hits": [], "refs": []}
    for sha, kind, content in all_objects(repo):
        report["objects"] += 1
        report["by_type"][kind] = report["by_type"].get(kind, 0) + 1
        target = tree_names(content) if kind == "tree" else content
        labels = scanner.hits(target)
        if labels:
            entry = {"object": sha, "type": kind, "labels": labels}
            if kind == "blob":
                entry["paths"] = sorted(blob_paths.get(sha, {"(unreachable)"}))
            if kind == "commit":
                entry["reachable"] = sha in reachable
            report["hits"].append(entry)
    for line in git(repo, "for-each-ref", "--format=%(refname)").decode().splitlines():
        if scanner.hits(line.encode()):
            report["refs"].append({"labels": scanner.hits(line.encode())})
    report["ok"] = not report["hits"] and not report["refs"]
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--json", help="write the full report here (labels, object ids and paths only)")
    parser.add_argument("--allow-no-hosts", action="store_true", help="scan for secret-like patterns only when no private host is configured")
    args = parser.parse_args(argv)
    rules = load_export_rules()
    hosts = list(rules.PRIVATE_HOSTS)
    if not hosts and not args.allow_no_hosts:
        print("refusing: no private host is configured (ATTEST_CODEX_BASE_URL, ~/.config/attest/notes.json or ATTEST_EXPORT_PRIVATE_HOSTS); "
              "a scan without them proves nothing", file=sys.stderr)
        return 2
    scanner = Scanner(hosts, rules.SCAN_PATTERNS, rules.SCAN_SENTINELS)
    report = scan(Path(args.repo), scanner)
    report["private_hosts_configured"] = len(hosts)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{report['repo']}: {report['objects']} objects {report['by_type']}; {len(report['hits'])} object(s) with hits, "
          f"{len(report['refs'])} ref name(s) with hits; {'CLEAN' if report['ok'] else 'NOT CLEAN'}")
    for entry in report["hits"][:40]:
        where = ", ".join(entry.get("paths", []))[:200] if entry["type"] == "blob" else entry["type"]
        print(f"  {entry['object'][:12]} {entry['type']}: {'; '.join(entry['labels'])[:160]} [{where}]")
    if len(report["hits"]) > 40:
        print(f"  ... {len(report['hits']) - 40} more in the JSON report")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
