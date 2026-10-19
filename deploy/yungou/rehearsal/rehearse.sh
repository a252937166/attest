#!/bin/bash
# Isolated deployment rehearsal for the OPS-01/02/03 repairs (19 Oct 2026 audit). Runs install.sh, rollback.sh and
# decommission.sh against throwaway roots under the shims in ./shims (systemctl, nginx-modern, useradd, chown, install and the
# interpreter) with a fake health server; nothing under /opt, /etc, /var or systemd is touched, no user is created, no network is
# used. The fake releases are built with build_bundle.sh from copies of a real tree (the public export) carrying synthetic
# versions, with the deploy/yungou directory under test copied over each tree.
#
#   deploy/yungou/rehearsal/rehearse.sh --source dist/public [--root DIR] [--python /usr/bin/python3.11] [--logs-out DIR] [--keep]
#
# Scenarios: (1) clean install; (2) second install keeps the previous release; (3) dependency installation failure; (4) health
# failure (the service answers with another version); (5) nginx -t failure; (6) rollback to the previous release with digest
# readback; (7) decommission refuses without --yes, executes with it; (8) migration from the real-directory layout with a shared
# venv, then rollback to the legacy release; (9) a tampered RELEASE.json entry is refused. The root is removed at the end
# (--keep keeps it); logs, summary.txt and summary.json are copied to --logs-out. Exit status is non-zero when a check fails.
# bash 3.2 compatible.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DEPLOY_SRC=$(cd "$HERE/.." && pwd)
SHIMS="$HERE/shims"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SOURCE=""; ROOT=""; REAL_PYTHON=""; LOGS_OUT=""; KEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SOURCE=$2; shift 2 ;;
    --root) ROOT=$2; shift 2 ;;
    --python) REAL_PYTHON=$2; shift 2 ;;
    --logs-out) LOGS_OUT=$2; shift 2 ;;
    --keep) KEEP=1; shift ;;
    -h|--help) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$SOURCE" ] && [ -d "$SOURCE/attest" ] || { echo "--source must be a tree containing attest/ (for example dist/public)" >&2; exit 2; }
