#!/bin/bash
# Sequential evidence runs across both profiles; each run logs to runs/<label>.log with its exit code appended.
set -u
cd "$(dirname "$0")/.."
run() {  # task-dir provider max-turns label
  python3 -m attest run --task "examples/$1/task.json" --out runs --provider "$2" --usd-cap 0.6 --max-turns "$3" > "runs/$4.log" 2>&1
  echo "exit=$?" >> "runs/$4.log"
  echo "$(date -u +%H:%M:%S) done $4 ($(grep -oE 'verdict [A-Z ]+' "runs/$4.log" | tail -1))"
}
run durationkit-task codex 12 p2-durationkit-codex
run durationkit-task nebius 12 p2-durationkit-nebius
run semver-is-compatible codex 14 p2-semver-codex
run semver-is-compatible nebius 14 p2-semver-nebius
run semver-is-compatible-v2 nebius 14 p2-semver-v2-nebius
echo "CHAIN2 DONE"
