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

Revision 8 was installed on 19 Oct at 20:42 UTC (`reports/attest-deployment-2026-10-19e/`) with `MEMORY_MAX=200M`.

- The installer's readback (`install-20261019e.log`, step 13, right after the restart): systemd `MemoryLimit=209715200`,
  `memory.limit_in_bytes=209715200`, `memory.memsw.limit_in_bytes=209715200`, main PID 2241 in the memory cgroup
  `/system.slice/attest.service`.
- The readback by hand, 20:49 UTC (`readback-after-deploy.txt`, produced by `readback.sh`, read-only): the same three limits;
  `MemoryAccounting=yes`; usage 41.8 MB (memory and memory plus swap), peak 43.5 MB, both fail counters 0, `oom_kill 0`; the main
  process 48.9 MB resident with no swap. Before the deployment (`readback-before-deploy.txt`) all of these read "no limit".
- The application drill, 20:50:53 UTC (`drill-app-run-1.txt`; `drill/drill_app.py`, `drill/attest-app-oom-drill.service`,
  `drill/run-app-drill.sh`): the deployed interpreter and code (`/opt/attest/app`) in a temporary unit with the same mechanism at
  128M (`MemoryLimit=128M` and the memory-plus-swap `ExecStartPre`, `Restart=on-failure`), a scratch store and no credentials. The
  first process imported the console application, recorded a run of the Nemotron profile in flight the way the worker does (its row
  `running`; its ledger journal with an open $0.0175 reservation and a Sandboxes operation accepted but not yet read; no request was
  sent anywhere) and allocated 8 MiB steps. At 96 MiB of allocations (137 MB resident) the kernel's memory-cgroup OOM killer ended
  it: `memory+swap: usage 131072kB, limit 131072kB`, `oom-kill:constraint=CONSTRAINT_MEMCG ...
  oom_memcg=/system.slice/attest-app-oom-drill.service`, `Killed process 2684 (python)`. systemd restarted the unit 3 s later; the
  new process's start-up settled the run: status `error`, stage and code `interrupted`, $0.0175 committed (the reservation kept at
  its bound), and the accepted operation `00000000-0000-0000-0000-00000000d311` named as never read. `attest.service` kept MainPID
  2241 and stayed healthy; the temporary unit, its directory and the uploaded files were removed by the script.

So the limit is enforced on the running service (configuration, systemd and kernel agree), the kernel ends the process at the limit
instead of letting it swap, systemd brings it back, and a run cut short this way is settled as interrupted with its committed cost
and its unread operation on record. The drill did not run `attest.service` itself out of memory: that would have interrupted the
public console.

## Sizing

The service uses 42 to 55 MB when idle (uvicorn, FastAPI and the worker). A run adds the pipeline: the development harness, which runs
the same pipeline without the web server, peaked at 55.7 MiB of resident memory while two pipelines ran at once, one of them a
complete VERIFIED run with mutation and adversarial testing (the second batch of this pass; 53.2 and 51.0 MiB in the others). The
largest bundle the console loads is 358 KB. 200M therefore leaves about three times the expected peak of one run plus the server.
