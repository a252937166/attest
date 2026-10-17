"""Parse test-runner output into per-method outcomes and raw events.

unittest: `python -m unittest -v`; subtests produce one event per subtest and leave the method's own line
without an outcome, so methods and events are counted separately.
pytest: `python -m pytest -q -rA`.
"""

from __future__ import annotations

import re

UNITTEST_LINE = re.compile(r"^(?P<name>\w+) \((?P<id>[^)]+)\)(?P<sub> \[[^\n]*\])?(?P<rest>.*)$")
RAN_RE = re.compile(r"^Ran (?P<n>\d+) tests? in", re.MULTILINE)
FAILED_RE = re.compile(r"^FAILED \((?P<detail>[^)]*)\)", re.MULTILINE)
OUTCOMES = ("ok", "FAIL", "ERROR", "skipped", "expected failure", "unexpected success")
BAD_OUTCOMES = {"FAIL", "ERROR", "unexpected success"}
RANK = {"ERROR": 4, "FAIL": 4, "unexpected success": 4, "unknown": 2, "skipped": 1, "expected failure": 1, "ok": 0}

PYTEST_LINE = re.compile(r"^(?P<outcome>PASSED|FAILED|ERROR|XFAIL|XPASS) (?P<id>\S+::\S+)(?P<rest>.*)$")
PYTEST_SUMMARY = re.compile(r"^=*\s*(?P<body>[^=\n]*?\b(?:passed|failed|errors?|skipped|xfailed|xpassed|no tests ran)\b[^=\n]*?) in [\d.]+s(?: \([^)]*\))?\s*=*\s*$", re.MULTILINE)
PYTEST_COUNT = re.compile(r"(?P<n>\d+) (?P<kind>passed|failed|errors?|skipped|xfailed|xpassed|warnings?|deselected)")


def _outcome(raw: str) -> str:
    raw = raw.strip()
    for outcome in OUTCOMES:
        if raw.startswith(outcome):
            return outcome
    return "unknown" if not raw else raw[:30]


def _empty(runner: str, exit_code, summary: str) -> dict:
    return {"runner": runner, "ran": 0, "tests": [], "events": [], "passed": 0, "failing": 0, "failures": 0,
            "errors": 0, "subtest_events": 0, "module_error": exit_code not in (0, None), "all_passed": False,
            "summary_line": summary}


def parse_unittest(stdout: str, stderr: str, exit_code: int | None) -> dict:
    text = (stderr or "") + "\n" + (stdout or "")
    events: list[dict] = []
    main: dict[str, str] = {}
    order: list[str] = []
    pending: tuple[str, str | None] | None = None

    def record(tid: str, sub: str | None, outcome: str) -> None:
        if tid not in main:
            main[tid] = ""
            order.append(tid)
        if sub is None:
            main[tid] = outcome
        if outcome:
            events.append({"id": tid, "subtest": sub, "outcome": outcome})

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = UNITTEST_LINE.match(line)
        if match and ("." not in match.group("id") or match.group("name") in ("FAILED", "OK")):
            match = None  # summary lines such as "FAILED (errors=24)" are not test IDs; unittest IDs are dotted
        if match:
            tid, sub, rest = match.group("id"), (match.group("sub") or "").strip() or None, match.group("rest")
            if " ... " in rest:
                record(tid, sub, _outcome(rest.split(" ... ")[-1]))
                pending = None
            else:
                if tid not in main:
                    main[tid] = ""
                    order.append(tid)
                pending = (tid, sub)
            continue
        if pending and " ... " in line:
            tid, sub = pending
            record(tid, sub, _outcome(line.split(" ... ")[-1]))
            pending = None

    methods = []
    for tid in order:
        outs = [e["outcome"] for e in events if e["id"] == tid]
        if main.get(tid) and main[tid] not in outs:
            outs.append(main[tid])
        worst = max(outs, key=lambda o: RANK.get(o, 2)) if outs else "unknown"
        methods.append({"id": tid, "outcome": worst, "events": len(outs)})
    ran_match = RAN_RE.search(text)
    failed_match = FAILED_RE.search(text)
    counts = {"failures": 0, "errors": 0}
    if failed_match:
        for key in counts:
            m = re.search(rf"{key}=(\d+)", failed_match.group("detail"))
            if m:
                counts[key] = int(m.group(1))
    ran = int(ran_match.group("n")) if ran_match else 0
    module_error = ran == 0 and exit_code not in (0, None)
    passed = sum(1 for t in methods if t["outcome"] == "ok")
    failing = sum(1 for t in methods if t["outcome"] in BAD_OUTCOMES)
    if module_error and not methods:
        counts["errors"] = max(counts["errors"], 1)
    summary = failed_match.group(0) if failed_match else ("OK" if exit_code == 0 and ran_match else "no summary")
    return {"runner": "unittest", "ran": ran, "tests": methods, "events": events, "passed": passed,
            "failing": failing, "failures": counts["failures"], "errors": counts["errors"],
            "subtest_events": sum(1 for e in events if e["subtest"]), "module_error": module_error,
            "all_passed": exit_code == 0 and ran > 0 and failing == 0, "summary_line": summary}


def parse_pytest(stdout: str, stderr: str, exit_code: int | None) -> dict:
    text = (stdout or "") + "\n" + (stderr or "")
    methods: list[dict] = []
    seen: dict[str, int] = {}
    for raw_line in text.splitlines():
        match = PYTEST_LINE.match(raw_line.strip())
        if not match:
            continue
        tid, outcome = match.group("id"), match.group("outcome")
        mapped = {"PASSED": "ok", "FAILED": "FAIL", "ERROR": "ERROR", "XFAIL": "expected failure", "XPASS": "unexpected success"}[outcome]
        if tid in seen:
            if RANK.get(mapped, 2) > RANK.get(methods[seen[tid]]["outcome"], 2):
                methods[seen[tid]]["outcome"] = mapped
            methods[seen[tid]]["events"] += 1
        else:
            seen[tid] = len(methods)
            methods.append({"id": tid, "outcome": mapped, "events": 1})
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0, "xfailed": 0, "xpassed": 0}
    summary_line = "no summary"
    for match in PYTEST_SUMMARY.finditer(text):
        summary_line = match.group(0).strip().strip("=").strip()
        for cm in PYTEST_COUNT.finditer(match.group("body")):
            kind = cm.group("kind").rstrip("s")
            if kind in counts:
                counts[kind] = int(cm.group("n"))
    ran = counts["passed"] + counts["failed"] + counts["error"] + counts["xfailed"] + counts["xpassed"]
    failing = counts["failed"] + counts["error"]
    module_error = exit_code in (2, 3, 4) or (ran == 0 and exit_code not in (0, 5, None))
    return {"runner": "pytest", "ran": ran, "tests": methods, "events": [], "passed": counts["passed"],
            "failing": failing, "failures": counts["failed"], "errors": counts["error"], "subtest_events": 0,
            "module_error": module_error, "all_passed": exit_code == 0 and ran > 0 and failing == 0,
            "summary_line": summary_line, "skipped": counts["skipped"]}


def parse_test_output(runner: str, stdout: str, stderr: str, exit_code: int | None) -> dict:
    if runner == "pytest":
        return parse_pytest(stdout, stderr, exit_code)
    return parse_unittest(stdout, stderr, exit_code)
