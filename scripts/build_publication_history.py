#!/usr/bin/env python3
"""Build a publishable copy of the review repository's history, with every private string removed (revision 9, 20 Oct 2026).

The review repository (dist/public) is the private record: its commits from before revision 8 carry the development gateway's host in
historical files (the export script's own redaction rule and the REDACTION.json of every redacted run copy) and two early EXPORT.json
files carry a local home directory. Rewriting that repository would destroy the record, so this tool leaves it untouched and replays
its history, commit by commit, into a separate repository:

- every commit keeps its author, committer, dates and message, so the replay is deterministic: the same review history always yields
  the same publication commits, and `publication-map.json` maps each review commit to its publication commit;
- a blob is changed only when the history scanner (scripts/scan_publication_history.py) finds a private string in it; it is then
  passed through the export's own redaction (scripts/export_public.py: the private hosts in every spelling become
  development-gateway.invalid, home directories /home/author/, key shapes [REDACTED-KEY]), so a historical file reads as an export
  made today would have written it;
- a run directory's manifest.json that lists a rewritten file gets that entry's digest and size, and its total, recomputed (the
  manifest of a redacted run copy is the export's own derived manifest, and REDACTION.json is listed in it); nothing else in it changes,
  and a manifest whose JSON would not round-trip byte for byte is refused rather than rewritten;
- everything else (the package, the harness, the examples, the bundles' evidence) is byte-identical, so every digest a pin or a report
  records stays valid in the publication history, and `--verify` proves it.

Nothing is pushed; the result is a local repository whose only branch is `main`.

Usage: build_publication_history.py --review dist/public --out dist/publication [--rev main] [--map OUT.json] [--verify REPORT.json]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_HOST = "development-gateway.invalid"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPORT = load("attest_export_rules_pub", ROOT / "scripts" / "export_public.py")
SCAN = load("attest_scan_pub", ROOT / "scripts" / "scan_publication_history.py")


def git(repo: Path, *args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], input=data, capture_output=True, check=True).stdout


class Objects:
    """Batch reader of one repository's objects."""

    def __init__(self, repo: Path):
        self.proc = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.cache: dict[str, bytes] = {}

    def read(self, sha: str) -> bytes:
        if sha in self.cache:
            return self.cache[sha]
        self.proc.stdin.write(sha.encode() + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) < 3:
            raise RuntimeError(f"object {sha} missing")
        size = int(header[2])
        data = self.proc.stdout.read(size)
        self.proc.stdout.read(1)
        if size < 4_000_000:
            self.cache[sha] = data
        return data

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def sanitize_text(data: bytes, hosts: list[str]) -> bytes:
    """The export's redaction, applied to one historical blob: the private hosts in every spelling the scanner knows (the separator
    style of a regex- or JSON-escaped spelling is kept), then the export's own rules (URL and host, home directory, key shapes)."""
    text = data.decode("utf-8")
    for host in hosts:
        labels = [re.escape(label) for label in host.split(".")]
        dot = "(?:" + "|".join(SCAN.DOT_SPELLINGS) + ")"
        pattern = re.compile("(" + labels[0] + ")" + "".join(f"({dot}){label}" for label in labels[1:]), re.I)

        def replace(match: re.Match) -> str:
            separator = match.group(2)  # the spelling of the first dot, reused for every dot of the placeholder
            return PLACEHOLDER_HOST.replace(".", separator if separator.endswith(".") or "\\" in separator else ".")
        text = pattern.sub(replace, text)
    text, _ = EXPORT.redact_text(text)
    return text.encode("utf-8")


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def quote_path(path: bytes) -> bytes:
    if re.fullmatch(rb"[A-Za-z0-9._/@+=,:~\-]+", path):
        return path
    out = b'"'
    for byte in path:
        char = bytes([byte])
        if char in (b'"', b"\\"):
            out += b"\\" + char
        elif byte < 0x20 or byte >= 0x7f:
            out += b"\\%03o" % byte
        else:
            out += char
    return out + b'"'


def commits(repo: Path, rev: str) -> list[str]:
    listing = git(repo, "rev-list", "--reverse", "--topo-order", "--parents", rev).decode().split("\n")
    out = []
    for line in listing:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) > 2:
            raise SystemExit(f"refusing: {parts[0]} is a merge; the replay handles linear history only")
        out.append(parts[0])
    return out


