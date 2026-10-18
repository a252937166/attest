#!/usr/bin/env python3
"""Real-browser verification of the 18 Oct 2026 console redesign: screenshots of the home page and of the case file in
every state, at 1440 px and 390 px, plus the guide (contextual onboarding) and the keyed-update test (an open
disclosure and keyboard focus must survive at least 20 refresh cycles of a running run).

Starts its own console (uvicorn) on a free port with a temporary data directory and recorded evidence imported from the
reports; replays recorded runs as synthetic fixtures for the queued and running states (scripts/console_replay.py).
No inference, no sandboxes, no network beyond localhost (the page's Google Fonts request falls back to system fonts when
offline). Uses Playwright for Python with the installed Google Chrome (channel="chrome").

Usage: python3 reports/attest-ui-2026-10-18/capture.py [--out reports/attest-ui-2026-10-18]
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
    "rle-hold": "reports/attest-evaluation-2026-10-16/runs/rle-encode-20261015T181805Z",
    "rle-baseline": "reports/attest-evaluation-2026-10-16/runs/rle-encode-20261015T181704Z",
    "roman-dispute": "reports/attest-evaluation-2026-10-16/rerun2/runs/roman-to-numeral-20261015T184550Z",
    "error-422": "reports/attest-first-slice-2026-10-15/nebius-pilot-attempt1-http422",
    "demo-run-1": "reports/attest-evaluation-2026-10-17-nebius-m5/demo/durationkit-units-001-20261017T172421506287Z",
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
    parser.add_argument("--quick", action="store_true", help="screenshots only, no refresh test")
    args = parser.parse_args()
    out = Path(args.out)
    screens = out / "screens"
    screens.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright

    tmp = Path(tempfile.mkdtemp(prefix="attest-ui-capture-"))
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
    record: dict = {"base": base, "data_dir": str(tmp), "screens": [], "refresh_test": None, "checks": {}, "errors": []}
    replays: list[subprocess.Popen] = []
    try:
        wait_http(base + "/api/health")
        runs = api(base, "/api/runs")["runs"]
        by: dict = {}
        for r in runs:
            by.setdefault((r["task_id"], r["verdict"]), r["run_id"])
        verified = by.get(("durationkit-units-001", "VERIFIED"))
        needs = by.get(("rle-encode", "NEEDS HUMAN"))
        demo = by.get(("durationkit-units-001", "NEEDS HUMAN"))
        roman = by.get(("roman-to-numeral", "NEEDS HUMAN"))
        error = by.get(("durationkit-units-001", "ERROR"))
        record["checks"]["runs_imported"] = len(runs)
        store = tmp / "data" / "attest.db"
        judge_dir = ROOT / FIXTURES["durationkit-judge"]
        replay_cmd = [sys.executable, str(ROOT / "scripts" / "console_replay.py"), "--store", str(store), "--run-dir", str(judge_dir), "--quiet"]
        replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-running", "--interval", "6.0"], cwd=str(ROOT)))
        time.sleep(1.5)
        replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-queued", "--interval", "2.0", "--delay-start", "240"], cwd=str(ROOT)))
        time.sleep(1.5)

        shots = [
            ("home", "/", "#evidence-list li", True),
            ("home-hero", "/", "#evidence-list li", False),
            ("running-overview", "/runs/replay-running", "#log li", False),
            ("queued-overview", "/runs/replay-queued", ".decision .statement", False),
            ("verified-overview", f"/runs/{verified}#overview", ".decision .statement", False),
            ("verified-tests", f"/runs/{verified}#tests", ".exhibit", True),
            ("needs-human-overview", f"/runs/{needs}#overview", ".decision .statement", False),
            ("needs-human-tests", f"/runs/{needs}#tests", ".counter", True),
            ("demo-hold-overview", f"/runs/{demo}#overview", ".decision .statement", False),
            ("contract-dispute-tests", f"/runs/{roman}#tests", ".counter", False),
            ("error-overview", f"/runs/{error}#overview", ".decision .statement", False),
            ("verified-activity", f"/runs/{verified}#activity", ".log li", False),
            ("verified-files", f"/runs/{verified}#files", ".files li", False),
            ("verified-patch", f"/runs/{verified}#patch", ".diff", False),
        ]
        narrow_only = {"home", "verified-overview", "needs-human-tests", "running-overview", "error-overview"}
        errors: list[str] = []
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            for vp_name, vp in VIEWPORTS.items():
                ctx = browser.new_context(viewport=vp, color_scheme="dark", device_scale_factor=1)
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
                page.on("console", lambda m: errors.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
                for name, path, wait_for, full in shots:
                    if vp_name == "390" and name not in narrow_only:
                        continue
                    if "None" in path:
                        continue
                    page.goto(base + path, wait_until="domcontentloaded")
                    page.wait_for_selector(wait_for, state="attached", timeout=20000)
                    page.wait_for_timeout(1200 if name.startswith("home") else 700)
                    if vp_name == "390" and name != "home":
                        page.locator("#rail-details").evaluate("d => { d.open = false; }")
                    file = screens / f"{name}-{vp_name}.png"
                    page.screenshot(path=str(file), full_page=full)
                    record["screens"].append({"file": file.name, "state": name, "viewport": vp, "url": path})
                ctx.close()
            # the guide: open on a finished run, step through to the gates and the counterexample, spotlight visible
            ctx = browser.new_context(viewport=VIEWPORTS["1440"], color_scheme="dark")
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"pageerror {e}"))
            page.goto(base + f"/runs/{needs}#overview", wait_until="domcontentloaded")
            page.wait_for_selector(".decision .statement", state="attached", timeout=20000)
            page.wait_for_timeout(600)
            guide_visible = page.evaluate("!document.querySelector('#guide').hidden")
            page.click("#guide-show")
            page.wait_for_timeout(800)
            page.screenshot(path=str(screens / "guide-step1-1440.png"))
            page.click("#guide-next")
            page.wait_for_timeout(900)
            page.screenshot(path=str(screens / "guide-step2-1440.png"))
            page.click("#guide-next")
            page.wait_for_timeout(900)
            tab_after = page.evaluate("document.querySelector('[role=tab][aria-selected=true]').dataset.tab")
            page.screenshot(path=str(screens / "guide-step3-1440.png"))
            page.click("#guide-next")
            page.wait_for_timeout(900)
            spot = page.evaluate("document.querySelector('.spot') && document.querySelector('.spot').className")
            page.screenshot(path=str(screens / "guide-step4-1440.png"))
            page.click("#guide-close")
            page.wait_for_timeout(300)
            launcher = page.evaluate("[document.querySelector('#guide').hidden, !document.querySelector('#guide-launch').hidden, localStorage.getItem('attest.guide')]")
            record["checks"]["guide"] = {"visible_on_open": guide_visible, "tab_after_step3": tab_after, "spot_at_step4": spot, "after_close": launcher}
            for n in ("guide-step1", "guide-step2", "guide-step3", "guide-step4"):
                record["screens"].append({"file": f"{n}-1440.png", "state": n, "viewport": VIEWPORTS["1440"], "url": f"/runs/{needs}"})
            # navigation: brand link returns home without a reload, the start panel gets the shared workspace form
            page.click(".brand")
            page.wait_for_timeout(800)
            record["checks"]["home_from_run"] = page.evaluate("[location.pathname, document.body.dataset.view, document.querySelector('#workspace').parentElement.id, !document.querySelector('#home').hidden]")
            page.click("[data-section=how]")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(screens / "home-how-1440.png"))
            record["screens"].append({"file": "home-how-1440.png", "state": "home scrolled to How it works", "viewport": VIEWPORTS["1440"], "url": "/#how"})
            # sticky header compaction on scroll, roving tabindex on the tab strip, arrow keys in the history rail
            page.goto(base + f"/runs/{verified}#tests", wait_until="domcontentloaded")
            page.wait_for_selector(".exhibit", state="attached", timeout=20000)
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(500)
            compact = page.evaluate("document.querySelector('.decision').classList.contains('compact')")
            page.screenshot(path=str(screens / "verified-tests-scrolled-compact-1440.png"))
            record["screens"].append({"file": "verified-tests-scrolled-compact-1440.png", "state": "verified-tests scrolled 900 px (compact header)", "viewport": VIEWPORTS["1440"], "url": f"/runs/{verified}#tests"})
            page.focus("#tab-overview")
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(200)
            arrow_right = page.evaluate("[document.activeElement.dataset.focus, document.querySelector('[role=tab][aria-selected=true]').dataset.tab, location.hash]")
            page.focus("#history li button")
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(100)
            hist_down = page.evaluate("document.activeElement.dataset.focus")
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
            opened = page.evaluate("[location.pathname, document.querySelector('#history button[aria-current=\"true\"]') && document.querySelector('#history button[aria-current=\"true\"]').dataset.focus]")
            record["checks"]["compact_header_after_scroll"] = compact
            record["checks"]["keyboard"] = {"arrow_right_from_overview_tab": arrow_right, "history_arrow_down_focus": hist_down, "enter_opened_path_and_current": opened}
            ctx.close()
            if not args.quick:
                # keyed-update test: a dedicated replay (one event every 0.8 s), the page polling every 300 ms; open a
                # disclosure, focus it, let at least 20 refresh cycles pass
                replays.append(subprocess.Popen(replay_cmd + ["--run-id", "replay-refresh", "--interval", "0.8"], cwd=str(ROOT)))
                time.sleep(2.0)
                ctx = browser.new_context(viewport=VIEWPORTS["1440"], color_scheme="dark")
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
                              "log_rows": page.locator("#log li").count(), "polls": page.evaluate("window.attestDebug.polls"),
                              "guide_title": page.evaluate("document.querySelector('#guide-title').textContent")}
                    target = before["polls"] + 20
                    deadline = time.time() + 60
                    while time.time() < deadline and page.evaluate("window.attestDebug.polls") < target:
                        time.sleep(0.5)
                    after = {"open": page.evaluate("document.querySelector('details[data-id=\"stages-help\"]').open"),
                             "focus": page.evaluate("document.activeElement && document.activeElement.dataset.focus"),
                             "log_rows": page.locator("#log li").count(), "polls": page.evaluate("window.attestDebug.polls"),
                             "renders": page.evaluate("window.attestDebug.renders"),
                             "guide_title": page.evaluate("document.querySelector('#guide-title').textContent")}
                    page.screenshot(path=str(screens / "running-after-refreshes-1440.png"))
                    record["screens"].append({"file": "running-after-refreshes-1440.png", "state": "running after 20 refresh cycles", "viewport": VIEWPORTS["1440"], "url": "/runs/replay-refresh"})
                    ok = after["open"] and after["focus"] == before["focus"] == "det-stages-help" and after["polls"] - before["polls"] >= 20 and after["renders"] == 1
                    record["refresh_test"] = {"ok": bool(ok), "before": before, "after": after}
                ctx.close()
            browser.close()
        record["errors"] = errors
    finally:
        for r in replays:
            r.terminate()
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
    (out / "capture-record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({"screens": len(record["screens"]), "errors": record["errors"], "checks": record["checks"], "refresh_test": record["refresh_test"]}, indent=2))
    return 0 if not record["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
