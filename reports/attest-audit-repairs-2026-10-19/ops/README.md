# Repairs of OPS-01, OPS-02 and OPS-03 (audit of 19 October 2026), with an isolated deployment rehearsal

This folder records how the three operations findings of `reports/attest-audit-2026-10-19/boundaries-findings.md` were
repaired in `deploy/yungou/`, how the repaired scripts were rehearsed on a throwaway root of the Aliyun host and on the macOS
workstation, and what the offline acceptance tests cover. Nothing was deployed: `yungou` (206.237.18.80) was not contacted,
no real `/opt`, `/etc` or systemd path was touched anywhere, no paid call was made. The historical records under `reports/`
were not modified. The production migration from the real directory `/opt/attest/app` to the release layout described below
happens at the next real deployment, performed by the orchestrator with the procedure in `deploy/yungou/README.md`.

## Findings, files and mechanism

| Finding | Files | What changed |
| --- | --- | --- |
| OPS-01 (P1): the documented rollback stopped the service and removed its vhost | `deploy/yungou/rollback.sh` (rewritten), `deploy/yungou/decommission.sh` (new), `deploy/yungou/attest.service`, `deploy/yungou/README.md` | `rollback.sh` is a scoped version rollback; the old behaviour lives in `decommission.sh`, which prints its plan and refuses without `--yes` (exit 2); the runbook describes both |
| OPS-02 (P2): the installer switched the application before validating | `deploy/yungou/install.sh` (rewritten), `deploy/yungou/attest.service`, `deploy/yungou/requirements.txt` (new), `deploy/yungou/snapshot.sh` | staged, verified, transactional install into `/opt/attest/releases/<version>-<digest12>` with a per-release venv; `/opt/attest/app` becomes a symlink; strict health; automatic restore of the previous release on any failure |
| OPS-03 (P2): the archive omitted `FREEZE.md` and `TESTING.md` | `deploy/yungou/build_bundle.sh` (rewritten), `deploy/yungou/install.sh` | authoritative required-file list, build fails on a missing path, `RELEASE.json` at the archive root, every entry verified by the installer before the switch and read back after it |

### OPS-01: version rollback versus decommissioning

`rollback.sh` (`bash rollback.sh`, `--to <label>`, `--list`):

1. Reads the layout: `/opt/attest/app -> releases/<active>`, `/opt/attest/app.prev -> releases/<previous>`.
2. Verifies the selected release before anything changes: the directory exists and carries `attest/__init__.py`; its
   recorded version and package digest are read from `RELEASE.json` (or `INSTALLED.json` for a migrated legacy release); the
   release imports with its own interpreter (`releases/<label>/venv/bin/python -c "import attest; from
   attest.core.provenance import attest_revision; ..."`) and `attest_revision()` reproduces the recorded digest; the pinned
   dependencies import.
3. Prints the store path (`/var/lib/attest/attest.db`) and the compatibility note: the service migrates forward only
   (`CREATE TABLE/INDEX IF NOT EXISTS`, `ALTER TABLE runs ADD COLUMN`, `attest/app/db.py` lines 14 to 63), so an older release
   keeps working with a newer database only if it tolerates extra columns. Verified for 0.4.0: `sqlite3.Row` row factory,
   `SELECT *` (`db.py:230`, `db.py:234`), `dict(row)` (`db.py:322`), inserts by column name; the added columns are nullable.
   This is the assumption to re-check for every release pair; the script says so and lists the latest `attest.db.bak-*` files.
4. Re-points `/opt/attest/app` atomically (`os.replace` of a temporary symlink), points `app.prev` at the release that was
   active, restarts only `attest.service`, polls `GET /api/health` until HTTP 200 with parsable JSON, `version` equal to the
   selected release's version and `worker_alive` true (60 s deadline; a 200 answer with another version is treated as
   definitive), then reads `attest_revision()` back through `/opt/attest/app/venv/bin/python` and verifies every
   `RELEASE.json` entry in place. nginx is never called.
