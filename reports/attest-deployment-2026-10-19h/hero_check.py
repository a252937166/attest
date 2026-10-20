"""The hero replay's finished state at several widths (local key-less server, or --base): the title beside the badge must stay on
one line and nothing may leave the viewport. GET only."""
import json, sys
sys.path.insert(0, sys.argv[1] + "/scripts")
import console_layout_audit as a
from playwright.sync_api import sync_playwright
out = sys.argv[2]; base = sys.argv[3] if len(sys.argv) > 3 else None
server = None
if not base:
    server, base = a.start_local(a.IMPORTS)
res = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True)
        for w, h, mobile, dsf in ((320, 800, True, 3), (390, 844, True, 3), (768, 1024, True, 2), (1024, 768, False, 1), (1280, 720, False, 1.5), (1440, 900, False, 1), (1920, 1080, False, 1)):
            ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=dsf, service_workers="block")
            ctx.route("**/*", lambda route, req: route.continue_() if req.method.upper() in ("GET", "HEAD") else route.abort("blockedbyclient"))
            pg = ctx.new_page(); pg.goto(base + "/", wait_until="domcontentloaded", timeout=120000); pg.wait_for_selector("#workspace", timeout=60000)
            pg.wait_for_function("() => /OK/.test(document.querySelector('[data-bm=check]').textContent)", timeout=30000); pg.wait_for_timeout(800)
            m = pg.evaluate("""() => { const t = document.querySelector('.bundle-title strong'); const lh = parseFloat(getComputedStyle(t).lineHeight) || 20;
                const r = t.getBoundingClientRect(); const c = document.querySelector('[data-bm=check]').getBoundingClientRect();
                return {titleLines: Math.round(r.height / lh), badge: document.querySelector('[data-bm=check]').textContent, badgeRight: Math.round(c.right),
                        vw: document.documentElement.clientWidth, docW: document.documentElement.scrollWidth}; }""")
            m["width"] = w; res.append(m)
            pg.locator(".bundle").screenshot(path=f"{out}/bundle-{w}.png")
            ctx.close()
        b.close()
finally:
    if server: server.terminate()
print(json.dumps(res, indent=0))
