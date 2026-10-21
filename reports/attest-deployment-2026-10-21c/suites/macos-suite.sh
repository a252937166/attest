#!/bin/bash
cd <scratch>/r12/wt-5359880
{
echo "=== $(date -u +%FT%TZ) clean checkout $(git rev-parse HEAD) (macOS, sandbox-exec profile offline-v2.sb: outbound network denied except loopback; env -i; HOME new and empty)"
echo "=== HOME entries before: $(ls -A <scratch>/r12/home-5359880 | wc -l)"
env -i PATH="<scratch>/venv-clean/bin:<node>/bin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=<scratch>/r12/home-5359880 LANG=C.UTF-8 sandbox-exec -f <scratch>/offline-v2.sb <scratch>/venv-clean/bin/python -m unittest discover -s tests -t . -v
echo "=== exit $?"
echo "=== HOME entries afterwards: $(ls -A <scratch>/r12/home-5359880 | wc -l); checkout status: $(git status --short | wc -l) changed"
} > <scratch>/r12/suite-macos-5359880.log 2>&1