def tree_entries(repo: Path, commit: str) -> dict[bytes, tuple[str, str]]:
    """path -> (mode, blob sha) of every file in a commit."""
    raw = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    entries = {}
    for item in raw.split(b"\0"):
        if not item:
            continue
        meta, _, path = item.partition(b"\t")
        mode, kind, sha = meta.decode().split()
        if kind != "blob":
            raise SystemExit(f"refusing: {path!r} in {commit} is a {kind} (submodules are not replayed)")
        entries[path] = (mode, sha)
    return entries


def parse_commit(raw: bytes) -> dict:
    head, _, message = raw.partition(b"\n\n")
    fields = {}
    for line in head.split(b"\n"):
        key, _, value = line.partition(b" ")
        if key in (b"author", b"committer"):
            fields[key.decode()] = value
        elif key in (b"encoding", b"gpgsig", b"mergetag"):
            raise SystemExit(f"refusing: commit header {key!r} is not replayed")
    return {"author": fields["author"], "committer": fields["committer"], "message": message}


def manifest_rewrite(data: bytes, rewritten: dict[str, tuple[str, int]]) -> bytes | None:
    """The manifest with the digest and size of every listed file that was rewritten replaced, and its total recomputed; None when it
    lists none. Refuses (raises) a manifest whose JSON does not round-trip byte for byte."""
    try:
        manifest = json.loads(data)
    except json.JSONDecodeError:
        return None
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        return None
    if json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8") + b"\n" != data:
        if any(isinstance(f, dict) and f.get("sha256") in rewritten for f in manifest["files"]):
            raise SystemExit("refusing: a manifest that lists a rewritten file does not round-trip byte for byte")
        return None
    changed = False
    for entry in manifest["files"]:
        if isinstance(entry, dict) and entry.get("sha256") in rewritten:
            entry["sha256"], entry["bytes"] = rewritten[entry["sha256"]]
            changed = True
    if not changed:
        return None
    manifest["total_bytes"] = sum(int(f.get("bytes") or 0) for f in manifest["files"] if isinstance(f, dict))
    return json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"


def build(review: Path, out: Path, rev: str) -> dict:
    hosts = list(EXPORT.PRIVATE_HOSTS)
    if not hosts:
        raise SystemExit("refusing: no private host is configured, so nothing would be known to remove (see scan_publication_history.py)")
    scanner = SCAN.Scanner(hosts, EXPORT.SCAN_PATTERNS, EXPORT.SCAN_SENTINELS)
    order = commits(review, rev)
    objects = Objects(review)
    # pass 1: every blob of the replayed history that holds a private string, rewritten once
    blob_paths: dict[str, set[bytes]] = {}
    trees = {}
    for commit in order:
        trees[commit] = tree_entries(review, commit)
        for path, (_, sha) in trees[commit].items():
            blob_paths.setdefault(sha, set()).add(path)
    sanitized: dict[str, bytes] = {}
    for sha in blob_paths:
        data = objects.read(sha)
        if scanner.hits(data):
            clean = sanitize_text(data, hosts)
            if scanner.hits(clean):
                raise SystemExit(f"refusing: blob {sha[:12]} ({sorted(blob_paths[sha])[0]!r}) still holds a private string after the export's redaction")
            sanitized[sha] = clean
    by_sha256 = {hashlib.sha256(objects.read(sha)).hexdigest(): (hashlib.sha256(clean).hexdigest(), len(clean)) for sha, clean in sanitized.items()}
    # pass 2: manifests that list a rewritten file
    manifests: dict[str, bytes] = {}
    for sha, paths in blob_paths.items():
        if sha in sanitized or not any(p.endswith(b"manifest.json") for p in paths):
            continue
        rewritten = manifest_rewrite(objects.read(sha), by_sha256)
        if rewritten is not None:
            manifests[sha] = rewritten
    replaced = {**sanitized, **manifests}
    old_digests = {hashlib.sha256(objects.read(sha)).hexdigest(): sha for sha in replaced}
    # nothing else in the history may refer to a rewritten file by its digest (it would now point at nothing)
    references = []
    for sha in blob_paths:
        if sha in replaced:
            continue
        data = objects.read(sha)
        for digest, source in old_digests.items():
            if digest.encode() in data and source in manifests:
                references.append({"blob": sha, "paths": sorted(p.decode("utf-8", "replace") for p in blob_paths[sha])[:3], "refers_to": source})
    # the replay
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    git(out, "init", "-q", "-b", "main")
    stream = bytearray()
    marks: dict[str, int] = {}
    next_mark = 1
    emitted: dict[str, int] = {}
    previous = None
    commit_marks = []
    for commit in order:
        meta = parse_commit(objects.read(commit))
        entries = trees[commit]
        before = trees[previous] if previous else {}
        lines = bytearray()
        for path, (mode, sha) in sorted(entries.items()):
            if before.get(path) == (mode, sha):
                continue
            if sha not in emitted:
                data = replaced.get(sha, objects.read(sha))
                stream += b"blob\nmark :%d\ndata %d\n" % (next_mark, len(data)) + data + b"\n"
                emitted[sha] = next_mark
                next_mark += 1
            lines += b"M %s :%d %s\n" % (mode.encode(), emitted[sha], quote_path(path))
        for path in sorted(set(before) - set(entries)):
            lines += b"D %s\n" % quote_path(path)
        mark = next_mark
        next_mark += 1
        stream += b"commit refs/heads/main\nmark :%d\nauthor %s\ncommitter %s\ndata %d\n" % (mark, meta["author"], meta["committer"], len(meta["message"]))
        stream += meta["message"] + b"\n"
        if previous:
            stream += b"from :%d\n" % marks[previous]
        stream += bytes(lines) + b"\n"
        marks[commit] = mark
        commit_marks.append((commit, mark))
        previous = commit
    objects.close()
    marks_file = out / ".git" / "attest-publication-marks"
    subprocess.run(["git", "-C", str(out), "fast-import", "--quiet", "--done", f"--export-marks={marks_file}"], input=bytes(stream) + b"done\n",
                   check=True, capture_output=True)
    by_mark = dict(line.split() for line in marks_file.read_text().splitlines())
    marks_file.unlink()
    git(out, "reset", "-q", "--hard", "main")
    mapping = [{"review": commit, "publication": by_mark[f":{mark}"]} for commit, mark in commit_marks]
    rewrites = [{"review_blob": sha, "publication_blob": git_blob_sha(replaced[sha]), "paths": sorted(p.decode("utf-8", "replace") for p in blob_paths[sha]),
                 "kind": "derived manifest (rewritten entries)" if sha in manifests else "private string removed (the export's redaction)"}
                for sha in sorted(replaced)]
    return {"review": str(review), "publication": str(out), "rev": rev, "commits": len(order), "map": mapping, "rewritten_blobs": rewrites,
            "rewritten_counts": {"sanitized": len(sanitized), "manifests": len(manifests)}, "dangling_digest_references": references,
            "placeholder_host": PLACEHOLDER_HOST}


