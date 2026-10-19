#!/bin/bash
# Build app.tar.gz for the server from a release tree. Run it from the public export so the server receives exactly the public
# tree plus the redacted evidence reports:   dist/public/deploy/yungou/build_bundle.sh /tmp/attest-app.tar.gz
#
# OPS-03 (audit of 19 Oct 2026): the archive is built from the authoritative required-file list below and the build fails when
# a required path is missing from the source tree (the 19 Oct archive had neither FREEZE.md nor TESTING.md). RELEASE.json at the
# archive root records the version, the package digest (the sha256 over attest/**/*.py that provenance.attest_revision()
# computes), the build time, every archived file with sha256 and size, the exclusion rules and the dependency pins; install.sh
# verifies every entry after extraction and refuses the release on any mismatch or unlisted file. After the build, the archive
# listing is checked for excluded content (env files, zips, screenshots, snapshots, AppleDouble files) and compared with the
# manifest: both must name exactly the same files.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT=$(pwd)
OUT=${1:-/tmp/attest-app.tar.gz}
PYTHON=${PYTHON:-python3}
# macOS tar adds AppleDouble files (._name, resource forks) unless told not to; they reached the server on 17 Oct 2026 and
# inflated the attest/ package digest recorded in bundles (2,060 files of 163 bytes, removed by hand at 18:00 UTC).
export COPYFILE_DISABLE=1

# The authoritative release content. Directories are archived recursively (minus EXCLUDES); every path must exist.
REQUIRED="README.md LICENSE pyproject.toml FREEZE.md TESTING.md PILOT.md PILOT_FEEDBACK.md METHOD.md attest-console.md attest examples deploy tests reports"
# Files the installer and the service need inside those directories.
REQUIRED_FILES="attest/__init__.py attest/core/provenance.py attest/app/server.py deploy/yungou/install.sh deploy/yungou/rollback.sh deploy/yungou/attest.service deploy/yungou/attest.axiqo.xyz.conf deploy/yungou/requirements.txt"
# Design documents shipped when present (not required).
OPTIONAL="attest-first-slice.md attest-product-design.md"
# Excluded on purpose, at any depth: caches, virtualenvs, env files, development screenshots and browser captures (reports/*/screens,
# refresh-sequence), batch source snapshots (reproducible from the recorded digests), downloaded bundle zips, AppleDouble files.
# Note: tar --exclude matches a name at any depth, so the top-level run data is kept out by not listing it, never by excluding
# 'runs' (that used to drop every reports/**/runs evidence directory as well).
EXCLUDES="__pycache__ *.pyc .pytest_cache .venv .impeccable *.env screens refresh-sequence snapshot *.zip *.png ._* .DS_Store"

fail() { echo "build_bundle: $*" >&2; exit 1; }

missing=""
for p in $REQUIRED; do
  if [ -d "$p" ]; then
    [ -n "$(ls -A "$p")" ] || missing="$missing $p(empty)"
  elif [ ! -f "$p" ]; then
    missing="$missing $p"
  fi
done
for p in $REQUIRED_FILES; do [ -f "$p" ] || missing="$missing $p"; done
[ -z "$missing" ] || fail "required path(s) missing from $ROOT:$missing"
present_optional=""
for p in $OPTIONAL; do
  if [ -f "$p" ]; then present_optional="$present_optional $p"; fi
done

TMP=$(mktemp -d "${TMPDIR:-/tmp}/attest-bundle.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

# RELEASE.json: version, package digest, build time, every member with sha256 and size, exclusion rules, dependency pins.
# (The program is written to a file first: bash 3.2 cannot parse a here-document inside $(...) when the body contains quotes.)
cat > "$TMP/manifest.py" <<'PY'
import datetime, fnmatch, hashlib, json, os, re, subprocess, sys

root, out, required, optional, excludes = sys.argv[1], sys.argv[2], sys.argv[3].split(), sys.argv[4].split(), sys.argv[5].split()
os.chdir(root)


def excluded(rel):
    return any(fnmatch.fnmatchcase(part, pattern) for part in rel.split("/") for pattern in excludes)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_digest(pkg="attest"):
    """The digest attest.core.provenance.attest_revision() computes: sha256 over `rel\\0content\\0` of every attest/**/*.py in
    pathlib order (Path objects compare by their parts), __pycache__ skipped."""
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


files = []
for top in required + optional:
    if os.path.isfile(top):
        if not excluded(top):
            files.append(top)
        continue
    for dirpath, dirnames, filenames in os.walk(top):
        rel_dir = dirpath.replace(os.sep, "/")
        dirnames[:] = sorted(d for d in dirnames if not excluded(rel_dir + "/" + d))
        for name in sorted(filenames):
            rel = rel_dir + "/" + name
            full = os.path.join(dirpath, name)
            if excluded(rel) or os.path.islink(full) or not os.path.isfile(full):
                continue
            files.append(rel)
entries = [{"path": rel, "sha256": sha256(rel), "size": os.path.getsize(rel)} for rel in sorted(set(files))]

with open("attest/__init__.py", encoding="utf-8") as handle:
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', handle.read(), re.M)
if not match:
    print("build_bundle: attest/__init__.py has no __version__", file=sys.stderr)
    sys.exit(1)
version = match.group(1)
try:
    with open("pyproject.toml", encoding="utf-8") as handle:
        pyproject = re.search(r'^version\s*=\s*"([^"]+)"', handle.read(), re.M)
    if pyproject and pyproject.group(1) != version:
        print("build_bundle: warning: pyproject.toml version %s differs from attest.__version__ %s" % (pyproject.group(1), version), file=sys.stderr)
except OSError:
    pass
digest, count = package_digest()
commit = None
try:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=5)
    if proc.returncode == 0:
        commit = proc.stdout.strip() or None
