# Deployment of revision 8 (version 0.8.0) to yungou, 19 Oct 2026

What is deployed: revision 8 (`reports/attest-revision7-repairs-2026-10-19/README.md`): the memory limit made effective on the
host's systemd 219, phase-aware transport with bounded resends of never-sent requests and reconciliation of uncertain ones, the
explicit-start confirmation (`X-Attest-Confirm`, the console's confirmation step), inference labelled by service, the phone layout,
and the export privacy repair, with the updated documentation and the new evidence folders. The release is built from a clean checkout of the review repository at the revision-8 pin record (`FREEZE.md`, revision-8 pin).

Scope: the Attest service only (`attest.service`, its unit, `/opt/attest`). The unit changes (memory directives); the vhost does not,
so nginx is not reloaded. No Docker component is needed; nothing changes on the Aliyun host. Every check of production is
read-only: GET requests, a browser that blocks every other request before it is sent, and read-only commands over SSH.
