#!/bin/bash
# Transactional installer for the Attest console on yungou (DogYun, no Docker). Run as root from /var/tmp/attest-deploy:
#
#   MEMORY_MAX=200M bash install.sh [app.tar.gz]
#
# Next to this script: the bundle built by deploy/yungou/build_bundle.sh (RELEASE.json inside), attest.service and
# attest.axiqo.xyz.conf (the copies inside the bundle are used when they are absent), optionally attest.env (secrets, created
# separately, never part of a bundle) and, for a fresh host, cpython-3.12-linux-x86_64.tar.gz (standalone interpreter).
#
# Release layout (OPS-02 of the 19 Oct 2026 audit): every release lives in $ATTEST_ROOT/releases/<version>-<digest12> with its
# own virtualenv; $ATTEST_ROOT/app is a symlink to the active release and $ATTEST_ROOT/app.prev to the previous one. The unit
# starts $ATTEST_ROOT/app/venv/bin/python, so re-pointing the link (rollback.sh) flips code and interpreter together. The first
# run on a host with the old layout moves the real directory $ATTEST_ROOT/app to releases/legacy-<version>-<digest12> and lets
# that release keep the shared $ATTEST_ROOT/venv through a symlink (a real $ATTEST_ROOT/app.prev is migrated the same way).
#
# Order: preflight; extraction into a staging directory and verification of every RELEASE.json entry (sha256, size, nothing
# missing, nothing unlisted, no env file, version and package digest of the tree); per-release venv with the pinned
# dependencies; compile, dependency-import and package-import checks with the release interpreter (version and digest must equal
# RELEASE.json); nginx -t with the new vhost swapped in on disk (the running nginx is untouched until the reload at the end);
# then the switch: symlink, unit, daemon-reload, restart; strict health (HTTP 200, JSON, expected version, worker alive, deadline);
# readback of every RELEASE.json entry and of the package digest through $ATTEST_ROOT/app; nginx reload when the vhost changed.
# Any failure exits non-zero, re-selects the previous release (symlink, unit, vhost), restarts it, confirms its health and never
# prints "install complete". Nothing but attest.service, its unit, its vhost and $ATTEST_ROOT is touched.
#
# Every host path and command is an environment variable with the production default, so the script runs unchanged under the
# shims of deploy/yungou/rehearsal/ and tests/test_audit_ops.py. bash 3.2 compatible (no associative arrays, mapfile, ${var,,}).
set -euo pipefail
umask 022

case "${1:-}" in -h|--help) sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

cd "$(dirname "$0")"
HERE=$(pwd)
BUNDLE=${1:-${BUNDLE:-app.tar.gz}}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