def package_digest(repo: Path, commit: str) -> dict:
    """attest/ package digest of a commit, as attest.core.provenance computes it for a tree (sha256 over path and content of every
    .py source), plus the harness and METHOD digests."""
    raw = git(repo, "ls-tree", "-r", "-z", "--full-tree", commit)
    sources = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        meta, _, path = item.partition(b"\t")
        sources.append((path.decode(), meta.decode().split()[2]))
    objects = Objects(repo)
    try:
        digest = hashlib.sha256()
        count = 0
        # the order attest_revision uses: Path objects compare by their parts, not by the joined string
        package = sorted(((path[len("attest/"):], sha) for path, sha in sources if path.startswith("attest/") and path.endswith(".py")
                          and "__pycache__" not in path.split("/")), key=lambda item: tuple(item[0].split("/")))
        for rel, sha in package:
            digest.update(rel.encode() + b"\0" + objects.read(sha) + b"\0")
            count += 1
        files = dict(sources)
        harness = hashlib.sha256(objects.read(files["scripts/run_evaluation.py"])).hexdigest() if "scripts/run_evaluation.py" in files else None
        method = hashlib.sha256(objects.read(files["METHOD.md"])).hexdigest() if "METHOD.md" in files else None
    finally:
        objects.close()
    return {"attest_package": digest.hexdigest(), "files": count, "harness": harness, "method": method}


