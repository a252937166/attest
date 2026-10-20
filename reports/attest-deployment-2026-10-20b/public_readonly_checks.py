"""Read-only checks of the public console after the 0.10.0 deployment: GET requests only, nothing else is ever sent.
Usage: public_readonly_checks.py <release tree> <out.json> [base URL]"""
import hashlib, json, ssl, sys, urllib.request
from pathlib import Path

tree, out = Path(sys.argv[1]), Path(sys.argv[2])
base = sys.argv[3] if len(sys.argv) > 3 else "https://attest.axiqo.xyz"
try:
    import certifi
    tls = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    tls = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=tls))


def get(path):
    req = urllib.request.Request(base + path, method="GET", headers={"User-Agent": "attest-readonly-check"})
    with opener.open(req, timeout=30) as resp:
        return resp.status, resp.read()


report, gateway_mentions = {"base": base, "method": "GET only", "checks": {}}, 0
static = {"/": "attest/app/static/index.html", "/static/app.js?v=20261020b": "attest/app/static/app.js",
          "/static/styles.css?v=20261020b": "attest/app/static/styles.css"}
for path, rel in static.items():
    status, body = get(path)
    same = hashlib.sha256(body).hexdigest() == hashlib.sha256((tree / rel).read_bytes()).hexdigest()
    report["checks"][path] = {"status": status, "bytes": len(body), "identical_to_release": same}
    gateway_mentions += body.lower().count(b"codex")
status, body = get("/api/health"); health = json.loads(body)
report["checks"]["/api/health"] = {"status": status, "version": health.get("version"), "worker_alive": health.get("worker_alive"),
                                   "ready": health.get("ready"), "busy": health.get("busy"), "queue": health.get("queue"),
                                   "budget": health.get("budget", {}).get("detail"), "reserved_usd": health.get("budget", {}).get("reserved_usd"),
                                   "active_runs": health.get("budget", {}).get("active_runs"), "data_dir_exposed": "data_dir" in health,
                                   "reconciliation": health.get("reconciliation")}
gateway_mentions += body.lower().count(b"codex")
status, body = get("/api/profiles"); prof = json.loads(body)
report["checks"]["/api/profiles"] = {"status": status, "profiles": [p.get("id") for p in prof.get("profiles", [])], "team": prof.get("team")}
gateway_mentions += body.lower().count(b"codex")
status, body = get("/api/runs?limit=200"); runs = json.loads(body)["runs"]
forbidden = sorted({k for r in runs for k in r if k in ("requester", "out_dir", "error", "error_detail")})
report["checks"]["/api/runs"] = {"status": status, "rows": len(runs), "forbidden_keys": forbidden, "providers": sorted({r.get("provider") for r in runs})}
gateway_mentions += body.lower().count(b"codex")
status, body = get("/api/openapi.json"); api = json.loads(body)
schema = api["components"]["schemas"]["RunRequest"]
post = api["paths"]["/api/runs"]["post"]
report["checks"]["/api/openapi.json"] = {"status": status, "RunRequest_additionalProperties": schema.get("additionalProperties"),
                                         "required": sorted(schema.get("required", [])), "provider_default": "default" in schema["properties"]["provider"],
                                         "confirmation_header_documented": any(p.get("in") == "header" and p.get("name", "").lower() == "x-attest-confirm" for p in post.get("parameters", []))}
gateway_mentions += body.lower().count(b"codex")
rid = next((r["run_id"] for r in runs if r.get("verdict") == "VERIFIED"), runs[0]["run_id"])
status, body = get("/runs/" + rid)
report["checks"]["/runs/<id>"] = {"status": status, "run_id": rid, "same_page_as_home": hashlib.sha256(body).hexdigest() == hashlib.sha256((tree / static["/"]).read_bytes()).hexdigest()}
report["gateway_name_in_responses"] = gateway_mentions
out.write_text(json.dumps(report, indent=1) + "\n")
print(json.dumps(report, indent=1))
