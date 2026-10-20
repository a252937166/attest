"""Viewport screenshots of the deployed console for the deployment record (GET only: every other request is aborted inside the
browser before it is sent; service workers blocked). Usage: evidence_shots.py <out dir>"""
import json, ssl, sys, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright
import certifi

BASE = "https://attest.axiqo.xyz"
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
rows = json.loads(op.open(BASE + "/api/runs?limit=200", timeout=30).read())["runs"]
hold = next(r["run_id"] for r in rows if r["run_id"].startswith("rle-encode") and r.get("verdict") == "NEEDS HUMAN")
log = {"base": "production", "method": "GET only", "non_get_attempts": [], "shots": []}


def context(browser, width, height, mobile):
    ctx = browser.new_context(viewport={"width": width, "height": height}, service_workers="block",
                              device_scale_factor=2 if mobile else 1, is_mobile=mobile, has_touch=mobile)
    def guard(route, request):
        if request.method.upper() in ("GET", "HEAD"):
            return route.continue_()
        log["non_get_attempts"].append({"method": request.method, "path": request.url.split("?")[0].replace(BASE, "")})
        return route.abort("blockedbyclient")
    ctx.route("**/*", guard)
    return ctx


def shot(page, name, note):
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / f"{name}.png"))
    log["shots"].append({"file": f"{name}.png", "state": note})


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    for width, height, mobile in ((1440, 900, False), (1024, 900, False), (390, 844, True)):
        ctx = context(browser, width, height, mobile); page = ctx.new_page()
        page.goto(BASE + "/", wait_until="domcontentloaded"); page.wait_for_selector("#workspace", timeout=20000); page.wait_for_timeout(2500)
        shot(page, f"home-{width}", "home page, recorded evidence first")
        page.locator("input[name=mode][value=live]").first.check(force=True); page.wait_for_timeout(300)
        page.locator("#go").click(); page.wait_for_timeout(900)
        page.locator("#confirm").scroll_into_view_if_needed(); page.evaluate("() => document.querySelector('#confirm').scrollIntoView({block: 'center'})")
        shot(page, f"confirm-{width}", "live mode: the Run button opened the confirmation; nothing was sent")
        page.locator("#confirm-go").click(); page.wait_for_timeout(1200)
        page.evaluate("() => document.querySelector('#start-note').scrollIntoView({block: 'center'})")
        shot(page, f"confirm-refused-{width}", "the confirmation pressed in an automated browser: refused by the page before any request")
        page.goto(BASE + "/runs/" + hold, wait_until="domcontentloaded"); page.wait_for_selector(".decision", timeout=20000); page.wait_for_timeout(1500)
        shot(page, f"hold-{width}", f"case file of {hold} (NEEDS HUMAN, recorded 15 Oct 2026)")
        page.locator("[role=tab][data-tab=tests]").first.click(); page.wait_for_timeout(600)
        page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
        page.evaluate("() => { const c = document.querySelector('.counter, .counterexample, [data-k=counterexample]'); if (c) c.scrollIntoView({block: 'start'}); }")
        shot(page, f"hold-tests-open-{width}", "tests and counterexample tab, every disclosure open")
        page.goto(BASE + "/runs/no-such-run-00000000T000000000000Z", wait_until="domcontentloaded"); page.wait_for_timeout(1800)
        shot(page, f"missing-run-{width}", "a run that does not exist")
        ctx.unroute("**/*")
        def failing(route, request):
            if request.method.upper() not in ("GET", "HEAD"):
                log["non_get_attempts"].append({"method": request.method, "path": request.url.split("?")[0].replace(BASE, "")})
                return route.abort("blockedbyclient")
            if request.url.split("?")[0].replace(BASE, "").startswith("/api/"):
                return route.fulfill(status=503, content_type="application/json", body=json.dumps({"error": "unavailable", "detail": "the service is restarting; retry in a minute"}))
            return route.continue_()
        ctx.route("**/*", failing)
        page.goto(BASE + "/runs/" + hold, wait_until="domcontentloaded"); page.wait_for_timeout(2200)
        shot(page, f"api-failure-{width}", "the case file with every API call answered 503 inside the browser")
        ctx.close()
    browser.close()
(OUT / "shots.json").write_text(json.dumps(log, indent=1) + "\n")
print(json.dumps(log, indent=1))
