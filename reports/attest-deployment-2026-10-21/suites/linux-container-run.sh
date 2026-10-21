#!/bin/sh
# The offline suite of a clean `git archive` of the review repository, in a container with no network interface (revision 9).
cd /work
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) container: Alpine $(cat /etc/alpine-release 2>/dev/null), $(python3 --version 2>&1), uid $(id -u)"
echo "=== network interfaces in this container (from /proc/net/dev):"
awk 'NR>2 {print "    " $1}' /proc/net/dev
echo "=== tools: bash $(command -v bash || echo absent), git $(command -v git || echo absent), node $(command -v node || echo absent), tar $(command -v tar || echo absent)"
echo "=== environment variable names: $(env | cut -d= -f1 | sort | tr '\n' ' ')"
python3 -m venv /work/venv && /work/venv/bin/pip install -q --no-index --disable-pip-version-check --find-links /work/wheels -r /work/requirements.txt || exit 3
echo "=== installed offline from the wheelhouse: $(/work/venv/bin/pip freeze --disable-pip-version-check | tr '\n' ' ')"
echo "=== probe:"
/work/venv/bin/python -c "
import socket
for target in (('1.1.1.1', 443), ('8.8.8.8', 53)):
    try:
        socket.create_connection(target, timeout=3); print('    connect', target, 'SUCCEEDED')
    except OSError as e: print('    connect', target, 'refused:', type(e).__name__, e.errno)
try:
    socket.getaddrinfo('example.com', 443); print('    name lookup SUCCEEDED')
except OSError as e: print('    name lookup refused:', type(e).__name__)"
echo "=== python -m unittest discover -s tests -t . -v"
cd /work/src && HOME=/work/home /work/venv/bin/python -m unittest discover -s tests -t . -v
status=$?
echo "=== exit $status"
exit $status
