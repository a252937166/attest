#!/bin/bash
set -u
cd "$(dirname "$0")/.."
run() { python3 -m attest run --task "examples/$1/task.json" --out runs --provider "$2" --usd-cap 0.6 --max-turns "$3" > "runs/$4.log" 2>&1; echo "exit=$?" >> "runs/$4.log"; echo "$(date -u +%H:%M:%S) done $4 ($(grep -oE 'verdict [A-Z ]+' "runs/$4.log" | tail -1))"; }
run semver-is-compatible codex 14 p3-semver-codex
run semver-is-compatible-v2 nebius 14 p3-semver-v2-nebius
echo "CHAIN3 DONE"
