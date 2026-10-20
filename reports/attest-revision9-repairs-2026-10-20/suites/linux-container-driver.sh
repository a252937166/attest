#!/bin/sh
# Runs the offline suite of the payload in a container with no network interface on the dedicated Docker daemon; removes it after.
set -u
D=/root/attest-r9-suite
cd "$D"
docker=/usr/local/bin/attest-docker
{
echo "=== host before: $(uptime | sed 's/.*load/load/'); $(free -m | awk '/Mem:/ {print "available " $7 " MB"}'); codex-api $(systemctl is-active codex-api)"
echo "=== payload sha256 $(sha256sum payload.tar.gz | cut -c1-64)"
$docker rm -f attest-r9-suite >/dev/null 2>&1 || true
$docker create --name attest-r9-suite --network none --memory 384m --memory-swap 384m --cpus 1 --pids-limit 400 --user 65534:65534 \
  --cap-drop ALL --security-opt no-new-privileges --workdir /work python:3.12-alpine /work/run.sh >/dev/null
gunzip -c payload.tar.gz | $docker cp -a - attest-r9-suite:/
echo "=== container config: $($docker inspect attest-r9-suite --format 'network={{.HostConfig.NetworkMode}} memory={{.HostConfig.Memory}} memory+swap={{.HostConfig.MemorySwap}} nano_cpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}} user={{.Config.User}} cap_drop={{.HostConfig.CapDrop}} security_opt={{.HostConfig.SecurityOpt}} image={{.Image}}')"
} > suite.log 2>&1
$docker start -a attest-r9-suite >> suite.log 2>&1
echo "=== container exit $?" >> suite.log
echo "=== container state: $($docker inspect attest-r9-suite --format 'oom_killed={{.State.OOMKilled}} exit={{.State.ExitCode}}')" >> suite.log
$docker rm -f attest-r9-suite >/dev/null 2>&1
echo "=== host after: $(uptime | sed 's/.*load/load/'); $(free -m | awk '/Mem:/ {print "available " $7 " MB"}'); codex-api $(systemctl is-active codex-api); containers left: $($docker ps -aq | wc -l)" >> suite.log
echo done > done.flag