def verify(review: Path, out: Path, result: dict, pinned: list[str]) -> dict:
    """The publication history is clean, differs from the review history exactly by the listed rewrites, keeps every pinned digest,
    and every bundle whose derived manifest changed still passes `attest check` at every commit where it changed."""
    report = {"scan": None, "commits_checked": 0, "unexpected_differences": [], "pins": [], "bundles_rechecked": [], "ok": False}
    hosts = list(EXPORT.PRIVATE_HOSTS)
    scan = SCAN.scan(out, SCAN.Scanner(hosts, EXPORT.SCAN_PATTERNS, EXPORT.SCAN_SENTINELS))
    report["scan"] = {"objects": scan["objects"], "by_type": scan["by_type"], "hits": len(scan["hits"]), "ref_hits": len(scan["refs"]), "clean": scan["ok"]}
    allowed = {(r["review_blob"], r["publication_blob"]) for r in result["rewritten_blobs"]}
    changed_dirs: dict[str, set[str]] = {}
    for pair in result["map"]:
        left = tree_entries(review, pair["review"])
        right = tree_entries(out, pair["publication"])
        report["commits_checked"] += 1
        if set(left) != set(right):
            report["unexpected_differences"].append({"commit": pair["review"], "paths": "the path sets differ"})
            continue
        for path, (mode, sha) in left.items():
            other_mode, other_sha = right[path]
            if mode != other_mode or (sha != other_sha and (sha, other_sha) not in allowed):
                report["unexpected_differences"].append({"commit": pair["review"], "path": path.decode("utf-8", "replace")})
            elif sha != other_sha and path.endswith(b"manifest.json"):
                changed_dirs.setdefault(pair["publication"], set()).add(str(Path(path.decode()).parent))
    by_review = {p["review"]: p["publication"] for p in result["map"]}
    for commit in pinned:
        full = git(review, "rev-parse", commit).decode().strip()
        if full not in by_review:
            report["pins"].append({"review": commit, "error": "not in the replayed history"})
            continue
        left, right = package_digest(review, full), package_digest(out, by_review[full])
        report["pins"].append({"review": full, "publication": by_review[full], "review_digests": left, "publication_digests": right, "equal": left == right})
    # attest check, with today's checker, on every run copy whose derived manifest changed, at the publication commit where it changed
    sys.path.insert(0, str(ROOT))
    from attest.core.check import check_bundle
    seen = set()
    for publication_commit, dirs in changed_dirs.items():
        pending = sorted(d for d in dirs if (d, publication_commit) not in seen)
        if not pending:
            continue
        with tempfile.TemporaryDirectory(prefix="attest-publication-check-") as tmpname:
            worktree = Path(tmpname) / "tree"
            git(out, "worktree", "add", "-q", "--detach", str(worktree), publication_commit)
            try:
                for rel in pending:
                    seen.add((rel, publication_commit))
                    run_dir = worktree / rel
                    if not (run_dir / "proof_bundle.json").is_file():
                        continue
                    outcome = check_bundle(run_dir)
                    report["bundles_rechecked"].append({"commit": publication_commit, "run": rel, "ok": outcome["ok"], "errors": outcome["errors"],
                                                        "warnings": outcome["warnings"]})
            finally:
                git(out, "worktree", "remove", "--force", str(worktree))
    report["ok"] = (report["scan"]["clean"] and not report["unexpected_differences"] and all(p.get("equal") for p in report["pins"])
                    and all(b["ok"] for b in report["bundles_rechecked"]) and not result["dangling_digest_references"])
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--review", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rev", default="main")
    parser.add_argument("--map", help="write the build record (commit map, rewritten blobs) here")
    parser.add_argument("--verify", help="verify the result and write the report here")
    parser.add_argument("--pin", action="append", default=[], help="a review commit whose package, harness and METHOD digests must survive (repeatable)")
    args = parser.parse_args(argv)
    review, out = Path(args.review).resolve(), Path(args.out).resolve()
    if out == review or review in out.parents:
        raise SystemExit("refusing: the publication repository must be a separate directory")
    result = build(review, out, args.rev)
    print(f"replayed {result['commits']} commits into {out}: {result['rewritten_counts']['sanitized']} blob(s) with a private string rewritten, "
          f"{result['rewritten_counts']['manifests']} derived manifest(s) recomputed; review {result['map'][-1]['review'][:12]} -> publication "
          f"{result['map'][-1]['publication'][:12]}")
    if args.map:
        Path(args.map).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.verify:
        report = verify(review, out, result, args.pin)
        Path(args.verify).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"verify: scan {'CLEAN' if report['scan']['clean'] else 'NOT CLEAN'} ({report['scan']['objects']} objects); {report['commits_checked']} commits compared, "
              f"{len(report['unexpected_differences'])} unexpected difference(s); pins {sum(1 for p in report['pins'] if p.get('equal'))}/{len(report['pins'])} "
              f"digests equal; {len(report['bundles_rechecked'])} rewritten bundle(s) re-checked, {sum(1 for b in report['bundles_rechecked'] if not b['ok'])} failed; "
              f"{'OK' if report['ok'] else 'NOT OK'}")
        return 0 if report["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
