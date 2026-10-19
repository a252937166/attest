# Deploying the Attest console to `yungou` (DogYun, 206.237.18.80)

Files: `build_bundle.sh` (release archive with `RELEASE.json`), `install.sh` (transactional installer), `rollback.sh` (scoped
version rollback), `decommission.sh` (stop the service and remove its vhost; needs `--yes`), `snapshot.sh` (read-only
before/after host snapshot), `attest.service` (systemd, placeholders `__MEMORY_MAX__`, `__MEMORY_MAX_BYTES__` and `__CGROUP_MEMORY_DIR__`), `attest.axiqo.xyz.conf` (nginx),
`requirements.txt` (the dependency pins, installed per release), `attest.env.example`, and `rehearsal/` (shims and the driver
that rehearse the scripts on a throwaway root). The 19 Oct 2026 audit findings OPS-01, OPS-02 and OPS-03 are repaired here;
the record of the repairs and of the rehearsal is `reports/attest-audit-repairs-2026-10-19/ops/README.md`.

## Release layout on the server (since the OPS-02 repair)

```
/opt/attest/python/                      standalone CPython 3.12 (unchanged)
/opt/attest/releases/<version>-<digest12>/   one directory per release: the extracted bundle, RELEASE.json, INSTALLED.json,
                                         DEPENDENCIES.txt and its own venv/ with the pins of requirements.txt
/opt/attest/releases/legacy-0.4.0-<digest12>/  the pre-audit real directory /opt/attest/app, moved here by the first install.sh
                                         run; its venv/ is a symlink to the shared /opt/attest/venv it always ran with
/opt/attest/app      -> releases/<active>      symlink; the unit's WorkingDirectory and ExecStart (/opt/attest/app/venv/bin/python)
/opt/attest/app.prev -> releases/<previous>    symlink; what rollback.sh re-selects
/var/lib/attest, /etc/attest/attest.env  store and secrets, never touched by install or rollback
```

`<digest12>` is the first twelve hex digits of the package digest (`sha256` over `attest/**/*.py`, the value
`attest.core.provenance.attest_revision()` reports and every Proof Bundle records). Code and interpreter are selected together
by the one symlink, so a rollback is one atomic re-point plus a restart of `attest.service`.

## Deployment procedure (orchestrator)

Local, from the project root:

