# Deployment of revision 8 (version 0.8.0) to yungou, 19 Oct 2026

What is deployed: revision 8 (`reports/attest-revision7-repairs-2026-10-19/README.md`): the memory limit made effective on the
host's systemd 219, phase-aware transport with bounded resends of never-sent requests and reconciliation of uncertain ones, the
explicit-start confirmation (`X-Attest-Confirm`, the console's confirmation step), inference labelled by service, the phone layout,
and the export privacy repair, with the updated documentation and the new evidence folders. The release is built from a clean
checkout of the review repository at the pin record `6eca557` (code commit `35248d0`); its package digest is `68e9de49df5b…` (37
sources).

Scope: the Attest service only (`attest.service`, its unit, `/opt/attest`). The unit changes (memory directives); the vhost does not,
so nginx is not reloaded. No Docker component is needed; nothing changes on the Aliyun host. Every check of production is
read-only: GET requests, a browser that blocks every other request before it is sent, and read-only commands over SSH.

## Build

`deploy/yungou/build_bundle.sh` run from a clean `git worktree` of `6eca557` (`build-20261019e.log`): `app.tar.gz`, 8,448,984 bytes,
4,343 members, sha256 `2237a5a9c9b1898f388367b0bc8320d8241097b4b3395ac40d950dc168ba54b9`, `RELEASE.json` with 3,856 entries
(version 0.8.0, package digest `68e9de49…`, label `0.8.0-68e9de49df5b`); no secret-like paths, screenshots, snapshots or AppleDouble
files. The bundle, the installer, the rollback, decommission and snapshot scripts, the unit, the vhost and the server-side step
script were uploaded with their digests (`upload-20261019e.sha256`) and checked with `sha256sum -c` on the host.