except (OSError, subprocess.SubprocessError):
    commit = None
pins = []
try:
    with open("deploy/yungou/requirements.txt", encoding="utf-8") as handle:
        pins = [line.split("#")[0].strip() for line in handle if line.split("#")[0].strip()]
except OSError:
    pass
manifest = {
    "schema": "attest-release/1",
    "version": version,
    "label": "%s-%s" % (version, digest[:12]),
    "package_digest": {"method": "sha256 over the relative path and content of every attest/**/*.py, sorted", "digest": digest, "files": count},
    "built_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "builder": "deploy/yungou/build_bundle.sh",
    "source": {"tree": os.path.basename(root), "git_commit": commit},
    "required": required,
    "optional_included": optional,
    "exclusions": excludes,
    "dependencies": pins,
    "file_count": len(entries),
    "total_bytes": sum(entry["size"] for entry in entries),
    "files": entries,
}
with open(out, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)
    handle.write("\n")
print("%s %s %d %d" % (version, digest, len(entries), count))
PY
manifest_line=$("$PYTHON" "$TMP/manifest.py" "$ROOT" "$TMP/RELEASE.json" "$REQUIRED" "$present_optional" "$EXCLUDES")
read -r VERSION DIGEST FILE_COUNT PKG_COUNT <<< "$manifest_line"

EXCL=()
for pattern in $EXCLUDES; do EXCL+=("--exclude=$pattern"); done
# shellcheck disable=SC2086  # REQUIRED and present_optional are word lists on purpose
tar -czf "$OUT" "${EXCL[@]}" -C "$TMP" RELEASE.json -C "$ROOT" $REQUIRED $present_optional

# Post-build checks on the archive itself.
tar -tzf "$OUT" > "$TMP/listing.txt"
for must in RELEASE.json FREEZE.md TESTING.md; do
  grep -qx "$must" "$TMP/listing.txt" || fail "$must is not in the archive"
done
# (the two key prefixes are written with bracketed characters so that this script itself never contains the shapes the
# public export's secret scan rejects)
if grep -E '\.env$|c[x]k_|t[v]ly-|\.png$|/screens/|/snapshot/|(^|/)\._|\.DS_Store' "$TMP/listing.txt"; then
  fail "EXCLUDED CONTENT IN BUNDLE"
fi
"$PYTHON" - "$TMP/RELEASE.json" "$TMP/listing.txt" <<'PY'
import json, sys

with open(sys.argv[1], encoding="utf-8") as handle:
    manifest = json.load(handle)
listed = set()
with open(sys.argv[2], encoding="utf-8") as handle:
    for line in handle:
        line = line.rstrip("\n")
        if not line or line.endswith("/"):
            continue
        if line.startswith("./"):
            line = line[2:]
        listed.add(line)
listed.discard("RELEASE.json")
expected = {entry["path"] for entry in manifest["files"]}
missing = sorted(expected - listed)
extra = sorted(listed - expected)
if missing or extra:
    for path in missing[:20]:
        print("build_bundle: in RELEASE.json but not archived: " + path, file=sys.stderr)
    for path in extra[:20]:
        print("build_bundle: archived but not in RELEASE.json: " + path, file=sys.stderr)
    sys.exit(1)
print("manifest and archive agree on %d files" % len(expected))
PY
SHA=$("$PYTHON" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$OUT")
echo "bundle: $OUT ($(du -h "$OUT" | cut -f1), $(wc -l < "$TMP/listing.txt" | tr -d ' ') members)"
echo "sha256: $SHA"
echo "release: version $VERSION, package digest $DIGEST ($PKG_COUNT sources), label $VERSION-${DIGEST:0:12}, $FILE_COUNT files in RELEASE.json"
echo "no secret-like paths, no screenshots, no snapshots, no AppleDouble files; FREEZE.md, TESTING.md and RELEASE.json present"
