#!/usr/bin/env python3
"""Real-browser verification of the M3 console: screenshots at 1440 px and 390 px, light and dark, for every state, plus
the keyed-update test (an open disclosure and keyboard focus must survive at least 20 refresh cycles of a running run).

Starts its own console (uvicorn) on a free port with a temporary data directory and recorded evidence imported from
the reports; replays recorded runs as synthetic fixtures for the queued and running states (scripts/console_replay.py).
No inference, no sandboxes, no network beyond localhost (the page's Google Fonts request falls back to system fonts
when offline). Uses Playwright for Python with the installed Google Chrome (channel="chrome").

Usage: python3 reports/attest-m3-2026-10-17/capture.py [--out reports/attest-m3-2026-10-17]
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = {
    "durationkit-judge": "reports/attest-verification-2026-10-15/console-run-durationkit-nebius",
    "semver-verified": "reports/attest-hardening-2026-10-16/semver-v2-codex-verified",
    "roman-dispute": "reports/attest-evaluation-2026-10-16/rerun2/runs/roman-to-numeral-20261015T184550Z",
    "rle-bug": "reports/attest-evaluation-2026-10-16/runs/rle-encode-20261015T180226Z",
    "brackets-m1": "reports/attest-m1-2026-10-16/runs/balanced-brackets-20261016T192809Z",
    "error-422": "reports/attest-first-slice-2026-10-15/nebius-pilot-attempt1-http422",
    "rle-infeasible": "reports/attest-m1-2026-10-16/evaluation-dryrun-codex/runs/rle-encode-20261016T193214Z",
}
VIEWPORTS = {"1440": {"width": 1440, "height": 960}, "390": {"width": 390, "height": 844}}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, timeout: float = 20) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            time.sleep(0.3)
    raise SystemExit(f"console did not come up at {url}")


def api(base: str, path: str) -> dict:
    with urllib.request.urlopen(base + path, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--keep-server", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    screens = out / "screens"
    screens.mkdir(parents=True, exist_ok=True)
    seq_dir = out / "refresh-sequence"
    seq_dir.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    tmp = Path(tempfile.mkdtemp(prefix="attest-m3-capture-"))
    imports = tmp / "imports"
    imports.mkdir()
    for name, rel in FIXTURES.items():
        src = ROOT / rel
        if src.is_dir():
            (imports / name).symlink_to(src, target_is_directory=True)
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    env = dict(os.environ, ATTEST_DATA_DIR=str(tmp / "data"), ATTEST_IMPORT_DIRS=str(imports), ATTEST_ADMIN_TOKEN="capture-token",
               ATTEST_PUBLIC_RUNS_PER_HOUR="3")
    python = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable
    server = subprocess.Popen([python, "-m", "uvicorn", "attest.app.server:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
                              cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    record: dict = {"base": base, "data_dir": str(tmp), "screens": [], "refresh_test": None, "checks": {}}
    replays: list[subprocess.Popen] = []
    try:
        wait_http(base + "/api/health")
        runs = api(base, "/api/runs")["runs"]
        by = {}
        for r in runs:
            by.setdefault((r["task_id"], r["verdict"]), r["run_id"])
        verified = by.get(("durationkit-units-001", "VERIFIED"))
        semver = by.get(("semver-is-compatible-pr368-v2", "VERIFIED"))
        needs = by.get(("rle-encode", "NEEDS HUMAN"))
        roman = by.get(("roman-to-numeral", "NEEDS HUMAN"))
        error = by.get(("durationkit-units-001", "ERROR"))
        infeasible = by.get(("rle-encode", "INFEASIBLE"))
        store = tmp / "data" / "attest.db"
        judge_dir = ROOT / FIXTURES["durationkit-judge"]
        replay_cmd = [sys.executable, str(ROOT / "scripts" / "console_replay.py"), "--store", str(store), "--run-dir", str(judge_dir), "--quiet"]
        # queued fixture: stays queued for 40 s, then replays slowly; running fixture: replays at 2 s per event (about 1 min)
        # running fixture: one event every 6 s (about 3 minutes); queued fixture: stays queued for 4 minutes, then replays
        replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-running", "--interval", "6.0"], cwd=str(ROOT)))
        time.sleep(1.5)
        replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-queued", "--interval", "2.0", "--delay-start", "240"], cwd=str(ROOT)))
        time.sleep(1.5)

        shots = [
            ("running-overview", "/runs/replay-running", "#log li"),
            ("queued-overview", "/runs/replay-queued", ".decision .statement"),
            ("empty", "/", None),
            ("verified-overview", f"/runs/{verified}#overview", ".decision .statement"),
            ("verified-tests", f"/runs/{verified}#tests", ".exhibit"),
            ("semver-heldout-overview", f"/runs/{semver}#overview", ".decision .statement"),
            ("needs-human-tests", f"/runs/{needs}#tests", ".counter"),
            ("needs-human-overview", f"/runs/{needs}#overview", ".decision .statement"),
            ("contract-dispute-tests", f"/runs/{roman}#tests", ".counter"),
            ("error-overview", f"/runs/{error}#overview", ".decision .statement"),
            ("error-tests", f"/runs/{error}#tests", ".exhibit"),
            ("infeasible-overview", f"/runs/{infeasible}#overview", ".decision .statement"),
            ("verified-activity", f"/runs/{verified}#activity", ".log li"),
            ("verified-files", f"/runs/{verified}#files", ".files li"),
            ("verified-patch", f"/runs/{verified}#patch", ".diff"),
        ]
        narrow_only = {"empty", "verified-overview", "needs-human-tests", "running-overview", "error-overview", "queued-overview"}
        errors: list[str] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            for scheme in ("light", "dark"):
                for vp_name, vp in VIEWPORTS.items():
                    ctx = browser.new_context(viewport=vp, color_scheme=scheme, device_scale_factor=1)
                    page = ctx.new_page()
                    page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
                    page.on("console", lambda m: errors.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
                    for name, path, wait_for in shots:
                        if vp_name == "390" and name not in narrow_only:
                            continue
                        if path.split("#")[0].endswith("None"):
                            continue
                        page.goto(base + path, wait_until="domcontentloaded")
                        # "attached" rather than visible: at 390 px the rail is a collapsed disclosure, and a sticky
                        # header can cover the top of a long panel
                        page.wait_for_selector(wait_for or "#history li[data-id]", state="attached", timeout=20000)
                        page.wait_for_timeout(400)
                        if vp_name == "390":
                            page.locator("#rail-details").evaluate("d => { d.open = false; }") if name != "empty" else None
                        file = screens / f"{name}-{vp_name}-{scheme}.png"
                        page.screenshot(path=str(file), full_page=(name not in ("running-overview",)))
                        record["screens"].append({"file": file.name, "state": name, "viewport": vp, "scheme": scheme, "url": path})
                    ctx.close()
            # sticky header compaction on scroll, roving tabindex on the tab strip, arrow keys in the history rail
            ctx = browser.new_context(viewport=VIEWPORTS["1440"], color_scheme="light")
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
            page.goto(base + f"/runs/{verified}#tests", wait_until="domcontentloaded")
            page.wait_for_selector(".exhibit", state="attached", timeout=20000)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(500)
            compact = page.evaluate("document.querySelector('.decision').classList.contains('compact')")
            page.screenshot(path=str(screens / "verified-tests-scrolled-compact-1440-light.png"))
            record["screens"].append({"file": "verified-tests-scrolled-compact-1440-light.png", "state": "verified-tests scrolled 900 px (compact header)",
                                      "viewport": VIEWPORTS["1440"], "scheme": "light", "url": f"/runs/{verified}#tests"})
            page.focus("#tab-overview")
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(200)
            arrow_right = page.evaluate("[document.activeElement.dataset.focus, document.querySelector('[role=tab][aria-selected=true]').dataset.tab, location.hash]")
            page.keyboard.press("End")
            page.wait_for_timeout(200)
            end_key = page.evaluate("[document.activeElement.dataset.focus, location.hash]")
            first_hist = page.evaluate("document.querySelector('#history li button').dataset.focus")
            page.focus("#history li button")
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(100)
            hist_down = page.evaluate("document.activeElement.dataset.focus")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
            opened = page.evaluate("[location.pathname, document.querySelector('#history button[aria-current=\"true\"]') && document.querySelector('#history button[aria-current=\"true\"]').dataset.focus]")
            record["checks"]["compact_header_after_scroll"] = compact
            record["checks"]["keyboard"] = {"arrow_right_from_overview_tab": arrow_right, "end_key": end_key, "history_first_row": first_hist,
                                            "history_arrow_down_focus": hist_down, "enter_opened_path_and_current": opened}
            ctx.close()
            # keyed-update test: a dedicated replay (one event every 0.8 s), the page polling every 300 ms; open a
            # disclosure, focus it, let at least 20 refresh cycles pass
            replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-refresh", "--interval", "0.8"], cwd=str(ROOT)))
            time.sleep(2.0)
            ctx = browser.new_context(viewport=VIEWPORTS["1440"], color_scheme="light")
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
            page.goto(base + "/runs/replay-refresh?poll=300", wait_until="domcontentloaded")
            page.wait_for_selector("#log li", timeout=20000)
            status = api(base, "/api/runs/replay-refresh/events?after=0")["status"]
            if status != "running":
                record["refresh_test"] = {"ok": False, "reason": f"fixture was {status} when the test started"}
            else:
                page.click('details[data-id="stages-help"] > summary')
                page.wait_for_timeout(100)
                page.focus('details[data-id="stages-help"] > summary')
                before = {"open": page.evaluate("document.querySelector('details[data-id=\"stages-help\"]').open"),
                          "focus": page.evaluate("document.activeElement && document.activeElement.dataset.focus"),
                          "log_rows": page.locator("#log li").count(), "polls": page.evaluate("window.attestDebug.polls")}
                sequence = []
                target = before["polls"] + 20
                last_shot = before["polls"]
                deadline = time.time() + 60
                while time.time() < deadline:
                    polls = page.evaluate("window.attestDebug.polls")
                    if polls - last_shot >= 5:
                        last_shot = polls
                        file = seq_dir / f"refresh-{polls:03d}.png"
                        page.screenshot(path=str(file))
                        sequence.append({"polls": polls, "file": file.name, "log_rows": page.locator("#log li").count(),
                                         "details_open": page.evaluate("document.querySelector('details[data-id=\"stages-help\"]').open"),
                                         "focus": page.evaluate("document.activeElement && document.activeElement.dataset.focus"),
                                         "tab": page.evaluate("document.querySelector('[role=tab][aria-selected=true]').dataset.tab"),
                                         "status": api(base, "/api/runs/replay-refresh/events?after=0")["status"]})
                    if polls >= target:
                        break
                    time.sleep(0.2)
                after = {"open": page.evaluate("document.querySelector('details[data-id=\"stages-help\"]') && document.querySelector('details[data-id=\"stages-help\"]').open"),
                         "focus": page.evaluate("document.activeElement && document.activeElement.dataset.focus"),
                         "log_rows": page.locator("#log li").count(), "polls": page.evaluate("window.attestDebug.polls"),
                         "renders": page.evaluate("window.attestDebug.renders"), "panel_renders": page.evaluate("window.attestDebug.panelRenders"),
                         "status": api(base, "/api/runs/replay-refresh/events?after=0")["status"]}
                ok = (after["polls"] - before["polls"] >= 20 and after["open"] is True and after["focus"] == "det-stages-help"
                      and after["log_rows"] > before["log_rows"] and after["status"] == "running")
                record["refresh_test"] = {"ok": ok, "before": before, "after": after, "sequence": sequence,
                                          "criterion": "after >= 20 refresh cycles the disclosure is still open, the focused element is the same, "
                                                       "new log rows arrived and the run was still running (no full re-render happened)"}
            ctx.close()
            # public page source and unauthenticated API responses must not name the development gateway
            leaks = {}
            for path in ("/", "/static/app.js", "/static/styles.css", "/api/health", "/api/tasks", "/api/profiles"):
                with urllib.request.urlopen(base + path, timeout=10) as r:
                    text = r.read().decode("utf-8", "replace").lower()
                leaks[path] = {"codex": text.count("codex"), "gateway_host": text.count("axiqo")}
            record["checks"]["public_source_gateway_mentions"] = leaks
            record["checks"]["browser_errors"] = errors
            browser.close()
    finally:
        for proc in replays:
            try:
                proc.terminate()
            except OSError:
                pass
        if not args.keep_server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
    (out / "capture-record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"screens": len(record["screens"]), "refresh_test": (record["refresh_test"] or {}).get("ok"),
                      "browser_errors": len(record["checks"].get("browser_errors") or []), "leaks": record["checks"].get("public_source_gateway_mentions")}, indent=1))
    return 0 if (record["refresh_test"] or {}).get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