ATTEST_ROOT=${ATTEST_ROOT:-/opt/attest}
APP_LINK=${APP_LINK:-$ATTEST_ROOT/app}
PREV_LINK=${PREV_LINK:-$ATTEST_ROOT/app.prev}
RELEASES_DIR=${RELEASES_DIR:-$ATTEST_ROOT/releases}
LEGACY_VENV=${LEGACY_VENV:-$ATTEST_ROOT/venv}
PYTHON_BIN=${PYTHON_BIN:-$ATTEST_ROOT/python/bin/python3.12}
ATTEST_DATA_DIR=${ATTEST_DATA_DIR:-/var/lib/attest}
ATTEST_ENV_DIR=${ATTEST_ENV_DIR:-/etc/attest}
SYSTEMD_UNIT_DIR=${SYSTEMD_UNIT_DIR:-/etc/systemd/system}
UNIT_NAME=${UNIT_NAME:-attest.service}
NGINX_CONF_DIR=${NGINX_CONF_DIR:-/etc/nginx/conf.d}
NGINX_BIN=${NGINX_BIN:-/usr/local/sbin/nginx-modern}
VHOST_NAME=${VHOST_NAME:-attest.axiqo.xyz.conf}
LETSENCRYPT_LIVE=${LETSENCRYPT_LIVE:-/etc/letsencrypt/live/attest.axiqo.xyz}
LETSENCRYPT_WEBROOT=${LETSENCRYPT_WEBROOT:-/var/www/letsencrypt}
SYSTEMCTL=${SYSTEMCTL:-systemctl}
USERADD=${USERADD:-useradd}
CHOWN=${CHOWN:-chown}
INSTALL=${INSTALL:-install}
ATTEST_USER=${ATTEST_USER:-attest}
ATTEST_GROUP=${ATTEST_GROUP:-attest}
HEALTH_URL=${HEALTH_URL:-http://127.0.0.1:4070/api/health}
HEALTH_DEADLINE_SECONDS=${HEALTH_DEADLINE_SECONDS:-60}
HEALTH_POLL_SECONDS=${HEALTH_POLL_SECONDS:-1}
MEMORY_MAX=${MEMORY_MAX:-220M}
KEEP_RELEASES=${KEEP_RELEASES:-3}
IMPORT_CHECK=${IMPORT_CHECK:-fastapi uvicorn jsonschema certifi}
DEFAULT_PINS="fastapi==0.115.5 uvicorn[standard]==0.32.1 jsonschema==4.23.0 certifi"

# ---- state for the failure path ------------------------------------------------------------------------------------------
STEP=0; CURRENT_STEP=start; COMPLETED=0
WORK=""
MODE=install                 # install | refresh (the bundle's release is already the active one: unit, vhost and restart only)
TARGET=""; TARGET_CREATED=0
SWITCHED=0; OLD_APP_TARGET=""; OLD_PREV_TARGET=""
UNIT_INSTALLED=0; UNIT_BACKUP=""
VHOST_INSTALLED=0; VHOST_BACKUP=""; NGINX_RELOADED=0
RESTARTED=0

say()  { printf '%s\n' "$*"; }
step() { STEP=$((STEP + 1)); CURRENT_STEP=$1; printf '\n[%02d] %s\n' "$STEP" "$1"; }
ok()   { printf '     ok: %s\n' "$*"; }
note() { printf '     %s\n' "$*"; }
fail() { printf '     FAILED: %s\n' "$*" >&2; exit 1; }     # the EXIT trap restores the previous state

py() { "$PYTHON_BIN" - "$@"; }      # a Python helper reads its program from stdin; its arguments follow "-"

sha256_file() { py "$1" <<'PY'
import hashlib, sys
digest = hashlib.sha256()
with open(sys.argv[1], "rb") as handle:
    for chunk in iter(lambda: handle.read(1 << 20), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
}

# tree_info manifest DIR: verify every RELEASE.json entry of DIR (sha256, size, nothing missing, nothing unlisted, no env file),
#   the version in attest/__init__.py and the package digest; prints "version digest listed_files package_files" or the errors.
# tree_info tree DIR: version and package digest of a tree without a manifest (legacy releases); prints "version digest package_files".
tree_info() { py "$1" "$2" <<'PY'
import hashlib, json, os, re, sys

mode, tree = sys.argv[1], sys.argv[2]
SKIP_TOP = ("RELEASE.json", "INSTALLED.json", "DEPENDENCIES.txt")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def version_of(tree):
    try:
        with open(os.path.join(tree, "attest", "__init__.py"), encoding="utf-8") as handle:
            match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', handle.read(), re.M)
    except OSError:
        return None
    return match.group(1) if match else None


def package_digest(pkg):
    # attest.core.provenance.attest_revision(): sha256 over `rel\0content\0` for every attest/**/*.py in pathlib order
    # (Path objects compare by their parts), __pycache__ skipped
    rels = []
    for dirpath, _dirnames, filenames in os.walk(pkg):
        if "__pycache__" in dirpath.split(os.sep):
            continue
        for name in filenames:
            if name.endswith(".py"):
                rels.append(os.path.relpath(os.path.join(dirpath, name), pkg).replace(os.sep, "/"))
    digest = hashlib.sha256()
    for rel in sorted(rels, key=lambda r: r.split("/")):
        with open(os.path.join(pkg, rel), "rb") as handle:
            digest.update(rel.encode("utf-8") + b"\0" + handle.read() + b"\0")
    return digest.hexdigest(), len(rels)


if not os.path.isdir(os.path.join(tree, "attest")):
    print("no attest/ package in " + tree)
    sys.exit(1)
version = version_of(tree)
digest, count = package_digest(os.path.join(tree, "attest"))
if mode == "tree":
    print("%s %s %d" % (version or "unknown", digest, count))
    sys.exit(0)
manifest_path = os.path.join(tree, "RELEASE.json")
if not os.path.isfile(manifest_path):
    print("no RELEASE.json in " + tree + " (rebuild the bundle with deploy/yungou/build_bundle.sh)")
    sys.exit(1)
with open(manifest_path, encoding="utf-8") as handle:
    manifest = json.load(handle)
errors = []
for rel in manifest.get("required") or []:
    if not os.path.exists(os.path.join(tree, rel)):
        errors.append("required path missing: " + rel)
listed = set()
for entry in manifest.get("files") or []:
    rel = entry["path"]
    listed.add(rel)
    path = os.path.join(tree, rel)
    if os.path.islink(path) or not os.path.isfile(path):
        errors.append("listed file missing: " + rel)
        continue
    size = os.path.getsize(path)
    if size != entry["size"]:
        errors.append("size mismatch: %s (%d bytes, RELEASE.json says %d)" % (rel, size, entry["size"]))
        continue
    if sha256(path) != entry["sha256"]:
        errors.append("sha256 mismatch: " + rel)
for dirpath, dirnames, filenames in os.walk(tree):
    rel_dir = os.path.relpath(dirpath, tree)
    parts = [] if rel_dir == "." else rel_dir.split(os.sep)
    if parts:
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
    else:
        dirnames[:] = [d for d in dirnames if d not in ("venv", "__pycache__")]
    for name in filenames:
        rel = "/".join(parts + [name])
        if (not parts and name in SKIP_TOP) or name.endswith(".pyc"):
            continue
        if name.endswith(".env"):
            errors.append("environment file inside the release tree: " + rel)
        if rel not in listed:
            errors.append("file not listed in RELEASE.json: " + rel)
if version is None:
    errors.append("attest/__init__.py has no __version__")
elif version != manifest.get("version"):
    errors.append("version mismatch: tree %s, RELEASE.json %s" % (version, manifest.get("version")))
recorded = (manifest.get("package_digest") or {}).get("digest")
if digest != recorded:
    errors.append("package digest mismatch: tree %s, RELEASE.json %s" % (digest, recorded))
if errors:
    for error in errors[:25]:
        print(error)
    if len(errors) > 25:
        print("... %d more" % (len(errors) - 25))
    sys.exit(1)
print("%s %s %d %d" % (version, digest, len(listed), count))
PY
}

# health_once EXPECTED_VERSION: one strict probe of HEALTH_URL. Exit 0 healthy, 2 the service answers with another version
# (definitive), 1 not yet (unreachable, non-200, not JSON, worker not alive).
health_once() { py "$HEALTH_URL" "$1" <<'PY'
import json, sys, urllib.error, urllib.request

url, expected = sys.argv[1], sys.argv[2]
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        status, body = response.status, response.read()
except urllib.error.HTTPError as error:
    print("HTTP %d" % error.code)
    sys.exit(1)
except Exception as error:  # connection refused while the service starts, timeouts
    print("unreachable: %s" % error)
    sys.exit(1)
if status != 200:
    print("HTTP %d" % status)
    sys.exit(1)
try:
    data = json.loads(body.decode("utf-8"))
except ValueError:
    print("body is not JSON")
    sys.exit(1)
if data.get("version") != expected:
    print("version %r, expected %r" % (data.get("version"), expected))
    sys.exit(2)
if data.get("worker_alive") is not True:
    print("worker_alive is %r" % (data.get("worker_alive"),))
    sys.exit(1)
disk = data.get("disk") or {}
print("HTTP 200, version %s, worker alive, queue %s, free %s MB" % (data.get("version"), data.get("queue"), disk.get("free_mb")))
PY
}

wait_health() {   # wait_health EXPECTED_VERSION: poll until healthy, a definitive wrong version, or the deadline
  local expected=$1 deadline out rc
  deadline=$(( $(date +%s) + HEALTH_DEADLINE_SECONDS ))
  while :; do
    rc=0; out=$(health_once "$expected") || rc=$?
    if [ "$rc" -eq 0 ]; then note "health: $out"; return 0; fi
    if [ "$rc" -eq 2 ]; then note "health: $out (definitive: the service serves another version)"; return 1; fi
    if [ "$(date +%s)" -ge "$deadline" ]; then note "health: no healthy answer within ${HEALTH_DEADLINE_SECONDS}s; last: $out"; return 1; fi
    sleep "$HEALTH_POLL_SECONDS"
  done
}

replace_symlink() { py "$1" "$2" <<'PY'
import os, sys

link, target = sys.argv[1], sys.argv[2]
tmp = "%s.tmp-%d" % (link, os.getpid())
if os.path.lexists(tmp):
    os.remove(tmp)
os.symlink(target, tmp)
os.replace(tmp, link)      # rename(2): the link is replaced atomically and is never missing
PY
}

link_target() { if [ -L "$1" ]; then readlink "$1"; else printf ''; fi; }

read_revision() {   # read_revision TREE INTERPRETER: "version digest files" from the package's own attest_revision()
  (cd "$1" && "$2" -c 'import attest
from attest.core.provenance import attest_revision
revision = attest_revision()
print(attest.__version__, revision["digest"], revision["files"])')
}

dependency_check() {   # dependency_check INTERPRETER: the pinned packages import
  "$1" -c "import $(printf '%s' "$IMPORT_CHECK" | tr ' ' ',')"
}

write_installed_json() { py "$@" <<'PY'
import datetime, json, os, sys

directory, label, version, digest, bundle_sha, previous, note = sys.argv[1:8]
pins = []
try:
    with open(os.path.join(directory, "deploy", "yungou", "requirements.txt"), encoding="utf-8") as handle:
        pins = [line.split("#")[0].strip() for line in handle if line.split("#")[0].strip()]
except OSError:
    pass
record = {"label": label, "version": version, "package_digest": digest, "bundle_sha256": bundle_sha or None,
          "installed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
          "previous": previous or None, "dependencies": pins, "note": note}
with open(os.path.join(directory, "INSTALLED.json"), "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2)
    handle.write("\n")
PY
}

# migrate_legacy DIR: move a real application directory of the old layout into the release store as legacy-<version>-<digest12>,
# with venv -> $LEGACY_VENV so the release keeps the interpreter it ran with. Prints the new path.
migrate_legacy() {
  local dir=$1 info version digest count dest
  if ! info=$(tree_info tree "$dir"); then say "cannot read the version and digest of $dir: $info" >&2; return 1; fi
  read -r version digest count <<< "$info"
  dest="$RELEASES_DIR/legacy-$version-${digest:0:12}"
  if [ -e "$dest" ]; then dest="$dest-$STAMP"; fi
  mv "$dir" "$dest"
  if [ ! -e "$dest/venv" ]; then ln -s "$LEGACY_VENV" "$dest/venv"; fi
  write_installed_json "$dest" "$(basename "$dest")" "$version" "$digest" "" "" \
    "migrated from the real directory $dir by install.sh on $STAMP; interpreter: the shared $LEGACY_VENV through the venv symlink"
  printf '%s\n' "$dest"
}

render_vhost() {   # render_vhost SOURCE DEST: the https vhost when the certificate exists, otherwise the http-only first server block
  if [ -f "$LETSENCRYPT_LIVE/fullchain.pem" ]; then
    cp "$1" "$2"; printf 'https vhost (certificate present)'
  else
    awk '/^server [{]/{n++} n==1' "$1" | sed 's#return 301 https://$host$request_uri;#proxy_pass http://127.0.0.1:4070;#' > "$2"
    printf 'http-only vhost (no certificate at %s yet)' "$LETSENCRYPT_LIVE"
  fi
}

prune_releases() {   # keep the active and previous releases and the newest others, KEEP_RELEASES in total; prints what it removes
  local name
  py "$RELEASES_DIR" "$APP_LINK" "$PREV_LINK" "$KEEP_RELEASES" <<'PY' | while read -r name; do
import json, os, sys

releases, app, prev, keep = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])


def target(link):
    return os.path.realpath(link) if os.path.islink(link) else None


protected = {t for t in (target(app), target(prev)) if t}
entries = []
for name in os.listdir(releases):
    path = os.path.join(releases, name)
    if name.startswith(".") or os.path.islink(path) or not os.path.isdir(path):
        continue
    installed_at = ""
    try:
        with open(os.path.join(path, "INSTALLED.json"), encoding="utf-8") as handle:
            installed_at = json.load(handle).get("installed_at") or ""
    except (OSError, ValueError):
        pass
    entries.append((installed_at, name, os.path.realpath(path)))
entries.sort()   # oldest first; ISO timestamps sort lexically, releases without a record first
excess = len(entries) - keep
for installed_at, name, path in entries:
    if excess <= 0:
        break
    if path in protected:
        continue
    print(name)
    excess -= 1
PY
    [ -n "$name" ] || continue
    rm -rf "$RELEASES_DIR/$name" && note "pruned old release $name"
  done
}

restore_previous() {
  say "-- restoring the previous state (only $UNIT_NAME, its unit file, its vhost and the $APP_LINK link are touched)"
  if [ "$VHOST_INSTALLED" = 1 ]; then
    if [ -n "$VHOST_BACKUP" ]; then
      cp "$VHOST_BACKUP" "$NGINX_CONF_DIR/$VHOST_NAME" && say "   vhost restored from the pre-install copy"
    else
      rm -f "$NGINX_CONF_DIR/$VHOST_NAME" && say "   new vhost removed (there was none before)"
    fi
    if "$NGINX_BIN" -t >/dev/null 2>&1; then say "   nginx -t: ok with the restored configuration"; else say "   nginx -t: FAILED with the restored configuration (inspect nginx by hand)"; fi
    if [ "$NGINX_RELOADED" = 1 ]; then
      if $SYSTEMCTL reload nginx; then say "   nginx reloaded with the restored vhost"; else say "   nginx reload FAILED"; fi
    fi
  fi
  if [ "$UNIT_INSTALLED" = 1 ]; then
    if [ -n "$UNIT_BACKUP" ]; then
      cp "$UNIT_BACKUP" "$SYSTEMD_UNIT_DIR/$UNIT_NAME" && say "   unit file restored"
    else
      rm -f "$SYSTEMD_UNIT_DIR/$UNIT_NAME" && say "   new unit file removed (there was none before)"
    fi
    $SYSTEMCTL daemon-reload || say "   daemon-reload FAILED"
  fi
  if [ "$SWITCHED" = 1 ]; then
    if [ -n "$OLD_APP_TARGET" ]; then
      if replace_symlink "$APP_LINK" "$OLD_APP_TARGET"; then say "   $APP_LINK -> $OLD_APP_TARGET (previous release re-selected)"; else say "   could not re-point $APP_LINK to $OLD_APP_TARGET"; fi
      if [ -n "$OLD_PREV_TARGET" ]; then replace_symlink "$PREV_LINK" "$OLD_PREV_TARGET" || true; else rm -f "$PREV_LINK"; fi
    else
      rm -f "$APP_LINK" "$PREV_LINK"; say "   $APP_LINK removed (there was no release before this run)"
    fi
  fi
  if [ "$RESTARTED" = 1 ] || [ "$SWITCHED" = 1 ]; then
    if [ -e "$APP_LINK" ]; then
      if $SYSTEMCTL restart "$UNIT_NAME"; then say "   $UNIT_NAME restarted"; else say "   restart of $UNIT_NAME FAILED"; fi
    else
      $SYSTEMCTL stop "$UNIT_NAME" >/dev/null 2>&1 || true; say "   $UNIT_NAME stopped (nothing to serve)"
    fi
  fi
  if [ -e "$APP_LINK" ]; then
    local expected active
    expected=$(tree_info tree "$APP_LINK" 2>/dev/null | cut -d' ' -f1)
    active=$(link_target "$APP_LINK"); [ -n "$active" ] || active=$APP_LINK
    if [ -n "$expected" ]; then
      if wait_health "$expected"; then say "   active release $(basename "$active") is healthy (version $expected)"; else say "   active release $(basename "$active") is NOT healthy: manual intervention required"; fi
    fi
  else
    say "   no active release"
  fi
  if [ "$TARGET_CREATED" = 1 ] && [ -n "$TARGET" ] && [ -d "$TARGET" ] && [ "$(link_target "$APP_LINK")" != "$TARGET" ]; then
    if [ "${KEEP_FAILED_RELEASE:-0}" = 1 ]; then
      say "   failed release kept for inspection: $TARGET"
    else
      rm -rf "$TARGET"; say "   failed release directory removed: $TARGET (KEEP_FAILED_RELEASE=1 keeps it)"
    fi
  fi
}

on_exit() {
  local rc=$?
  set +e
  trap - EXIT
  if [ "$COMPLETED" = 1 ]; then
    [ -n "$WORK" ] && rm -rf "$WORK"
    exit 0
  fi
  [ "$rc" -eq 0 ] && rc=1
  printf '\nINSTALL FAILED (exit %d) during step "%s"\n' "$rc" "$CURRENT_STEP" >&2
  restore_previous
  [ -n "$WORK" ] && rm -rf "$WORK"
  rm -rf "$RELEASES_DIR"/.staging-* 2>/dev/null
  printf 'install NOT complete; see the messages above\n' >&2
  exit "$rc"
}
trap on_exit EXIT

# ---- 1. preflight --------------------------------------------------------------------------------------------------------
say "== install.sh $STAMP: bundle $BUNDLE, root $ATTEST_ROOT, MemoryMax $MEMORY_MAX"
step "preflight"
[ -f "$BUNDLE" ] || fail "bundle not found: $HERE/$BUNDLE"
if [ "$(id -u)" != 0 ] && [ "$ATTEST_ROOT" = /opt/attest ]; then fail "run as root (or point ATTEST_ROOT and the other paths at a rehearsal root)"; fi
mkdir -p "$ATTEST_ROOT" "$RELEASES_DIR" "$ATTEST_DATA_DIR/runs" "$ATTEST_ENV_DIR" "$LETSENCRYPT_WEBROOT"
chmod 0755 "$RELEASES_DIR"
if [ ! -x "$PYTHON_BIN" ]; then
  [ -f "$HERE/cpython-3.12-linux-x86_64.tar.gz" ] || fail "no interpreter at $PYTHON_BIN and no cpython-3.12-linux-x86_64.tar.gz next to install.sh"
  note "installing the standalone CPython 3.12 into $ATTEST_ROOT/python"
  rm -rf "$ATTEST_ROOT/python.tmp" && mkdir -p "$ATTEST_ROOT/python.tmp"
  tar -xzf "$HERE/cpython-3.12-linux-x86_64.tar.gz" -C "$ATTEST_ROOT/python.tmp"
  mv "$ATTEST_ROOT/python.tmp/python" "$ATTEST_ROOT/python" && rmdir "$ATTEST_ROOT/python.tmp"
  [ -x "$PYTHON_BIN" ] || fail "interpreter still missing after extraction: $PYTHON_BIN"
fi
ok "interpreter: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"
BUNDLE_SHA=$(sha256_file "$BUNDLE")
ok "bundle sha256 $BUNDLE_SHA"
if id "$ATTEST_USER" >/dev/null 2>&1; then
  ok "user $ATTEST_USER exists"
else
  $USERADD -r -s /sbin/nologin -d "$ATTEST_DATA_DIR" "$ATTEST_USER" || fail "could not create user $ATTEST_USER"
  ok "user $ATTEST_USER created"
fi
if [ -f "$HERE/attest.env" ]; then
  $INSTALL -o root -g "$ATTEST_GROUP" -m 0640 "$HERE/attest.env" "$ATTEST_ENV_DIR/attest.env" || fail "could not install the secrets file"
  ok "secrets: $ATTEST_ENV_DIR/attest.env installed from the staged attest.env (root:$ATTEST_GROUP 0640)"
elif [ -f "$ATTEST_ENV_DIR/attest.env" ]; then
  ok "secrets: existing $ATTEST_ENV_DIR/attest.env kept (no staged attest.env)"
else
  fail "no $ATTEST_ENV_DIR/attest.env and no attest.env next to install.sh; the unit cannot start without it"
fi
$CHOWN -R "$ATTEST_USER:$ATTEST_GROUP" "$ATTEST_DATA_DIR" || fail "chown of $ATTEST_DATA_DIR failed"
WORK=$(mktemp -d "${TMPDIR:-/tmp}/attest-install.XXXXXX")
if [ -L "$APP_LINK" ]; then
  ok "current layout: $APP_LINK -> $(readlink "$APP_LINK"); previous: $(link_target "$PREV_LINK")"
elif [ -d "$APP_LINK" ]; then
  ok "current layout: $APP_LINK is a real directory (old layout; it will be migrated to $RELEASES_DIR at the switch)"
else
  ok "current layout: no application installed yet"
fi

# ---- 2. stage and verify --------------------------------------------------------------------------------------------------
step "extract the bundle into a staging directory"
rm -rf "$RELEASES_DIR"/.staging-*
STAGING="$RELEASES_DIR/.staging-$STAMP"
mkdir -p "$STAGING"
if ! tar -xzf "$BUNDLE" -C "$STAGING" 2>"$WORK/tar.err"; then cat "$WORK/tar.err" >&2; fail "extraction failed"; fi
xattr_warnings=$(grep -c 'Ignoring unknown extended header' "$WORK/tar.err" 2>/dev/null || true)
[ "${xattr_warnings:-0}" = 0 ] || note "tar reported $xattr_warnings macOS extended-attribute headers (ignored, harmless)"
grep -v 'Ignoring unknown extended header' "$WORK/tar.err" >&2 || true
[ -f "$STAGING/RELEASE.json" ] || fail "the bundle has no RELEASE.json at its root: rebuild it with deploy/yungou/build_bundle.sh"
ok "extracted into $STAGING"

step "verify RELEASE.json against the extracted tree"
if ! info=$(tree_info manifest "$STAGING"); then say "$info" | sed 's/^/     /'; fail "RELEASE.json verification failed; the release is refused"; fi
read -r VERSION DIGEST MANIFEST_FILES PKG_FILES <<< "$info"
LABEL="$VERSION-${DIGEST:0:12}"
case "$LABEL" in *[!A-Za-z0-9._+-]*) fail "release label has unexpected characters: $LABEL" ;; esac
ok "version $VERSION, package digest $DIGEST ($PKG_FILES sources), $MANIFEST_FILES files verified (sha256 and size), no unlisted file, no env file"
ok "release label $LABEL"

step "release directory"
TARGET="$RELEASES_DIR/$LABEL"
CUR_TARGET=$(link_target "$APP_LINK")
if [ -d "$TARGET" ] && [ -n "$CUR_TARGET" ] && [ "$CUR_TARGET" = "$TARGET" ]; then
  MODE=refresh
  rm -rf "$STAGING"
  ok "release $LABEL is already active: refresh mode (validation, unit, vhost, restart and health; no switch, venv kept)"
else
  if [ -e "$TARGET" ]; then rm -rf "$TARGET"; note "replaced the inactive release directory $TARGET"; fi
  mv "$STAGING" "$TARGET"
  TARGET_CREATED=1
  ok "$TARGET (not active until the switch)"
fi

# ---- 3. dependencies and validation -----------------------------------------------------------------------------------------
step "per-release virtualenv and pinned dependencies"
if [ "$MODE" = refresh ]; then
  note "kept $TARGET/venv"
else
  "$PYTHON_BIN" -m venv "$TARGET/venv" || fail "virtualenv creation failed"
  REQ="$TARGET/deploy/yungou/requirements.txt"
  if [ -f "$REQ" ]; then
    "$TARGET/venv/bin/python" -m pip install --quiet --disable-pip-version-check -r "$REQ" || fail "dependency installation failed ($REQ)"
    ok "pins from deploy/yungou/requirements.txt installed into $TARGET/venv"
  else
    # shellcheck disable=SC2086  # DEFAULT_PINS is a word list on purpose
    "$TARGET/venv/bin/python" -m pip install --quiet --disable-pip-version-check $DEFAULT_PINS || fail "dependency installation failed (built-in pins)"
    ok "built-in pins installed into $TARGET/venv ($DEFAULT_PINS)"
  fi
  "$TARGET/venv/bin/python" -m pip freeze --disable-pip-version-check > "$TARGET/DEPENDENCIES.txt" 2>/dev/null || note "pip freeze unavailable; DEPENDENCIES.txt not written"
fi

step "validate the release with its own interpreter (before switching)"
(cd "$TARGET" && "$TARGET/venv/bin/python" -m compileall -q attest) || fail "compileall of attest/ failed"
ok "compileall attest/"
dependency_check "$TARGET/venv/bin/python" || fail "dependencies do not import ($IMPORT_CHECK)"
ok "import $IMPORT_CHECK"
if ! out=$(read_revision "$TARGET" "$TARGET/venv/bin/python"); then fail "import of attest and attest.core.provenance failed"; fi
read -r REV_VERSION REV_DIGEST REV_FILES <<< "$out"
[ "$REV_VERSION" = "$VERSION" ] || fail "attest.__version__ is $REV_VERSION, RELEASE.json says $VERSION"
[ "$REV_DIGEST" = "$DIGEST" ] || fail "attest_revision() digest $REV_DIGEST differs from RELEASE.json ($DIGEST)"
ok "import attest, attest.core.provenance: version $REV_VERSION, attest_revision() digest $REV_DIGEST over $REV_FILES files (equal to RELEASE.json)"

step "render the unit and the vhost"
UNIT_SRC="$HERE/attest.service"; [ -f "$UNIT_SRC" ] || UNIT_SRC="$TARGET/deploy/yungou/attest.service"
[ -f "$UNIT_SRC" ] || fail "no attest.service next to install.sh or in the release"
sed "s/__MEMORY_MAX__/$MEMORY_MAX/" "$UNIT_SRC" > "$WORK/unit.new"
if grep -q 'ExecStart=.*/app/venv/bin/python' "$WORK/unit.new"; then
  ok "unit from $UNIT_SRC (MemoryMax=$MEMORY_MAX; ExecStart uses the active release's interpreter through the app link)"
else
  note "warning: the unit's ExecStart does not use <root>/app/venv/bin/python; a rollback will not flip the interpreter"
fi
VHOST_SRC="$HERE/$VHOST_NAME"; [ -f "$VHOST_SRC" ] || VHOST_SRC="$TARGET/deploy/yungou/$VHOST_NAME"
[ -f "$VHOST_SRC" ] || fail "no $VHOST_NAME next to install.sh or in the release"
kind=$(render_vhost "$VHOST_SRC" "$WORK/vhost.new")
ok "vhost from $VHOST_SRC: $kind"

step "nginx configuration test with the new vhost in place (nginx is not reloaded yet)"
LIVE_VHOST="$NGINX_CONF_DIR/$VHOST_NAME"
if [ -f "$LIVE_VHOST" ] && cmp -s "$LIVE_VHOST" "$WORK/vhost.new"; then
  ok "vhost unchanged; nginx is not touched by this install"
else
  if [ -f "$LIVE_VHOST" ]; then cp "$LIVE_VHOST" "$WORK/vhost.bak"; VHOST_BACKUP="$WORK/vhost.bak"; fi
  $INSTALL -m 0644 "$WORK/vhost.new" "$LIVE_VHOST" || fail "could not write $LIVE_VHOST"
  VHOST_INSTALLED=1
  if "$NGINX_BIN" -t > "$WORK/nginx-t.out" 2>&1; then
    tail -2 "$WORK/nginx-t.out" | sed 's/^/     /'
    ok "nginx -t passed with the new vhost; the running nginx still uses the old one until the reload after the health check"
  else
    sed 's/^/     /' "$WORK/nginx-t.out" >&2
    fail "nginx -t failed with the new vhost (the previous vhost is restored)"
  fi
fi

# ---- 4. switch ------------------------------------------------------------------------------------------------------------------
if [ "$MODE" = refresh ]; then
  step "switch (skipped: $LABEL is already the active release)"
  note "$APP_LINK -> $CUR_TARGET"
else
  step "switch $APP_LINK to $LABEL"
  if [ -d "$APP_LINK" ] && [ ! -L "$APP_LINK" ]; then
    OLD_APP_TARGET=$(migrate_legacy "$APP_LINK") || fail "migration of the real directory $APP_LINK failed"
    ok "old layout migrated: $APP_LINK moved to $OLD_APP_TARGET (venv -> $LEGACY_VENV)"
  else
    OLD_APP_TARGET=$CUR_TARGET
  fi
  if [ -d "$PREV_LINK" ] && [ ! -L "$PREV_LINK" ]; then
    legacy_prev=$(migrate_legacy "$PREV_LINK") || fail "migration of the real directory $PREV_LINK failed"
    ok "old layout migrated: $PREV_LINK moved to $legacy_prev (kept as an installed release)"
  fi
  OLD_PREV_TARGET=$(link_target "$PREV_LINK")
  replace_symlink "$APP_LINK" "$TARGET" || fail "could not point $APP_LINK at $TARGET"
  SWITCHED=1
  if [ -n "$OLD_APP_TARGET" ]; then replace_symlink "$PREV_LINK" "$OLD_APP_TARGET" || fail "could not point $PREV_LINK at $OLD_APP_TARGET"; fi
  previous_label=""; [ -z "$OLD_APP_TARGET" ] || previous_label=$(basename "$OLD_APP_TARGET")
  write_installed_json "$TARGET" "$LABEL" "$VERSION" "$DIGEST" "$BUNDLE_SHA" "$previous_label" "installed by install.sh on $STAMP from $BUNDLE"
  $CHOWN -R root:root "$TARGET" || fail "chown of $TARGET failed"
  chmod -R o-w "$TARGET"
  ok "$APP_LINK -> $TARGET; $PREV_LINK -> ${OLD_APP_TARGET:-(none)}"
fi

step "systemd unit"
if [ -f "$SYSTEMD_UNIT_DIR/$UNIT_NAME" ]; then cp "$SYSTEMD_UNIT_DIR/$UNIT_NAME" "$WORK/unit.bak"; UNIT_BACKUP="$WORK/unit.bak"; fi
if [ -n "$UNIT_BACKUP" ] && cmp -s "$UNIT_BACKUP" "$WORK/unit.new"; then
  ok "unit unchanged"
else
  $INSTALL -m 0644 "$WORK/unit.new" "$SYSTEMD_UNIT_DIR/$UNIT_NAME" || fail "could not write the unit"
  UNIT_INSTALLED=1
  ok "unit written to $SYSTEMD_UNIT_DIR/$UNIT_NAME"
fi
$SYSTEMCTL daemon-reload || fail "daemon-reload failed"
$SYSTEMCTL enable "$UNIT_NAME" >/dev/null 2>&1 || fail "enable $UNIT_NAME failed"
ok "daemon-reload, enabled"

step "restart $UNIT_NAME"
RESTARTED=1
$SYSTEMCTL restart "$UNIT_NAME" || fail "restart of $UNIT_NAME failed"
ok "restarted"

step "health (strict: HTTP 200, JSON, version $VERSION, worker alive; deadline ${HEALTH_DEADLINE_SECONDS}s) at $HEALTH_URL"
wait_health "$VERSION" || fail "the restarted service is not healthy with version $VERSION"

step "read back the installed release through $APP_LINK"
if ! info=$(tree_info manifest "$APP_LINK"); then say "$info" | sed 's/^/     /'; fail "RELEASE.json readback failed on $APP_LINK"; fi
read -r RB_VERSION RB_DIGEST RB_FILES _ <<< "$info"
ok "$RB_FILES RELEASE.json entries verified in place (version $RB_VERSION, digest $RB_DIGEST)"
if ! out=$(read_revision "$APP_LINK" "$APP_LINK/venv/bin/python"); then fail "attest_revision() readback through $APP_LINK failed"; fi
read -r RB2_VERSION RB2_DIGEST RB2_FILES <<< "$out"
[ "$RB2_VERSION" = "$VERSION" ] && [ "$RB2_DIGEST" = "$DIGEST" ] || fail "readback through $APP_LINK gives version $RB2_VERSION digest $RB2_DIGEST, expected $VERSION $DIGEST"
ok "$APP_LINK/venv/bin/python reports version $RB2_VERSION, attest_revision() digest $RB2_DIGEST ($RB2_FILES files)"

step "nginx reload"
if [ "$VHOST_INSTALLED" = 1 ]; then
  $SYSTEMCTL reload nginx || fail "nginx reload failed"
  NGINX_RELOADED=1
  ok "nginx reloaded with the new vhost"
else
  ok "not needed (vhost unchanged)"
fi

if [ "$MODE" = install ]; then
  step "prune old releases (keeping $KEEP_RELEASES, never the active or previous one)"
  prune_releases || note "pruning skipped (non-fatal)"
  ok "releases now: $(ls -1 "$RELEASES_DIR" | grep -v '^\.' | tr '\n' ' ')"
fi

COMPLETED=1
say ""
say "install complete: $LABEL active at $APP_LINK (version $VERSION, package digest $DIGEST)"
say "     previous release: ${OLD_APP_TARGET:-$(link_target "$PREV_LINK")}"
say "     rollback: bash rollback.sh (re-selects the previous release and restarts only $UNIT_NAME); list: bash rollback.sh --list"
say "     store: $ATTEST_DATA_DIR/attest.db is not modified by the installer; the service migrates its schema forward at start"