SOURCE=$(cd "$SOURCE" && pwd)
REAL_PYTHON=${REAL_PYTHON:-$(command -v python3)}
ROOT=${ROOT:-${TMPDIR:-/tmp}/attest-rehearsal-$STAMP}
mkdir -p "$ROOT"
ROOT=$(cd "$ROOT" && pwd)
LOGS="$ROOT/logs"
mkdir -p "$LOGS" "$ROOT/state" "$ROOT/tmp" "$ROOT/work" "$ROOT/deploy"
PORT=$("$REAL_PYTHON" -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')

# Parameters of the scripts under test, shared by every scenario; the per-root paths come from with_root.
export REHEARSAL_DIR="$ROOT" REHEARSAL_SHIMS="$SHIMS" REHEARSAL_REAL_PYTHON="$REAL_PYTHON" REHEARSAL_HEALTH_PORT="$PORT"
export PYTHON_BIN="$SHIMS/python3.12" SYSTEMCTL="$SHIMS/systemctl" NGINX_BIN="$SHIMS/nginx-modern" USERADD="$SHIMS/useradd" CHOWN="$SHIMS/chown" INSTALL="$SHIMS/install"
export HEALTH_URL="http://127.0.0.1:$PORT/api/health" HEALTH_DEADLINE_SECONDS=15 HEALTH_POLL_SECONDS=0.5 MEMORY_MAX=200M TMPDIR="$ROOT/tmp" PYTHON="$REAL_PYTHON"
export CGROUP_MEMORY_DIR="$ROOT/fake-cgroup/memory" PROC_DIR="$ROOT/fake-proc"   # revision 8: written by the systemctl shim as systemd 219 would

{
  echo "rehearsal $STAMP"
  echo "host: $(hostname)  uname: $(uname -srm)"
  echo "bash: $BASH_VERSION  real python: $REAL_PYTHON ($("$REAL_PYTHON" --version 2>&1))  tar: $(tar --version 2>&1 | head -1)"
  echo "source tree: $SOURCE  scripts under test: $DEPLOY_SRC  root: $ROOT  health port: $PORT"
  echo "user: $(id -un) (uid $(id -u)); nothing under /opt, /etc, /var or systemd is touched"
} | tee "$LOGS/environment.txt"

make_root() {   # make_root NAME: a fake host tree; prints its path
  local r="$ROOT/$1"
  mkdir -p "$r/opt/attest" "$r/etc/systemd/system" "$r/etc/nginx/conf.d" "$r/etc/attest" "$r/var/lib/attest" "$r/var/www/letsencrypt"
  printf '%s\n' "$r"
}

with_root() {   # with_root ROOT COMMAND...: run with the script parameters pointed at that fake host tree
  local r=$1; shift
  ATTEST_ROOT="$r/opt/attest" SYSTEMD_UNIT_DIR="$r/etc/systemd/system" NGINX_CONF_DIR="$r/etc/nginx/conf.d" ATTEST_ENV_DIR="$r/etc/attest" \
  ATTEST_DATA_DIR="$r/var/lib/attest" LETSENCRYPT_LIVE="$r/etc/letsencrypt/live/attest.axiqo.xyz" LETSENCRYPT_WEBROOT="$r/var/www/letsencrypt" \
  REHEARSAL_APP_LINK="$r/opt/attest/app" "$@"
}

make_tree() {   # make_tree NAME VERSION: copy of the source tree (no .git) with the deploy dir under test and a synthetic version
  local t="$ROOT/work/$1"
  mkdir -p "$t"
  (cd "$SOURCE" && COPYFILE_DISABLE=1 tar -cf - --exclude=.git --exclude=__pycache__ --exclude='._*' .) | (cd "$t" && tar -xf -)
  rm -rf "$t/deploy/yungou"
  mkdir -p "$t/deploy"
  cp -R "$DEPLOY_SRC" "$t/deploy/yungou"
  sed "s/^__version__ = .*/__version__ = \"$2\"/" "$t/attest/__init__.py" > "$t/attest/__init__.py.new"
  mv "$t/attest/__init__.py.new" "$t/attest/__init__.py"
  printf '%s\n' "$t"
}

build_bundle() {   # build_bundle NAME: app bundle of the tree NAME; prints the release label
  local t="$ROOT/work/$1"
  bash "$t/deploy/yungou/build_bundle.sh" "$ROOT/work/$1.tar.gz" > "$LOGS/build-$1.log" 2>&1 || { cat "$LOGS/build-$1.log" >&2; echo "build of $1 failed" >&2; exit 1; }
  sed -n 's/.*label \([^,]*\),.*/\1/p' "$LOGS/build-$1.log"
}

# ---- state probes (run under with_root) --------------------------------------------------------------------------------------
active_label() { if [ -L "$ATTEST_ROOT/app" ]; then basename "$(readlink "$ATTEST_ROOT/app")"; elif [ -d "$ATTEST_ROOT/app" ]; then echo REAL-DIRECTORY; else echo none; fi; }
prev_label() { if [ -L "$ATTEST_ROOT/app.prev" ]; then basename "$(readlink "$ATTEST_ROOT/app.prev")"; elif [ -d "$ATTEST_ROOT/app.prev" ]; then echo REAL-DIRECTORY; else echo none; fi; }
served() {
  "$REAL_PYTHON" -c 'import json, sys, urllib.request
try:
    data = json.load(urllib.request.urlopen(sys.argv[1], timeout=3))
    print("%s worker_alive=%s" % (data.get("version"), data.get("worker_alive")))
except Exception:
    print("unreachable")' "$HEALTH_URL"
}
service_state() { "$SYSTEMCTL" is-active attest.service 2>/dev/null || true; }
state_lines() {
  echo "active: $(active_label)"
  echo "previous: $(prev_label)"
  echo "service: $(service_state)"
  echo "health: $(served)"
  echo "releases: $(ls -1 "$ATTEST_ROOT/releases" 2>/dev/null | tr '\n' ' ')"
  echo "vhost files: $(ls -1 "$NGINX_CONF_DIR" 2>/dev/null | tr '\n' ' ')"
  echo "unit files: $(ls -1 "$SYSTEMD_UNIT_DIR" 2>/dev/null | tr '\n' ' ')"
}

# ---- scenario bookkeeping -----------------------------------------------------------------------------------------------------
SUMMARY="$LOGS/summary.txt"; : > "$SUMMARY"
RESULTS="$ROOT/state/results.tsv"; : > "$RESULTS"
FAILED_SCENARIOS=0; CURRENT_LOG=""; CHECKS_FAILED=0; LAST_RC=0

run_scenario() {   # run_scenario N SLUG EXPECTED_RC ROOT COMMAND...: run the command from the fake deploy directory, record the state
  local n=$1 slug=$2 want=$3 r=$4; shift 4
  CURRENT_LOG="$LOGS/scenario-$n-$slug.log"; CHECKS_FAILED=0
  { echo "=== scenario $n: $slug"; echo "=== command: $*"; echo "=== expected exit code: $want"; echo "=== state before:"; with_root "$r" state_lines; echo; echo "=== output:"; } > "$CURRENT_LOG" 2>&1
  set +e
  (cd "$ROOT/deploy" && with_root "$r" "$@") >> "$CURRENT_LOG" 2>&1
  LAST_RC=$?
  set -e
  { echo; echo "=== exit code: $LAST_RC (expected $want)"; echo "=== state after:"; with_root "$r" state_lines; echo; echo "=== checks:"; } >> "$CURRENT_LOG" 2>&1
  expect "exit code" "$LAST_RC" "$want"
}
expect() {   # expect DESCRIPTION ACTUAL WANTED
  if [ "$2" = "$3" ]; then printf '  PASS  %s: %s\n' "$1" "$2" | tee -a "$CURRENT_LOG"; else printf '  FAIL  %s: got "%s", expected "%s"\n' "$1" "$2" "$3" | tee -a "$CURRENT_LOG"; CHECKS_FAILED=1; fi
}
expect_log() {   # expect_log DESCRIPTION PATTERN present|absent
  local hits; hits=$(grep -c -- "$2" "$CURRENT_LOG" || true)
  if [ "$3" = present ]; then expect "$1 (log contains '$2')" "$([ "$hits" -gt 0 ] && echo yes || echo no)" yes
  else expect "$1 (log free of '$2')" "$([ "$hits" -gt 0 ] && echo no || echo yes)" yes; fi
}
finish_scenario() {   # finish_scenario N SLUG TITLE
  local verdict=PASS; [ "$CHECKS_FAILED" = 0 ] || { verdict=FAIL; FAILED_SCENARIOS=$((FAILED_SCENARIOS + 1)); }
  printf '%s  scenario %s  %-32s exit %s  %s\n' "$verdict" "$1" "$2" "$LAST_RC" "$3" | tee -a "$SUMMARY"
  printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$verdict" "$LAST_RC" "$3" >> "$RESULTS"
  echo "=== verdict: $verdict" >> "$CURRENT_LOG"
}
shim_lines() { grep -c -- "$1" "$LOGS/shim-calls.log" 2>/dev/null || true; }

# ---- fixtures ---------------------------------------------------------------------------------------------------------------------
echo; echo "building the fake releases from $SOURCE (synthetic versions 9.0.1/9.0.2/9.0.3-rehearsal; 9.0.0 for the legacy previous tree)"
TREE_A=$(make_tree a 9.0.1-rehearsal); LABEL_A=$(build_bundle a); echo "  a: $LABEL_A"
TREE_B=$(make_tree b 9.0.2-rehearsal); LABEL_B=$(build_bundle b); echo "  b: $LABEL_B"
TREE_C=$(make_tree c 9.0.3-rehearsal); LABEL_C=$(build_bundle c); echo "  c: $LABEL_C"
TREE_Z=$(make_tree z 9.0.0-rehearsal); echo "  z: legacy previous tree (version 9.0.0-rehearsal)"
DIGEST_A=$(sed -n 's/.*package digest \([0-9a-f]*\).*/\1/p' "$LOGS/build-a.log")
# the fake /var/tmp/attest-deploy: scripts, unit, vhost and a synthetic secrets file (placeholders only)
cp "$DEPLOY_SRC/install.sh" "$DEPLOY_SRC/rollback.sh" "$DEPLOY_SRC/decommission.sh" "$DEPLOY_SRC/snapshot.sh" "$DEPLOY_SRC/attest.service" "$DEPLOY_SRC/attest.axiqo.xyz.conf" "$ROOT/deploy/"
printf '%s=placeholder\n' NEBIUS_API_KEY ATTEST_ADMIN_TOKEN > "$ROOT/deploy/attest.env"   # short synthetic values, never echoed
R1=$(make_root fake-host)

# ---- scenario 1: clean install -----------------------------------------------------------------------------------------------
run_scenario 1 clean-install 0 "$R1" bash install.sh "$ROOT/work/a.tar.gz"
expect "active release" "$(with_root "$R1" active_label)" "$LABEL_A"
expect "previous release" "$(with_root "$R1" prev_label)" none
expect "served health" "$(served)" "9.0.1-rehearsal worker_alive=True"
expect_log "completion line" "install complete" present
expect "unit starts the release interpreter" "$(grep -c 'ExecStart=/opt/attest/app/venv/bin/python' "$R1/etc/systemd/system/attest.service" || true)" 1
expect "http-only vhost rendered" "$(grep -c 'proxy_pass http://127.0.0.1:4070;' "$R1/etc/nginx/conf.d/attest.axiqo.xyz.conf" || true)" 1
expect "INSTALLED.json written" "$([ -f "$R1/opt/attest/releases/$LABEL_A/INSTALLED.json" ] && echo yes || echo no)" yes
finish_scenario 1 clean-install "install of $LABEL_A on an empty root"

# ---- scenario 2: second install keeps the previous release ----------------------------------------------------------------
run_scenario 2 second-install 0 "$R1" bash install.sh "$ROOT/work/b.tar.gz"
expect "active release" "$(with_root "$R1" active_label)" "$LABEL_B"
expect "previous release" "$(with_root "$R1" prev_label)" "$LABEL_A"
expect "previous release directory kept" "$([ -d "$R1/opt/attest/releases/$LABEL_A/venv" ] && echo yes || echo no)" yes
expect "served health" "$(served)" "9.0.2-rehearsal worker_alive=True"
expect_log "vhost unchanged" "vhost unchanged; nginx is not touched" present
finish_scenario 2 second-install "install of $LABEL_B keeps $LABEL_A as previous"

# ---- scenario 3: dependency installation failure --------------------------------------------------------------------------------
run_scenario 3 pip-failure 1 "$R1" env REHEARSAL_PIP_FAIL=1 bash install.sh "$ROOT/work/c.tar.gz"
expect "active release unchanged" "$(with_root "$R1" active_label)" "$LABEL_B"
expect "previous release unchanged" "$(with_root "$R1" prev_label)" "$LABEL_A"
expect "served health" "$(served)" "9.0.2-rehearsal worker_alive=True"
expect "failed release directory removed" "$([ -e "$R1/opt/attest/releases/$LABEL_C" ] && echo present || echo absent)" absent
expect_log "failure reported" "INSTALL FAILED" present
expect_log "cause reported" "dependency installation failed" present
expect_log "no completion line" "install complete" absent
expect_log "active release confirmed healthy" "is healthy" present
finish_scenario 3 pip-failure "pip exits 1: refused before the switch, $LABEL_B keeps serving"

# ---- scenario 4: health failure (wrong version) ----------------------------------------------------------------------------------
run_scenario 4 health-failure 1 "$R1" env REHEARSAL_HEALTH_BAD_VERSION=9.0.3-rehearsal bash install.sh "$ROOT/work/c.tar.gz"
expect "active release restored" "$(with_root "$R1" active_label)" "$LABEL_B"
expect "previous release restored" "$(with_root "$R1" prev_label)" "$LABEL_A"
expect "served health" "$(served)" "9.0.2-rehearsal worker_alive=True"
expect_log "wrong version detected" "the service serves another version" present
expect_log "previous release re-selected" "previous release re-selected" present
expect_log "previous release healthy" "is healthy" present
expect_log "no completion line" "install complete" absent
finish_scenario 4 health-failure "service answers 9.9.9-misreported: switched back to $LABEL_B"

# ---- scenario 5: nginx -t failure ---------------------------------------------------------------------------------------------------
cp "$R1/etc/nginx/conf.d/attest.axiqo.xyz.conf" "$ROOT/state/vhost-before-5.conf"
# the change must sit inside the first server block: the http-only rendering keeps only that block
awk '{print} /listen 80;/{print "    # rehearsal: vhost change that makes the nginx test run"}' "$ROOT/deploy/attest.axiqo.xyz.conf" > "$ROOT/deploy/vhost.changed"
mv "$ROOT/deploy/vhost.changed" "$ROOT/deploy/attest.axiqo.xyz.conf"
run_scenario 5 nginx-test-failure 1 "$R1" env REHEARSAL_NGINX_T_FAIL=1 bash install.sh "$ROOT/work/c.tar.gz"
expect "active release unchanged" "$(with_root "$R1" active_label)" "$LABEL_B"
expect "served health" "$(served)" "9.0.2-rehearsal worker_alive=True"
expect "vhost restored byte for byte" "$(cmp -s "$R1/etc/nginx/conf.d/attest.axiqo.xyz.conf" "$ROOT/state/vhost-before-5.conf" && echo yes || echo no)" yes
expect_log "nginx failure reported" "nginx -t failed" present
expect_log "vhost restore reported" "vhost restored" present
expect_log "no nginx reload" "nginx reloaded with the new vhost" absent
expect_log "no completion line" "install complete" absent
finish_scenario 5 nginx-test-failure "nginx -t exits 1: vhost restored, $LABEL_B keeps serving"

# ---- scenario 6: rollback --------------------------------------------------------------------------------------------------------------
nginx_calls_before=$(shim_lines nginx-modern); reload_calls_before=$(shim_lines "systemctl reload")
run_scenario 6 rollback 0 "$R1" bash rollback.sh
expect "active release" "$(with_root "$R1" active_label)" "$LABEL_A"
expect "previous release" "$(with_root "$R1" prev_label)" "$LABEL_B"
expect "served health" "$(served)" "9.0.1-rehearsal worker_alive=True"
expect_log "digest readback" "attest_revision() digest $DIGEST_A" present
expect_log "completion line" "rollback complete" present
expect "nginx binary never called during the rollback" "$(( $(shim_lines nginx-modern) - nginx_calls_before ))" 0
expect "nginx never reloaded during the rollback" "$(( $(shim_lines "systemctl reload") - reload_calls_before ))" 0
finish_scenario 6 rollback "rollback.sh re-selects $LABEL_A, digest read back, nginx untouched"
(cd "$ROOT/deploy" && with_root "$R1" bash rollback.sh --list) > "$LOGS/scenario-6-rollback-list.log" 2>&1 || true

# ---- scenario 9: tampered RELEASE.json entry (run before the decommission so the service is still up) -----------------------------
mkdir -p "$ROOT/work/tamper" && tar -xzf "$ROOT/work/c.tar.gz" -C "$ROOT/work/tamper"
printf '\nrehearsal: a line appended after the manifest was written\n' >> "$ROOT/work/tamper/README.md"
(cd "$ROOT/work/tamper" && COPYFILE_DISABLE=1 tar -czf "$ROOT/work/c-tampered.tar.gz" .)
run_scenario 9 tampered-manifest 1 "$R1" bash install.sh "$ROOT/work/c-tampered.tar.gz"
expect "active release unchanged" "$(with_root "$R1" active_label)" "$LABEL_A"
expect "served health" "$(served)" "9.0.1-rehearsal worker_alive=True"
expect_log "mismatch reported" "mismatch: README.md" present
expect_log "release refused" "the release is refused" present
expect_log "no completion line" "install complete" absent
finish_scenario 9 tampered-manifest "README.md changed after build: RELEASE.json verification refuses the release"

# ---- scenario 7: decommission refuses without --yes, executes with it ---------------------------------------------------------------
run_scenario 7 decommission-refused 2 "$R1" bash decommission.sh
expect "service still active" "$(with_root "$R1" service_state)" active
expect "vhost still present" "$([ -f "$R1/etc/nginx/conf.d/attest.axiqo.xyz.conf" ] && echo yes || echo no)" yes
expect_log "refusal printed" "refusing: pass --yes" present
expect_log "plan printed" "decommission.sh will:" present
finish_scenario 7 decommission-refused "decommission.sh without --yes prints the plan and changes nothing"
run_scenario 7b decommission-yes 0 "$R1" bash decommission.sh --yes
expect "service stopped" "$(with_root "$R1" service_state)" inactive
expect "vhost removed" "$([ -f "$R1/etc/nginx/conf.d/attest.axiqo.xyz.conf" ] && echo yes || echo no)" no
expect "releases kept" "$([ -d "$R1/opt/attest/releases/$LABEL_A" ] && [ -d "$R1/opt/attest/releases/$LABEL_B" ] && echo yes || echo no)" yes
finish_scenario 7b decommission-yes "decommission.sh --yes stops the unit and removes only the vhost"

# ---- scenario 8: migration from the real-directory layout, then rollback to the legacy release --------------------------------------
R2=$(make_root fake-host-legacy)
cp -R "$TREE_A" "$R2/opt/attest/app"; rm -f "$R2/opt/attest/app/RELEASE.json"
cp -R "$TREE_Z" "$R2/opt/attest/app.prev"
with_root "$R2" "$SHIMS/python3.12" -m venv "$R2/opt/attest/venv"
with_root "$R2" "$R2/opt/attest/venv/bin/python" -m pip install --quiet -r "$TREE_A/deploy/yungou/requirements.txt"
sed 's/__MEMORY_MAX__/200M/; s#/opt/attest/app/venv/bin/python#/opt/attest/venv/bin/python#; s#/opt/attest/app/venv/lib#/opt/attest/venv/lib#' "$DEPLOY_SRC/attest.service" > "$R2/etc/systemd/system/attest.service"
awk '/^server [{]/{n++} n==1' "$DEPLOY_SRC/attest.axiqo.xyz.conf" | sed 's#return 301 https://$host$request_uri;#proxy_pass http://127.0.0.1:4070;#' > "$R2/etc/nginx/conf.d/attest.axiqo.xyz.conf"
cp "$ROOT/deploy/attest.env" "$R2/etc/attest/attest.env"
with_root "$R2" "$SHIMS/systemctl" restart attest.service
sleep 1
{ echo "legacy layout prepared: app (real directory, 9.0.1-rehearsal), app.prev (real directory, 9.0.0-rehearsal), shared venv, old-style unit"; with_root "$R2" state_lines; } > "$LOGS/scenario-8-legacy-before.log" 2>&1
LEGACY_A="legacy-9.0.1-rehearsal-${DIGEST_A:0:12}"
run_scenario 8 legacy-migration 0 "$R2" bash install.sh "$ROOT/work/b.tar.gz"
expect "active release" "$(with_root "$R2" active_label)" "$LABEL_B"
expect "previous is the migrated legacy release" "$(with_root "$R2" prev_label)" "$LEGACY_A"
expect "legacy venv is a symlink to the shared venv" "$([ -L "$R2/opt/attest/releases/$LEGACY_A/venv" ] && readlink "$R2/opt/attest/releases/$LEGACY_A/venv")" "$R2/opt/attest/venv"
expect "legacy app.prev migrated too" "$(ls -1d "$R2"/opt/attest/releases/legacy-9.0.0-rehearsal-* 2>/dev/null | wc -l | tr -d ' ')" 1
expect "served health" "$(served)" "9.0.2-rehearsal worker_alive=True"
expect_log "migration reported" "old layout migrated" present
expect_log "completion line" "install complete" present
finish_scenario 8 legacy-migration "real /opt/attest/app migrated to $LEGACY_A, $LABEL_B active"
run_scenario 8b legacy-rollback 0 "$R2" bash rollback.sh
expect "active release" "$(with_root "$R2" active_label)" "$LEGACY_A"
expect "served health" "$(served)" "9.0.1-rehearsal worker_alive=True"
expect_log "recorded digest from INSTALLED.json" "recorded in INSTALLED.json" present
expect_log "digest readback" "attest_revision() digest $DIGEST_A" present
expect_log "no RELEASE.json note" "legacy tree" present
finish_scenario 8b legacy-rollback "rollback.sh re-selects the legacy release through the shared venv"
with_root "$R2" "$SHIMS/systemctl" stop attest.service

# ---- wrap up ------------------------------------------------------------------------------------------------------------------------------
"$REAL_PYTHON" - "$RESULTS" "$LOGS/summary.json" "$STAMP" "$(hostname)" "$ROOT" <<'PY'
import json, sys
rows = []
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        n, slug, verdict, rc, title = line.rstrip("\n").split("\t")
        rows.append({"scenario": n, "slug": slug, "verdict": verdict, "exit_code": int(rc), "title": title})
record = {"rehearsal": sys.argv[3], "host": sys.argv[4], "root": sys.argv[5], "scenarios": rows,
          "passed": sum(1 for r in rows if r["verdict"] == "PASS"), "failed": sum(1 for r in rows if r["verdict"] != "PASS"),
          "note": "shims rehearse the control flow of install.sh, rollback.sh and decommission.sh; systemd, nginx, pip and the real service were not involved"}
with open(sys.argv[2], "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2)
    handle.write("\n")
PY
echo
echo "summary: $(grep -c '^PASS' "$SUMMARY" || true) passed, $FAILED_SCENARIOS failed"
if [ -n "$LOGS_OUT" ]; then mkdir -p "$LOGS_OUT" && cp "$LOGS"/* "$LOGS_OUT"/ && echo "logs copied to $LOGS_OUT"; fi
if [ "$KEEP" = 1 ]; then echo "root kept: $ROOT"; else rm -rf "$ROOT"; echo "root removed: $ROOT"; fi
[ "$FAILED_SCENARIOS" = 0 ]
