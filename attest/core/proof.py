"""Proof Bundle writer: JSON record plus a human-readable Markdown rendering (PROOF.md).

PROOF.md is a deterministic function of proof_bundle.json: `attest check` re-renders it and compares. The decision block,
the exhibits E1 to E7 and "What this bundle proves, and what it does not" come from `attest.core.exhibits`, the same
module the console uses, so the two never disagree.
"""

from __future__ import annotations

import json
from pathlib import Path

from .exhibits import counterexamples, decision, exhibits, gates_table, proves
from .manifest import MANIFEST_FILE, purpose_of


def _table(rows: list[list], header: list[str]) -> str:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in row) + " |")
    return "\n".join(lines) if rows else "(none)"


def _test_rows(red: dict | None, verify: dict | None) -> list[list[str]]:
    base = {t["id"]: t for t in (red or {}).get("tests", [])}
    patched = {t["id"]: t for t in (verify or {}).get("tests", [])}
    rows = []
    for tid in sorted(set(base) | set(patched)):
        b, p = base.get(tid), patched.get(tid)
        rows.append([tid, f"{b['outcome']} ({b.get('events', 1)} ev)" if b else "-", f"{p['outcome']} ({p.get('events', 1)} ev)" if p else "-"])
    return rows


def _fmt(value, digits=3):
    return "-" if value is None else (f"{value:.{digits}f}" if isinstance(value, float) else value)


def _status_word(status: str) -> str:
    return {"pass": "pass", "fail": "FAIL", "not_run": "not run", "informative": "advisory", "none": "none"}.get(status, status)


def _provenance_lines(prov: dict | None) -> list[str]:
    if not prov:
        return ["Provenance: not recorded (bundle predates milestone M2)."]
    rev = prov.get("attest_revision") or {}
    sup = prov.get("supervisor") or {}
    sampling = prov.get("sampling") or {}
    limits = prov.get("limits") or {}
    upstream = prov.get("upstream")
    roles = sampling.get("roles") or {}
    lines = [
        f"Attest {prov.get('attest_version')} revision `{(rev.get('digest') or '-')[:16]}` ({rev.get('files')} package sources; "
        f"{'git commit ' + rev['git_commit'] if rev.get('git_commit') else 'no git repository'}). "
        f"Guest programs: supervisor `{sup.get('version')}` sha256 `{(sup.get('sha256') or '-')[:16]}`, per-test child `{(prov.get('child_sha256') or '-')[:16]}`, "
        f"canary module `{(prov.get('canary_sha256') or '-')[:16]}`, sandbox runner `{(prov.get('guest_runner_sha256') or '-')[:16]}`.",
        *([f"Runtime: Python {prov['runtime'].get('python')} on {prov['runtime'].get('platform')}; package executed from `{prov['runtime'].get('package_dir')}`."]
          if prov.get("runtime") else []),
        *([f"Pacing (development gateway): {prov['pacing'].get('budget')} of an assumed {prov['pacing'].get('hourly_limit_assumed')} requests per hour per key, "
           f"at most {prov['pacing'].get('max_concurrency')} in flight, bounded wait {prov['pacing'].get('max_wait_s')} s; {prov.get('retry_policy')}."]
          if prov.get("pacing") else []),
        "",
        f"Sampling ({sampling.get('provider')}): temperature {sampling.get('temperature') if sampling.get('temperature') is not None else 'controlled by the gateway'}, "
        f"max_tokens {sampling.get('max_tokens') if sampling.get('max_tokens') is not None else 'controlled by the gateway'}; "
        + "; ".join(f"{role}: {spec.get('model')}" + (f" ({spec.get('effort')})" if spec.get("effort") else "") for role, spec in roles.items()) + ".",
        "",
        "Limits: " + ", ".join(f"{k} {v}" for k, v in limits.items()) + ".",
        "",
        (f"Upstream: {upstream.get('url')} at commit `{upstream.get('commit')}`" + (f"; {upstream.get('reference')}" if upstream.get("reference") else "") + ".")
        if upstream else "Upstream: none (task authored for this project, not taken from an external repository).",
    ]
    return lines


