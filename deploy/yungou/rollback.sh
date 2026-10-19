#!/bin/bash
# Scoped version rollback for the Attest console (OPS-01 of the 19 Oct 2026 audit). Re-selects the previous release (or the one
# named with --to), restarts only attest.service and verifies version and package digest. nginx, the other services, the store
# and the secrets are not touched. Stopping the service and removing its vhost is a different operation: decommission.sh --yes.
#
#   bash rollback.sh             # back to the release $ATTEST_ROOT/app.prev points at
#   bash rollback.sh --to LABEL  # to any installed release ($ATTEST_ROOT/releases/LABEL)
#   bash rollback.sh --list      # show the installed releases and exit
#
# Before switching: the selected release must exist, carry attest/__init__.py, import with its own interpreter and reproduce
# the recorded package digest (RELEASE.json, or INSTALLED.json for migrated legacy releases); its dependencies must import.
# Then: atomic re-point of $ATTEST_ROOT/app (app.prev then points at the release that was active), restart, strict health
# (HTTP 200, JSON, version of the selected release, worker alive, deadline), readback of the package digest through
# $ATTEST_ROOT/app and of every RELEASE.json entry when the release has one. If anything fails after the switch, the previously
# active release is re-selected and restarted; the script exits non-zero and says which release is serving.
# Hosts still on the old layout (a real directory $ATTEST_ROOT/app with a real $ATTEST_ROOT/app.prev) are swapped by renaming,
# which is not atomic, with the shared $ATTEST_ROOT/venv; the next install.sh run migrates them to the release layout.
# Store compatibility: the schema only grows (CREATE TABLE/INDEX IF NOT EXISTS, ALTER TABLE ... ADD COLUMN); an older release
# keeps working with the newer database only if it tolerates extra columns. Verified for 0.4.0 (attest/app/db.py: sqlite3.Row,
# SELECT *, dict(row), INSERT by column name); re-check for every release pair before relying on it.
# Every host path and command is an environment variable with the production default (rehearsable under shims). bash 3.2.
set -euo pipefail

usage() { sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'; }

cd "$(dirname "$0")"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TO=""; LIST=0
while [ $# -gt 0 ]; do
  case "$1" in
    --to) [ -n "${2:-}" ] || { echo "--to needs a release label" >&2; exit 2; }; TO=$2; shift 2 ;;
    --list) LIST=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

