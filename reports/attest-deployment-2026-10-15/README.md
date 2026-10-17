# Deployment of the Attest console to `yungou` (DogYun `206.237.18.80`), 2026-10-15/16

Owner decision: `yungou` = `206.237.18.80`; console, API, orchestration and application data on this host, no Docker;
Nebius Sandboxes remain the executor; the Aliyun `attest-docker` daemon is reserved for components that genuinely need
Docker (none deployed). All timestamps UTC unless marked host time (CST).

## What was installed

| Item | Value |
| --- | --- |
| Interpreter | python-build-standalone CPython 3.12.15 (`20261013`, x86_64 glibc 2.17 build, bundled OpenSSL 3.5.9), SHA-256 verified locally against the release `SHA256SUMS` and again after upload; `/opt/attest/python` |
| Virtualenv | `/opt/attest/venv` with `fastapi==0.115.5`, `uvicorn[standard]==0.32.1`, `jsonschema==4.23.0`, `certifi` |
| Application | `/opt/attest/app` from `app.tar.gz` (package, examples, tests, deploy files, evidence reports; no runs, venv or secrets) |
| Service | `attest.service`, user `attest` (no shell), `uvicorn` on `127.0.0.1:4070`, `MemoryMax=200M`, `CPUQuota=60%`, `NoNewPrivileges`, `ProtectSystem=full`, `ProtectHome`, `PrivateTmp`, `ReadWritePaths=/var/lib/attest` |
| Data | `/var/lib/attest` (SQLite `attest.db`, run directories); evidence runs imported from the bundled reports on startup |
| Secrets | `/etc/attest/attest.env` root:attest 0640, written over SSH from the private vault (never through chat or git); admin token kept in the private deployment note |
| Web entry | `https://attest.axiqo.xyz` via the existing `nginx-modern` (1.30.3): vhost `/etc/nginx/conf.d/attest.axiqo.xyz.conf`, rate-limit zone 5 r/s on `/api/`, Let's Encrypt certificate issued with the webroot method (`/var/www/letsencrypt`), `renew_hook = systemctl reload nginx`, renewal dry run succeeded |
| Scripts | `deploy/yungou/`: `install.sh` (idempotent), `rollback.sh` (scoped), `snapshot.sh`, `build_bundle.sh`; config tests use the running binary `/usr/local/sbin/nginx-modern -t` |

## Health and resource usage before and after

Before snapshot `before.txt` (15:40:19Z) and after snapshot `after.txt` (16:14Z, taken after the public judge run):

```
running services: added ['attest.service'] | removed -
failed services: added - | removed -
listeners: added ['127.0.0.1:4070'] | removed -
containers: added - | removed -
health endpoints: added - | removed -
memory used/available: before 376/220 MB -> after 336/263 MB
disk free: before 1.7G (88%) -> after 1.4G (90%)
```

Only `attest.service` and its loopback listener were added. No other unit, listener, container or health endpoint changed;
the four pre-existing public endpoints answered 200 before and after. The ~300 MB of disk went to the interpreter and venv.

Service memory (systemd `MemoryCurrent`): 45.7 MB right after start, 55 MB at the start of the judge run, 41.8 MB after the
reinstall; see `memory-peak.txt` for the sampled peak during the judge run. The 200 MB cap is therefore at least three times
the observed footprint; it is a hard cgroup limit and is kept at 200M.

## Public judge-style run (no admin token, Nemotron profile)

`POST /api/runs` from this Mac: run `durationkit-units-001-20261015T161057714040Z`, requester 63.88.223.28, profile `judge-demo`,
status `finished`, verdict **NEEDS HUMAN**, 27 progress events, 17 model calls,
9 sandbox operations, computed cost $0.059635, wall 16:10:57 to 16:13:53.
Reasons recorded: implementer did not finish within 14 turns; child process nonzero exit: test_number_without_unit_in_multi_component_raises exit 1. Record: `judge-run-record.json`; the downloadable Proof Bundle
fetched from the public API: `judge-run-proof-bundle.zip`. The verdict is consistent with the evidence: one sealed test failed
and the implementer ran out of turns, so the console shows the unresolved failures rather than a success.

## Rollback test (`rollback-test.log`)

`rollback.sh` stopped and disabled only `attest.service` and removed only its vhost; the four other sites still answered 200
and the console hostname stopped answering; `install.sh` then reinstalled, the service came back active (41.8 MB) and the
public health endpoint and page answered 200 again. Data, interpreter and venv were preserved throughout.

## Residual notes

- The host has about 260 MB available memory; the console uses 40 to 60 MB. Running the pipeline inside the worker keeps it in
  that range because execution happens in Sandboxes.
- CentOS 7 is end of life; the standalone interpreter avoids the system Python and OpenSSL.
- `certbot renew` is driven by the existing timer; the dry run for this certificate succeeded.
- Disk is at 90 %; run directories under `/var/lib/attest/runs` should be pruned periodically (not yet automated).

## Second public judge-style run (python-semver, 30 files, pinned pytest) with memory sampling

- peak MemoryCurrent during judge run semver-is-compatible-pr368-20261015T161925564951Z: 52 MB over 6 samples
- JUDGE RUN 2 semver-is-compatible-pr368-20261015T161925564951Z finished NEEDS HUMAN cost 0.063988 events 22 gates {'existing_suite': True, 'sealed_binding': True, 'heldout_suite': False, 'mutation': True, 'adversarial_tests': False, 'drift_audit': True} reasons ['held-out tests failed: 3 of 328 (tests/test_heldout_pr368.py::test_should_fail_with_incompatible_type_for_compatible_mat', 'model-written adversarial tests failed: 1 of 14 (test_breaker.TestIsCompatibleBreaker.test_subclass_accepted_with_extra_'] wall 16:19:25 -> 16:21:17