5. If anything fails after the switch, the release that was serving is re-selected and restarted, its health is checked and
   reported, and the script exits non-zero saying which release serves.

A host still in the old layout (real directories `app` and `app.prev`) is swapped by renaming with the shared venv, which is
not atomic; the script says so. `decommission.sh --yes` stops and disables the unit, removes only the Attest vhost, runs
`nginx -t` and reloads nginx; without `--yes` it prints the plan and exits 2.

### OPS-02: transactional installer

`install.sh` (`MEMORY_MAX=200M bash install.sh app.tar.gz`), in order, printing each step and its result:

1. Preflight: the bundle and its sha256, the interpreter (the standalone CPython is installed from the tarball next to the
   script only when missing), the `attest` user (`useradd` when absent), the secrets (`attest.env` next to the script is
   installed root:attest 0640; otherwise the existing `/etc/attest/attest.env` is kept; neither present is a failure), data
   ownership, the current layout.
2. Extraction into `/opt/attest/releases/.staging-<stamp>`; a bundle without `RELEASE.json` is refused.
3. Verification of `RELEASE.json` against the extracted tree: every listed file's sha256 and size, no listed file missing, no
   file present that is not listed, no `*.env` file, every required path present, `attest/__init__.py` version equal to the
   manifest, package digest of the tree (independent implementation of `attest_revision()`) equal to the manifest. The label is
   `<version>-<digest12>`.
4. The release directory `releases/<label>`. Re-installing the active label is a refresh (validation, unit, vhost, restart,
   health, no switch); an inactive directory with the same label is replaced.
5. A per-release venv (`python3.12 -m venv releases/<label>/venv`) with the pins of `deploy/yungou/requirements.txt` from
   the release itself (`DEPENDENCIES.txt` records `pip freeze`).
6. Validation with the release interpreter, before any switch: `python -m compileall -q attest`, `import fastapi, uvicorn,
   jsonschema, certifi`, `import attest, attest.core.provenance` with `attest_revision()` equal to the manifest's version and
   digest.
7. Rendering of the unit (`__MEMORY_MAX__`) and of the vhost (https when `/etc/letsencrypt/live/attest.axiqo.xyz/fullchain.pem`
   exists, the http-only first server block otherwise), from the files next to the script or from the release.
8. nginx test: when the rendered vhost equals the live one, nginx is not touched at all. Otherwise the live vhost is copied
   aside, the new one written in place, `nginx -t` run; on failure the old vhost is restored before the script fails. The
   running nginx keeps its loaded configuration until the reload in step 13. (Testing a staged copy under a second name in
   `conf.d` is not possible: the `limit_req_zone attest_api` would be defined twice.)
9. Switch: on the first run the real directory `/opt/attest/app` is moved to `releases/legacy-<version>-<digest12>` with
   `venv -> /opt/attest/venv` and an `INSTALLED.json` (a real `/opt/attest/app.prev` is migrated the same way); then
   `/opt/attest/app` is re-pointed atomically to the new release and `app.prev` to the previous one; `INSTALLED.json` (label,
   version, digest, bundle sha256, time, previous label, pins) is written; `chown -R root:root`, `chmod -R o-w`.
10. Unit: written only when it differs from the live one (the old copy is kept for the failure path), `daemon-reload`,
    `enable`. The unit now starts `/opt/attest/app/venv/bin/python` and reads `SSL_CERT_FILE` under `/opt/attest/app/venv`, so
    the interpreter follows the link.
11. `systemctl restart attest.service`.
12. Strict health as in the rollback, with the new release's version.
13. Readback through `/opt/attest/app`: every `RELEASE.json` entry again, and `attest_revision()` with
    `/opt/attest/app/venv/bin/python`; then `systemctl reload nginx` only when the vhost changed; then pruning of release
    directories beyond `KEEP_RELEASES` (3), never the active or previous one.