def _audit_lines(audit: dict | None) -> str:
    if not audit:
        return "Not run (bundle predates the contract audit, or the run ended before the specification)."
    if audit.get("error"):
        return f"Unavailable: {audit['error']}"
    head = (f"Outcome: {audit.get('outcome')}. Auditor `{audit.get('model')}`; consistent={audit.get('consistent')}. {audit.get('notes') or ''} "
            f"Rule: {audit.get('rule') or ''}")
    rows = [[", ".join(c.get("requirement_ids") or []), (c.get("summary") or "")[:160], c.get("status"), c.get("exit_code") if c.get("exit_code") is not None else "-",
             (c.get("stdout_tail") or "").strip().splitlines()[0][:160] if (c.get("stdout_tail") or "").strip() else "-", c.get("operation_uuid") or "-"]
            for c in audit.get("conflicts") or []]
    return head + "\n\n" + _table(rows, ["Requirements", "Claimed conflict", "Witness result", "Exit", "First output line", "Operation"])


def render_markdown(bundle: dict) -> str:
    verdict = bundle["verdict"]
    ledger = (bundle.get("ledger") or {}).get("totals") or {}
    sealed = bundle.get("sealed_tests") or {"path": None, "sha256": None, "test_count": 0, "sealed_at_utc": None,
                                            "author_model": None, "attempts": 0, "expected_ids": []}
    red = bundle.get("red_run") or {}
    verify = bundle.get("verification") or {}
    spec = dict(bundle.get("spec") or {})
    spec.setdefault("feasible", None)
    spec.setdefault("restated_task", "(specification stage did not complete)")
    spec.setdefault("interface_contract", [])
    spec.setdefault("acceptance_criteria", [])
    task = bundle.get("task") or {"title": "(unknown)", "id": "(unknown)", "spec_sha256": "-", "base_image": "-", "statement": "",
                                  "test_runner": "-", "install_command": None}
    execution = bundle.get("execution") or {}
    candidate = bundle.get("candidate") or {"changed_paths": [], "scope_ok": None, "diff": ""}
    trajectory = bundle.get("trajectory") or {"turns": 0}
    breaker = bundle.get("breaker")
    mutation = (breaker or {}).get("mutation") if breaker else None
    adversarial = (breaker or {}).get("adversarial") if breaker else None
    drift = bundle.get("drift")
    arbitration = bundle.get("arbitration")
    grounding = bundle.get("grounding")
    binding = verify.get("binding") or {}
    heldout = verify.get("heldout")
    sealed_v = verify.get("sealed") or {}
    existing = verify.get("existing") or {}
    tamper = candidate.get("tamper_scan") or {}
    existing_class = existing.get("evidence_class") or "stdout"
    existing_binding = existing.get("binding") or {}
    model_calls = (bundle.get("ledger") or {}).get("model_calls") or []
    sandbox_ops = (bundle.get("ledger") or {}).get("sandbox_ops") or []
    derivation = verdict.get("derivation") or {}
    dec = decision(bundle)
    items = exhibits(bundle)
    shown = [e for e in items if e.get("shown")]
    what = proves(bundle)
    gate_rows = gates_table(bundle)
    counter = counterexamples(bundle)
    parts = [
        f"# Attest Proof Bundle: {task['title']}",
        "",
        f"**Verdict: {verdict['verdict']}**  ",
        f"Run `{bundle['run_id']}` · profile `{bundle['profile']['label']}` · provider `{bundle['profile']['provider']['provider']}` · executor `{bundle['profile']['executor']['executor']}`  ",
        f"Started {bundle['started_at_utc']}, finished {bundle['finished_at_utc']}.",
        "",
        f"**{dec['statement']}** {dec['explanation']}",
        "",
        f"Key evidence ({dec['evidence']['ref']}): {dec['evidence']['text']}",
        "",
        ("Weak spots: " + " ".join(dec["weak"])) if dec.get("weak") else "",
        "",
        "What to do: " + " ".join(dec["decide"]),
        "",
        "Reasons: " + ("; ".join(verdict["reasons"]) if verdict["reasons"] else "all gates passed"),
        ("Warnings: " + "; ".join(verdict.get("warnings") or [])) if verdict.get("warnings") else "",
        "",
        "## 0. What this bundle proves, and what it does not",
        "Generated from the recorded gates; each statement cites the exhibit that carries it.",
        "",
        "Proves:",
        "\n".join(f"- {line}" for line in what["proves"]) or "- nothing: no gate was reached",
        "",
        "Does not prove:",
        "\n".join(f"- {line}" for line in what["does_not_prove"]),
        "",
        _table([[e["ref"], e["title"], _status_word(e["status"]), e.get("evidence_class") or "-", e["summary"]] for e in shown],
               ["Exhibit", "Evidence", "Status", "Class", "Summary"]),
        "",
        "## 1. Frozen task and provenance",
        f"Task `{task['id']}`, spec digest `{task['spec_sha256']}`; base image `{task['base_image']}` "
        f"(uuid `{execution.get('base_image_uuid')}`), checkpoint `{execution.get('checkpoint_image_uuid')}`; "
        f"test runner `{task.get('test_runner')}`; install: `{' '.join(task.get('install_command') or []) or 'none'}` "
        f"(checkpoint networking {'on' if execution.get('checkpoint_networking') else 'off'}).",
        "",
        *_provenance_lines(bundle.get("provenance")),
        "",
        task["statement"],
        "",
        "## 2. Specification and contract",
        f"Feasible: {spec['feasible']}. {spec['restated_task']}",
        "",
        _table([[c["name"], c["signature"], c["behavior"][:160], "; ".join(c["error_cases"])[:160]] for c in spec["interface_contract"]],
               ["Name", "Signature", "Behavior", "Errors"]),
        "",
        "Acceptance criteria:",
        "\n".join(f"AC{i + 1}. {c}" for i, c in enumerate(spec["acceptance_criteria"])) or "(none)",
        "",
        "## 2b. Contract audit (executed witnesses)",
        _audit_lines(bundle.get("contract_audit")),
        "",
        "## 3. E1 Sealed tests (written before implementation by an independent model instance)",
        f"`{sealed['path']}` sha256 `{sealed['sha256']}`, {sealed['test_count']} test methods, sealed at {sealed['sealed_at_utc']} "
        f"by `{sealed['author_model']}`; attempts: {sealed['attempts']}.",
        "",
        f"Red check on the unmodified checkpoint (one child process per test under the supervisor): {red.get('summary_line', 'n/a')}: "
        f"{red.get('failing', 0)} of {red.get('ran', 0)} methods failing, {red.get('passed', 0)} passing; operation `{red.get('operation_uuid')}`.",
        (f"Coverage map (the sealer's own claim): " + (f"criteria without a claimed test: {', '.join(sealed['coverage_gaps'])}." if sealed.get("coverage_gaps")
         else "every acceptance criterion is claimed by at least one existing test method.")) if sealed.get("coverage") is not None else "",
        "",
        _table(_test_rows(red, sealed_v), ["Sealed test method", "Base (red)", "Candidate"]),
        (f"Corrected sealed module (E6): `{verify['corrected'].get('path')}` sha256 `{verify['corrected'].get('sha256')}`; corrected tests "
         f"{', '.join(t.split('.')[-1] for t in verify['corrected'].get('changed_tests') or [])}; on the candidate {(verify['corrected'].get('summary') or {}).get('summary_line')}; "
         f"validated: {verify['corrected'].get('discrimination')}; operation `{verify['corrected'].get('operation_uuid')}`. The sealed gate was re-run on it.")
        if verify.get("corrected") else "",
        "",
        "## 4. Candidate patch",
        f"{len(candidate['changed_paths'])} changed path(s); scope check {'passed' if candidate['scope_ok'] else ('not run' if candidate['scope_ok'] is None else 'FAILED')}; "
        f"{trajectory['turns']} implementer turn(s).",
        "",
        "```diff",
        (candidate["diff"] or "").rstrip() or "(no changes)",
        "```",
        "",
        (f"Static tamper scan of the added lines: {tamper.get('summary')} ({tamper.get('added_lines', 0)} added lines checked against "
         f"{tamper.get('patterns_checked', 0)} patterns; a warning, never a gate).") if tamper else "",
        _table([[f["path"], f["line"], f["pattern"], f["text"]] for f in tamper.get("flagged", [])], ["File", "Line", "Pattern", "Added line"]) if tamper.get("flagged") else "",
        "",
        "## 5. Fresh-branch verification (E1 binding; E4 held-out)",
        "Order: " + "; ".join(verify.get("order") or ["sealed supervisor and existing suite in one branch (bundle predates the order rule)"]) + ".",
        "",
        f"Sealed suite: {sealed_v.get('summary_line', 'n/a')}. Operation `{verify.get('operation_uuid')}`, networking disabled, disposable branch from the "
        f"checkpoint; the supervisor is the first step and runs two verifier canaries after the suite"
        + (f" (canary ok: {sealed_v.get('canary_ok')})" if sealed_v.get("canary_ok") is not None else "") + ".",
        "",
        _table([[k, "pass" if v else "FAIL"] for k, v in (binding.get("checks") or {}).items()], ["Binding check", "Result"]),
        "",
        f"Existing suite (evidence class `{existing_class}`): {existing.get('summary_line', 'n/a')} ({existing.get('passed', 0)} passed of {existing.get('ran', 0)}); "
        f"operation `{existing.get('operation_uuid')}`"
        + (f", bound through the supervisor: {len(existing.get('modules') or [])} module(s), binding {'ok' if existing_binding.get('ok') else 'FAILED'}"
           if existing_class == "bound" else f"; parsed from console output ({existing.get('evidence_note', '')})") + ".",
        "",
        (f"E4 held-out suite (evidence class `{heldout.get('evidence_class', 'stdout')}`; {', '.join(heldout.get('files', []))}): {heldout.get('summary_line')} "
         f"({heldout.get('passed', 0)} passed of {heldout.get('ran', 0)}); operation `{heldout.get('operation_uuid')}`. Gate: failures block VERIFIED.")
        if heldout else "E4 held-out suite: none configured.",
        "",
        "## 6. Gates and verdict rule",
        "Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the "
        "repository's test command; `model` = a model judgement. Skipped gates never count as passed.",
        "",
        _table([[row["gate"], row["label"], _status_word(row["result"]), row["evidence_class"], row["exhibit"] or "-", row["detail"]] for row in gate_rows],
               ["Gate", "Meaning", "Result", "Evidence", "Exhibit", "Detail"]),
        "",
        (f"Verdict rule: {derivation.get('rule')} Derived {derivation.get('verdict')}; blocking: "
         f"{', '.join(derivation.get('blocking') or []) or 'nothing'}.") if derivation else
        "Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons (derivation not recorded; bundle predates M2).",
        "",
        "## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)",
        (f"E2: mutants of changed lines, each in its own branch: {mutation['generated']} generated, {mutation['evaluated']} evaluated: {mutation['killed']} killed, "
         f"{mutation['survived']} survived, {mutation['unknown']} unknown; mutation score {_fmt(mutation['score'])} (threshold {mutation['threshold']}).") if mutation else "E2: mutation pass not run (verification did not pass).",
        "",
        _table([[m["id"], m["path"], m["lineno"], m["description"], m["status"], ", ".join(m["killed_by"])[:120], m["operation_uuid"]]
                for m in (mutation or {}).get("mutants", [])], ["Mutant", "File", "Line", "Mutation", "Status", "Killed by", "Operation"]),
        "",
        (f"E3: model-written adversarial tests (`breaker_tests.py`, by `{adversarial.get('author_model')}`, sha256 `{adversarial.get('sha256')}`): "
         f"{(adversarial.get('summary') or {}).get('summary_line', 'n/a')}; binding {'ok' if (adversarial.get('binding') or {}).get('ok') else 'FAILED'}; operation `{adversarial.get('operation_uuid')}`. "
         f"Notes: {adversarial.get('notes', '')}") if adversarial and not adversarial.get("unusable") and "summary" in adversarial else
        (f"E3: model-written adversarial tests: unusable ({adversarial.get('unusable')}); the gate fails." if adversarial and adversarial.get("unusable") else
         (f"E3: model-written adversarial tests: none ran ({adversarial.get('skipped')}); the gate of this older bundle counted it as a pass." if adversarial and adversarial.get("skipped")
          else "E3: model-written adversarial tests: not run.")),
        "",
        _table([[t["id"].split(".")[-1], t["outcome"]] for t in ((adversarial or {}).get("summary") or {}).get("tests", []) if t["outcome"] != "ok"],
               ["Failing adversarial test", "Outcome"]) if adversarial and not adversarial.get("unusable") and "summary" in adversarial else "",
        (f"Corrected adversarial module (E6): `{adversarial['corrected'].get('path')}` sha256 `{adversarial['corrected'].get('sha256')}`; corrected tests "
         f"{', '.join(t.split('.')[-1] for t in adversarial['corrected'].get('changed_tests') or [])}; on the candidate {(adversarial['corrected'].get('summary') or {}).get('summary_line')}; "
         f"validated: {adversarial['corrected'].get('discrimination')}; operation `{adversarial['corrected'].get('operation_uuid')}`. The adversarial gate was re-run on it.")
        if adversarial and adversarial.get("corrected") else "",
        (f"Adversarial authoring: {adversarial.get('attempts')} attempt(s)" + ("; the last escalated to the arbiter's model after syntax errors" if adversarial.get("escalated") else "") + ".")
        if adversarial and adversarial.get("attempts") else "",
        "",
        "### Counterexamples",
        ("\n".join(
            f"- {c['exhibit']} `{c['name']}`: {c['outcome']}"
            + (f"; {c['assertion']['kind']}: {c['assertion']['message']}" if c["assertion"].get("kind") else "")
            + (f"; first `{c['assertion']['first']}` vs second `{c['assertion']['second']}` (the test's argument order decides which is the actual value)"
               if c["assertion"].get("first") is not None else "")
            + (f"; arbiter: {c['classification_label']}" if c.get("classification_label") else "")
            + (f"; contract basis: {c['contract_basis']}" if c.get("contract_basis") else "")
            for c in counter) if counter else "None: no sealed, adversarial or held-out test failed on the candidate."),
        "",
        "## 8. E5 Drift audit",
        (f"Score {_fmt(float(drift.get('drift_score', 0)))} ({drift.get('assessment')}; threshold {drift.get('threshold')}). {drift.get('summary', '')}") if drift and "drift_score" in drift else
        (f"Drift audit unavailable: {drift.get('error')}" if drift else "Drift audit not run."),
        "",
        ("Scope narrowed: " + ("; ".join(drift.get("scope_narrowed") or []) or "none") + "  \n" +
         "Scope widened: " + ("; ".join(drift.get("scope_widened") or []) or "none") + "  \n" +
         "Unsupported claims: " + ("; ".join(drift.get("unsupported_claims") or []) or "none")) if drift and "drift_score" in drift else "",
        "",
        "## 8b. E6 Arbitration of generated-test failures",
        (f"{arbitration['headline']} (mode: {'validated corrections re-run their gates' if arbitration.get('applied') else 'advisory'}). "
         f"Classifications: {arbitration['counts']}. {arbitration.get('note', '')}"
         + (f" Rule: {arbitration['rule']}" if arbitration.get("rule") else "")
         + (" Gates re-run on validated corrections: " + "; ".join(f"{a.get('gate')} (tests {', '.join(t.split('.')[-1] for t in a.get('changed_tests') or [])}; {a.get('discrimination')})"
                                                                 for a in arbitration.get("applied_to_gates") or []) + "." if arbitration.get("applied_to_gates") else "")) if arbitration else
        "Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).",
        "",
        _table([[c["test_id"].split(".")[-1], c["classification"], (c.get("rationale") or "")[:140], (c.get("contract_basis") or "")[:140]]
                for m in (arbitration or {}).get("modules", []) for c in m.get("classifications", [])],
               ["Failing test", "Classification", "Rationale", "Contract basis"]) if arbitration else "",
        "",
        "\n".join(f"- `{m['module']}` corrected re-run: candidate {((m.get('candidate_rerun') or {}).get('summary_line') or 'n/a')}; "
                 f"base {((m.get('base_rerun') or {}).get('summary_line') or 'n/a')}"
                 + (f"; mutant re-runs {len(m.get('mutant_reruns') or [])}" if m.get("mutant_reruns") else "")
                 + f"; validated={m.get('validated', m.get('cleared_module'))}"
                 + ("; sealed assertion or exception failure: never overridden, the hold stands" if m.get("sealed_assertion_hold") else "")
                 + (f"; base evidence: {(m.get('base_rerun') or {}).get('untrusted')}" if (m.get("base_rerun") or {}).get("untrusted") else "")
                 + (f"; not applied: {m['error']}" if m.get('error') else "")
                 for m in (arbitration or {}).get("modules", [])) if arbitration else "",
        "",
        "## 9. Grounding",
        (f"{grounding['calls']} Tavily call(s) for {len(grounding['queries'])} quer{'y' if len(grounding['queries']) == 1 else 'ies'}; {len(grounding['sources'])} sources cited below.") if grounding and grounding.get("calls") else
        (f"No grounding calls ({grounding.get('skipped')})." if grounding else "Grounding not configured."),
        "",
        _table([[s.get("query"), s.get("title"), s.get("url")] for s in (grounding or {}).get("sources", [])], ["Query", "Title", "URL"]) if grounding and grounding.get("sources") else "",
        "",
        "## 10. Ledger",
        _table([[f"{c['provider']}:{c['requested_model']}", c["role"], c["stage"], c["requested_effort"] or "-", c["tokens_in"] if c["tokens_in"] is not None else "-",
                 c["tokens_out"] if c["tokens_out"] is not None else "-", c["tokens_cached"] if c["tokens_cached"] is not None else "-",
                 _fmt(c["cost_usd"], 6), f"{c['elapsed_ms'] / 1000:.1f}s",
                 "ok" if c["ok"] else ("not sent" if c.get("request_sent") is False else "malformed" if c["malformed_output"] else "error")]
                for c in model_calls],
               ["Model", "Role", "Stage", "Effort", "In", "Out", "Cached", "USD", "Elapsed", "Status"]),
        "",
        f"Model calls: {ledger.get('model_calls')} ({ledger.get('model_calls_failed')} failed, {ledger.get('malformed_outputs')} malformed"
        + (f", {ledger.get('rate_limited_calls')} rejected by the provider's hourly limit and retried after waiting {round((ledger.get('pacing_wait_ms') or 0) / 1000)} s in total"
           if ledger.get("rate_limited_calls") or ledger.get("pacing_wait_ms") else "") + "); "
        f"tokens in/out/cached {ledger.get('tokens_in')}/{ledger.get('tokens_out')}/{ledger.get('tokens_cached')}; "
        f"Inference USD: {ledger.get('cost_usd') if ledger.get('cost_usd') is not None else 'n/a (development gateway allowance, not billed in USD)'}"
        + (f"; {ledger.get('calls_not_sent')} attempt(s) were never sent (the connection failed first) and cost nothing" if ledger.get("calls_not_sent") else "") + ".",
        "",
        _table([[o["stage"], o["operation_uuid"], o["status"], o["exit_code"], f"{o['duration_s']}s" if o["duration_s"] is not None else "-",
                 "retained" if o["result_image_uuid"] else "disposable", "on" if o.get("networking_enabled") else "off", o["raw_cost_diag"]]
                for o in sandbox_ops],
               ["Sandbox op", "Operation", "Status", "Exit", "Duration", "Image", "Net", "raw cost diag (not USD)"]),
        "",
        f"Sandbox operations: {ledger.get('sandbox_operations')}, total guest duration {ledger.get('sandbox_duration_s')}s, retained images {ledger.get('sandbox_retained_images')}"
        + (f", {ledger.get('sandbox_spawn_retries')} spawn(s) sent again after a connection failure" if ledger.get("sandbox_spawn_retries") else "")
        + (f", {ledger.get('sandbox_uncertain')} operation(s) with an unknown outcome (never replayed)" if ledger.get("sandbox_uncertain") else "") + ".",
        "",
        "Inference, Token Factory Sandboxes and Tavily search are separate services, metered and billed separately; this record never adds "
        "them into one figure. The inference figure above is the only USD amount it states: Sandboxes operations carry raw cost diagnostics "
        f"with no confirmed currency, and Tavily used {(grounding or {}).get('calls') or 0} search call(s) (section 9).",
        "",
        "## 11. Limitations of this bundle",
        "\n".join(f"- {item}" for item in bundle.get("limitations") or []),
        "",
    ]
    if verdict["verdict"] == "ERROR":
        e7 = next(e for e in items if e["ref"] == "E7")
        d = e7["detail"]
        parts += [
            "## 12. E7 Failure record",
            f"Component: {d.get('component')}; stage: {d.get('stage')}; model calls {d.get('model_calls')} ({d.get('model_calls_failed')} failed); "
            f"sandbox operations {d.get('sandbox_operations')}; committed inference USD {d.get('cost_usd_committed')}; "
            f"uncertain unpriced calls {d.get('uncertain_unpriced_calls')}; retried: no; outcome uncertain: {'yes' if d.get('uncertain') else 'no'}.",
            "",
            "\n".join(f"- {r}" for r in d.get("reasons") or []),
            "",
        ]
    parts += [
        "## 13. Artifacts",
        f"Every file of the run directory is listed in `{MANIFEST_FILE}` with its sha256 and size (written last, so it covers this file and "
        "proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from "
        "`verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.",
        "",
        _table([[name, purpose_of(name)] for name in ("proof_bundle.json", "PROOF.md", MANIFEST_FILE, "task.frozen.json", "spec.json", "contract_audit.json",
                                                       "sealed/test_sealed.py", "candidate.patch", "verify.json", "verify_raw.json", "breaker.json", "breaker_tests.py",
                                                       "drift.json", "arbitration.json", "ledger.json", "ledger.jsonl")], ["Artifact", "Purpose"]),
        "",
    ]
    return "\n".join(p for p in parts if p is not None)


def _write_atomic(path: Path, text: str) -> None:
    """Temporary file plus rename: a concurrent reader (the console's detail endpoint) never sees a half-written artifact (API-08)."""
    import os
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_bundle(out_dir: Path, bundle: dict) -> None:
    _write_atomic(out_dir / "proof_bundle.json", json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
    _write_atomic(out_dir / "PROOF.md", render_markdown(bundle))
