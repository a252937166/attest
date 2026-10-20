#!/usr/bin/env python3
"""`attest check` of every proof bundle in an exported tree with two checkers (two package trees), offline, and the differences.

    python compare_checkers.py --bundles <export checkout> --before <0.9.0 tree> --after <0.10.0 tree> --out result.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROBE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from attest.core.check import check_bundle
import attest
out = []
for path in sys.argv[3:]:
    try:
        report = check_bundle(path)
        out.append({"path": path, "ok": report.get("ok"), "warnings": sum(1 for c in report.get("checks", []) if c.get("severity") == "warning" and c.get("ok") is not True),
                    "errors": [c.get("name") for c in report.get("checks", []) if c.get("severity") != "warning" and c.get("ok") is False],
                    "protocol": report.get("evidence_protocol"), "complete": report.get("evidence_complete")})
    except Exception as error:
        out.append({"path": path, "ok": False, "exception": f"{type(error).__name__}: {error}"})
json.dump({"version": attest.__version__, "results": out}, open(sys.argv[2], "w"))
'''


def run(tree: Path, bundles: list[str], out: Path) -> dict:
    subprocess.run([sys.executable, "-c", PROBE, str(tree), str(out), *bundles], check=True, cwd=str(tree))
    return json.loads(out.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundles", required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = Path(args.bundles).resolve()
    bundles = sorted(str(p.parent) for p in root.glob("reports/**/proof_bundle.json"))
    out = Path(args.out).resolve()
    before = run(Path(args.before).resolve(), bundles, out.with_suffix(".before.tmp"))
    after = run(Path(args.after).resolve(), bundles, out.with_suffix(".after.tmp"))
    out.with_suffix(".before.tmp").unlink()
    out.with_suffix(".after.tmp").unlink()
    changed = []
    for b, a in zip(before["results"], after["results"]):
        if (b.get("ok"), b.get("warnings"), b.get("errors")) != (a.get("ok"), a.get("warnings"), a.get("errors")):
            changed.append({"bundle": str(Path(b["path"]).relative_to(root)), "before": {k: b.get(k) for k in ("ok", "warnings", "errors")},
                            "after": {k: a.get(k) for k in ("ok", "warnings", "errors")}})
    result = {"what": f"attest check of every bundle in the exported tree, with the checker of {before['version']} and of {after['version']}",
              "bundles": len(bundles), "ok_before": sum(1 for r in before["results"] if r.get("ok")), "ok_after": sum(1 for r in after["results"] if r.get("ok")),
              "warnings_before": sum(r.get("warnings") or 0 for r in before["results"]), "warnings_after": sum(r.get("warnings") or 0 for r in after["results"]),
              "exceptions": [r for r in before["results"] + after["results"] if r.get("exception")], "bundles_whose_result_changed": changed}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "bundles_whose_result_changed"}, indent=2), "changed:", len(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
