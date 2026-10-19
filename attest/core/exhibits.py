"""Exhibits E1 to E7: the one evidence scheme shared by PROOF.md, the console API and `attest check`.

Everything here is derived from the gates and stage records of a Proof Bundle; nothing is authored per run. Sentences
are authored per verdict and per reason class (see `decision`), so two runs that fail for the same reason read the same
way, and a bundle that lacks a stage says "not reached" instead of implying a pass. Old bundles (before milestone M1)
lack some fields; every accessor tolerates that.

Exhibit statuses: `pass`, `fail`, `not_run` (skipped or never reached), `informative` (advisory evidence such as the
arbitration), `none` (nothing of this kind exists for the run, for example no held-out suite was configured).
"""

from __future__ import annotations

import re

EXHIBITS: tuple[tuple[str, str, str | None], ...] = (
    ("E1", "Sealed tests, written before the patch", "sealed_binding"),
    ("E2", "Mutation check", "mutation"),
    ("E3", "Tests written after the patch", "adversarial_tests"),
    ("E4", "Held-out tests", "heldout_suite"),
    ("E5", "Drift audit", "drift_audit"),
    ("E6", "Arbitration of generated-test failures", None),
    ("E7", "Failure record", None),
)
EXHIBIT_TITLE = {ref: title for ref, title, _ in EXHIBITS}
GATE_EXHIBIT = {gate: ref for ref, _, gate in EXHIBITS if gate}
GATE_LABEL = {"existing_suite": "Existing test suite", "sealed_binding": "Sealed tests, nonce-bound", "heldout_suite": "Held-out tests",
              "mutation": "Mutation check", "adversarial_tests": "Tests written after the patch", "drift_audit": "Drift audit"}
GATE_ORDER = ("existing_suite", "sealed_binding", "heldout_suite", "mutation", "adversarial_tests", "drift_audit")
ABORT_VERDICTS = ("INFEASIBLE", "NO CHANGE", "ERROR", "BASELINE")
CLASSIFICATION_LABEL = {"implementation_bug": "Implementation bug, by the arbiter", "test_defect": "Defective test, by the arbiter",
                        "contract_dispute": "Contract dispute, by the arbiter"}
DEFECT_KIND_LABEL = {"wrong_expectation": "wrong expected value", "unspecified_behavior": "tests behaviour the contract leaves unspecified",
                     "excessive_workload": "excessive workload; the oracle itself is correct", "python_incompatibility": "Python 3.12 incompatibility in the test",
                     "other": "other test defect"}
# binding checks whose failure means the result cannot be trusted at all (tamper, forgery or an incomplete supervisor),
# as opposed to an honest failing test (all_expected_pass, no_nonzero_exit, no_signal, no_timeout)
INTEGRITY_CHECKS = ("result_file_present", "supervisor_completed", "verifier_isolation_active", "nonce_matches", "no_discovery_error",
                    "sealed_file_unchanged_before", "sealed_file_unchanged_after", "static_ids_match_red", "expected_test_ids_present",
                    "no_unexpected_test_ids", "no_missing_or_forged_result", "no_startup_hooks_on_import_path", "canary_must_pass_ok",
                    "canary_must_fail_failed", "module_set_matches", "module_digests_unchanged", "static_ids_match_expected")
WHY = {
    "E1": "Acceptance tests written by an independent model instance before any code existed, shown failing on the unmodified checkpoint, "
          "then run against the candidate in a fresh sandbox under a supervisor that checks a nonce, the file digest and two canaries.",
    "E2": "Each changed line is altered one way at a time and the sealed tests run again; a mutant that survives marks a line the tests do not constrain.",
    "E3": "A second independent model instance reads the patch and writes tests meant to break it; every failure is a bug or a contract "
          "disagreement to resolve, never ignored. A test that exceeds its per-test time budget is recorded as a timeout, which holds the "
          "verdict but is not a demonstrated defect.",
    "E4": "Tests the implementer never saw (for example the upstream pull request's own tests), run on the candidate in a separate branch.",
    "E5": "A model compares the action trail and the diff against the request. It is a judgement (evidence class model), never the basis "
          "of VERIFIED on its own.",
    "E6": "An arbiter classifies each failing generated test as an implementation bug, a test defect or a contract dispute and offers a "
          "corrected module for pure test defects. A correction counts only after mechanical validation (same test methods, only the failing "
          "ones changed, passes on the candidate, still fails on the base or is caught by a mutant); the corrected gate is then re-run. The "
          "classification itself is a model judgement; a sealed test that failed by assertion or by an exception raised in the code under test is never overridden.",
    "E7": "What failed, in which component and stage, what was spent, and that nothing was retried or certified.",
}


def _short(test_id: str | None) -> str:
    return (test_id or "").split(".")[-1]