ATTEST_ROOT=${ATTEST_ROOT:-/opt/attest}
APP_LINK=${APP_LINK:-$ATTEST_ROOT/app}
PREV_LINK=${PREV_LINK:-$ATTEST_ROOT/app.prev}
RELEASES_DIR=${RELEASES_DIR:-$ATTEST_ROOT/releases}
LEGACY_VENV=${LEGACY_VENV:-$ATTEST_ROOT/venv}
PYTHON_BIN=${PYTHON_BIN:-$ATTEST_ROOT/python/bin/python3.12}
ATTEST_DATA_DIR=${ATTEST_DATA_DIR:-/var/lib/attest}
SYSTEMD_UNIT_DIR=${SYSTEMD_UNIT_DIR:-/etc/systemd/system}
UNIT_NAME=${UNIT_NAME:-attest.service}
SYSTEMCTL=${SYSTEMCTL:-systemctl}
HEALTH_URL=${HEALTH_URL:-http://127.0.0.1:4070/api/health}
HEALTH_DEADLINE_SECONDS=${HEALTH_DEADLINE_SECONDS:-60}
HEALTH_POLL_SECONDS=${HEALTH_POLL_SECONDS:-1}
IMPORT_CHECK=${IMPORT_CHECK:-fastapi uvicorn jsonschema certifi}

STEP=0; CURRENT_STEP=start; COMPLETED=0
LAYOUT=""; SWITCHED=0; OLD_APP_TARGET=""; OLD_PREV_TARGET=""; SEL=""; SEL_VERSION=""

say()  { printf '%s\n' "$*"; }
step() { STEP=$((STEP + 1)); CURRENT_STEP=$1; printf '\n[%02d] %s\n' "$STEP" "$1"; }
ok()   { printf '     ok: %s\n' "$*"; }
note() { printf '     %s\n' "$*"; }
fail() { printf '     FAILED: %s\n' "$*" >&2; exit 1; }

py() { "$PYTHON_BIN" - "$@"; }

# Shared with install.sh (kept byte-identical there): tree_info, health_once, wait_health, replace_symlink, link_target,
# read_revision, dependency_check.
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

wait_health() {
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

read_revision() {
  (cd "$1" && "$2" -c 'import attest
from attest.core.provenance import attest_revision
revision = attest_revision()
print(attest.__version__, revision["digest"], revision["files"])')
}

dependency_check() { "$1" -c "import $(printf '%s' "$IMPORT_CHECK" | tr ' ' ',')"; }

# recorded_release DIR: "source version digest" from RELEASE.json, else INSTALLED.json, else "none - -"
recorded_release() { py "$1" <<'PY'
import json, os, sys

directory = sys.argv[1]
for name, version_key, digest_path in (("RELEASE.json", "version", ("package_digest", "digest")), ("INSTALLED.json", "version", ("package_digest",))):
    path = os.path.join(directory, name)
    if not os.path.isfile(path):
        continue
    try:
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
    except (OSError, ValueError):
        continue
    digest = record
    for key in digest_path:
        digest = digest.get(key) if isinstance(digest, dict) else None
    if record.get(version_key) and digest:
        print(name, record[version_key], digest)
        sys.exit(0)
print("none - -")
PY
}

list_releases() {
  local active prev dir label info version digest marker
  active=$(link_target "$APP_LINK"); prev=$(link_target "$PREV_LINK")
  say "releases in $RELEASES_DIR:"
  for dir in "$RELEASES_DIR"/*/; do
    [ -d "$dir" ] || continue
    dir=${dir%/}; label=$(basename "$dir")
    case "$label" in .*) continue ;; esac
    info=$(tree_info tree "$dir" 2>/dev/null) || info="? ? ?"
    read -r version digest _ <<< "$info"
    marker=""
    if [ "$dir" = "$active" ]; then marker=" (active)"; fi
    if [ "$dir" = "$prev" ]; then marker="$marker (previous)"; fi
    printf '  %-44s version %-18s digest %s%s\n' "$label" "$version" "${digest:0:12}" "$marker"
  done
  if [ -d "$APP_LINK" ] && [ ! -L "$APP_LINK" ]; then say "  $APP_LINK is a real directory (old layout); $PREV_LINK: $([ -d "$PREV_LINK" ] && echo 'real directory' || echo 'absent')"; fi
}

swap_legacy_dirs() {   # old layout: exchange the two real directories by renaming (three moves, not atomic)
  mv "$APP_LINK" "$APP_LINK.rolling-$STAMP" && mv "$PREV_LINK" "$APP_LINK" && mv "$APP_LINK.rolling-$STAMP" "$PREV_LINK"
}

on_exit() {
  local rc=$? expected active
  set +e
  trap - EXIT
  if [ "$COMPLETED" = 1 ]; then exit 0; fi
  [ "$rc" -eq 0 ] && rc=1
  printf '\nROLLBACK FAILED (exit %d) during step "%s"\n' "$rc" "$CURRENT_STEP" >&2
  if [ "$SWITCHED" = 1 ]; then
    say "-- re-selecting the release that was active before this rollback"
    if [ "$LAYOUT" = release ]; then
      if replace_symlink "$APP_LINK" "$OLD_APP_TARGET"; then say "   $APP_LINK -> $OLD_APP_TARGET"; else say "   could not re-point $APP_LINK"; fi
      if [ -n "$OLD_PREV_TARGET" ]; then replace_symlink "$PREV_LINK" "$OLD_PREV_TARGET" || true; fi
    else
      if swap_legacy_dirs; then say "   directories swapped back"; else say "   could not swap the directories back"; fi
    fi
    if $SYSTEMCTL restart "$UNIT_NAME"; then say "   $UNIT_NAME restarted"; else say "   restart of $UNIT_NAME FAILED"; fi
  else
    say "-- nothing was switched; the active release was not touched"
  fi
  if [ -e "$APP_LINK" ]; then
    expected=$(tree_info tree "$APP_LINK" 2>/dev/null | cut -d' ' -f1)
    active=$(link_target "$APP_LINK"); [ -n "$active" ] || active=$APP_LINK
    if [ -n "$expected" ]; then
      if wait_health "$expected"; then say "   serving: $(basename "$active") (version $expected), healthy"; else say "   serving: $(basename "$active") (version $expected) is NOT healthy: manual intervention required"; fi
    fi
  fi
  printf 'rollback NOT complete; nginx was not touched\n' >&2
  exit "$rc"
}
trap on_exit EXIT

# ---- 1. current state ------------------------------------------------------------------------------------------------------
say "== rollback.sh $STAMP: root $ATTEST_ROOT, unit $UNIT_NAME (nginx is never touched by this script)"
step "current state"
if [ -L "$APP_LINK" ]; then
  LAYOUT=release
  ACTIVE=$(link_target "$APP_LINK")
  ok "release layout: $APP_LINK -> $ACTIVE"
  ok "previous: $(link_target "$PREV_LINK" | sed "s/^$/(none)/")"
elif [ -d "$APP_LINK" ]; then
  LAYOUT=legacy
  ACTIVE=$APP_LINK
  ok "old layout: $APP_LINK is a real directory; previous tree: $PREV_LINK $([ -d "$PREV_LINK" ] && echo '(present)' || echo '(absent)')"
else
  fail "no application at $APP_LINK"
fi
if [ "$LIST" = 1 ]; then list_releases; COMPLETED=1; exit 0; fi

# ---- 2. verify the selected release ------------------------------------------------------------------------------------------
step "verify the selected release"
if [ "$LAYOUT" = release ]; then
  if [ -n "$TO" ]; then
    SEL="$RELEASES_DIR/$TO"
  else
    SEL=$(link_target "$PREV_LINK")
    [ -n "$SEL" ] || fail "no previous release: $PREV_LINK is not a symlink (use --to LABEL; see --list)"
  fi
  [ -d "$SEL" ] || fail "release directory missing: $SEL"
  [ "$SEL" != "$ACTIVE" ] || fail "$(basename "$SEL") is already the active release"
  SEL_PY="$SEL/venv/bin/python"
else
  [ -z "$TO" ] || fail "--to needs the release layout; this host still has a real directory at $APP_LINK"
  SEL=$PREV_LINK
  [ -d "$SEL" ] || fail "no previous tree at $PREV_LINK"
  SEL_PY="$LEGACY_VENV/bin/python"
fi
[ -f "$SEL/attest/__init__.py" ] || fail "$SEL has no attest/__init__.py"
[ -x "$SEL_PY" ] || fail "interpreter missing for the selected release: $SEL_PY"
ok "selected: $SEL (interpreter $SEL_PY)"
read -r REC_SOURCE REC_VERSION REC_DIGEST <<< "$(recorded_release "$SEL")"
if [ "$REC_SOURCE" = none ]; then
  info=$(tree_info tree "$SEL") || fail "cannot read $SEL: $info"
  read -r REC_VERSION REC_DIGEST _ <<< "$info"
  note "warning: no RELEASE.json or INSTALLED.json in $SEL; version $REC_VERSION and digest $REC_DIGEST computed from the tree now (not a recorded value)"
else
  ok "recorded in $REC_SOURCE: version $REC_VERSION, package digest $REC_DIGEST"
fi
if ! out=$(read_revision "$SEL" "$SEL_PY"); then fail "the selected release does not import with $SEL_PY"; fi
read -r SEL_VERSION SEL_DIGEST SEL_FILES <<< "$out"
[ "$SEL_VERSION" = "$REC_VERSION" ] || fail "version mismatch: the tree says $SEL_VERSION, recorded $REC_VERSION"
[ "$SEL_DIGEST" = "$REC_DIGEST" ] || fail "package digest mismatch: attest_revision() gives $SEL_DIGEST, recorded $REC_DIGEST"
ok "import attest, attest.core.provenance with $SEL_PY: version $SEL_VERSION, attest_revision() digest $SEL_DIGEST ($SEL_FILES files) equal to the recorded values"
dependency_check "$SEL_PY" || fail "dependencies do not import with $SEL_PY ($IMPORT_CHECK)"
ok "import $IMPORT_CHECK"
if [ -f "$SYSTEMD_UNIT_DIR/$UNIT_NAME" ] && ! grep -q 'ExecStart=.*/app/venv/bin/python' "$SYSTEMD_UNIT_DIR/$UNIT_NAME"; then
  note "warning: $SYSTEMD_UNIT_DIR/$UNIT_NAME does not start <root>/app/venv/bin/python; the interpreter stays the shared one (old layout unit)"
fi

# ---- 3. store compatibility ----------------------------------------------------------------------------------------------------
step "store compatibility"
note "database: $ATTEST_DATA_DIR/attest.db (not modified by the rollback; the service migrates forward only: CREATE TABLE/INDEX IF NOT EXISTS, ALTER TABLE ... ADD COLUMN)"
note "an older release keeps working with a newer schema only if it tolerates extra columns: verified for 0.4.0 (attest/app/db.py uses sqlite3.Row, SELECT *, dict(row) and INSERTs by column name); re-check this assumption for $SEL_VERSION against the schema of the release it replaces"
backups=$(ls -1t "$ATTEST_DATA_DIR"/attest.db.bak-* 2>/dev/null | head -3 || true)
if [ -n "$backups" ]; then note "latest store backups: $(printf '%s' "$backups" | tr '\n' ' ')"; else note "no attest.db.bak-* backup found in $ATTEST_DATA_DIR"; fi

# ---- 4. switch, restart, verify -------------------------------------------------------------------------------------------------
step "select $(basename "$SEL")"
if [ "$LAYOUT" = release ]; then
  OLD_APP_TARGET=$ACTIVE; OLD_PREV_TARGET=$(link_target "$PREV_LINK")
  replace_symlink "$APP_LINK" "$SEL" || fail "could not re-point $APP_LINK"
  SWITCHED=1
  replace_symlink "$PREV_LINK" "$OLD_APP_TARGET" || note "warning: could not re-point $PREV_LINK at $OLD_APP_TARGET"
  ok "$APP_LINK -> $SEL (atomic); $PREV_LINK -> $OLD_APP_TARGET"
else
  swap_legacy_dirs || fail "could not swap $APP_LINK and $PREV_LINK"
  SWITCHED=1
  ok "directories swapped by renaming (old layout, not atomic): $APP_LINK is now the former $PREV_LINK"
fi

step "restart only $UNIT_NAME"
$SYSTEMCTL restart "$UNIT_NAME" || fail "restart of $UNIT_NAME failed"
ok "restarted (nginx and every other service untouched)"

step "health (strict: HTTP 200, JSON, version $SEL_VERSION, worker alive; deadline ${HEALTH_DEADLINE_SECONDS}s) at $HEALTH_URL"
wait_health "$SEL_VERSION" || fail "the service is not healthy with version $SEL_VERSION"

step "read back the active release through $APP_LINK"
if [ "$LAYOUT" = release ]; then ACTIVE_PY="$APP_LINK/venv/bin/python"; else ACTIVE_PY="$LEGACY_VENV/bin/python"; fi
if ! out=$(read_revision "$APP_LINK" "$ACTIVE_PY"); then fail "attest_revision() readback through $APP_LINK failed"; fi
read -r RB_VERSION RB_DIGEST RB_FILES <<< "$out"
[ "$RB_VERSION" = "$SEL_VERSION" ] && [ "$RB_DIGEST" = "$REC_DIGEST" ] || fail "readback gives version $RB_VERSION digest $RB_DIGEST, expected $SEL_VERSION $REC_DIGEST"
ok "$ACTIVE_PY reports version $RB_VERSION, attest_revision() digest $RB_DIGEST ($RB_FILES files) equal to the recorded digest"
if [ -f "$APP_LINK/RELEASE.json" ]; then
  if ! info=$(tree_info manifest "$APP_LINK"); then say "$info" | sed 's/^/     /'; fail "RELEASE.json readback failed on $APP_LINK"; fi
  read -r _ _ RB_LISTED _ <<< "$info"
  ok "$RB_LISTED RELEASE.json entries verified in place"
else
  note "no RELEASE.json in this release (legacy tree): entries not verifiable, digest only"
fi

COMPLETED=1
say ""
say "rollback complete: $(basename "$SEL") active at $APP_LINK (version $SEL_VERSION, package digest $REC_DIGEST); nginx untouched"
say "     previous is now: $(basename "${OLD_APP_TARGET:-$PREV_LINK}") (bash rollback.sh again rolls forward to it)"
