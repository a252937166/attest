#!/usr/bin/env python3
"""The console's case file of a run held for reconciliation, in a real Chrome (revision 9). Offline: a halted bundle is written by the
offline pipeline with the test fakes (named as a Nemotron run, so the local console imports it as a public row), a local console with
no credential serves it, and Chrome opens it at 1440 px and at 390 px with mobile emulation. Every request that is not a GET is aborted
inside the browser. Checks: nothing wider than the viewport, the decision says the run stopped for reconciliation, the case file offers
"Held for reconciliation" and no "Start a new run", and exhibit E7 shows the reconciliation line. Usage: held_run_check.py OUTDIR"""
import contextlib, io, json, os, secrets, shutil, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("ATTEST_TREE", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT))
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

from attest.core.pipeline import Pipeline  # noqa: E402
from attest.core.task import TaskSpec  # noqa: E402
from attest.ledger import Ledger  # noqa: E402
from attest.sandbox.tf_sandboxes import SandboxError  # noqa: E402
from tests.test_verification import TASK, FakeExecutor, FakeProvider  # noqa: E402


class Provider(FakeProvider):
    name = "nebius_tokenfactory"

    def describe(self):
        return {"provider": "nebius_tokenfactory", "note": "offline fake for the layout check"}


class Executor(FakeExecutor):
    def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
        if stage == "breaker-tests":
            raise SandboxError("spawn outcome uncertain (RemoteDisconnected); inspect account operations, do not replay", uncertain=True)
        return super().run_branch(image, files, steps, stage, deletes, timeout, networking)


runs = Path(tempfile.mkdtemp(prefix="attest-held-runs-"))
ledger = Ledger()
pipeline = Pipeline(task=TaskSpec.load(TASK), provider=Provider(ledger, "honest"), executor=Executor(ledger, "honest"), ledger=ledger,
                    out_dir=runs, max_turns=4, max_mutants=6, mutant_workers=1, tavily=None, profile_label="judge-demo")
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    bundle = pipeline.run()
assert bundle["reconciliation"]["required"], bundle["verdict"]

with socket.socket() as s:
    s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
data, home = Path(tempfile.mkdtemp(prefix="attest-held-data-")), Path(tempfile.mkdtemp(prefix="attest-held-home-"))
env = {k: v for k, v in os.environ.items() if k not in ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY") and not k.startswith("ATTEST_")}
env.update({"HOME": str(home), "ATTEST_SECRETS_NOTES": str(home / "none.json"), "ATTEST_DATA_DIR": str(data), "ATTEST_IMPORT_DIRS": str(runs),
            "ATTEST_IMPORT_PROVIDERS": "nebius", "ATTEST_ADMIN_TOKEN": secrets.token_hex(12), "NO_PROXY": "*"})
python = os.environ.get("ATTEST_AUDIT_SERVER_PYTHON") or sys.executable
server = subprocess.Popen([python, "-m", "uvicorn", "attest.app.server:app", "--host", "127.0.0.1", "--port", str(port)], cwd=str(ROOT), env=env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
base = f"http://127.0.0.1:{port}"
report = {"run_id": pipeline.run_id, "verdict": bundle["verdict"]["verdict"], "reconciliation_items": len(bundle["reconciliation"]["items"]), "widths": {}}
try:
    for _ in range(120):
        try:
            urllib.request.urlopen(base + "/api/health", timeout=2); break
        except Exception:
            time.sleep(0.5)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for width, mobile in ((1440, False), (390, True)):
            context = browser.new_context(viewport={"width": width, "height": 900 if not mobile else 844}, is_mobile=mobile, has_touch=mobile,
                                          device_scale_factor=3 if mobile else 1, service_workers="block")
            page = context.new_page()
            seen = {"get": 0, "aborted": 0}

            def route(r, request, seen=seen):
                if request.method in ("GET", "HEAD"):
                    seen["get"] += 1; r.continue_()
                else:
                    seen["aborted"] += 1; r.abort()
            page.route("**/*", route)
            page.goto(base + "/runs/" + pipeline.run_id, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".decision", timeout=60000)
            page.wait_for_timeout(1500)
            facts = page.evaluate("""() => {
              const vw = document.documentElement.clientWidth;
              const wide = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
                return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && (r.right > vw + 0.5 || r.left < -0.5) && !e.closest('[hidden],.backdrop,.skip'); });
              const decision = document.querySelector('.decision');
              return {vw, scroll_width: document.documentElement.scrollWidth, wider_than_viewport: wide.length,
                      decision: decision ? decision.innerText.slice(0, 300) : null,
                      held: [...document.querySelectorAll('.btn')].some(b => /Held for reconciliation/.test(b.textContent)),
                      new_run_buttons: document.querySelectorAll('[data-new-run]').length};
            }""")
            # exhibit E7 (the failure record) and its reconciliation line, when the case file shows it
            e7 = page.locator("text=reconciliation").first
            facts["reconciliation_line_found"] = e7.count() > 0
            page.screenshot(path=str(out / f"held-run-{width}.png"), full_page=False)
            facts.update(requests=seen)
            report["widths"][str(width)] = facts
            context.close()
        browser.close()
finally:
    server.terminate()
    shutil.rmtree(runs, ignore_errors=True); shutil.rmtree(data, ignore_errors=True); shutil.rmtree(home, ignore_errors=True)
report["ok"] = all(w["wider_than_viewport"] == 0 and w["scroll_width"] <= w["vw"] and w["held"] and w["new_run_buttons"] == 0 and w["requests"]["aborted"] == 0
                   and "stopped for reconciliation" in (w["decision"] or "") for w in report["widths"].values())
(out / "held-run-check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
