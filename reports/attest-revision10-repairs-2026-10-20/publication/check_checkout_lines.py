#!/usr/bin/env python3
"""Every published checkout instruction resolves (revision 10): for each `git checkout <commit>` line of FREEZE.md as the publication
repository's HEAD carries it, the commit must exist in the publication repository, be the publication commit the replay map assigns to the
review commit the following comment names ("# the same tree as review-repository commit <commit>"), carry the same `attest/` package digest
and harness digest as that review commit, and keep `scripts/run_evaluation.py` and `examples/eval/SUITE-M5.json` (the command's inputs).
Offline; reads git objects only.

    python check_checkout_lines.py --publication dist/publication --review dist/public --map publication-map.json --out result.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def package_digest(repo: Path, commit: str) -> str:
    """attest.core.provenance.attest_revision over the commit's attest/**/*.py: sha256 of every relative path and content, sorted."""
    names = sorted((n for n in git(repo, "ls-tree", "-r", "--name-only", commit, "attest").decode().splitlines() if n.endswith(".py")), key=lambda n: n.split("/"))
    h = hashlib.sha256()
    for name in names:
        rel = name[len("attest/"):]
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(git(repo, "show", f"{commit}:{name}"))
        h.update(b"\0")
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--publication", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    pub, review = Path(args.publication), Path(args.review)
    entries = json.loads(Path(args.map).read_text(encoding="utf-8"))["map"]  # [{"review": ..., "publication": ...}, ...]
    mapping = {e["review"]: e["publication"] for e in entries} if isinstance(entries, list) else dict(entries)
    freeze = git(pub, "show", "HEAD:FREEZE.md").decode("utf-8").splitlines()
    results = []
    for index, line in enumerate(freeze):
        match = re.search(r"git checkout ([0-9a-f]{40})", line)
        if not match:
            continue
        target = match.group(1)
        claim = next((re.search(r"review-repository commit ([0-9a-f]{40})", l) for l in freeze[index + 1:index + 3] if "review-repository commit" in l), None)
        source = claim.group(1) if claim else None
        entry = {"line": index + 1, "checkout": target, "review_commit": source}
        try:
            entry["exists"] = git(pub, "cat-file", "-t", target).decode().strip() == "commit"
        except subprocess.CalledProcessError:
            entry["exists"] = False
        entry["mapped"] = bool(source) and mapping.get(source) == target
        if entry["exists"] and source:
            entry["package_digest_equal"] = package_digest(pub, target) == package_digest(review, source)
            harness = [hashlib.sha256(git(repo, "show", f"{c}:scripts/run_evaluation.py")).hexdigest() for repo, c in ((pub, target), (review, source))]
            entry["harness_equal"] = harness[0] == harness[1]
            entry["command_inputs_present"] = all(git(pub, "cat-file", "-t", f"{target}:{p}").decode().strip() == "blob"
                                                  for p in ("scripts/run_evaluation.py", "examples/eval/SUITE-M5.json"))
        entry["ok"] = all(entry.get(k) for k in ("exists", "mapped", "package_digest_equal", "harness_equal", "command_inputs_present"))
        results.append(entry)
    report = {"checkout_lines": len(results), "ok": bool(results) and all(r["ok"] for r in results), "results": results}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checkout_lines": report["checkout_lines"], "ok": report["ok"],
                      "failed": [r for r in results if not r["ok"]]}, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
