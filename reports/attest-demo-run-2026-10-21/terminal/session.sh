#!/bin/bash
# A real terminal session for the film: each command is typed at a human pace, then really run. Usage: session.sh <bundle.zip>
ZIP="$1"
type_run() {
  printf '\033[1;38;5;191m$\033[0m '
  local s="$1" i
  for ((i = 0; i < ${#s}; i++)); do printf '%s' "${s:i:1}"; sleep 0.035; done
  sleep 0.35; printf '\n'
  eval "$1"
  sleep 0.9
}
cd "$(dirname "$0")/work"
sleep 0.8
type_run "git clone https://github.com/a252937166/attest"
type_run "cd attest"
type_run "python3 -m attest check ../$(basename "$ZIP")"
sleep 2.5
