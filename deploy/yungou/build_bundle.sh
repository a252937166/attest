#!/bin/bash
# Build app.tar.gz for the server from the public export (run it inside dist/public): package, examples, deploy files,
# tests, docs and redacted evidence reports. No run data, venv, screenshots, snapshots or secrets.
set -euo pipefail
cd "$(dirname "$0")/../.."
out=${1:-/tmp/attest-app.tar.gz}
# Excluded on purpose: development screenshots and browser captures (reports/*/screens, refresh-sequence), batch source
# snapshots (reproducible from the recorded digests), downloaded bundle zips, run data, virtualenvs, caches and any env file.
# Note: tar --exclude matches a name at any depth, so the top-level run data is kept out by not listing it, never by
# excluding 'runs' (that used to drop every reports/**/runs evidence directory as well).
tar -czf "$out" \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='.impeccable' --exclude='*.env' \
  --exclude='screens' --exclude='refresh-sequence' --exclude='snapshot' --exclude='*.zip' --exclude='*.png' \
  attest examples deploy tests reports pyproject.toml README.md LICENSE PILOT.md PILOT_FEEDBACK.md METHOD.md attest-console.md \
  attest-first-slice.md attest-product-design.md
echo "bundle: $out ($(du -h "$out" | cut -f1))"
tar -tzf "$out" | grep -E '\.env$|cxk_|tvly-|\.png$|/screens/|/snapshot/' && { echo "EXCLUDED CONTENT IN BUNDLE"; exit 1; } || echo "no secret-like paths, no screenshots, no snapshots"
