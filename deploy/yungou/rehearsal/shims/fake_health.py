#!/usr/bin/env python3
"""Rehearsal stand-in for the Attest service: answers GET /api/health with the shape of attest.app.server.health, reporting the
version of the tree --app-link pointed at when the server started (like the real process, which loads its code once), and
optionally misreporting the version or a dead worker for one specific tree version (failure injection). Python 3.6 compatible."""
import argparse
import datetime
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


def tree_version(app_link):
    try:
        with open(os.path.join(app_link, "attest", "__init__.py"), encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return None
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--app-link", required=True)
    parser.add_argument("--misreport-version", default=None, help="when the tree has this version, report 9.9.9-misreported instead")
    parser.add_argument("--dead-worker-version", default=None, help="when the tree has this version, report worker_alive false")
    args = parser.parse_args()
    served_tree = os.path.realpath(args.app_link)
    version = tree_version(args.app_link)
    reported = "9.9.9-misreported" if args.misreport_version and version == args.misreport_version else version
    worker_alive = not (args.dead_worker_version and version == args.dead_worker_version)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] != "/api/health":
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps({"ok": True, "version": reported, "worker_alive": worker_alive, "queue": 0, "current": None,
                               "data_dir": "(rehearsal)", "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               "disk": {"free_mb": 1000, "free_frac": 0.5, "low": False, "accepting_runs": True},
                               "rehearsal": True, "served_tree": served_tree}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *values):
            sys.stderr.write("%s fake-health %s\n" % (datetime.datetime.utcnow().isoformat(), fmt % values))

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    sys.stderr.write("%s fake-health serving %s (tree %s, version %s, reported %s, worker_alive %s) on port %d\n" % (
        datetime.datetime.utcnow().isoformat(), args.app_link, served_tree, version, reported, worker_alive, args.port))
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
