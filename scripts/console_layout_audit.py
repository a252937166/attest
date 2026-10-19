#!/usr/bin/env python3
"""Horizontal-overflow audit of the Attest console in a real Chrome (Playwright, channel=chrome; revision 8, 19 Oct 2026).

Against a local key-less server (default) or --base URL. Every request whose method is not GET or HEAD is intercepted inside the
browser before it is sent: aborted, or (local only, --synthetic-posts) answered with a synthetic response that never reaches any
server. Service workers are blocked so nothing bypasses the interception. The report lists every element whose box leaves the
viewport without a fitting scroll container around it, per page, state and width, the text that runs past it, and the controls an
overflow:hidden box clips. Widths up to 820 px use mobile emulation (mobile viewport, touch, overlay scrollbars, scale 3).

Usage: console_layout_audit.py --out DIR [--base URL] [--widths 320,360,390,414,768,1440] [--synthetic-posts --press-confirm]
       [--team-token TOKEN] [--per-verdict 3]. The local server's interpreter is ATTEST_AUDIT_SERVER_PYTHON, else .venv, else this one."""
import argparse, json, os, secrets, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
IMPORTS = ["reports/attest-verification-2026-10-15/evidence-runs", "reports/attest-first-slice-2026-10-15",
           "reports/attest-evaluation-2026-10-16/runs", "reports/attest-evaluation-2026-10-17-nebius-m5/batch/runs",
           "reports/attest-revision6-repairs-2026-10-19/evaluation-codex/runs", "reports/attest-revision6-repairs-2026-10-19/evaluation-codex-3/runs"]

AUDIT_JS = r"""() => {
  const vw = document.documentElement.clientWidth;
  const describe = (el) => {
    const parts = [];
    for (let e = el, i = 0; e && e !== document.body && i < 4; e = e.parentElement, i++) {
      let s = e.tagName.toLowerCase();
      if (e.id) s += "#" + e.id;
      const cls = [...e.classList].slice(0, 2).join(".");
      if (cls) s += "." + cls;
      parts.unshift(s);
    }
    return parts.join(" > ");
  };
  const fits = (r) => r.right <= vw + 0.5 && r.left >= -0.5;
  const out = [];
  for (const el of document.querySelectorAll("body *")) {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden" || cs.position === "fixed" && el.closest(".backdrop")) continue;
    if (el.closest(".backdrop,.skip,[hidden]")) continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || fits(r)) continue;
    let held = false;
    for (let a = el.parentElement; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if (ox === "auto" || ox === "scroll" || ox === "hidden" || ox === "clip") { if (fits(a.getBoundingClientRect())) { held = true; break; } }
    }
    if (held) continue;
    // report the outermost offender only: skip elements whose parent is itself an offender
    out.push({el, sel: describe(el), left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
              text: (el.innerText || el.getAttribute("aria-label") || "").replace(/\s+/g, " ").slice(0, 80)});
  }
  // text that runs past the viewport although its element's box fits (a long token with no break opportunity)
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seenText = new Set();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || seenText.has(el) || !n.textContent.trim() || el.closest(".backdrop,[hidden]")) continue;
    const range = document.createRange(); range.selectNodeContents(n);
    let right = 0; for (const rc of range.getClientRects()) right = Math.max(right, rc.right);
    if (right <= vw + 0.5) continue;
    let held = false;
    for (let a = el; a && a !== document.body && a !== document.documentElement; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if (ox === "auto" || ox === "scroll" || ox === "hidden" || ox === "clip") { if (fits(a.getBoundingClientRect())) { held = true; break; } }
    }
    if (held) continue;
    seenText.add(el);
    out.push({el, sel: describe(el) + " (text)", left: Math.round(el.getBoundingClientRect().left), right: Math.round(right), width: Math.round(right - el.getBoundingClientRect().left),
              text: n.textContent.replace(/\s+/g, " ").slice(0, 80)});
  }
  // clipped content: a nowrap control or text cut by an overflow:hidden box that fits (the box hides it; still a defect for controls)
  const clipped = [];
  for (const el of document.querySelectorAll("a.btn,button,.chip,.seal,.price")) {
    const r = el.getBoundingClientRect(); if (!r.width) continue;
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.overflowX === "hidden" || cs.overflowX === "clip") { const ar = a.getBoundingClientRect(); if (r.right > ar.right + 0.5 || r.left < ar.left - 0.5) clipped.push({sel: describe(el), right: Math.round(r.right), boxRight: Math.round(ar.right), text: (el.innerText||"").slice(0,40)}); break; }
      if (cs.overflowX === "auto" || cs.overflowX === "scroll") break;
    }
  }
  const set = new Set(out.map(o => o.el));
  const outer = out.filter(o => !set.has(o.el.parentElement)).map(({el, ...rest}) => rest);
  return {vw, docScroll: document.documentElement.scrollWidth, bodyScroll: document.body.scrollWidth, offenders: outer.slice(0, 25), clipped: clipped.slice(0, 10),
          count: outer.length + clipped.length + (document.documentElement.scrollWidth > vw + 1 ? 1 : 0), pageScrollsSideways: document.documentElement.scrollWidth > vw + 1};
}"""