def _clip(text: str | None, limit: int) -> str:
    """Cut long recorded text at a word boundary instead of mid-token."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut[limit // 2:]:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:") + " ..."


def _failing(tests: list | None) -> list[dict]:
    return [t for t in (tests or []) if t.get("outcome") != "ok"]


def _gate_result(gate: dict | None) -> str:
    if not gate:
        return "not_run"
    if gate.get("ok"):
        return "pass"
    return "not_run" if gate.get("skipped") else "fail"


def gates_table(bundle: dict) -> list[dict]:
    """The gates in a fixed order with their labels, results and evidence classes; skipped gates are never a pass."""
    gates = bundle.get("gates") or {}
    adversarial = (bundle.get("breaker") or {}).get("adversarial") or {}
    legacy_fail_open = bool(adversarial.get("skipped")) and "summary" not in adversarial
    rows = []
    for name in list(GATE_ORDER) + [g for g in gates if g not in GATE_ORDER]:
        gate = gates.get(name)
        if gate is None:
            continue
        result, detail, legacy = _gate_result(gate), gate.get("detail") or "", False
        if name == "adversarial_tests" and legacy_fail_open and gate.get("ok"):
            # pre-M1 bundles recorded this gate as passed although no adversarial test ran: a skipped gate is never a pass
            result, legacy = "not_run", True
            detail = f"no adversarial tests ran ({detail}); recorded as a pass by a rule that no longer exists"
        rows.append({"gate": name, "label": GATE_LABEL.get(name, name.replace("_", " ")), "result": result,
                     "evidence_class": gate.get("evidence_class") or ("model" if name == "drift_audit" else "stdout" if name in ("existing_suite", "heldout_suite") else "bound"),
                     "detail": detail, "weak": bool(gate.get("weak")), "exhibit": GATE_EXHIBIT.get(name),
                     "failing": list(gate.get("failing") or []), "legacy_fail_open": legacy})
    return rows


def exhibits(bundle: dict) -> list[dict]:
    """E1 to E7 with status, one-line summary, the reason the exhibit exists and structured detail for renderers."""
    gates = bundle.get("gates") or {}
    verdict = (bundle.get("verdict") or {}).get("verdict") or "ERROR"
    sealed = bundle.get("sealed_tests") or {}
    red = bundle.get("red_run") or {}
    ver = bundle.get("verification") or {}
    sealed_v = ver.get("sealed") or {}
    binding = ver.get("binding") or {}
    breaker = bundle.get("breaker") or {}
    mutation = breaker.get("mutation") or {}
    adversarial = breaker.get("adversarial") or {}
    adv_summary = adversarial.get("summary") or {}
    heldout = ver.get("heldout")
    task = bundle.get("task") or {}
    drift = bundle.get("drift") or {}
    arbitration = bundle.get("arbitration")
    totals = (bundle.get("ledger") or {}).get("totals") or {}
    items: list[dict] = []

    # E1 sealed tests: red check, candidate run and binding
    count = sealed.get("test_count") or red.get("ran") or 0
    cand_ran = bool(sealed_v.get("tests")) or bool(sealed_v.get("ran"))
    gate = gates.get("sealed_binding")
    failed_checks = [k for k, ok in (binding.get("checks") or {}).items() if not ok]
    if gate is not None:
        status = _gate_result(gate)
    else:
        status = "not_run"
    corrected_sealed = ver.get("corrected") if (gate or {}).get("corrected") else None
    if count and cand_ran and corrected_sealed:
        summary = (f"{sealed_v.get('failing', 0)} of {count} failed on the candidate as sealed; {len(corrected_sealed.get('changed_tests') or [])} test(s) corrected "
                   f"by the arbiter and validated ({corrected_sealed.get('discrimination')}); the corrected module passes "
                   f"({(corrected_sealed.get('summary') or {}).get('summary_line')})")
    elif count and cand_ran:
        summary = (f"{red.get('failing', 0)} of {count} failed on the unmodified base; {sealed_v.get('passed', 0)} of {count} pass on the candidate"
                   + ("" if binding.get("ok") else "; binding FAILED" if binding else ""))
    elif count:
        summary = f"{red.get('failing', 0)} of {count} failed on the base; the candidate was never verified"
    else:
        summary = "not reached"
    items.append({"ref": "E1", "title": EXHIBIT_TITLE["E1"], "gate": "sealed_binding", "status": status, "shown": True, "summary": summary,
                  "why": WHY["E1"], "evidence_class": "bound",
                  "detail": {"count": count, "red_failing": red.get("failing"), "red_passing": red.get("passed"),
                             "candidate_passing": sealed_v.get("passed") if cand_ran else None,
                             "candidate_failing": sealed_v.get("failing") if cand_ran else None,
                             "failing_ids": [t.get("id") for t in _failing(sealed_v.get("tests"))],
                             "binding_ok": binding.get("ok"), "failed_checks": failed_checks,
                             "integrity_failed": [c for c in failed_checks if c in INTEGRITY_CHECKS],
                             "canary_ok": sealed_v.get("canary_ok"), "author_model": sealed.get("author_model"),
                             "sha256": sealed.get("sha256"), "attempts": sealed.get("attempts"),
                             "red_operation_uuid": red.get("operation_uuid"), "verify_operation_uuid": ver.get("operation_uuid"),
                             "corrected": ({"changed_tests": corrected_sealed.get("changed_tests"), "sha256": corrected_sealed.get("sha256"),
                                            "discrimination": corrected_sealed.get("discrimination"),
                                            "summary_line": (corrected_sealed.get("summary") or {}).get("summary_line")} if corrected_sealed else None),
                             "coverage_gaps": sealed.get("coverage_gaps") or []}})

    # E2 mutation check
    gate = gates.get("mutation")
    survivors = [{"id": m.get("id"), "path": m.get("path"), "lineno": m.get("lineno"), "description": m.get("description")}
                 for m in (mutation.get("mutants") or []) if m.get("status") == "survived"]
    if mutation.get("generated"):
        summary = (f"{mutation.get('killed', 0)} of {mutation.get('evaluated', 0)} one-line mutants caught, {mutation.get('survived', 0)} survived, "
                   f"{mutation.get('unknown', 0)} unknown; score {mutation.get('score')} (threshold {mutation.get('threshold')})")
    elif gate is not None:
        summary = gate.get("detail") or ("not run" if gate.get("skipped") else "no detail")
    else:
        summary = "not reached"
    items.append({"ref": "E2", "title": EXHIBIT_TITLE["E2"], "gate": "mutation", "status": _gate_result(gate), "shown": True, "summary": summary,
                  "why": WHY["E2"], "evidence_class": (gate or {}).get("evidence_class") or "bound", "weak": bool((gate or {}).get("weak")),
                  "detail": {"generated": mutation.get("generated"), "evaluated": mutation.get("evaluated"), "killed": mutation.get("killed"),
                             "survived": mutation.get("survived"), "unknown": mutation.get("unknown"), "score": mutation.get("score"),
                             "threshold": mutation.get("threshold"), "survivors": survivors}})

    # E3 tests written after the patch
    gate = gates.get("adversarial_tests")
    adv_failing = _failing(adv_summary.get("tests"))
    adv_binding = adversarial.get("binding") or {}
    corrected_adv = adversarial.get("corrected") if (gate or {}).get("corrected") else None
    if adversarial.get("unusable"):
        status, summary = "fail", f"unusable: {str(adversarial['unusable'])[:160]}"
    elif corrected_adv:
        status = _gate_result(gate)
        summary = (f"{len(adv_failing)} of {adv_summary.get('ran', 0)} failed as written ({', '.join(_short(t.get('id')) for t in adv_failing)[:120]}); "
                   f"{len(corrected_adv.get('changed_tests') or [])} test(s) corrected by the arbiter and validated ({corrected_adv.get('discrimination')}); "
                   f"the corrected module passes ({(corrected_adv.get('summary') or {}).get('summary_line')})")
    elif adversarial.get("skipped") and not adv_summary:
        # pre-M1 fail-open record: the gate was recorded as passed although no adversarial test ran
        status, summary = "not_run", f"no adversarial tests ran ({str(adversarial['skipped'])[:120]}); the gate of this older bundle counted it as a pass, which the current rule no longer allows"
    elif adv_summary.get("ran"):
        status = _gate_result(gate)
        summary = f"{adv_summary.get('passed', 0)} of {adv_summary.get('ran', 0)} pass"
        if adv_failing:
            summary += f"; {len(adv_failing)} failing: " + ", ".join(_short(t.get("id")) for t in adv_failing)[:200]
            timeouts = [t for t in adv_failing if t.get("outcome") == "TIMEOUT" or t.get("timed_out")]
            if timeouts:
                summary += f" ({len(timeouts)} timed out, no assertion failed)"
        if adv_binding and not adv_binding.get("ok"):
            summary += "; binding FAILED"
    elif gate is not None:
        status, summary = _gate_result(gate), gate.get("detail") or "not run"
    else:
        status, summary = "not_run", "not reached"
    items.append({"ref": "E3", "title": EXHIBIT_TITLE["E3"], "gate": "adversarial_tests", "status": status, "shown": True, "summary": summary,
                  "why": WHY["E3"], "evidence_class": (gate or {}).get("evidence_class") or "bound",
                  "detail": {"ran": adv_summary.get("ran"), "passed": adv_summary.get("passed"), "failing": adv_summary.get("failing"),
                             "failing_ids": [t.get("id") for t in adv_failing], "binding_ok": adv_binding.get("ok") if adv_binding else None,
                             "timeout_ids": [t.get("id") for t in adv_failing if t.get("outcome") == "TIMEOUT" or t.get("timed_out")],
                             "failed_checks": [k for k, ok in (adv_binding.get("checks") or {}).items() if not ok],
                             "author_model": adversarial.get("author_model"), "sha256": adversarial.get("sha256"),
                             "notes": adversarial.get("notes"), "unusable": adversarial.get("unusable"),
                             "canary_ok": adv_summary.get("canary_ok"), "operation_uuid": adversarial.get("operation_uuid"),
                             "escalated": adversarial.get("escalated"), "attempts": adversarial.get("attempts"),
                             "corrected": ({"changed_tests": corrected_adv.get("changed_tests"), "sha256": corrected_adv.get("sha256"),
                                            "discrimination": corrected_adv.get("discrimination"),
                                            "summary_line": (corrected_adv.get("summary") or {}).get("summary_line")} if corrected_adv else None)}})

    # E4 held-out tests
    gate = gates.get("heldout_suite")
    configured = bool(heldout) or bool(task.get("heldout_tests_sha256"))
    if not configured:
        status, summary = "none", "none configured for this task"
    elif heldout:
        status = _gate_result(gate)
        summary = f"{heldout.get('passed', 0)} of {heldout.get('ran', 0)} pass ({', '.join(heldout.get('files') or sorted(task.get('heldout_tests_sha256') or {}))})"
        if heldout.get("evidence_class") == "stdout":
            summary += "; parsed console output"
    else:
        status, summary = "not_run", "configured but not reached"
    items.append({"ref": "E4", "title": EXHIBIT_TITLE["E4"], "gate": "heldout_suite", "status": status, "shown": True, "summary": summary,
                  "why": WHY["E4"], "evidence_class": (heldout or {}).get("evidence_class") or (gate or {}).get("evidence_class") or ("bound" if heldout else None),
                  "detail": {"files": (heldout or {}).get("files") or sorted(task.get("heldout_tests_sha256") or {}), "ran": (heldout or {}).get("ran"),
                             "passed": (heldout or {}).get("passed"), "failing_ids": [t.get("id") for t in _failing((heldout or {}).get("tests"))],
                             "binding_ok": ((heldout or {}).get("binding") or {}).get("ok"), "operation_uuid": (heldout or {}).get("operation_uuid")}})

    # E5 drift audit
    gate = gates.get("drift_audit")
    if "drift_score" in drift:
        status = _gate_result(gate)
        summary = f"score {drift.get('drift_score')}, {drift.get('assessment')} (threshold {drift.get('threshold')})"
    elif drift.get("error"):
        status, summary = "fail", f"audit call failed: {str(drift['error'])[:160]}"
    else:
        status, summary = "not_run", "not reached"
    items.append({"ref": "E5", "title": EXHIBIT_TITLE["E5"], "gate": "drift_audit", "status": status, "shown": True, "summary": summary,
                  "why": WHY["E5"], "evidence_class": "model",
                  "detail": {"score": drift.get("drift_score"), "assessment": drift.get("assessment"), "threshold": drift.get("threshold"),
                             "summary": drift.get("summary"), "scope_narrowed": drift.get("scope_narrowed") or [],
                             "scope_widened": drift.get("scope_widened") or [], "unsupported_claims": drift.get("unsupported_claims") or []}})

    # E6 arbitration (advisory)
    if arbitration:
        classifications = [{"test_id": c.get("test_id"), "name": _short(c.get("test_id")), "classification": c.get("classification"),
                            "label": CLASSIFICATION_LABEL.get(c.get("classification"), c.get("classification")), "rationale": c.get("rationale"),
                            "contract_basis": c.get("contract_basis"), "module": m.get("module"), "defect_kind": c.get("defect_kind"),
                            "defect_kind_label": DEFECT_KIND_LABEL.get(c.get("defect_kind")) if c.get("defect_kind") else None}
                           for m in arbitration.get("modules") or [] for c in m.get("classifications") or []]
        reruns = [{"module": m.get("module"), "candidate": (m.get("candidate_rerun") or {}).get("summary_line"),
                   "base": (m.get("base_rerun") or {}).get("summary_line"), "cleared": m.get("cleared_module"), "validated": m.get("validated"),
                   "discrimination": (m.get("corrected") or {}).get("discrimination"), "changed_tests": (m.get("corrected") or {}).get("changed_tests"),
                   "mutant_reruns": len(m.get("mutant_reruns") or []), "sealed_assertion_hold": m.get("sealed_assertion_hold"), "error": m.get("error")}
                  for m in arbitration.get("modules") or []]
        applied = arbitration.get("applied_to_gates") or []
        items.append({"ref": "E6", "title": EXHIBIT_TITLE["E6"], "gate": None, "status": "informative", "shown": True,
                      "summary": arbitration.get("headline") or "", "why": WHY["E6"], "evidence_class": "model",
                      "detail": {"applied": bool(arbitration.get("applied")), "cleared": bool(arbitration.get("cleared")),
                                 "applied_to_gates": applied, "validated_modules": arbitration.get("validated_modules") or [],
                                 "rule": arbitration.get("rule"),
                                 "counts": arbitration.get("counts") or {}, "classifications": classifications, "reruns": reruns,
                                 "note": arbitration.get("note")}})
    else:
        items.append({"ref": "E6", "title": EXHIBIT_TITLE["E6"], "gate": None, "status": "none", "shown": False,
                      "summary": "not run: no generated-test failure to arbitrate", "why": WHY["E6"], "evidence_class": "model", "detail": {}})

    # E7 failure record
    if verdict == "ERROR":
        reasons = (bundle.get("verdict") or {}).get("reasons") or []
        first = reasons[0] if reasons else "unknown failure"
        component = ("inference provider" if first.startswith("model provider") else
                     "sandbox executor" if "Sandbox" in first or "sandbox" in first else
                     "verifier" if "verification" in first else "pipeline")
        items.append({"ref": "E7", "title": EXHIBIT_TITLE["E7"], "gate": None, "status": "fail", "shown": True,
                      "summary": f"{component} failed {('at stage ' + bundle['stage']) if bundle.get('stage') else 'before the first stage was recorded'}: {_clip(first, 200)}",
                      "why": WHY["E7"], "evidence_class": "bound",
                      "detail": {"component": component, "stage": bundle.get("stage"), "reasons": reasons,
                                 "model_calls": totals.get("model_calls"), "model_calls_failed": totals.get("model_calls_failed"),
                                 "cost_usd_committed": totals.get("cost_usd_committed"), "uncertain_unpriced_calls": totals.get("uncertain_unpriced_calls"),
                                 "sandbox_operations": totals.get("sandbox_operations"), "retried": False,
                                 "uncertain": any("uncertain" in r for r in reasons)}})
    else:
        items.append({"ref": "E7", "title": EXHIBIT_TITLE["E7"], "gate": None, "status": "none", "shown": False,
                      "summary": "no infrastructure failure recorded", "why": WHY["E7"], "evidence_class": "bound", "detail": {}})
    return items


_ASSERTION = re.compile(r"^(?P<kind>[A-Za-z_][\w.]*(?:Error|Exception|Failure|Interrupt|Exit)[^:]*):\s?(?P<message>.*)$")


def parse_assertion(tail: str | None) -> dict:
    """Pull the last exception line out of a failure traceback. For unittest's `first != second` assertions the two sides
    are returned as `first` and `second`; which one is the actual value depends on the test's argument order, so the
    renderer labels them as such instead of guessing."""
    lines = [line.rstrip() for line in (tail or "").strip().splitlines() if line.strip()]
    for line in reversed(lines):
        match = _ASSERTION.match(line.strip())
        if match:
            message = match.group("message").strip()
            first = second = None
            if " != " in message and match.group("kind").startswith("AssertionError"):
                left, _, right = message.partition(" != ")
                first, second = left.strip(), right.split(" : ")[0].strip()
            return {"kind": match.group("kind"), "message": message[:400], "first": first, "second": second, "parsed": True}
    return {"kind": None, "message": lines[-1][:400] if lines else "", "first": None, "second": None, "parsed": False}


def counterexamples(bundle: dict) -> list[dict]:
    """Every failing test from E3, E1 (candidate run) and E4 with its captured failure text and the arbiter's classification."""
    arbitration = bundle.get("arbitration") or {}
    classified = {c.get("test_id"): c for m in arbitration.get("modules") or [] for c in m.get("classifications") or []}
    ver = bundle.get("verification") or {}
    breaker = bundle.get("breaker") or {}
    sources = (("E3", "adversarial", ((breaker.get("adversarial") or {}).get("summary") or {}).get("tests")),
               ("E1", "sealed", (ver.get("sealed") or {}).get("tests")),
               ("E4", "heldout", (ver.get("heldout") or {}).get("tests")))
    items = []
    for ref, module, tests in sources:
        for test in _failing(tests):
            tail = test.get("failure_tail") or test.get("captured_tail") or ""
            parsed = parse_assertion(tail)
            cls = classified.get(test.get("id")) or {}
            items.append({"exhibit": ref, "module": module, "test_id": test.get("id"), "name": _short(test.get("id")), "outcome": test.get("outcome"),
                          "exit_code": test.get("exit_code"), "signal": test.get("signal"), "timed_out": bool(test.get("timed_out")),
                          "duration_s": test.get("duration_s"),
                          "assertion": parsed, "tail": tail[-800:], "classification": cls.get("classification"),
                          "classification_label": CLASSIFICATION_LABEL.get(cls.get("classification")) if cls else None,
                          "defect_kind": cls.get("defect_kind"), "defect_kind_label": DEFECT_KIND_LABEL.get(cls.get("defect_kind")) if cls.get("defect_kind") else None,
                          "rationale": cls.get("rationale"), "contract_basis": cls.get("contract_basis")})
    return items


