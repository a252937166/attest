"""Memory-limit drill for the mechanism of attest.service's unit on yungou (revision 8, 19 Oct 2026).

Allocates memory in 8 MiB steps, writing to every page so the memory is really used, and logs each step durably. Under MemoryLimit=
plus memory.memsw.limit_in_bytes the kernel's memory-cgroup OOM killer must end it at the limit, and Restart=on-failure must start it
again; the second start finds the marker and exits 0. With --no-marker (the contrast unit, MemoryLimit= alone) it allocates up to
the given size and exits 0, logging VmSwap so the log shows where the excess went.
Usage: drill.py <state dir> <max MiB> [--no-marker]"""
import os
import sys
import time

state, max_mb = sys.argv[1], int(sys.argv[2])
marker = os.path.join(state, "allocated-once")


def log(message):
    with open(os.path.join(state, "drill.log"), "a") as handle:
        handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} pid={os.getpid()} {message}\n")
        handle.flush()
        os.fsync(handle.fileno())


def memory_cgroup():
    with open("/proc/self/cgroup") as handle:
        return next((line.strip() for line in handle if ":memory:" in line), "no memory cgroup")


def status():
    with open("/proc/self/status") as handle:
        return " ".join(f"{line.split()[0]}{line.split()[1]}kB" for line in handle if line.startswith(("VmRSS", "VmSwap")))


if os.path.exists(marker) and "--no-marker" not in sys.argv:
    log(f"started again after the previous process ended; {memory_cgroup()}; exiting 0")
    sys.exit(0)
open(marker, "w").close()
log(f"start; {memory_cgroup()}; allocating up to {max_mb} MiB in 8 MiB steps")
blocks = []
for step in range(1, max_mb // 8 + 1):
    block = bytearray(8 << 20)
    for offset in range(0, len(block), 4096):
        block[offset] = 1
    blocks.append(block)
    log(f"allocated {step * 8} MiB; {status()}")
log(f"reached {max_mb} MiB without being killed; exiting 0")
