"""The one gate-to-verdict rule, used by the pipeline when it decides and by `attest check` when it re-derives.

VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the
scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing
generated test was classified as a defect, corrected and re-verified. Abort verdicts (INFEASIBLE, NO CHANGE, ERROR,
BASELINE) are decided before any gate exists and are outside this rule.
"""

from __future__ import annotations

RULE = ("VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the "
        "scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing "
        "generated test was corrected and re-verified.")
ABORT_VERDICTS = ("INFEASIBLE", "NO CHANGE", "ERROR", "BASELINE")


def derive(gates: dict, candidate: dict | None, binding_ok: bool | None = None, arbitration: dict | None = None,
           apply: bool = False) -> dict:
    """Pure function of the recorded gates and candidate facts. Returns the verdict and what blocked VERIFIED."""
    candidate = candidate or {}
    failed = [name for name, gate in gates.items() if not gate.get("ok") and not gate.get("skipped")]
    skipped = [name for name, gate in gates.items() if gate.get("skipped")]
    blocking = list(failed) + [f"{name} (not run)" for name in skipped]
    if binding_ok is False and "sealed_binding" not in failed:
        blocking.append("sealed binding failed")
    if candidate.get("scope_ok") is False:
        blocking.append("scope policy violated")
    if candidate.get("implementer_finished") is False:
        blocking.append("implementer did not finish")
    verdict = "VERIFIED" if not blocking else "NEEDS HUMAN"
    cleared = False
    if verdict == "NEEDS HUMAN" and apply and arbitration and arbitration.get("cleared"):
        verdict, cleared = "VERIFIED", True
    return {"verdict": verdict, "gates_failed": failed, "gates_skipped": skipped, "blocking": blocking,
            "cleared_by_arbitration": cleared, "rule": RULE}


def expected_verdict(bundle: dict) -> dict:
    """Re-derive the verdict of a recorded bundle. For abort verdicts only the absence of gates is checked."""
    recorded = (bundle.get("verdict") or {}).get("verdict")
    gates = bundle.get("gates") or {}
    if not gates:
        # decided before verification: anything but VERIFIED is admissible
        ok = recorded != "VERIFIED"
        return {"applicable": False, "recorded": recorded, "derived": None, "consistent": ok,
                "detail": "no gates recorded; a verdict decided before verification cannot be VERIFIED" if not ok else "no gates recorded (decided before verification)"}
    arbitration = bundle.get("arbitration")
    apply = bool((bundle.get("verdict") or {}).get("cleared_by_arbitration")) or bool((arbitration or {}).get("applied"))
    derived = derive(gates, bundle.get("candidate"), ((bundle.get("verification") or {}).get("binding") or {}).get("ok"), arbitration, apply)
    if recorded in ABORT_VERDICTS:
        # gates exist but the run aborted afterwards (for example an error in a late stage): nothing to compare
        return {"applicable": False, "recorded": recorded, "derived": derived["verdict"], "consistent": True,
                "detail": f"{recorded} recorded after the gates; derivation not applicable"}
    consistent = derived["verdict"] == recorded
    return {"applicable": True, "recorded": recorded, "derived": derived["verdict"], "consistent": consistent,
            "blocking": derived["blocking"], "cleared_by_arbitration": derived["cleared_by_arbitration"],
            "detail": ("gates and verdict agree" if consistent else f"gates derive {derived['verdict']} but the bundle records {recorded}")}