def start_local(imports, team_token=None):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    data = Path(tempfile.mkdtemp(prefix="attest-overflow-"))
    home = Path(tempfile.mkdtemp(prefix="attest-overflow-home-"))
    env = {k: v for k, v in os.environ.items() if k not in ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY") and not k.startswith("ATTEST_")}
    # no credentials and no credential notes: this server cannot build a provider, so no request it makes can be paid
    env.update({"HOME": str(home), "ATTEST_SECRETS_NOTES": str(home / "none.json"), "ATTEST_DATA_DIR": str(data),
                "ATTEST_IMPORT_DIRS": ":".join(str(ROOT / p) for p in imports), "ATTEST_IMPORT_PROVIDERS": "codex,nebius",
                "ATTEST_ADMIN_TOKEN": team_token or secrets.token_hex(12), "NO_PROXY": "*"})  # the local server's own throwaway token
    python = os.environ.get("ATTEST_AUDIT_SERVER_PYTHON") or (str(ROOT / ".venv/bin/python") if (ROOT / ".venv/bin/python").exists() else sys.executable)
    server = subprocess.Popen([python, "-m", "uvicorn", "attest.app.server:app", "--host", "127.0.0.1", "--port", str(port)],
                              cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    for _ in range(120):
        try:
            urllib.request.urlopen(base + "/api/health", timeout=2); return server, base
        except Exception:
            time.sleep(0.5)
    server.terminate(); raise SystemExit("local server did not start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base"); ap.add_argument("--out", required=True)
    ap.add_argument("--widths", default="320,360,375,390,414,768,1024,1440")
    ap.add_argument("--runs", default="", help="comma-separated run ids; default one per verdict from /api/runs")
    ap.add_argument("--synthetic-posts", action="store_true", help="local only: answer intercepted POSTs with synthetic error bodies")
    ap.add_argument("--screens", default="390,1440")
    ap.add_argument("--per-verdict", type=int, default=3)
    ap.add_argument("--headed", action="store_true", help="show the browser window (the same installed Chrome, not headless)")
    ap.add_argument("--press-confirm", action="store_true", help="press the confirmation button (local: answered synthetically; public host: the page must refuse in an automated browser, and every non-GET is aborted anyway)")
    ap.add_argument("--team-token", default="", help="local only: sign in through the console with this token (POST /api/profiles to the local server)")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    server = None
    base = args.base
    if not base:
        server, base = start_local(IMPORTS, args.team_token or None)
    elif args.synthetic_posts:
        raise SystemExit("--synthetic-posts is for the local server only")
    host = urlparse(base).hostname
    import ssl
    try:
        import certifi
        tls = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        tls = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}) if host == "127.0.0.1" else urllib.request.ProxyHandler(),
                                         urllib.request.HTTPSHandler(context=tls))
    headers = {"X-Attest-Token": args.team_token} if args.team_token else {}
    rows = json.loads(opener.open(urllib.request.Request(base + "/api/runs?limit=200", headers=headers), timeout=30).read())["runs"]
    if args.runs:
        picks = [r for r in rows if r["run_id"] in args.runs.split(",")]
    else:
        seen, picks = {}, []
        for r in sorted(rows, key=lambda r: -len(r["run_id"])):  # longest identifiers first: the hardest case per verdict
            key = r.get("verdict") or r.get("status")
            if seen.get(key, 0) < args.per_verdict:
                seen[key] = seen.get(key, 0) + 1; picks.append(r)
    report = {"base": base if host == "127.0.0.1" else "production", "runs": [r["run_id"] for r in picks], "widths": [], "blocked_requests": [],
              "requests": {"GET": 0, "HEAD": 0, "other": 0}}
    synthetic = {"status": 422, "body": {"error": "invalid_request", "detail": "invalid request: provider: unknown inference profile"}}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not args.headed)
        for width in [int(w) for w in args.widths.split(",")]:
            mobile = width <= 820  # phones and small tablets: mobile viewport semantics, touch, overlay scrollbars
            ctx = browser.new_context(viewport={"width": width, "height": 900}, service_workers="block", device_scale_factor=3 if mobile else 1,
                                      is_mobile=mobile, has_touch=mobile)

            def guard(route, request):
                method = request.method.upper()
                if method in ("GET", "HEAD"):
                    report["requests"][method] += 1
                    return route.continue_()
                report["requests"]["other"] += 1
                path = urlparse(request.url).path
                local = host == "127.0.0.1" and urlparse(request.url).hostname == "127.0.0.1"
                if local and (path == "/api/profiles" or path.endswith("/download-ticket")):
                    report["blocked_requests"].append({"width": width, "method": method, "path": path, "answered": "passed to the local key-less server"})
                    return route.continue_()
                report["blocked_requests"].append({"width": width, "method": method, "path": path,
                                                   "answered": "synthetic" if args.synthetic_posts and local else "aborted"})
                if args.synthetic_posts and local:
                    return route.fulfill(status=synthetic["status"], content_type="application/json", body=json.dumps(synthetic["body"]))
                return route.abort("blockedbyclient")

            ctx.route("**/*", guard)
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            entry = {"width": width, "pages": []}

            def audit(label, shot=None):
                page.wait_for_timeout(350)
                res = page.evaluate(AUDIT_JS)
                res["label"] = label
                entry["pages"].append(res)
                if shot and str(width) in args.screens.split(","):
                    page.screenshot(path=str(out / f"{shot}-{width}.png"), full_page=True)

            page.goto(base + "/", wait_until="domcontentloaded"); page.wait_for_selector("#workspace", timeout=20000); page.wait_for_timeout(1500)
            if args.team_token:
                page.evaluate("() => { const d = document.querySelector('#signin'); if (d) d.open = true; }")
                page.fill("#admin", args.team_token); page.click("#signin-go"); page.wait_for_timeout(1200)
            audit("home", "home")
            page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
            audit("home, every details open", "home-open")
            # live mode selected (the paid mode): its explanation and the start button must fit too
            live = page.locator("input[name=mode][value=live]")
            if live.count():
                live.first.check(force=True); page.wait_for_timeout(300)
                audit("home, live mode selected", "home-live")
                if page.locator("#confirm").count():
                    # the Run button only opens the confirmation (it sends nothing); the confirmation must fit too
                    page.locator("#go").click(); page.wait_for_timeout(900)
                    report.setdefault("confirmation", []).append({"width": width, "visible": page.locator("#confirm").is_visible(),
                                                                  "requests_after_run_button": report["requests"]["other"]})
                    audit("home, confirmation open", "home-confirm")
                    if args.press_confirm:
                        before = report["requests"]["other"]
                        page.locator("#confirm-go").click(); page.wait_for_timeout(1200)
                        report["confirmation"][-1].update({"pressed": True, "non_get_requests_from_confirm": report["requests"]["other"] - before,
                                                           "note": page.locator("#start-note").inner_text()})
                        audit("home, confirm pressed (" + ("synthetic 422 locally, never sent" if args.synthetic_posts else "refused in the automated browser") + ")", "home-start-error")
                page.locator("input[name=mode][value=browse]").first.check(force=True)
            for r in picks:
                rid = r["run_id"]
                page.goto(base + "/runs/" + rid, wait_until="domcontentloaded")
                try:
                    page.wait_for_selector(".decision", timeout=20000)
                except Exception:
                    pass
                page.wait_for_timeout(1200)
                tag = (r.get("verdict") or r.get("status") or "run").lower().replace(" ", "-")
                audit(f"run {rid} overview", f"run-{tag}")
                tabs = page.locator("[role=tab]:not([disabled])")
                for i in range(tabs.count()):
                    name = tabs.nth(i).inner_text().strip().split("\n")[0][:20]
                    tabs.nth(i).click(); page.wait_for_timeout(400)
                    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
                    audit(f"run {rid} tab {name}, details open", f"run-{tag}-{name.lower().replace(' ', '-')}")
            page.goto(base + "/runs/no-such-run-00000000T000000000000Z", wait_until="domcontentloaded"); page.wait_for_timeout(1500)
            audit("missing run", "missing-run")
            # API failure, simulated inside the browser (the request is answered locally; GETs only)
            ctx.unroute("**/*")
            def failing(route, request):
                if request.method.upper() not in ("GET", "HEAD"):
                    report["blocked_requests"].append({"width": width, "method": request.method, "path": urlparse(request.url).path, "answered": "aborted"})
                    return route.abort("blockedbyclient")
                if urlparse(request.url).path.startswith("/api/"):
                    return route.fulfill(status=503, content_type="application/json", body=json.dumps({"error": "unavailable", "detail": "the service is restarting; retry in a minute"}))
                return route.continue_()
            ctx.route("**/*", failing)
            page.goto(base + "/runs/" + picks[0]["run_id"], wait_until="domcontentloaded"); page.wait_for_timeout(1800)
            audit("run page with every API call failing (simulated 503)", "api-failure")
            entry["page_errors"] = errors
            report["widths"].append(entry)
            ctx.close()
        browser.close()
    if server:
        server.terminate()
    summary = []
    for entry in report["widths"]:
        for pg in entry["pages"]:
            for c in pg.get("clipped", []):
                summary.append(f"{entry['width']:>5} {pg['label'][:70]:70} CLIPPED {c['sel'][:60]} right={c['right']} box={c['boxRight']} {c['text']!r}")
            if pg["offenders"] or pg.get("pageScrollsSideways"):
                first = pg["offenders"][0] if pg["offenders"] else {"sel": "(document only)", "right": pg["docScroll"], "text": ""}
                summary.append(f"{entry['width']:>5} {pg['label'][:70]:70} offenders={len(pg['offenders'])} doc={pg['docScroll']} first={first['sel'][:70]} right={first['right']} text={first['text'][:40]!r}")
            if False:
                summary.append(f"{entry['width']:>5} {pg['label'][:70]:70} offenders={pg['count']} first={pg['offenders'][0]['sel'][:70]} right={pg['offenders'][0]['right']} text={pg['offenders'][0]['text'][:40]!r}")
    report["summary"] = summary
    (out / "overflow-report.json").write_text(json.dumps(report, indent=1))
    print("\n".join(summary) or "no offenders")
    print("requests:", report["requests"], "blocked:", len(report["blocked_requests"]))


if __name__ == "__main__":
    main()
