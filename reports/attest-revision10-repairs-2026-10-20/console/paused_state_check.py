#!/usr/bin/env python3
"""The console's home page while new runs are paused (revision 10), in a real Chrome. Offline: a local console with no credential is
started twice over a store prepared beforehand, (1) with a reconciliation hold open, (2) failed closed: a run left `running` whose
bundle requires reconciliation and a database that refuses the hold insert (an SQLite trigger), so the start-up recovery fails. The
home page is opened at 320, 390, 768, 1024 and 1440 px with live mode selected; every request that is not a GET is aborted inside the
browser. Checks: the runs chip says "paused for reconciliation", the live start is disabled and the estimate says why, nothing is wider
than the viewport, and only GET requests were made. Usage: paused_state_check.py OUTDIR"""
import contextlib, io, json, os, secrets, shutil, socket, sqlite3, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("ATTEST_TREE", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)

from attest.app.db import Store  # noqa: E402
from attest.core.pipeline import Pipeline  # noqa: E402
from attest.core.task import TaskSpec  # noqa: E402
from attest.ledger import Ledger, utcnow  # noqa: E402
from attest.sandbox.tf_sandboxes import SandboxError  # noqa: E402
from tests.test_verification import TASK, FakeExecutor, FakeProvider  # noqa: E402


class Executor(FakeExecutor):
    def run_branch(self, image, files, steps, stage, deletes=None, timeout=120, networking=False):
        if stage == "verify":
            raise SandboxError("spawn outcome uncertain (RemoteDisconnected); inspect account operations, do not replay", uncertain=True)
        return super().run_branch(image, files, steps, stage, deletes, timeout, networking)


def prepare(kind: str) -> Path:
    data = Path(tempfile.mkdtemp(prefix=f"attest-paused-{kind}-"))
    store = Store(data / "attest.db")
    if kind == "hold":
        store.create_run(run_id="held-run", task_id="durationkit-units-001", task_title="T", provider="nebius", profile_label="judge", status="error",
                         stage="reconciliation", created_at=utcnow(), requester="203.0.113.7")
        with contextlib.redirect_stderr(io.StringIO()):
            store.record_reconciliation("held-run", "stopped for reconciliation at verify (uncertain_operation): 1 operation(s) to settle", [{"kind": "sandbox_spawn"}])
    else:
        ledger = Ledger()
        pipeline = Pipeline(task=TaskSpec.load(TASK), provider=FakeProvider(ledger, "honest"), executor=Executor(ledger, "honest"), ledger=ledger,
                            out_dir=data / "runs", max_turns=4, max_mutants=4, mutant_workers=1, tavily=None, profile_label="judge", run_id="crashed-run")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            pipeline.run()
        store.create_run(run_id="crashed-run", task_id="durationkit-units-001", task_title="T", provider="nebius", profile_label="judge", status="running",
                         stage="verify", created_at=utcnow(), requester="203.0.113.7", out_dir=str(pipeline.out_dir))
        conn = sqlite3.connect(str(data / "attest.db"))
        conn.execute("CREATE TRIGGER refuse BEFORE INSERT ON holds BEGIN SELECT RAISE(FAIL, 'injected: database or disk is full'); END")
        conn.commit(); conn.close()
    return data


report = {"states": {}}
for kind in ("hold", "fail_closed"):
    data = prepare(kind)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
    home = Path(tempfile.mkdtemp(prefix="attest-paused-home-"))
    env = {k: v for k, v in os.environ.items() if k not in ("NEBIUS_API_KEY", "CODEX_API_KEY", "TAVILY_API_KEY") and not k.startswith("ATTEST_")}
    env.update({"HOME": str(home), "ATTEST_SECRETS_NOTES": str(home / "none.json"), "ATTEST_DATA_DIR": str(data), "ATTEST_IMPORT_DIRS": str(data / "none"),
                "ATTEST_ADMIN_TOKEN": secrets.token_hex(12), "NO_PROXY": "*"})
    python = os.environ.get("ATTEST_AUDIT_SERVER_PYTHON") or sys.executable
    server = subprocess.Popen([python, "-m", "uvicorn", "attest.app.server:app", "--host", "127.0.0.1", "--port", str(port)], cwd=str(ROOT), env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    state = {"widths": {}}
    try:
        for _ in range(120):
            try:
                state["health"] = json.loads(urllib.request.urlopen(base + "/api/health", timeout=2).read())["reconciliation"]; break
            except Exception:
                time.sleep(0.5)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            for width in (320, 390, 768, 1024, 1440):
                mobile = width <= 390
                context = browser.new_context(viewport={"width": width, "height": 844 if mobile else 900}, is_mobile=mobile, has_touch=mobile,
                                              device_scale_factor=3 if mobile else 1, service_workers="block")
                page = context.new_page()
                seen = {"get": 0, "aborted": 0}

                def route(r, request, seen=seen):
                    if request.method in ("GET", "HEAD"):
                        seen["get"] += 1; r.continue_()
                    else:
                        seen["aborted"] += 1; r.abort()
                page.route("**/*", route)
                page.goto(base + "/", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_function("document.querySelector('#chip-runs-text') && document.querySelector('#chip-runs-text').textContent !== 'loading'", timeout=60000)
                page.wait_for_timeout(800)
                page.evaluate("() => { const r = document.querySelector('input[name=mode][value=live]'); r.click(); }")
                page.wait_for_timeout(400)
                facts = page.evaluate("""() => {
                  const vw = document.documentElement.clientWidth;
                  const wide = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
                    return cs.display !== 'none' && cs.visibility !== 'hidden' && r.width > 0 && (r.right > vw + 0.5 || r.left < -0.5) && !e.closest('[hidden],.backdrop,.skip'); });
                  return {vw, scroll_width: document.documentElement.scrollWidth, wider_than_viewport: wide.length,
                          chip: document.querySelector('#chip-runs-text').textContent, go_disabled: document.querySelector('#go').disabled,
                          go_text: document.querySelector('#go').textContent, estimate: document.querySelector('#estimate').innerText.slice(0, 400)};
                }""")
                page.screenshot(path=str(out / f"paused-{kind}-{width}.png"), full_page=False)
                facts.update(requests=seen)
                state["widths"][str(width)] = facts
                context.close()
            browser.close()
    finally:
        server.terminate()
        shutil.rmtree(data, ignore_errors=True); shutil.rmtree(home, ignore_errors=True)
    state["ok"] = all(w["wider_than_viewport"] == 0 and w["scroll_width"] <= w["vw"] and w["chip"] == "paused for reconciliation" and w["go_disabled"]
                      and "New runs are paused" in w["estimate"] and w["requests"]["aborted"] == 0 for w in state["widths"].values())
    report["states"][kind] = state
report["ok"] = all(s["ok"] for s in report["states"].values())
(out / "paused-state-check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: {"ok": v["ok"], "health": v.get("health"), "widths": {w: {kk: f[kk] for kk in ("chip", "go_disabled", "wider_than_viewport", "requests")} for w, f in v["widths"].items()}} for k, v in report["states"].items()}, indent=1))
