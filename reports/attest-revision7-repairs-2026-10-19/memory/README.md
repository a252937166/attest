# Memory limit on yungou: made effective and verified (revision 8, 19 October 2026)

## What was wrong

The unit has carried `MemoryMax=200M` since the first deployment. yungou runs CentOS 7.9 with systemd 219 and a 5.13 kernel on
cgroup v1: systemd 219 does not know `MemoryMax=` (it logs `Unknown lvalue 'MemoryMax' in section 'Service'` at every
daemon-reload, for example on 19 Oct at 16:47, 19:03 and 23:29 host time) and nothing else limited the service:
`MemoryAccounting=no`, `MemoryLimit=18446744073709551615`, `memory.limit_in_bytes` and `memory.memsw.limit_in_bytes`
9223372036854771712 (read on 19 Oct at about 17:40 UTC, `memory.max_usage_in_bytes` 55 MB since the 15:29 UTC restart). The host has
728 MB of memory and 1.5 GB of swap, and the kernel has swap accounting (`memory.memsw.*` exists).

## The repair

`deploy/yungou/attest.service` sets `MemoryAccounting=yes` and `MemoryLimit=` (systemd 219 applies it as
`memory.limit_in_bytes`; `MemoryMax=` stays for newer systemd), and an `ExecStartPre` running as root writes the same size to
`memory.memsw.limit_in_bytes` (memory plus swap) before the service process exists, so the service can neither exceed the limit in
memory nor page past it into swap. `deploy/yungou/install.sh` reads the limit in force back after every restart (systemd's
`MemoryLimit`, both cgroup limits, the main process's cgroup) and fails, restoring the previous release and unit, when it differs.
Tests: `tests/test_audit_ops.py` scenario 1 (the readback on a fake systemd-219 host), scenario 9 (a unit with only `MemoryMax=`,
as before revision 8, fails the install and the previous unit is restored) and scenario 10 (a memory-plus-swap file that cannot be
written fails the start and the install).

## The drill on the host (temporary units; attest.service untouched)

`drill/` holds the script and the two units; `run-drill.sh` installed them, ran them, collected the logs and removed everything
(units, files) again. `attest.service` kept the same main process throughout (PID 29680 before and after) and stayed healthy.

- First attempt (`drill-run-1-failed-privatetmp.txt`, 18:49 UTC): both units failed to start with status 200 (working
  directory): the drill directory was under `/var/tmp`, which `PrivateTmp=true` replaces with a private one. Nothing ran. The
  directory was moved to `/var/lib/attest-oom-drill` and the drill repeated.
- Drill 1 (`drill-run-2.txt`, 18:51:29 UTC): the same mechanism as the service at 96M (MemoryLimit and the memory-plus-swap
  `ExecStartPre`, `Restart=on-failure`), a process that allocates 8 MiB steps and writes to every page. It reached 88 MiB of
  allocations (RSS 101 MB) and the kernel's memory-cgroup OOM killer ended it: `memory: usage 98304kB, limit 98304kB`,
  `memory+swap: usage 98304kB, limit 98304kB`, `oom-kill:constraint=CONSTRAINT_MEMCG ... oom_memcg=/system.slice/attest-oom-drill.service`,
  `Killed process 588 (python) ... anon-rss:97760kB`. systemd recorded `main process exited, code=killed, status=9/KILL`, scheduled
  the restart and started the unit 3 s later; the second start logged itself and exited 0.
- Drill 2, the contrast (`drill-run-2.txt`, 18:51:33 UTC): `MemoryLimit=96M` alone, without the memory-plus-swap limit. The same
  process allocated 160 MiB and was not killed: its resident memory stayed at about 105 MB and `VmSwap` grew to 70 MB. A memory
  limit alone does not bound what the service can take from the host.

## On the service (after the deployment)

To be recorded after the deployment of revision 8: the limit read back by the installer and by hand (systemd, both cgroup files,
the main process's cgroup), and a drill of the application itself (the deployed release, in a temporary unit with a scratch store:
a run in flight is ended by the OOM killer, and the restarted process settles it as interrupted with its reservation committed).

## Sizing

The service uses 42 to 55 MB when idle (uvicorn, FastAPI and the worker). A run adds the pipeline: the development harness, which runs
the same pipeline without the web server, peaked at 55.7 MiB of resident memory while two pipelines ran at once, one of them a
complete VERIFIED run with mutation and adversarial testing (the second batch of this pass; 53.2 and 51.0 MiB in the others). The
largest bundle the console loads is 358 KB. 200M therefore leaves about three times the expected peak of one run plus the server.
