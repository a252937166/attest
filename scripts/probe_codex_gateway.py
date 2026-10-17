#!/usr/bin/env python3
"""Probe the existing Codex gateway without storing credentials or retrying inference."""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def tls_context():
    """Use trusted CA certificates; never disable certificate verification."""
    configured = os.environ.get("SSL_CERT_FILE")
    if configured:
        return ssl.create_default_context(cafile=configured), "SSL_CERT_FILE"
    paths = ssl.get_default_verify_paths()
    if paths.cafile or paths.capath:
        return ssl.create_default_context(), "python-default"
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where()), "certifi"
    except ImportError:
        if Path("/etc/ssl/cert.pem").is_file():
            return ssl.create_default_context(cafile="/etc/ssl/cert.pem"), "system-ca-file"
        return ssl.create_default_context(), "python-default"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://development-gateway.invalid")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="Make three minimal inference calls.")
    args = parser.parse_args()
    key = os.environ.get("CODEX_API_KEY", "")
    if not key:
        parser.error("Set CODEX_API_KEY in the process environment; do not pass it as an argument.")
    parsed = urllib.parse.urlsplit(args.base_url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error("The base URL must be HTTPS without embedded credentials, query, or fragment.")
    base = args.base_url.rstrip("/")
    origin = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    context, ca_source = tls_context()
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=context))
    report = {
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_url": base,
        "tls_verification": True,
        "ca_source": ca_source,
        "automatic_inference_retries": False,
        "live_inference_requested": args.live,
        "checks": [],
    }

    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if key in text:
            raise RuntimeError("Refusing to write a report containing the credential.")
        args.output.write_text(text)

    def request(name, path, payload=None, public=False):
        started = time.monotonic()
        url = origin + "/health" if public else base + path
        headers = {"Accept": "application/json"}
        if not public:
            headers["Authorization"] = "Bearer " + key
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        req = urllib.request.Request(url, headers=headers, data=data)
        record = {"name": name, "method": req.get_method(), "path": "/health" if public else "/v1" + path}
        if payload is not None:
            record["request"] = payload
        print(json.dumps({"starting": name}), flush=True)
        body = None
        try:
            try:
                response = opener.open(req, timeout=150 if payload else 25)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                record["http_status"] = response.code
                raw = response.read(1_000_000).decode("utf-8", errors="replace")
                body = json.loads(raw)
                if name == "status":
                    record["response"] = {
                        k: body.get(k) for k in ["defaults", "streaming", "running", "waiting", "expected_runtime_s"]
                    }
                else:
                    record["response"] = body
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            record["error_type"] = type(error).__name__
            record["error"] = str(error).replace(key, "[REDACTED]")[:300]
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["checks"].append(record)
        save()
        print(json.dumps({"completed": name, "http_status": record.get("http_status"), "elapsed_seconds": record["elapsed_seconds"]}), flush=True)
        return record, body

    health, _ = request("health", "", public=True)
    status, _ = request("status", "/status")
    catalog_record, catalog = request("models", "/models")
    preflight_passed = all(record.get("http_status") == 200 for record in [health, status, catalog_record])
    if not args.live:
        report["preflight_passed"] = preflight_passed
        save()
        print(json.dumps({"report": str(args.output), "mode": "preflight-only", "passed": preflight_passed}), flush=True)
        if not preflight_passed:
            raise SystemExit(1)
        return
    if not preflight_passed:
        report["live_inference_skipped"] = "Preflight failed; no inference requests were attempted."
        save()
        raise SystemExit(1)

    for name, payload in [
        ("reject_stream", {"messages": [{"role": "user", "content": "Return OK."}], "stream": True}),
        ("reject_effort_conflict", {"messages": [{"role": "user", "content": "Return OK."}], "effort": "low", "reasoning_effort": "high"}),
        ("reject_model_format", {"messages": [{"role": "user", "content": "Return OK."}], "model": "nvidia/not-a-codex-model"}),
    ]:
        record, _ = request(name, "/chat/completions", payload)
        record["passed"] = record.get("http_status") == 400
        save()

    available = {item.get("id"): item for item in (catalog or {}).get("data", [])}
    schema = {"type": "object", "properties": {"result": {"type": "integer", "enum": [4]}}, "required": ["result"], "additionalProperties": False}
    live_cases = [
        ("luna_chat", "/chat/completions", "gpt-6-luna", {"messages": [{"role": "user", "content": "Return exactly OK, with no punctuation or formatting."}], "effort": "low", "stream": False}),
        ("sol_chat_effort_alias", "/chat/completions", "gpt-6-sol", {"messages": [{"role": "user", "content": "Return exactly OK, with no punctuation or formatting."}], "reasoning_effort": "low", "stream": False}),
        ("astra_run_schema", "/run", "gpt-6-astra", {"prompt": "Compute 2 + 2. Return a JSON object with the integer field result, and no other fields.", "effort": "low", "output_schema": schema}),
    ]
    for name, route, model, payload in live_cases:
        metadata = available.get(model)
        efforts = metadata.get("supported_reasoning_efforts", []) if metadata else []
        if not metadata or (efforts and "low" not in efforts):
            report["checks"].append({"name": name, "model": model, "skipped": "Requested combination absent from current cached catalog; no request sent."})
            save()
            continue
        payload.update({"model": model, "timeout_s": 100, "deadline_s": 130})
        record, body = request(name, route, payload)
        selected = isinstance(body, dict) and body.get("model") == model and body.get("effort") == "low"
        if route == "/run":
            output_ok = isinstance(body, dict) and body.get("json") == {"result": 4}
        else:
            choices = body.get("choices", []) if isinstance(body, dict) else []
            output_ok = bool(choices) and choices[0].get("message", {}).get("content", "").strip() == "OK"
        record["checks"] = {"http_200": record.get("http_status") == 200, "requested_selection_echoed": selected, "expected_output": output_ok}
        record["passed"] = all(record["checks"].values())
        save()
    report["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["scope"] = "Availability and request-contract checks only; no comparative model-quality benchmark or independent backend identity attestation."
    save()
    skipped = sum("skipped" in c for c in report["checks"])
    print(json.dumps({"report": str(args.output), "passed": sum(c.get("passed") is True for c in report["checks"]), "failed": sum(c.get("passed") is False for c in report["checks"]), "skipped": skipped}), flush=True)
    if any(c.get("passed") is False for c in report["checks"]):
        raise SystemExit(1)
    if skipped:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