`set -euo pipefail` with an `EXIT` trap: any failure (dependency installation, validation, nginx test, restart, health,
readback, reload) prints `INSTALL FAILED (exit N) during step "..."`, restores the vhost copy and re-runs `nginx -t`
(and reloads if a reload had happened), restores the unit file and `daemon-reload`s, re-points `app` and `app.prev` to what
they were (or removes them when nothing was installed before), restarts the unit (or stops it when nothing is left to serve),
confirms the health of the release that is serving, removes the failed release directory (`KEEP_FAILED_RELEASE=1` keeps it)
and the staging directory, and exits non-zero. `install complete` is printed only after the last step.

Every host path and command is an environment variable with the production default: `ATTEST_ROOT` (/opt/attest), `APP_LINK`,
`PREV_LINK`, `RELEASES_DIR`, `LEGACY_VENV`, `PYTHON_BIN` (/opt/attest/python/bin/python3.12), `ATTEST_DATA_DIR`
(/var/lib/attest), `ATTEST_ENV_DIR` (/etc/attest), `SYSTEMD_UNIT_DIR` (/etc/systemd/system), `UNIT_NAME`, `NGINX_CONF_DIR`
(/etc/nginx/conf.d), `NGINX_BIN` (/usr/local/sbin/nginx-modern), `VHOST_NAME`, `LETSENCRYPT_LIVE`, `LETSENCRYPT_WEBROOT`,
`SYSTEMCTL`, `USERADD`, `CHOWN`, `INSTALL`, `ATTEST_USER`, `ATTEST_GROUP`, `HEALTH_URL` (http://127.0.0.1:4070/api/health),
`HEALTH_DEADLINE_SECONDS` (60), `HEALTH_POLL_SECONDS` (1), `MEMORY_MAX` (220M), `KEEP_RELEASES` (3), `IMPORT_CHECK`.
`MEMORY_MAX`, user creation, permissions and the http-only vhost fallback behave as before. The scripts are bash 3.2
compatible (no associative arrays, `mapfile`, `readarray`, `${var,,}`, `timeout` or `realpath -m`); the Python helpers they
embed run on the production interpreter and on Python 3.6 or later.

### OPS-03: authoritative release content and `RELEASE.json`

`build_bundle.sh` requires `README.md`, `LICENSE`, `pyproject.toml`, `FREEZE.md`, `TESTING.md`, `PILOT.md`,
`PILOT_FEEDBACK.md`, `METHOD.md`, `attest-console.md`, `attest/`, `examples/`, `deploy/`, `tests/`, `reports/` (as the export
allows them) and, inside those, `attest/__init__.py`, `attest/core/provenance.py`, `attest/app/server.py`,
`deploy/yungou/{install.sh,rollback.sh,attest.service,attest.axiqo.xyz.conf,requirements.txt}`; it fails with the list of
missing paths otherwise. `attest-first-slice.md` and `attest-product-design.md` are shipped when present. The exclusions are
unchanged (`__pycache__`, `*.pyc`, `.venv`, `.impeccable`, `*.env`, `screens`, `refresh-sequence`, `snapshot`, `*.zip`,
`*.png`, `._*`, `.DS_Store`, plus `.pytest_cache`), applied to any path component as tar does. `RELEASE.json`
(`schema attest-release/1`) records the version, the label, the package digest (method, value, file count), the build time in
UTC, the builder, the source tree name and git commit when available, the required and optional lists, the exclusions, the
dependency pins and every archived file with sha256 and size. It is added from a temporary directory, so the export tree is not
modified. After the build the listing is checked for `RELEASE.json`, `FREEZE.md` and `TESTING.md`, for excluded content, and
compared with the manifest: the archive's regular-file members and the manifest's entries must be the same set. The installer
verifies every entry after extraction (step 3) and again in place after the switch (step 13).

## Rehearsal

The scripts were rehearsed twice with `deploy/yungou/rehearsal/rehearse.sh`, which runs the unchanged scripts against a
throwaway root. Shims replace the host commands: `systemctl` (`restart` starts `fake_health.py`, which answers
`GET /api/health` with the JSON shape of the real endpoint and the version of the tree the `app` link pointed at when it
started; `stop`/`disable --now` stop it; `is-active` reports it; `reload`, `daemon-reload`, `enable` are logged no-ops),
`nginx-modern` (`-t` passes, or fails when `REHEARSAL_NGINX_T_FAIL=1`), `useradd` and `chown` (logged, no change), `install`
(copies and applies `-m`), and the interpreter `python3.12` (`-m venv` creates a fake venv whose `bin/python` dispatcher
answers `pip install` by writing stub packages, or by failing when `REHEARSAL_PIP_FAIL=1`, and runs everything else on the
real interpreter with the stubs importable, so `compileall`, the `attest` import and the `attest_revision()` readback are
real). The fake releases were built by `build_bundle.sh` from copies of the public export (`dist/public`, version 0.4.0,
package digest `b27a1c07...`) with the `deploy/yungou` directory under test copied over each copy and synthetic versions
`9.0.1-rehearsal`, `9.0.2-rehearsal`, `9.0.3-rehearsal` (labels `9.0.1-rehearsal-ccf5e0966f75`, `9.0.2-rehearsal-d1fc91722826`,
`9.0.3-rehearsal-970c1318a428`) and `9.0.0-rehearsal` for the legacy previous tree. Every call to a shim is in
`shim-calls.log`; the fake server's log is `fake-health.log`.

1. **Aliyun host** (`rehearsal-aliyun-20261019T075738Z/`): the existing Aliyun Beijing host of `docker-development-environment.md`,
   reached with `ssh -o BatchMode=yes` as root; Linux 5.10.134 (Alibaba Cloud Linux 3) x86_64, bash 4.4.20,
   `/usr/bin/python3.11` (3.11.13; the system `python3` is 3.6.8 and cannot compile the package), GNU tar 1.30. Everything ran
   inside `/tmp/attest-rehearsal-20261019T075738Z/` (uploads: `public-tree.tar.gz` sha256
   `fda660dd560739dc417f341c07dc0843eb8b8191d39671c3caa77a6b63dd4b64`, `deploy-yungou.tar.gz` sha256
   `c5398ca307d956dde8d6fe5f1e0ce3e199fce41a19c294104d1a6344e6567a79`); the dedicated Docker daemon was not used; no systemd
   unit, nginx file or user was created; the directory was removed at the end (`ls -d /tmp/attest-rehearsal-*` found nothing).
   The host name in the copied logs is replaced by `<aliyun-host>`.
2. **macOS workstation** (`rehearsal-local-macos-20261019T075321Z/`): the identical run under bash 3.2.57 with bsdtar 3.5.3 and
   Python 3.12.0, in the session's scratch directory, removed at the end. Local paths and the machine name are replaced by
   `<rehearsal-root>`, `<project>`, `<home>`, `<macos-workstation>` in the copied logs.

Outcomes (both runs identical; `summary.txt`, `summary.json` and one log per scenario):

| Scenario | Injected condition | Expected | Observed |
| --- | --- | --- | --- |
| 1 clean install (`scenario-1-clean-install.log`) | empty root | exit 0, `install complete` | exit 0; `app -> releases/9.0.1-rehearsal-ccf5e0966f75`, no `app.prev`; health `9.0.1-rehearsal`, worker alive; unit with `ExecStart=/opt/attest/app/venv/bin/python`; http-only vhost; `INSTALLED.json` written; 3,125 manifest entries verified twice |
| 2 second install (`scenario-2-second-install.log`) | new version | exit 0, previous kept | exit 0; `app -> 9.0.2-rehearsal-d1fc91722826`, `app.prev -> 9.0.1-...` with its venv; health `9.0.2-rehearsal`; "vhost unchanged; nginx is not touched" |
| 3 dependency failure (`scenario-3-pip-failure.log`) | `pip install` exits 1 | non-zero, previous healthy | exit 1 in step 5, before the switch; `INSTALL FAILED`, "dependency installation failed"; `9.0.2` still active and healthy; the failed release directory removed; no `install complete` |
| 4 health failure (`scenario-4-health-failure.log`) | the service reports `9.9.9-misreported` for the new version | non-zero, previous restored | exit 1 in step 12 ("definitive: the service serves another version"); `app` re-pointed to `9.0.2-...`, restarted, "is healthy (version 9.0.2-rehearsal)"; failed release removed |
| 5 nginx test failure (`scenario-5-nginx-test-failure.log`) | vhost changed, `nginx -t` exits 1 | non-zero, vhost and release untouched | exit 1 in step 8, before the switch; the pre-install vhost restored byte for byte; `9.0.2` active and healthy; no reload |
| 6 rollback (`scenario-6-rollback.log`, `scenario-6-rollback-list.log`) | none | exit 0, previous version serving, digest read back | exit 0; `app -> 9.0.1-...`, `app.prev -> 9.0.2-...`; health `9.0.1-rehearsal`; recorded digest `ccf5e096...a145b8` read back with the release interpreter and equal; 3,125 entries verified in place; zero calls to `nginx-modern` and zero `systemctl reload` during the run; `--list` marks active and previous |
| 7 decommission refused (`scenario-7-decommission-refused.log`) | no `--yes` | exit 2, nothing changed | exit 2; plan printed; service still active; vhost still present |
| 7b decommission (`scenario-7b-decommission-yes.log`) | `--yes` | exit 0 | exit 0; service inactive; vhost removed; both release directories kept |
| 8 legacy migration (`scenario-8-legacy-before.log`, `scenario-8-legacy-migration.log`) | real `app` (9.0.1) and `app.prev` (9.0.0) directories, shared venv, old-style unit | exit 0, migration | exit 0; `app` moved to `releases/legacy-9.0.1-rehearsal-ccf5e0966f75` with `venv -> <root>/opt/attest/venv` and `INSTALLED.json`; `app.prev` moved to `releases/legacy-9.0.0-rehearsal-e32762405a8b`; `app -> 9.0.2-...`, `app.prev -> legacy-9.0.1-...`; health `9.0.2-rehearsal`; unit rewritten to the link interpreter |
| 8b rollback to the legacy release (`scenario-8b-legacy-rollback.log`) | none | exit 0 | exit 0; recorded digest taken from `INSTALLED.json`; `app -> legacy-9.0.1-...`; health `9.0.1-rehearsal` served through the shared venv; "no RELEASE.json in this release (legacy tree)" noted |
| 9 tampered manifest (`scenario-9-tampered-manifest.log`) | `README.md` changed after the build, archive re-packed | non-zero, refused | exit 1 in step 3: "sha256 mismatch: README.md" (size mismatch when the length changes), "the release is refused"; the active release untouched and healthy |

The 19 Oct audit's acceptance for OPS-01 (the expected old revision becomes healthy, the store is preserved, unrelated
configuration unchanged) is met by scenarios 6 and 8b within the shims' reach: the store directory is never opened by either
script, and `shim-calls.log` shows no nginx call during the rollbacks. For OPS-02 (injected dependency, health, config-test and
reload failures never report success and restore the previous release) by scenarios 3, 4, 5 and the unit tests below (the
reload failure path shares the code of the health failure path and is exercised by `test_rollback_failure_after_the_switch...`
only for the rollback; see the limitations). For OPS-03 (the archive carries the promised documents and the installed files
are read back) by the build logs (`build-*.log`: "FREEZE.md, TESTING.md and RELEASE.json present", "manifest and archive agree
on 3125 files") and the readback lines of scenarios 1, 2, 6, 8.

## Acceptance tests (`tests/test_audit_ops.py`, offline, 18 tests)

Run with the whole suite (`python3 -m unittest discover -s tests -t .`, 314 tests, OK) or alone
(`python3 -m unittest tests.test_audit_ops`, about one minute). They run the same scripts under the same shims against a
temporary root with a small release tree (the real `attest/` package with a synthetic version, the deploy directory under
test and one-line documents) bundled by `build_bundle.sh`; skipped when bash or tar is missing; pass under bash 3.2 on macOS
and were written for Linux as well.

- OPS-03: `test_release_manifest_records_version_digest_and_every_member` (the independent digest equals
  `attest.core.provenance.attest_revision()`; archive members and manifest entries agree; sha256 and sizes),
  `test_build_fails_when_a_required_document_is_missing`, `test_build_excludes_env_files_and_lists_nothing_it_did_not_archive`.
- OPS-02: `test_scenario_1_clean_install_switches_and_passes_strict_health`, `test_scenario_2_second_install_keeps_the_previous_release`,
  `test_scenario_3_dependency_failure_leaves_the_previous_release_serving`, `test_scenario_4_health_failure_restores_the_previous_release`,
  `test_scenario_5_nginx_test_failure_restores_vhost_and_previous_release`, `test_install_refuses_a_tampered_release_manifest`,
  `test_install_refuses_a_bundle_without_manifest`, `test_scenario_8_legacy_directory_layout_is_migrated_and_rolled_back`,
  `test_clean_install_health_failure_leaves_no_release_and_stops_the_service`,
  `test_reinstalling_the_active_release_refreshes_without_switching`, `test_old_releases_are_pruned_but_never_the_active_or_previous_one`.
- OPS-01: `test_scenario_6_rollback_restores_previous_release_and_reads_back_its_digest`,
  `test_rollback_refuses_without_a_previous_release_and_changes_nothing`,
  `test_rollback_failure_after_the_switch_re_selects_the_release_that_was_serving`,
  `test_scenario_7_decommission_requires_yes_and_then_removes_only_the_vhost`.

## Residual limitations

- The shims rehearse the scripts' control flow, not systemd, nginx or pip: `systemctl restart` is a fake server start, `nginx -t`
  never parses a configuration (so a duplicate `limit_req_zone`, a missing certificate path or a syntax error in the real vhost
  are only caught on the server), `pip install` writes stubs, and `certifi`, `fastapi`, `uvicorn` are never really imported.
  The fake health answer has the real endpoint's `version` and `worker_alive` fields but synthetic values elsewhere.
- Not reached by the rehearsal: the standalone-interpreter extraction (the interpreter shim existed), the https vhost branch
  (no certificate in the fake roots; the http-only branch ran), a real `systemctl reload nginx` failure (the install path's
  reload failure shares the restore code that scenarios 4 and the rollback failure test exercise), and the `useradd` call
  beyond logging.
- The production migration happens at the next real deployment: the first `install.sh` run on `yungou` moves the real
  `/opt/attest/app` (0.4.0, digest `b27a1c07...`) to `releases/legacy-0.4.0-b27a1c070a85` and `/opt/attest/app.prev` (0.3.0,
  digest `166cdcbd...`) to `releases/legacy-0.3.0-166cdcbd46a7`, both using the shared `/opt/attest/venv` through a symlink;
  their `INSTALLED.json` digests are computed from the trees at migration time, not recorded at build time. Until then
  `rollback.sh` on the server performs the non-atomic directory swap of the old layout.
- The nginx test swaps the vhost on disk for the duration of `nginx -t` (restored on failure, kept until the reload on
  success); a concurrent reload by another operator during that window would pick up the new file early.
- `certifi` stays unpinned in `requirements.txt`, as in the previous installer.
- Each release adds a venv of some tens of megabytes on a volume with about 1.3 GB free; `KEEP_RELEASES=3` prunes older
  releases after a successful install, but free space should be checked before installing (the health JSON reports it).
- `dist/public` was exported before these repairs; the next deployment must re-run the export so that the bundle and the
  uploaded scripts are the repaired ones (`build_bundle.sh` refuses a tree without `deploy/yungou/requirements.txt`).
- The rehearsal logs were copied with local paths and host names replaced (`<rehearsal-root>`, `<project>`, `<home>`,
  `<macos-workstation>`, `<aliyun-host>`); the two `shim-calls.log` files list every host command the scripts issued.

## Delivered files (sha256 of the scripts as rehearsed)

The scripts were not changed after the Aliyun run; these digests identify the rehearsed content (the uploaded
`deploy-yungou.tar.gz` additionally carried the deployment README, which was still being rewritten at upload time).
The driver's own stamp inside the Aliyun logs is `20261019T080407Z`, the start of the run after the upload into
`/tmp/attest-rehearsal-20261019T075738Z/`.

| File | sha256 |
| --- | --- |
| `deploy/yungou/install.sh` | `2273b6b4b83dfd4b73e04501ce55ebf4ec79e88c7d96d701e860bdb76a3dc103` |
| `deploy/yungou/rollback.sh` | `6c800209d321f6aad40e3b262bc07cfb761311b1d46b15ec1369042d91ac9e27` |
| `deploy/yungou/decommission.sh` | `805d9af2cef22563eb4a8a062017343e09c8fc94f1237f5e5f3bdc372ae6e41b` |
| `deploy/yungou/build_bundle.sh` | `f859fbb1444bf043dff893f69ba6ab5a50ff35a632945f37e088d15275688eda` |
| `deploy/yungou/snapshot.sh` | `865216d3e8a9efcf7617e1c65dba0e22768cfa85aabf5e84773f650d53a9c0a7` |
| `deploy/yungou/attest.service` | `c98104a8bead8890ddf0f5b51cfd2dd0219a635d901fea48ab92d3f7c94555f7` |
| `deploy/yungou/requirements.txt` | `8dbbf4b7ac7bed7623b65f6f841b79861ac06b9bc115d0d3aeb2a73c9997af70` |
| `deploy/yungou/rehearsal/rehearse.sh` | `ee78589dd58d69287740299f9d85593257fc2441af92dabf0a15d30849f67efb` |
| `deploy/yungou/rehearsal/shims/systemctl` | `2bbd44dba641b1648bcac5a597baf34116433093c6e64e8d9a74d4d93c54361a` |
| `deploy/yungou/rehearsal/shims/nginx-modern` | `0bb484253b334325f0bc22e5857119c678bea0267312c6b3a636e91b6edd4596` |
| `deploy/yungou/rehearsal/shims/python3.12` | `abe731173930922718c96aef6d3b43e4bd07a6b714d2435ad8a5ce0499742eb4` |
| `deploy/yungou/rehearsal/shims/venv-python` | `4e818366428a858126771220cc4b25516fcec7f584aa2002fde377692cd8a510` |
| `deploy/yungou/rehearsal/shims/install` | `74004a2fd1b0e724ab66ac6bd03f5f699d314843118dab9a7a3f914cd6af46b1` |
| `deploy/yungou/rehearsal/shims/useradd` | `73f428ec79c0fdd99c4eb238bfff966cbcd2de50b85a27569e921ef0faf84c5c` |
| `deploy/yungou/rehearsal/shims/chown` | `536ef52717db0b3205e5686058839e42e4c800c0c79132a9a887d0cf6cc4df83` |
| `deploy/yungou/rehearsal/shims/_log.sh` | `b2376278bc6f8f690b2db4b670ab31b74dcd5003f94f79f980d72e2cf5dadc29` |
| `deploy/yungou/rehearsal/shims/fake_health.py` | `34b106b18a10fa18c5117bffe175d0b0acebf37f93490e40b7eb351b269ce27c` |

## Changes needed outside these files

- The next deployment record (`reports/attest-deployment-<date>/README.md`) must describe `rollback.sh` as the scoped version
  rollback above and `decommission.sh --yes` as the removal; the 19 Oct record's "Rollback" paragraph describes the old
  scripts and stays as written (historical). `deployment-plan-yungou.md` line 52 defines the old stop-and-remove rollback;
  it is the plan of 15 Oct and was left untouched.
- `TESTING.md` may mention that the offline suite now includes the deployment-script tests (about one extra minute);
  `FREEZE.md` is unaffected (no change under `attest/`).
- `reports/attest-audit-2026-10-19/README.md` keeps its OPS rows as the audit's statement; the orchestrator decides how the
  repair status is recorded.
