#!/bin/bash
# Operator loop (17 Oct 2026): the frozen method stops the batch on any transport-uncertain operation and never replays it;
# the operator resumes the batch so that the cells never started get their turn. Each resumption is recorded by the harness
# in schedule.json (resumptions) and the ERROR cells keep their records. Bounded to 8 resumptions.
F=/tmp/attest-session/cf18679a-7623-4fd1-bc3b-8078747f8e50/scratchpad/attest-eval-frozen
OUT=/work/attest/reports/attest-evaluation-2026-10-17-nebius-m5/batch
cd "$F" || exit 1
for i in 3 4 5 6 7 8 9 10; do
  left=$(python3 -c "import json; e=json.load(open('$OUT/evaluation.json')); print(sum(1 for r in e['rows'] if r.get('status')=='not_run'))")
  echo "[$(date -u +%H:%M:%S)] segment $i: $left cells not run"
  [ "$left" = "0" ] && break
  python3 scripts/run_evaluation.py --provider nebius --suite examples/eval/SUITE-M5.json --systems baseline,attest --attempts 2 --workers 2 --usd-cap 0.5 --max-calls 20 --max-turns 14 --approve-usd 9.00 --label m5-final --resume "$OUT" > "$OUT-segment$i.log" 2>&1
  grep -E 'stopped|refusing' "$OUT-segment$i.log" | tail -1 | cut -c1-160
done
python3 -c "import json; e=json.load(open('$OUT/evaluation.json')); import collections; print('final status', dict(collections.Counter(r['status'] for r in e['rows'])), 'committed', e['budget']['committed_usd'], 'resumptions', len(e['schedule'].get('resumptions', [])))"