def reason_class(bundle: dict) -> str:
    """The first applicable reason a run is not VERIFIED, in a fixed precedence; 'verified' when it is."""
    verdict = (bundle.get("verdict") or {}).get("verdict") or "ERROR"
    if verdict == "VERIFIED":
        return "verified"
    if verdict == "NO CHANGE" and ((bundle.get("candidate") or {}).get("unfinished") or (bundle.get("candidate") or {}).get("implementer_finished") is False):
        return "unfinished_no_patch"
    if verdict in ABORT_VERDICTS:
        return verdict.lower().replace(" ", "_")
    gates = bundle.get("gates") or {}
    if not gates and verdict == "NEEDS HUMAN" and (bundle.get("spec") or {}).get("feasible") is False:
        return "infeasibility_unproven"
    ver = bundle.get("verification") or {}
    checks = (ver.get("binding") or {}).get("checks") or {}
    candidate = bundle.get("candidate") or {}
    if any(not checks.get(c, True) for c in INTEGRITY_CHECKS):
        return "integrity"
    if gates.get("sealed_binding") and not gates["sealed_binding"].get("ok"):
        arb_modules = (bundle.get("arbitration") or {}).get("modules") or []
        if any(m.get("module") == "sealed" and m.get("sealed_assertion_hold") for m in arb_modules):
            return "sealed_assertion_hold"
        return "sealed_failed"
    if gates.get("existing_suite") and not gates["existing_suite"].get("ok"):
        return "existing_failed"
    if gates.get("heldout_suite") and not gates["heldout_suite"].get("ok"):
        return "heldout_failed"
    adversarial = gates.get("adversarial_tests")
    if adversarial and not adversarial.get("ok") and not adversarial.get("skipped"):
        counts = ((bundle.get("arbitration") or {}).get("counts") or {})
        kinds = {k for k, v in counts.items() if v}
        if kinds == {"test_defect"}:
            return "adversarial_test_defects"
        if "implementation_bug" in kinds:
            return "adversarial_implementation_bug"
        if "contract_dispute" in kinds:
            return "adversarial_contract_dispute"
        failing = _failing((((bundle.get("breaker") or {}).get("adversarial") or {}).get("summary") or {}).get("tests"))
        if failing and all(t.get("outcome") == "TIMEOUT" or t.get("timed_out") for t in failing):
            return "adversarial_timeout"  # no assertion failed: the test exceeded its budget (unarbitrated)
        return "adversarial_failed"
    if gates.get("mutation") and not gates["mutation"].get("ok") and not gates["mutation"].get("skipped"):
        mutation = ((bundle.get("breaker") or {}).get("mutation") or {})
        if (mutation.get("unknown") or 0) > 0 and not (mutation.get("survived") or 0):
            return "mutation_incomplete"  # nothing survived; too few mutants could be evaluated (sandbox operations unknown)
        return "mutation_failed"
    if gates.get("drift_audit") and not gates["drift_audit"].get("ok"):
        return "drift_failed"
    if candidate.get("implementer_finished") is False:
        return "implementer_unfinished"
    if candidate.get("scope_ok") is False:
        return "scope_violated"
    return "other"


