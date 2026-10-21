#!/bin/bash
cd <scratch>/r11/wt-7c48b3f
{
echo "=== $(date -u +%FT%TZ) clean checkout $(git rev-parse HEAD) (macOS, sandbox-exec profile offline-v2.sb: outbound network denied except loopback; env -i; HOME new and empty)"
echo "=== HOME entries before: $(ls -A <scratch>/r11/home-7c48b3f | wc -l)"
env -i PATH="<scratch>/venv-clean/bin:<node>/bin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=<scratch>/r11/home-7c48b3f LANG=C.UTF-8 sandbox-exec -f <scratch>/offline-v2.sb <scratch>/venv-clean/bin/python -m unittest discover -s tests -t . -v
echo "=== exit $?"
echo "=== HOME entries afterwards: $(ls -A <scratch>/r11/home-7c48b3f | wc -l); checkout status: $(git status --short | wc -l) changed"
} > <scratch>/r11/suite-macos-7c48b3f.log 2>&1
