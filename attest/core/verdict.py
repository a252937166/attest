"""The one gate-to-verdict rule, used by the pipeline when it decides and by `attest check` when it re-derives.

VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the
scope policy held; otherwise NEEDS HUMAN. A gate may pass on a corrected generated-test module only when the correction
was validated by execution and the gate was re-run (the gate record then carries `corrected: true`); the arbiter's
classification alone never changes a gate. Abort verdicts (INFEASIBLE, NO CHANGE, ERROR, BASELINE) are decided before any
gate exists and are outside this rule.

Evidence protocol (19 Oct 2026, audit finding CORE-06): a bundle written by this revision carries
`evidence_protocol.version` = EVIDENCE_PROTOCOL_VERSION, and `attest check` then requires the complete evidence for its
verdict. A bundle without that field is HISTORICAL: it is checked for internal consistency only and never receives the
fully-verified badge. The former explicit apply mode (`cleared_by_arbitration`, bundles recorded before 19 Oct 2026) is
honoured only when re-deriving a historical bundle dated before LEGACY_CLEARING_CUTOFF; a current bundle that carries such
flags over a failed gate is inconsistent.
"""

from __future__ import annotations

RULE = ("VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the "
        "scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was "
        "validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the "
        "base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never "
        "changes a gate, and a sealed test that failed by assertion or exception is never overridden.")
ABORT_VERDICTS = ("INFEASIBLE", "NO CHANGE", "ERROR", "BASELINE")
# 2 (19 Oct 2026, revision 5): complete evidence for the verdict is required. 3 (19 Oct 2026, revision 6, follow-up review R5-02
# and R5-03): the mandatory stage records are derived from the frozen task and the execution mode, not from what survived; an
# INFEASIBLE verdict needs a GROUNDED conflict (authoritative task criteria only, a constrained witness within the input domain).
# 4 (19 Oct 2026, revision 7, review R6-1): "constrained" means conformance to the positive witness language attest-witness/1
# (attest.core.witness) with every call origin resolved against the frozen repository; every witness carries its language
# analysis, the bundle keeps copies of the repository files the resolution read, and attest check repeats the analysis offline.
EVIDENCE_PROTOCOL_VERSION = 4
LEGACY_CLEARING_CUTOFF = "2026-10-19"  # bundles started before this UTC date may carry the former explicit apply mode


def protocol_version(bundle: dict) -> int | None:
    """The evidence protocol a bundle declares; None for a historical bundle (recorded before the protocol existed)."""
    record = (bundle or {}).get("evidence_protocol")
    try:
        return int(record.get("version")) if isinstance(record, dict) and record.get("version") is not None else None
    except (TypeError, ValueError):
        return None


def legacy_clearing_allowed(bundle: dict) -> bool:
    """Only a historical bundle with a recorded start before the cutoff may be re-derived with the former apply mode."""
    if protocol_version(bundle) is not None:
        return False
    started = (bundle or {}).get("started_at_utc") or ""
    return bool(started) and started[:10] < LEGACY_CLEARING_CUTOFF


def derive(gates: dict, candidate: dict | None, binding_ok: bool | None = None, arbitration: dict | None = None,
           apply: bool = False) -> dict:
    """Pure function of the recorded gates and candidate facts. Returns the verdict and what blocked VERIFIED."""
    candidate = candidate or {}
    failed = [name for name, gate in gates.items() if not gate.get("ok") and not gate.get("skipped")]
    skipped = [name for name, gate in gates.items() if gate.get("skipped")]
    blocking = list(failed) + [f"{name} (not run)" for name in skipped]
    if binding_ok is False and "sealed_binding" not in failed and not (gates.get("sealed_binding") or {}).get("corrected"):
        blocking.append("sealed binding failed")  # the original binding; a corrected sealed gate carries the re-run's own binding
    if candidate.get("scope_ok") is False:
        blocking.append("scope policy violated")
    if candidate.get("implementer_finished") is False:
        blocking.append("implementer did not finish")
    verdict = "VERIFIED" if not blocking else "NEEDS HUMAN"
    cleared = False
    if verdict == "NEEDS HUMAN" and apply and arbitration and arbitration.get("cleared") and not any(g.get("corrected") for g in gates.values()):
        verdict, cleared = "VERIFIED", True  # legacy explicit apply mode (bundles before 19 Oct 2026)
    corrected = sorted(name for name, gate in gates.items() if gate.get("corrected"))
    return {"verdict": verdict, "gates_failed": failed, "gates_skipped": skipped, "blocking": blocking,
            "cleared_by_arbitration": cleared, "corrected_gates": corrected, "rule": RULE}


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
    # the former explicit apply mode is honoured only for a dated historical bundle; a current bundle's gates must carry their own re-run
    apply = legacy_clearing_allowed(bundle) and (bool((bundle.get("verdict") or {}).get("cleared_by_arbitration")) or bool((arbitration or {}).get("applied")))
    derived = derive(gates, bundle.get("candidate"), ((bundle.get("verification") or {}).get("binding") or {}).get("ok"), arbitration, apply)
    if recorded in ABORT_VERDICTS:
        # gates exist but the run aborted afterwards (for example an error in a late stage): nothing to compare
        return {"applicable": False, "recorded": recorded, "derived": derived["verdict"], "consistent": True,
                "detail": f"{recorded} recorded after the gates; derivation not applicable"}
    consistent = derived["verdict"] == recorded
    return {"applicable": True, "recorded": recorded, "derived": derived["verdict"], "consistent": consistent,
            "blocking": derived["blocking"], "cleared_by_arbitration": derived["cleared_by_arbitration"],
            "detail": ("gates and verdict agree" if consistent else f"gates derive {derived['verdict']} but the bundle records {recorded}")}