def decision(bundle: dict) -> dict:
    """The decision header: statement, explanation, the key exhibit line and what to do, authored per verdict and reason class."""
    verdict_record = bundle.get("verdict") or {}
    verdict = verdict_record.get("verdict") or "ERROR"
    reasons = verdict_record.get("reasons") or []
    items = {e["ref"]: e for e in exhibits(bundle)}
    e1, e2, e3, e4, e5, e7 = (items[r] for r in ("E1", "E2", "E3", "E4", "E5", "E7"))
    examples = counterexamples(bundle)
    klass = reason_class(bundle)
    task_title = (bundle.get("task") or {}).get("title") or ""
    spec = bundle.get("spec") or {}
    weak: list[str] = []
    gates = bundle.get("gates") or {}

    def example_line(ref: str | None = None) -> str | None:
        for ex in examples:
            if ref and ex["exhibit"] != ref:
                continue
            assertion = ex["assertion"]
            if assertion.get("parsed") and assertion.get("first") is not None:
                return f"{ex['name']}: {assertion['first']} != {assertion['second']} (the test's first argument against its second)"
            if assertion.get("message"):
                return f"{ex['name']}: {assertion['kind'] + ': ' if assertion.get('kind') else ''}{assertion['message']}"
            return f"{ex['name']}: {ex['outcome']}" + (" (timed out)" if ex["timed_out"] else "")
        return None

    if verdict == "VERIFIED":
        d = e1["detail"]
        others = ["the existing test suite"] if (gates.get("existing_suite") or {}).get("ok") else []
        for ref, label in (("E2", "the mutation check"), ("E3", "the tests written after the patch"), ("E4", "the held-out tests"), ("E5", "the drift audit")):
            if items[ref]["status"] == "pass":
                others.append(label)
        joined = (", ".join(others[:-1]) + " and " + others[-1]) if len(others) > 1 else (others[0] if others else "")
        explanation = (f"All {d['count']} sealed tests pass on the candidate in a fresh sandbox, and {d['red_failing']} of them failed on the unmodified base."
                       + (f" {joined[0].upper() + joined[1:]} all passed." if len(others) > 1 else f" {joined[0].upper() + joined[1:]} passed." if others else ""))
        evidence = {"ref": "E1", "text": f"{d['candidate_passing']} of {d['count']} sealed tests pass, each in its own process; the nonce and the sealed-file digest matched."}
        if e2["detail"].get("survived"):
            weak.append(f"{e2['detail']['survived']} one-line change(s) to the patch were not caught by the sealed tests (score {e2['detail']['score']}, "
                        f"threshold {e2['detail']['threshold']}). They mark lines the acceptance tests do not constrain (E2).")
        if e2.get("weak"):
            weak.append("No mutable sites were found on the changed lines, so only the tests written after the patch test it structurally (E2, E3).")
        if e3["status"] == "not_run":
            weak.append("No test written after the patch ran in this run; its adversarial gate was recorded as passed by a rule that no longer exists, so the verdict rests on the other gates (E3).")
        for row in gates_table(bundle):
            if row["evidence_class"] == "stdout":
                weak.append(f"The {row['label'].lower()} result is parsed console output, not per-test exit codes under the supervisor.")
        if e4["status"] == "none":
            weak.append("No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).")
        decide = ["Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself."]
        statement = "Accept this patch."
        if verdict_record.get("cleared_by_arbitration"):
            weak.append("The verdict was cleared by arbitration in apply mode: every failing generated test was classified as a defect, corrected and re-verified (E6).")
        for correction in verdict_record.get("corrections") or []:
            label = "sealed tests" if correction.get("gate") == "sealed_binding" else "tests written after the patch"
            weak.append(f"{len(correction.get('changed_tests') or [])} of the {label} failed as written and were corrected by the arbiter; the correction kept every "
                        f"test method, changed only the failing ones, passes on the candidate and discriminates ({correction.get('discrimination')}), and the gate "
                        "was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.")
        if d.get("coverage_gaps"):
            weak.append(f"The sealer's own coverage map names no test for acceptance criteria {', '.join(d['coverage_gaps'])} (E1); the sealed suite may not exercise them.")
        audit = bundle.get("contract_audit") or {}
        if audit.get("outcome") == "conflicts claimed, none demonstrated":
            weak.append("The contract auditor suspected a conflict between requirements but its witness program could not demonstrate one; the suspicion was "
                        "handed to the sealer and is recorded in contract_audit.json.")
    elif verdict == "NEEDS HUMAN":
        statement = "Hold this patch."
        decide = []
        if klass == "integrity":
            failed = e1["detail"]["integrity_failed"] or e1["detail"]["failed_checks"]
            explanation = ("The sealed verification could not be bound to the suite that was proven red, so its results are not trusted. "
                           f"Failed binding checks: {', '.join(failed)[:200]}. The run is recorded as possibly tampered or incomplete, not as a pass or a failure.")
            evidence = {"ref": "E1", "text": f"Binding checks failed: {', '.join(failed)[:160]}."}
            decide = ["Inspect the candidate patch and the supervisor record in verify.json for tampering.",
                      "Run the task again on a fresh checkpoint; a second integrity failure is a security finding, not noise."]
        elif klass == "sealed_assertion_hold":
            n = e1["detail"].get("candidate_failing") or len(e1["detail"]["failing_ids"])
            arbitration = bundle.get("arbitration") or {}
            module = next((m for m in arbitration.get("modules") or [] if m.get("module") == "sealed"), {})
            validated = bool(module.get("cleared_module"))
            explanation = (f"{n} of the {e1['detail']['count']} sealed acceptance tests fail on the candidate because the candidate's behaviour contradicts "
                           "the test written before the patch (an assertion failed, or the code under test raised). The arbiter classified the failing test(s) as defective"
                           + (" and its corrected tests pass on the candidate and still fail on the unmodified base" if validated else "")
                           + ". A sealed test is the pre-registered acceptance criterion, so Attest never overrides it on a model's judgement: the hold "
                           "stands and the arbiter's view, the original test and the corrected test are all recorded for you (E6).")
            evidence = {"ref": "E6", "text": arbitration.get("headline") or example_line("E1") or ""}
            decide = ["Compare the original sealed test with the arbiter's correction and the contract; decide which encodes the requirement.",
                      "If the correction is right, accept the patch on that basis and tighten the task statement so the next sealer reads it the same way."]
        elif klass == "sealed_failed":
            n = e1["detail"].get("candidate_failing") or len(e1["detail"]["failing_ids"])
            explanation = (f"{n} of the {e1['detail']['count']} sealed acceptance tests fail on the candidate. The sealed tests were written before the patch "
                           "from the task statement; each failure is either a missing behaviour or a test that misreads the request.")
            arbitration = bundle.get("arbitration") or {}
            counts = arbitration.get("counts") or {}
            if arbitration and set(k for k, v in counts.items() if v) == {"test_defect"}:
                module = next((m for m in arbitration.get("modules") or [] if m.get("module") == "sealed"), {})
                if module.get("cleared_module") or arbitration.get("all_corrected") or arbitration.get("cleared"):
                    explanation += (" The arbiter classified every failing sealed test as defective, and the corrected tests pass on the candidate and still "
                                    "fail on the base; the hold stands because "
                                    + (module.get("error") or "this bundle recorded the correction as advisory (the sealed failure skipped the mutation check)")
                                    + " (E6).")
                else:
                    explanation += (" The arbiter classified every failing sealed test as defective, but the correction did not pass the mechanical validation"
                                    + (f" ({module.get('error')})" if module.get("error") else "") + "; the hold stands (E6).")
            elif arbitration and counts.get("implementation_bug"):
                explanation += f" The arbiter classified {counts['implementation_bug']} of them as implementation bugs (E6)."
            evidence = {"ref": "E1", "text": example_line("E1") or f"Failing sealed tests: {', '.join(_short(i) for i in e1['detail']['failing_ids'])[:160]}."}
            decide = ["Read the failing sealed test and decide whether it states the requirement correctly.",
                      "If it does, the implementation is incomplete; if not, correct the task statement and run again."]
        elif klass == "existing_failed":
            explanation = ("The repository's own test suite fails on the candidate. Whatever the new behaviour does, it broke something the project already "
                           "relied on, so the patch cannot be accepted as it stands.")
            evidence = {"ref": "gates", "text": (gates.get("existing_suite") or {}).get("detail") or "existing suite failed"}
            decide = ["Open the failing existing tests in the Tests tab; they name the regression.", "Fix the regression and run the task again."]
        elif klass == "heldout_failed":
            explanation = ("Tests the implementer never saw fail on the candidate. The held-out suite is the closest thing this bundle has to an external "
                           "acceptance check, so the hold stands until the failures or the contract disagreement behind them are resolved.")
            evidence = {"ref": "E4", "text": example_line("E4") or f"Failing held-out tests: {', '.join(_short(i) for i in e4['detail']['failing_ids'])[:160]}."}
            decide = ["Compare the failing held-out test with the contract; decide whether the test or the contract is right.",
                      "Resolve the disagreement in the task statement, then run again."]
        elif klass == "adversarial_implementation_bug":
            explanation = ("A test written after the patch found an input the implementation handles wrongly. The arbiter classified it as an "
                           "implementation bug, so this is a defect in the candidate, not in the test. The hold stands until a human decides.")
            evidence = {"ref": "E3", "text": example_line("E3") or e3["summary"]}
            decide = ["Read the counterexample: input, actual result and the arbiter's contract basis.",
                      "Fix the implementation and run the task again, or reject the patch."]
        elif klass == "adversarial_contract_dispute":
            explanation = ("A test written after the patch asks a question the contract does not answer. The arbiter classified it as a contract dispute, "
                           "which only the requester can settle, so Attest holds the patch instead of guessing the intent.")
            evidence = {"ref": "E3", "text": example_line("E3") or e3["summary"]}
            decide = ["State the missing requirement in the task statement (the arbiter's contract basis names the gap).",
                      "Run the task again; if the patch already matches the clarified contract, the disputed test is void."]
        elif klass == "adversarial_test_defects":
            arbitration = bundle.get("arbitration") or {}
            kinds = sorted({c.get("defect_kind") for m in arbitration.get("modules") or []
                            for c in m.get("classifications") or [] if c.get("defect_kind")})
            kind_text = (" Defect kinds: " + "; ".join(DEFECT_KIND_LABEL.get(k, k) for k in kinds) + ".") if kinds else ""
            module = next((m for m in arbitration.get("modules") or [] if m.get("module") == "adversarial"), {})
            if not arbitration.get("applied"):
                why = "Arbitration ran in advisory mode, so the hold stands until a human confirms."
            elif module.get("error"):
                why = f"The correction did not pass the mechanical validation ({module['error']}), so the gate was not re-run and the hold stands."
            else:
                why = "The correction was not validated, so the gate was not re-run and the hold stands."
            explanation = ("Every failing test written after the patch was classified as defective by the arbiter. " + why + kind_text)
            evidence = {"ref": "E6", "text": arbitration.get("headline") or e3["summary"]}
            decide = ["Check the arbiter's classifications and the correction in E6 (original and corrected tests are both kept).",
                      "If you agree with the arbiter, accept the patch on that basis; otherwise treat the failing test as a finding."]
        elif klass == "adversarial_timeout":
            ids = e3["detail"].get("timeout_ids") or e3["detail"].get("failing_ids") or []
            explanation = ("A test written after the patch did not finish within its per-test time budget and was killed; no assertion failed. "
                           "A timeout is not a demonstrated defect: it is an open question about the test's workload (or, in rare cases, an "
                           "infinite loop in the candidate), so the verdict holds instead of guessing.")
            evidence = {"ref": "E3", "text": f"Timed out: {', '.join(_short(i) for i in ids)[:160]}."}
            decide = ["Run the timed-out test by hand on the candidate; if it finishes with the expected result, its workload is the problem.",
                      "Reduce the test's enumeration or raise the task's test_timeout, then run again."]
        elif klass == "adversarial_failed":
            explanation = ("Tests written after the patch fail on the candidate and were not arbitrated, so each failure is still an open question: "
                           "a bug in the patch, a defective test or a contract gap.")
            evidence = {"ref": "E3", "text": example_line("E3") or e3["summary"]}
            decide = ["Read each failing test and classify it yourself; the bundle keeps the test source and the captured output.",
                      "Fix the patch or the task statement accordingly, then run again."]
        elif klass == "mutation_incomplete":
            d = e2["detail"]
            explanation = (f"Every mutant that could be evaluated was caught ({d.get('killed') or 0} of {d.get('evaluated') or 0}), but {d.get('unknown') or 0} "
                           f"mutant branch(es) could not be evaluated (a sandbox operation ended uncertain or failed and is never replayed), so fewer than "
                           "the minimum number of mutants were scored. This is an infrastructure gap, not a finding against the patch; the verdict fails closed.")
            evidence = {"ref": "E2", "text": e2["summary"]}
            decide = ["Run the task again; a small patch yields only a handful of mutants, so one lost sandbox operation is enough to hold it.",
                      "The unknown mutant and its error are listed in breaker.json (mutation.mutants)."]
        elif klass == "mutation_failed":
            explanation = ("Too few one-line mutants of the patch were caught by the sealed tests, or none could be evaluated. The acceptance tests "
                           "do not constrain enough of the change for a pass to mean much, so the verdict fails closed.")
            evidence = {"ref": "E2", "text": e2["summary"]}
            decide = ["Look at the surviving mutants in E2; they name the lines no test constrains.",
                      "Strengthen the acceptance criteria so the sealed tests cover those lines, then run again."]
        elif klass == "drift_failed":
            explanation = ("The drift audit judged that the work departed from the request (scope widened, narrowed or claims unsupported by the diff). "
                           "This is a model judgement, so it holds the patch for a person rather than rejecting it.")
            evidence = {"ref": "E5", "text": e5["summary"]}
            decide = ["Read the audit findings against the diff.", "If the drift is real, narrow the patch; if not, accept it on the gates that passed."]
        elif klass == "implementer_unfinished":
            explanation = "The implementer ran out of turns before declaring the work finished, so the candidate is a partial attempt even where tests pass."
            evidence = {"ref": "gates", "text": reasons[0] if reasons else "turn budget exhausted"}
            decide = ["Treat the patch as a draft; run again with a larger turn budget or a narrower task."]
        elif klass == "scope_violated":
            explanation = "The candidate changed files outside the allowed write scope or touched protected paths, so it is rejected regardless of test results."
            evidence = {"ref": "gates", "text": reasons[0] if reasons else "scope policy violated"}
            decide = ["Review the violations in the Patch tab; then narrow the patch or widen the task's write scope deliberately."]
        elif klass == "infeasibility_unproven":
            explanation = ("The specification stage judged the task infeasible, but the contract auditor's witness programs did not demonstrate a "
                           "contradiction when they ran on the unmodified repository. An undemonstrated claim of infeasibility is a hold, not a verdict: "
                           "no sealed tests were written and no implementation was attempted.")
            evidence = {"ref": "contract_audit", "text": (spec.get("infeasibility_reason") or (reasons[0] if reasons else ""))[:300]}
            decide = ["Read the specification's reason and the witness results in contract_audit.json.",
                      "If the task is feasible, clarify the statement so the specification stage reads it that way and run again; if not, record the contradiction."]
        else:
            explanation = "The gates did not all pass. The recorded reasons name what failed; nothing was certified."
            evidence = {"ref": "gates", "text": reasons[0][:200] if reasons else "see the recorded reasons"}
            decide = ["Read the recorded reasons and the gates table; resolve each failure, then run again."]
    elif verdict == "INFEASIBLE":
        statement = "This task cannot be implemented as stated."
        audit = bundle.get("contract_audit") or {}
        shown_conflict = next((c for c in audit.get("conflicts") or [] if c.get("demonstrated")), None)
        if shown_conflict:
            explanation = (f"The contract auditor claimed that requirements {', '.join(shown_conflict.get('requirement_ids') or [])} cannot both hold, and its "
                           "witness program demonstrated the conflict when Attest ran it on the unmodified repository in a sandbox (exit code "
                           f"{shown_conflict.get('exit_code')}, operation {shown_conflict.get('operation_uuid')}). No sealed tests were written and no "
                           "implementation was attempted. The witness's reasoning is the model's; its execution and output are recorded.")
            evidence = {"ref": "contract_audit", "text": ((shown_conflict.get("stdout_tail") or "").strip().splitlines() or [shown_conflict.get("summary") or ""])[0][:300]}
            decide = ["Read the witness program and its output in contract_audit/; it names the input on which the requirements conflict.",
                      "Revise the task statement or the contract so the conflict disappears, then run again."]
        else:
            explanation = ("The specification stage judged the request infeasible before any code was written, and recorded why. No sealed tests "
                           "were written and no implementation was attempted.")
            evidence = {"ref": "spec", "text": (spec.get("infeasibility_reason") or (reasons[0] if reasons else ""))[:300]}
            decide = ["Revise the task statement or the contract so the conflict disappears, then run again."]
    elif verdict == "NO CHANGE" and klass == "unfinished_no_patch":
        statement = "The implementer did not produce a patch."
        turns = (bundle.get("trajectory") or {}).get("turns")
        explanation = (f"The implementer used its whole turn budget ({turns} turn(s)) without finishing and without changing a file. This is an "
                       "unfinished task, not a judgement that no change was needed and not a repair: there is no candidate, so nothing was verified "
                       "and nothing was certified.")
        evidence = {"ref": "trajectory", "text": reasons[0][:200] if reasons else "turn budget exhausted without a patch"}
        decide = ["Read the implementer's action trail (the Activity tab) to see where the turns went.",
                  "Run again with a larger turn budget or a narrower task; a task the model cannot navigate in the budget stays unfinished."]
    elif verdict == "NO CHANGE":
        statement = "The implementer changed nothing."
        explanation = "The implementer finished without modifying any file, so there is no candidate to verify. Nothing was certified."
        evidence = {"ref": "trajectory", "text": reasons[0][:200] if reasons else "no files changed"}
        decide = ["Read the implementer's action trail; then clarify the task or raise the turn budget and run again."]
    elif verdict == "BASELINE":
        statement = "Baseline run: no verification."
        explanation = ("This run belongs to the evaluation's plain-agent arm: the implementer worked without sealed tests, breaker or audit, "
                       "and the candidate was judged only by the harness. It certifies nothing.")
        evidence = {"ref": "trajectory", "text": "candidate produced for the independent judge; no gates recorded"}
        decide = ["Compare with the Attest run of the same task in the evaluation report."]
    else:  # ERROR
        statement = "This run did not complete."
        d = e7["detail"]
        first = (reasons[0] if reasons else "unknown failure")
        where = f"at stage {d['stage']}" if d.get("stage") else "before the first stage was recorded"
        explanation = (f"The {d.get('component', 'pipeline')} failed {where}. "
                       + ("The outcome of the failing call was uncertain, so Attest did not retry it and certified nothing." if d.get("uncertain")
                          else "Attest did not retry it and certified nothing.") + " The repository was not changed by this run.")
        evidence = {"ref": "E7", "text": (f"{d.get('component', 'pipeline')} error after {d.get('model_calls') or 0} model call(s): {_clip(first, 220)}"
                                          + (f"; {d['uncertain_unpriced_calls']} call(s) counted at the reservation" if d.get("uncertain_unpriced_calls") else ""))}
        decide = ["Start a new run. This failure is infrastructure, not a judgement about the task."]
    return {"verdict": verdict, "statement": statement, "explanation": explanation, "evidence": evidence, "weak": weak, "decide": decide,
            "reason_class": klass, "title": task_title}


