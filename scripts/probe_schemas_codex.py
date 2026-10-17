#!/usr/bin/env python3
"""Exercise every structured-output schema directly against the development gateway (one tiny request per schema).

Why: the gateway and Token Factory run structured output in strict mode; a schema that lists a property without naming it
in `required` is rejected with HTTP 502 before any model runs. The 17 Oct external-task run lost its arbitration that way.
This probe sends each real schema with a small prompt and validates the answer against the same schema, so the path that
`tests/test_reliability.py::StrictSchemas` checks statically is also exercised live. Development gateway only; no USD.

Usage: probe_schemas_codex.py --out reports/<dir>/schema-probe.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from attest.core import prompts  # noqa: E402
from attest.ledger import Ledger, utcnow  # noqa: E402
from attest.models.base import ModelError, validate_json  # noqa: E402
from attest.models.codex_gateway import CodexGateway  # noqa: E402
from attest.secrets import load_secret  # noqa: E402

PROBES = {
    "SPEC_SCHEMA": ("spec", "Task: add a function add(a, b) returning a + b for ints to module m. Produce the specification JSON; keep every list to one short entry."),
    "SEAL_SCHEMA": ("seal", "Return a minimal unittest module as test_file (one TestCase, one test asserting add(1, 2) == 3 from `from m import add`), test_count 1, notes one line."),
    "BREAKER_SCHEMA": ("break", "Return a minimal unittest module as test_file (one TestCase, one test asserting add(0, 0) == 0 from `from m import add`), test_count 1, notes one line."),
    "ARBITRATION_SCHEMA": ("arbitrate", "One generated test `test_mod.T.test_x` failed with AssertionError: -1 != 1 while asserting a private helper's result that the contract leaves unspecified. "
                                        "Classify it (test_defect, defect_kind unspecified_behavior), rationale and contract_basis one sentence each, corrected_module null, corrected_notes one sentence."),
    "DRIFT_SCHEMA": ("audit", "The implementer added exactly the requested function and nothing else. Return drift_score 0.0, assessment aligned, empty lists, a two-sentence summary."),
    "ACTION_SCHEMA": ("implement", "Return the single action `finish` with summary 'done' and reason 'probe'; every other field null."),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ledger = Ledger()
    client = CodexGateway(load_secret("CODEX_API_KEY"), ledger, notify=lambda m: print(f"[pacing] {m}", flush=True))
    results = []
    for name, (role, prompt) in PROBES.items():
        schema = getattr(prompts, name)
        t0 = time.monotonic()
        entry = {"schema": name, "role": role, "model": None, "effort": None, "ok": False, "elapsed_s": None, "error": None, "answer_head": None}
        try:
            result = client.structured(role, prompt, schema, f"probe-{name}")
            entry.update({"ok": validate_json(result.json, schema) is None, "model": result.call.returned_model, "effort": result.call.returned_effort,
                          "answer_head": json.dumps(result.json)[:200], "tokens_in": result.call.tokens_in, "tokens_out": result.call.tokens_out})
        except ModelError as error:
            entry["error"] = str(error)[:300]
        entry["elapsed_s"] = round(time.monotonic() - t0, 1)
        results.append(entry)
        print(f"{name:<19} {'ok' if entry['ok'] else 'FAILED'} {entry['elapsed_s']}s {entry['error'] or entry['answer_head']}", flush=True)
    record = {"probed_at_utc": utcnow(), "gateway_policy": client.governor.policy_source, "results": results,
              "all_ok": all(r["ok"] for r in results), "ledger_totals": ledger.totals()}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("all schemas accepted and answers valid" if record["all_ok"] else "SOME SCHEMAS FAILED", "->", args.out)
    return 0 if record["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
