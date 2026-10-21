#!/bin/bash
cd <scratch>/r11/wt-7c48b3f
{
echo "=== $(date -u +%FT%TZ) clean checkout $(git rev-parse HEAD) (macOS, sandbox-exec profile offline-v2.sb: outbound network denied except loopback; env -i; HOME new and empty; shutil.disk_usage patched by lowdisk-sitecustomize.py to report 1 % free)"
echo "=== the patch inside the same sandbox and environment: $(env -i PATH="<scratch>/venv-clean/bin:/usr/bin:/bin" HOME=<scratch>/r11/home-lowdisk LANG=C.UTF-8 PYTHONPATH=<scratch>/lowdisk sandbox-exec -f <scratch>/offline-v2.sb <scratch>/venv-clean/bin/python -c 'import shutil; u = shutil.disk_usage("."); print("disk_usage reports", round(u.free / u.total, 4), "free")')"
echo "=== HOME entries before: $(ls -A <scratch>/r11/home-lowdisk | wc -l)"
env -i PATH="<scratch>/venv-clean/bin:<node>/bin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=<scratch>/r11/home-lowdisk LANG=C.UTF-8 PYTHONPATH=<scratch>/lowdisk sandbox-exec -f <scratch>/offline-v2.sb <scratch>/venv-clean/bin/python -m unittest discover -s tests -t . -v
echo "=== exit $?"
echo "=== HOME entries afterwards: $(ls -A <scratch>/r11/home-lowdisk | wc -l); checkout status: $(git status --short | wc -l) changed"
} > <scratch>/r11/suite-lowdisk-7c48b3f.log 2>&1