1. `python3 scripts/export_public.py --out dist/public --force` (redacted public tree; the export's own checks must pass).
2. `(cd dist/public && deploy/yungou/build_bundle.sh /tmp/attest-app.tar.gz)`. The build fails if any required path is
   missing (README.md, LICENSE, pyproject.toml, FREEZE.md, TESTING.md, PILOT.md, PILOT_FEEDBACK.md, METHOD.md,
   attest-console.md, attest/, examples/, deploy/, tests/, reports/, plus the installer's files inside deploy/yungou/) and
   prints the archive's sha256, the version, the package digest and the release label. `RELEASE.json` at the archive root
   lists every member with sha256 and size, the exclusion rules and the pins; the post-build check compares the archive
   listing with that list and refuses env files, zips, screenshots, snapshots and AppleDouble files.
3. Upload to `/var/tmp/attest-deploy/` on the server: the archive as `app.tar.gz`, and from `dist/public/deploy/yungou/`:
   `install.sh`, `rollback.sh`, `decommission.sh`, `snapshot.sh`, `attest.service`, `attest.axiqo.xyz.conf`
   (`requirements.txt` travels inside the bundle). Check `sha256sum app.tar.gz` against the build output.

On the server, as root in `/var/tmp/attest-deploy`:

4. `bash snapshot.sh before-<label>`; store backup with the SQLite backup API from the service interpreter
   (`/opt/attest/venv/bin/python` before the first symlink-layout install, `/opt/attest/app/venv/bin/python` afterwards).
5. `MEMORY_MAX=200M bash install.sh app.tar.gz 2>&1 | tee install-<label>.log` (check `${PIPESTATUS[0]}`, not `tee`'s status).
   The installer prints each step and its result: preflight (interpreter, user, secrets, data ownership); extraction into
   `releases/.staging-<stamp>`; verification of every `RELEASE.json` entry (sha256, size, nothing missing, nothing unlisted, no
   env file, version and package digest of the tree); the release directory `releases/<label>`; a per-release venv with the
   pins; `compileall`, `import fastapi, uvicorn, jsonschema, certifi` and `import attest, attest.core.provenance` with the
   release interpreter (version and digest must equal `RELEASE.json`); unit and vhost rendering (https when the certificate
   exists, http-only otherwise); `nginx -t` with the new vhost swapped in on disk (skipped when the vhost is unchanged; the
   running nginx keeps its configuration until the reload); the switch (first run: the real `/opt/attest/app` becomes
   `releases/legacy-0.4.0-<digest12>` with `venv -> /opt/attest/venv`, a real `/opt/attest/app.prev` is migrated the same way);
   unit, `daemon-reload`, `enable`, `restart`; strict health (HTTP 200, JSON, version, worker alive, 60 s deadline); readback
   of every `RELEASE.json` entry and of `attest_revision()` through `/opt/attest/app`; nginx reload only when the vhost
   changed; pruning to `KEEP_RELEASES` (3) never touching the active or previous release. The last line is
   `install complete: <label> ...` and nothing else ends in it: any failure exits non-zero, re-selects the previous release
   (symlink, unit, vhost), restarts it and reports its health.
6. Verify: the readback lines of the log; `curl -s http://127.0.0.1:4070/api/health` (version, `worker_alive`);
   `readlink /opt/attest/app /opt/attest/app.prev`; `cat /opt/attest/app/INSTALLED.json`; the public checks of the previous
   records (`https://attest.axiqo.xyz/`, `/api/health`, `/api/profiles`, served assets); `bash snapshot.sh after-<label>` and
   its diff against `before-<label>` (the timestamp, memory, disk and load lines, plus the new `app -> releases/...` lines on
   the first symlink-layout install, are the only expected differences).
7. Record the deployment under `reports/attest-deployment-<date>/` with the archive sha256, the label, the readback and the
   two snapshots. The rollback paragraph of that record must describe `rollback.sh` as below, not a directory swap.

First deployment with this installer: 19 Oct 2026, 08:47 UTC, revision 5 (`0.5.0-1e12d46217fb`), which migrated the host from
the directory layout to the release layout (`reports/attest-deployment-2026-10-19b/README.md`).

## Memory limit (revision 8, 19 Oct 2026)

yungou runs systemd 219 on cgroup v1. That version ignores `MemoryMax=` (it logs `Unknown lvalue 'MemoryMax'` at every
daemon-reload) and applies `MemoryLimit=` as `memory.limit_in_bytes`, so from the first deployment until revision 8 no limit
was in force although the unit carried `MemoryMax=200M`. A memory limit alone would still let the service page its excess out to
the host's swap instead of failing. The unit therefore sets `MemoryLimit=` (and keeps `MemoryMax=` for newer systemd versions),
and an `ExecStartPre` that runs as root (`PermissionsStartOnly=true`) writes the same size to `memory.memsw.limit_in_bytes`
(memory plus swap) before the service process exists; a failing write fails the start. At the limit the kernel's memory-cgroup
OOM killer ends the process, `Restart=on-failure` starts it again 5 s later, and the new process settles any run that was in
flight as interrupted (its journaled reservations stay committed, an accepted Sandboxes operation is named for reconciliation;
nothing is replayed).

`install.sh` renders all three placeholders from `MEMORY_MAX` (sizes are powers of 1024: `200M` is 209715200 bytes) and, after
the restart and the health check, reads the limit in force back: systemd's `MemoryLimit`, the cgroup's `memory.limit_in_bytes`
and `memory.memsw.limit_in_bytes`, and the main process's memory cgroup from `/proc/<pid>/cgroup`. Any difference fails the
install, which then restores the previous release and unit. To check by hand:

```bash
systemctl show attest -p MemoryLimit -p MainPID
cat /sys/fs/cgroup/memory/system.slice/attest.service/memory.{limit_in_bytes,memsw.limit_in_bytes,max_usage_in_bytes,failcnt}
grep memory /proc/$(systemctl show attest -p MainPID --value 2>/dev/null || systemctl show attest -p MainPID | cut -d= -f2)/cgroup
```

The drill that verified the mechanism on this host (temporary units only) is recorded in
`reports/attest-revision7-repairs-2026-10-19/memory/`. The rehearsal shims simulate systemd 219's handling of these directives
(`CGROUP_MEMORY_DIR` and `PROC_DIR` point at a fake hierarchy); `REHEARSAL_NO_SWAP_ACCOUNTING=1` simulates a kernel without swap
accounting.

## Rollback (version) and decommissioning (service removal) are different commands

`bash rollback.sh` re-selects the release `/opt/attest/app.prev` points at (`--to <label>` selects any installed release,
`--list` shows them). Before switching it verifies that the release exists, carries `attest/__init__.py`, imports with its own
interpreter and reproduces the recorded package digest (`RELEASE.json`, or `INSTALLED.json` for migrated legacy releases),
and that its dependencies import. It prints the store path and the schema-compatibility note (the schema only grows: an
older release keeps working with the newer database only if it tolerates extra columns, verified for 0.4.0, to be re-checked
per release), re-points `/opt/attest/app` atomically, restarts only `attest.service`, waits for strict health with the
selected release's version, reads the package digest back through `/opt/attest/app` and verifies the `RELEASE.json` entries
in place. nginx, the other services, the store and the secrets are not touched. If anything fails after the switch, the
release that was serving is re-selected and restarted, the script exits non-zero and says which release serves. On a host still
in the old layout (real directories) it swaps `app` and `app.prev` by renaming (not atomic) with the shared venv.

`bash decommission.sh --yes` is the old "rollback": it stops and disables `attest.service`, removes only the Attest vhost,
runs `nginx -t` and reloads nginx; it keeps `/opt/attest`, `/var/lib/attest`, `/etc/attest` and the (disabled) unit file.
Without `--yes` it prints the plan and exits 2.

## Rehearsing the scripts without a server

`deploy/yungou/rehearsal/rehearse.sh --source dist/public [--python /usr/bin/python3.11] [--logs-out DIR] [--keep]` runs
install, rollback and decommission against a throwaway root with shims for `systemctl` (starts a fake health server that
answers with the version of the tree the `app` link points at), `nginx-modern` (`-t` can be made to fail), `useradd`,
`chown`, `install`, and the interpreter (a fake venv whose `pip install` writes stub packages or fails on request; compile,
import and digest checks run on the real interpreter). Every host path and command of the scripts is an environment variable
with the production default (`ATTEST_ROOT`, `SYSTEMD_UNIT_DIR`, `NGINX_CONF_DIR`, `NGINX_BIN`, `SYSTEMCTL`, `HEALTH_URL`,
`PYTHON_BIN`, `ATTEST_ENV_DIR`, `ATTEST_DATA_DIR`, `USERADD`, `CHOWN`, `INSTALL`, ...), so the scripts under test are the ones
deployed. `tests/test_audit_ops.py` runs the same scenarios with a small tree in the offline suite. The shims rehearse the
scripts' control flow, not systemd, nginx or pip themselves.

## Static files and browser caches (18 Oct 2026)

Before building a bundle that changes anything under `attest/app/static/`, bump the version query on both asset links
in `index.html` (`/static/styles.css?v=<stamp>` and `/static/app.js?v=<stamp>`). The vhost sends `Cache-Control: no-cache`
on every response, so browsers revalidate against the ETag; the version query additionally defeats copies cached before
that header existed. A browser holding the previous build's assets otherwise renders the new markup with the old
stylesheet and script (seen on 18 Oct 2026, `reports/attest-deployment-2026-10-18/README.md`).

macOS `tar` also stores extended attributes as `LIBARCHIVE.xattr.com.apple.provenance` headers; GNU tar on the host
prints "Ignoring unknown extended header keyword" for each and extracts the files unchanged (seen on the 18 Oct 15:03 UTC
deployment; `install.sh` now counts and hides these warnings). Harmless; `COPYFILE_DISABLE=1` in `build_bundle.sh` is what
keeps AppleDouble `._*` files out.

## History of the procedure

The deployments of 15 to 19 Oct 2026 (`reports/attest-deployment-2026-10-1*/README.md`) used the previous scripts: an
installer that replaced `/opt/attest/app` before validating, one shared venv, and a `rollback.sh` that actually stopped the
service and removed its vhost while the records described a swap of `app` and `app.prev` (audit finding OPS-01). Those
records are historical and were not rewritten; from the next deployment on, the procedure above applies and the first
`install.sh` run migrates the real directories into the release layout. The 19 Oct record's scripting note still holds:
`grep -c` exits 1 on a zero count, which ends a `set -e -o pipefail` script before the remaining checks run; use
`grep -c ... || true`.