def proves(bundle: dict) -> dict:
    """'What this bundle proves, and what it does not', generated from the gates and citing the exhibits."""
    verdict = (bundle.get("verdict") or {}).get("verdict") or "ERROR"
    items = {e["ref"]: e for e in exhibits(bundle)}
    e1, e2, e3, e4, e5, e6, e7 = (items[r] for r in ("E1", "E2", "E3", "E4", "E5", "E6", "E7"))
    gates = bundle.get("gates") or {}
    existing = gates.get("existing_suite") or {}
    yes: list[str] = []
    no: list[str] = []
    d1 = e1["detail"]
    if e1["status"] == "pass":
        yes.append(f"The candidate passes all {d1['count']} sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).")
        if d1.get("red_failing"):
            yes.append(f"{d1['red_failing']} of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).")
        if d1.get("red_passing"):
            no.append(f"That the {d1['red_passing']} sealed test(s) which already passed on the base say anything about the change (E1).")
    elif e1["status"] == "fail":
        if d1.get("integrity_failed"):
            yes.append(f"The sealed verification result could not be trusted: {', '.join(d1['integrity_failed'])} failed (E1).")
        elif d1.get("failing_ids"):
            yes.append(f"{len(d1['failing_ids'])} sealed acceptance test(s) fail on the candidate (E1).")
    elif d1.get("count"):
        yes.append(f"{d1['red_failing']} of {d1['count']} sealed tests fail on the unmodified base; the candidate was never run against them (E1).")
    if existing:
        if existing.get("ok"):
            yes.append(f"The repository's own suite passes on the candidate (gates table, evidence class {existing.get('evidence_class') or 'stdout'}).")
        else:
            yes.append("The repository's own suite fails on the candidate (gates table).")
    if e2["status"] == "pass" and e2["detail"].get("generated"):
        yes.append(f"{e2['detail']['killed']} of {e2['detail']['evaluated']} one-line mutants of the changed lines were caught by the sealed tests (E2).")
        if e2["detail"].get("survived"):
            no.append(f"That the sealed tests constrain the lines marked by the {e2['detail']['survived']} surviving mutant(s) (E2).")
    elif e2["status"] == "pass" and e2.get("weak"):
        no.append("That the mutation check tested anything: no mutable sites were found on the changed lines (E2).")
    elif e2["status"] == "fail":
        yes.append(f"The mutation check failed: {e2['summary']} (E2).")
    else:
        no.append("Anything about mutation resistance: the mutation check did not run (E2).")
    if e3["status"] == "pass" and e3["detail"].get("ran"):
        yes.append(f"{e3['detail']['ran']} tests written after the patch by an independent model instance pass on the candidate (E3).")
    elif e3["status"] == "fail":
        yes.append(f"{len(e3['detail'].get('failing_ids') or [])} test(s) written after the patch fail on the candidate (E3)." if e3["detail"].get("failing_ids")
                   else f"The tests written after the patch could not be used: {e3['summary']} (E3).")
    else:
        no.append("Anything from tests written after the patch: that stage did not run (E3).")
    if e4["status"] == "pass":
        yes.append(f"The held-out tests ({', '.join(e4['detail'].get('files') or [])}), which the implementer never saw, pass on the candidate (E4).")
    elif e4["status"] == "fail":
        yes.append(f"The held-out tests fail on the candidate: {', '.join(_short(i) for i in e4['detail'].get('failing_ids') or [])[:160]} (E4).")
    elif e4["status"] == "none":
        no.append("Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).")
    if e5["status"] == "pass":
        yes.append(f"A model audit found the work aligned with the request ({e5['summary']}; E5). This is a judgement, not evidence.")
    elif e5["status"] == "fail":
        yes.append(f"The drift audit judged the work misaligned with the request ({e5['summary']}; E5).")
    no.append("That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).")
    no.append("That the patch is correct for inputs none of the suites exercise.")
    if e5["status"] != "not_run":
        no.append("That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).")
    for row in gates_table(bundle):
        if row["evidence_class"] == "stdout":
            no.append(f"That the {row['label'].lower()} result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).")
    if e6["status"] == "informative":
        if e6["detail"].get("applied_to_gates"):
            no.append("That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, "
                      "but which side was wrong is a model judgement; the original tests and results are preserved (E6).")
        else:
            no.append("That the arbiter's classifications are correct: arbitration is a model judgement and the original tests and results are preserved (E6).")
    audit = bundle.get("contract_audit") or {}
    if verdict == "INFEASIBLE" and any(c.get("demonstrated") for c in audit.get("conflicts") or []):
        yes.append("A witness program written by the contract auditor demonstrated the contract's contradiction when executed on the unmodified repository (contract_audit).")
        no.append("That the witness's reasoning is sound beyond what its recorded output shows: the program is the model's, only its execution is Attest's.")
    if verdict == "NEEDS HUMAN":
        no.append("That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).")
    if verdict == "ERROR":
        yes.append(f"The run failed in the {e7['detail'].get('component', 'pipeline')} at stage {e7['detail'].get('stage') or 'unknown'}; nothing was retried (E7).")
        no.append("Anything about the patch or the task: no verdict about the candidate was reached (E7).")
    if verdict in ("INFEASIBLE", "NO CHANGE", "BASELINE"):
        no.append("Anything about a candidate patch: none was verified in this run.")
    return {"proves": yes, "does_not_prove": no}


def summary(bundle: dict) -> dict:
    """Everything a renderer needs in one call: decision, exhibits, gates table, counterexamples and the proves list."""
    return {"decision": decision(bundle), "exhibits": exhibits(bundle), "gates": gates_table(bundle),
            "counterexamples": counterexamples(bundle), "proves": proves(bundle)}
