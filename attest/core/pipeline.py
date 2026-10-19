"""One task, end to end: freeze, checkpoint, spec, contract audit, ground, seal, red, implement, verify, hold out, break, audit,
arbitrate, attest.

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons; infrastructure
failures yield ERROR. Held-out failures, surviving mutants beyond the threshold, failing model-written adversarial tests and
high drift all block VERIFIED. INFEASIBLE requires an executed witness program that demonstrates the contract's contradiction
on the unmodified repository; a claim of infeasibility without a demonstration is a hold. A failing generated test may be
corrected by the arbiter only under mechanical validation (same test set, only the failing tests' bodies changed, passes
on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results); the corrected
gate is then re-run and the verdict re-derived. A sealed test that failed by assertion or by an exception, whatever its
origin, is never overridden (audit finding CORE-02: an exception's type or frame does not establish that the test, rather
than the candidate, is at fault); only a test the supervisor killed at its timeout may be corrected. Lost, forged,
incomplete or non-isolated execution results are never evidence of anything (CORE-01/03): they leave a mutant unknown and a
correction unvalidated. NO CHANGE distinguishes "finished without editing" from "turn budget exhausted without a patch"
(an unfinished task, never a successful repair).
"""

from __future__ import annotations

import ast
import datetime as dt
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..ledger import JOURNAL_FILE, Ledger, utcnow
from ..models.base import ModelError
from .diagnostics import SIDECAR_DIR, Diagnostics
from .external import LIMITS as EXTERNAL_LIMITS, external_policy_problems, repository_problems
from .grounding import ground, sources_text
from .mutate import generate_mutants
from .prompts import (ACTION_SCHEMA, ARBITRATION_SCHEMA, BREAKER_SCHEMA, CONTRACT_AUDIT_SCHEMA, DRIFT_SCHEMA, SEAL_SCHEMA, SPEC_SCHEMA,
                      WITNESS_EXIT_CODE, WITNESS_INPUT_DOMAIN, WITNESS_MARKER, arbitrate_prompt, breaker_prompt, contract_audit_prompt,
                      drift_prompt, implement_prompt, seal_prompt, spec_prompt)
from .manifest import MANIFEST_FILE, build_manifest
from .proof import write_bundle
from .provenance import build_provenance
from .sealed import (BAD_OUTCOMES, SEALED_FILE, SUPERVISOR_VERSION, bind_modules, bind_verification, guest_files_for, is_supervisor_step,
                     module_name_for, new_nonce, outcome_classes, read_sealed_result, repair_escapes, repo_suite_files, sealed_steps,
                     sha256_text, static_repo_tests, static_test_ids, structural_problems, summarize)
from .tamper import scan_diff
from .task import GUEST_PYTHON, GUEST_REPO, GUEST_SEALED_DIR, TaskSpec
from .testparse import parse_test_output
from .verdict import EVIDENCE_PROTOCOL_VERSION, derive
from .witness import REPOSITORY_COPY_DIR, WITNESS_LANGUAGE, Repository, analyze_witness
from .workspace import PolicyViolation, Workspace, snapshot_repo

GUEST_BREAKER_DIR = "/tmp/breaker"
GUEST_SUITE_DIR = "/tmp/attest_suite"      # verifier files for the repository's own suite run through the supervisor
GUEST_HELDOUT_DIR = "/tmp/attest_heldout"  # verifier files for held-out modules run through the supervisor
MAX_SEAL_ATTEMPTS = 3
MIN_SEALED_TESTS = 5
MIN_MUTANTS_FOR_SCORE = 4
MIN_ADVERSARIAL_WHEN_NO_MUTANTS = 6  # a patch with no mutable sites passes the mutation gate only with a real adversarial suite
MAX_BREAKER_ATTEMPTS = 3            # the third attempt escalates to the arbiter's model (a syntax error twice in a row is a weak author, not a verdict)
MAX_CORRECTED_TESTS = 3             # more defective generated tests than this is a human's review, not an arbitration
MAX_MUTANTS_FOR_DISCRIMINATION = 3  # mutants a corrected adversarial module is run against when it passes on the base
MAX_WITNESSES = 3                   # contract-audit witness programs executed per run
WITNESS_TIMEOUT = 60
GUEST_AUDIT_DIR = "/tmp/attest_audit"
VERIFICATION_ORDER = ("verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it)",
                      "existing: the repository's own suite runs afterwards in its own disposable branch",
                      "heldout: held-out modules run afterwards in their own disposable branch")


class PipelineAbort(RuntimeError):
    def __init__(self, verdict: str, reason: str):
        super().__init__(reason)
        self.verdict = verdict
        self.reason = reason


def _tail(text: str, limit: int = 3500) -> str:
    text = text or ""
    return text if len(text) <= limit else "...[earlier output omitted]...\n" + text[-limit:]


# Exception types that, raised in the last frame of the test module itself ON THE UNMODIFIED BASE, suggest the test body is
# broken rather than the behaviour missing. Used only as feedback to the sealer before the suite is sealed (the red check);
# never as grounds to weaken an executed oracle (CORE-02: a bad candidate's return value can raise exactly these in correct
# test code, so neither the exception type nor the frame establishes which side is at fault).
TEST_INTERNAL_EXCEPTIONS = ("ValueError: too many values to unpack", "ValueError: not enough values to unpack", "NameError:",
                            "UnboundLocalError:", "ZeroDivisionError:", "IndentationError:", "SyntaxError:")


def test_internal_errors(tests: list[dict], module_file: str = f"/{SEALED_FILE}") -> list[str]:
    """Sealed tests whose red failure on the base is an error raised by the test module's own code (traceback's last frame in
    the test file and an exception that cannot come from calling an unimplemented API). Returned as `name: exception` strings
    and fed back to the sealer; a heuristic for re-sealing, not evidence about a candidate."""
    found = []
    for test in tests or []:
        if test.get("outcome") != "ERROR":
            continue
        tail = (test.get("failure_tail") or "").strip().splitlines()
        if not tail:
            continue
        last_frame = next((line for line in reversed(tail) if line.strip().startswith('File "')), "")
        exception = tail[-1].strip()
        if module_file in last_frame and exception.startswith(TEST_INTERNAL_EXCEPTIONS):
            found.append(f"{test.get('id', '').split('.')[-1]}: {exception[:120]}")
    return found


def oracle_disagreement(test: dict) -> bool:
    """True when a failing sealed test contradicts the candidate: an assertion failed or an exception was raised, whatever
    its type and wherever its innermost frame lies (a candidate that returns the wrong shape makes correct test code raise,
    so neither tells the test from the candidate; CORE-02). False only for a test the supervisor itself killed at the
    per-test timeout, which is a workload fact, not a disagreement about behaviour. Only the latter may be corrected by
    arbitration; the former is the pre-registered oracle disagreeing with the candidate, which a model's judgement never
    overrides."""
    if test.get("outcome") == "TIMEOUT" or test.get("timed_out"):
        return False
    return True


def _is_testcase(node: ast.ClassDef) -> bool:
    return any(str(getattr(b, "attr", getattr(b, "id", ""))).endswith("TestCase") for b in node.bases)


def _module_shape(source: str, module_name: str) -> dict:
    """The parts of a test module a correction may and may not touch (CORE-05). `methods` maps every test id to the dump
    of its body; `skeleton` is the dump of the whole module with every test method's body replaced by `pass` and the import
    statements removed, so that class bases, decorators, keywords, method signatures, helpers, setUp and module-level code are
    all compared verbatim; `imports` are the import statements' dumps and `bound` the names the module binds at top level."""
    tree = ast.parse(source)
    methods: dict[str, str] = {}
    skeleton: list[str] = []
    imports: list[str] = []
    import_statements: list[tuple[str, set[str]]] = []
    import_names: set[str] = set()
    bound: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = {(alias.asname or alias.name).split(".")[0] for alias in node.names}
            imports.append(ast.dump(node, include_attributes=False))
            import_statements.append((imports[-1], names))
            import_names |= names
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                for name in ast.walk(target):
                    if isinstance(name, ast.Name):
                        bound.add(name.id)
        if isinstance(node, ast.ClassDef) and _is_testcase(node):
            new_body = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test"):
                    methods[f"{module_name}.{node.name}.{item.name}"] = ast.dump(ast.Module(body=item.body, type_ignores=[]), include_attributes=False)
                    placeholder = type(item)(name=item.name, args=item.args, body=[ast.Pass()], decorator_list=item.decorator_list,
                                             returns=item.returns, type_comment=None, type_params=getattr(item, "type_params", []))
                    new_body.append(placeholder)
                else:
                    new_body.append(item)
            node = ast.ClassDef(name=node.name, bases=node.bases, keywords=node.keywords, body=new_body, decorator_list=node.decorator_list,
                                type_params=getattr(node, "type_params", []))
        skeleton.append(ast.dump(node, include_attributes=False))
    return {"methods": methods, "skeleton": skeleton, "imports": imports, "import_statements": import_statements, "import_names": import_names,
            "bound": bound | import_names}


def correction_problems(original: str, corrected: str, module_name: str, failing_ids: set[str] | None = None,
                        max_tests: int | None = None) -> tuple[list[str], set[str]]:
    """Mechanical scope rule for a corrected test module (CORE-05). Returns (problems, changed test ids). A correction may
    change only the bodies of the failing test methods and may ADD import statements that bind new names; it may not remove
    or rewrite an existing import, rebind a name the module already binds, or change anything else (class bases, decorators,
    keywords, method signatures, helpers, setUp/tearDown, module-level code). Raises SyntaxError when a module does not parse."""
    before = _module_shape(original, module_name)
    after = _module_shape(corrected, module_name)
    problems: list[str] = []
    if set(static_test_ids(original, module_name)) != set(static_test_ids(corrected, module_name)):
        problems.append("the set of test methods changed")
    if before["skeleton"] != after["skeleton"]:
        problems.append("module-level code, class metadata (bases, decorators, keywords), helpers or a method signature changed")
    removed = [imp for imp in before["imports"] if imp not in after["imports"]]
    if removed:
        problems.append(f"{len(removed)} existing import statement(s) removed or rewritten")
    # every import statement that is new binds names; none of them may already be bound by the original module (a second
    # `from other import f` next to the original `from m import f` rebinds f for the unchanged tests)
    new_names: set[str] = set()
    for dump, names in after["import_statements"]:
        if dump not in before["imports"]:
            new_names |= names
    collisions = sorted(new_names & before["bound"])
    if collisions:
        problems.append("new import(s) rebind name(s) the module already binds: " + ", ".join(collisions)[:120])
    changed = {tid for tid in set(before["methods"]) | set(after["methods"]) if before["methods"].get(tid) != after["methods"].get(tid)}
    if failing_ids is not None:
        extra = changed - set(failing_ids)
        if extra:
            problems.append("tests that were not failing were altered: " + ", ".join(sorted(extra))[:200])
        if not changed and not problems:
            problems.append("the correction is identical to the original module")
    if max_tests is not None and len(changed) > max_tests:
        problems.append(f"{len(changed)} tests would be corrected, more than the limit of {max_tests}")
    return problems, changed


def methods_changed(original: str, corrected: str, module_name: str) -> set[str]:
    """Test methods whose body differs between two versions of a module, plus "<module>" when anything outside those bodies
    differs other than an additive, non-colliding import (CORE-05). Kept for `attest check` and older callers."""
    problems, changed = correction_problems(original, corrected, module_name)
    if any(not p.startswith("the set of test methods") for p in problems):
        changed = set(changed) | {"<module>"}
    return changed


def classification_problems(classifications: list[dict], failing_ids: set[str]) -> tuple[list[str], dict[str, dict]]:
    """Exactly one classification per failing test id (CORE-05): no unknown, duplicate or missing ids. A short method name is
    accepted only when it names exactly one failing test. Returns (problems, classification by full id)."""
    by_id: dict[str, dict] = {}
    problems: list[str] = []
    short = {}
    for fid in failing_ids:
        short.setdefault(fid.split(".")[-1], []).append(fid)
    for entry in classifications or []:
        cid = str(entry.get("test_id") or "")
        full = cid if cid in failing_ids else (short[cid][0] if len(short.get(cid, [])) == 1 else None)
        if full is None:
            problems.append(f"unknown test id {cid!r}")
            continue
        if full in by_id:
            problems.append(f"duplicate classification for {full}")
            continue
        by_id[full] = entry
    missing = sorted(set(failing_ids) - set(by_id))
    if missing:
        problems.append("failing test(s) without a classification: " + ", ".join(missing)[:200])
    return problems, by_id


def coverage_gaps(coverage, criteria: list[str], test_ids: list[str]) -> list[str]:
    """Acceptance criteria (as `ACn`) that no entry of the sealer's coverage map ties to an existing test method. The map is
    the sealer's own claim; this only checks that the claim is complete and names real tests."""
    if coverage is None or not criteria:
        return []
    names = {tid.split(".")[-1] for tid in test_ids}
    covered: set[int] = set()
    for entry in coverage or []:
        try:
            index = int(entry.get("criterion"))
        except (TypeError, ValueError, AttributeError):
            continue
        tests = [t for t in (entry.get("tests") or []) if str(t).split(".")[-1] in names]
        if tests:
            covered.add(index)
    return [f"AC{i}" for i in range(1, len(criteria) + 1) if i not in covered]


def witness_constraint_problems(source: str, repository: Repository | None = None) -> list[str]:
    """Why a witness program is outside the constrained witness language (attest.core.witness, WITNESS_LANGUAGE; review findings
    R5-03 and R6-1). Empty when it conforms. The language is a positive grammar with statically resolved call origins: without a
    `repository` every repository import is unresolved, so only a witness that imports nothing from the repository can conform."""
    return analyze_witness(source, repository)["problems"]


def requirement_provenance(ids: list[str], task_ids: set[str], derived_ids: set[str]) -> str:
    """'task' when every id is an authoritative task criterion, 'derived' when every id is a specification criterion, 'mixed'
    otherwise; 'unknown' when an id matches neither (the caller refuses such a conflict)."""
    if not ids or any(i not in task_ids and i not in derived_ids for i in ids):
        return "unknown"
    if all(i in task_ids for i in ids):
        return "task"
    if all(i in derived_ids for i in ids):
        return "derived"
    return "mixed"


ARBITRATION_RULE = ("a correction counts only when it keeps every test method, changes only the bodies of the failing ones (imports may be "
                    "added, nothing existing may be rebound), is classified for exactly the failing tests, passes on the candidate under the "
                    "supervisor and still discriminates with authentic, structurally sound results (every corrected sealed test fails on the "
                    "unmodified base; a corrected adversarial test fails on the base or catches a validly killed mutant of the patch); a sealed "
                    "test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor "
                    "killed at its timeout may be corrected); a validated correction re-runs its gate and the verdict is derived from the gates")
MUTANT_POLICY = ("a mutant is killed only when at least one expected sealed test failed with an authentic child result (exit code 1 and a FAIL "
                 "or ERROR report bound to the nonce) under a structurally sound supervisor run (completed, isolated, nonce and digests intact, "
                 "the expected test ids and nothing else, no lost, forged or mismatched result, no crash, no start-up hook); it survived only when "
                 "every expected test passed authentically; a run with any structural problem, untrusted record or timed-out test is unknown and "
                 "excluded from the score")


def base_discrimination(result: dict | None, summary: dict, expected_ids: list[str], module_sha: str, nonce: str, changed_tests: list[str],
                        label: str) -> dict:
    """The base re-run of a corrected module as discrimination evidence (CORE-01): the record carries the recomputable binding,
    the structural problems, every corrected test's outcome class and the resulting discrimination (or why there is none).
    Shared with `attest check`."""
    binding = bind_verification(result, expected_ids, module_sha, nonce)
    problems = structural_problems(binding, result)
    classes = outcome_classes(result)
    outcomes = {t: classes.get(t, "missing") for t in changed_tests}
    red = sorted(t for t in changed_tests if outcomes[t] == "red")
    untrusted = sorted(t for t in changed_tests if outcomes[t] in ("untrusted", "missing"))
    entry = {"summary_line": summary.get("summary_line"), "failing": summary.get("failing"), "nonce": nonce, "expected_ids": list(expected_ids),
             "binding": binding, "structural_problems": problems, "outcomes": outcomes, "corrected_tests_failing_on_base": red,
             "discrimination": None, "untrusted": None}
    if problems:
        entry["untrusted"] = "structural problems in the base run: " + ", ".join(problems)[:200]
    elif untrusted:
        entry["untrusted"] = "corrected test(s) without an authentic result on the base: " + ", ".join(f"{t.split('.')[-1]} {outcomes[t]}" for t in untrusted)[:200]
    elif label == "sealed":
        if set(red) == set(changed_tests) and changed_tests:
            entry["discrimination"] = "every corrected sealed test fails on the unmodified base with an authentic result (red check preserved)"
    elif red:
        entry["discrimination"] = f"{len(red)} of {len(changed_tests)} corrected test(s) fail on the unmodified base with an authentic result"
    return entry


def mutant_rerun_discrimination(result: dict | None, summary: dict, expected_ids: list[str], module_sha: str, nonce: str, changed_tests: list[str]) -> dict:
    """One corrected adversarial module run against one validly killed mutant (CORE-01): corrected tests count as catching the
    mutant only with an authentic red result under a structurally sound run. Shared with `attest check`."""
    binding = bind_verification(result, expected_ids, module_sha, nonce, canary=False)
    problems = structural_problems(binding, result)
    classes = outcome_classes(result)
    caught = sorted(t for t in changed_tests if classes.get(t) == "red") if not problems else []
    return {"summary_line": summary.get("summary_line"), "nonce": nonce, "expected_ids": list(expected_ids), "binding": binding,
            "structural_problems": problems, "outcomes": {t: classes.get(t, "missing") for t in changed_tests}, "corrected_tests_failing": caught,
            "untrusted": ("structural problems in the mutant run: " + ", ".join(problems)[:200]) if problems else None}


def classify_mutant_run(result: dict | None, binding: dict, expected_ids: list[str]) -> tuple[str, str, list[str]]:
    """killed / survived / unknown for one mutant run, from the raw supervisor result and its binding (CORE-03). Shared with
    `attest check`, which recomputes every mutant's status from the raw results."""
    if result is None:
        return "unknown", "no trusted supervisor result", []
    problems = structural_problems(binding, result)
    if problems:
        return "unknown", "untrusted execution: " + ", ".join(problems)[:200], []
    classes = outcome_classes(result)
    expected = list(expected_ids)
    untrusted = [i for i in expected if classes.get(i, "untrusted") == "untrusted"]
    if untrusted:
        return "unknown", "untrusted per-test record(s): " + ", ".join(i.split(".")[-1] for i in untrusted)[:200], []
    timed_out = [i for i in expected if classes.get(i) == "timeout"]
    if timed_out:
        return "unknown", "a test timed out under this mutant; a timeout is not counted as a kill: " + ", ".join(i.split(".")[-1] for i in timed_out)[:200], []
    red = [i for i in expected if classes.get(i) == "red"]
    if red:
        return "killed", f"{len(red)} sealed test(s) failed with an authentic child result", red
    return "survived", "every sealed test passed with an authentic child result", []


class Pipeline:
    def __init__(self, task: TaskSpec, provider, executor, ledger: Ledger, out_dir: Path, max_turns: int = 12,
                 max_mutants: int = 12, mutation_threshold: float = 0.5, mutant_workers: int = 8,
                 drift_threshold: float = 0.6, tavily=None, profile_label: str = "development", progress=None,
                 arbitrate: bool = True, arbitration_apply: bool = True, run_id: str | None = None):
        self.task = task
        self.provider = provider
        self.executor = executor
        self.ledger = ledger
        # externally sourced tasks are capped at the pilot's turn budget (recorded in provenance.limits)
        self.max_turns = min(max_turns, EXTERNAL_LIMITS["max_turns"]) if task.upstream else max_turns
        self.max_mutants = max_mutants
        self.mutation_threshold = mutation_threshold
        self.mutant_workers = mutant_workers
        self.drift_threshold = drift_threshold
        self.tavily = tavily
        self.profile_label = profile_label
        self.progress = progress
        self.arbitrate = arbitrate
        self.arbitration_apply = arbitration_apply
        self.checkpoint_uuid: str | None = None
        self.final_changed: dict[str, bytes] = {}
        self.final_deleted: list[str] = []
        self.bound_plan: dict | None = None
        self.raw_results: dict = {}  # raw supervisor results per suite, written to verify_raw.json for `attest check`
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_id = run_id or f"{task.id}-{stamp}"
        self.out_dir = out_dir / self.run_id
        try:
            self.out_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            if run_id:
                raise  # an explicit id must be unique; never write into another run's directory
            # two runs of the same task started within the same second (for example a baseline and an Attest run in a
            # batch): take the next free suffix instead of failing or sharing a directory
            for suffix in range(2, 1000):
                candidate = out_dir / f"{task.id}-{stamp}-{suffix}"
                try:
                    candidate.mkdir(parents=True, exist_ok=False)
                except FileExistsError:
                    continue
                self.run_id, self.out_dir = candidate.name, candidate
                break
            else:
                raise
        (self.out_dir / "sealed").mkdir()
        if getattr(ledger, "sink", None) is None and hasattr(ledger, "attach_sink"):
            ledger.attach_sink(self.out_dir / JOURNAL_FILE)  # reservations and call records survive an interrupted process
        self.started_at = utcnow()
        # full exception texts go to a private sidecar next to the run directories (never inside a bundle); public records carry a
        # fixed-vocabulary sentence plus the correlation reference (R5-04)
        self.diagnostics = Diagnostics(self.run_id, out_dir / SIDECAR_DIR)
        self.ledger.diagnostics = self.diagnostics  # providers route failed-call text through the same private sidecar (R5-04)
        self.bundle: dict = {
            "run_id": self.run_id, "started_at_utc": self.started_at, "finished_at_utc": None,
            "profile": {"label": profile_label, "provider": provider.describe(), "executor": executor.describe()},
            "provenance": None, "task": None, "execution": {}, "spec": None, "grounding": None, "sealed_tests": None, "red_run": None,
            "trajectory": {"turns": 0, "actions": [], "path": "trajectory.jsonl", "finished": False},
            "candidate": {"changed_paths": [], "deleted_paths": [], "scope_ok": None, "violations": [], "diff": "", "sha256": {}},
            "contract_audit": None, "verification": None, "breaker": None, "drift": None, "arbitration": None, "gates": {},
            "verdict": {"verdict": "ERROR", "reasons": [], "warnings": []}, "ledger": None, "limitations": [], "stage": "created",
            # the evidence protocol this bundle follows: `attest check` requires the complete evidence for its verdict (CORE-06)
            "evidence_protocol": {"version": EVIDENCE_PROTOCOL_VERSION, "supervisor": SUPERVISOR_VERSION,
                                  "note": ("a VERIFIED bundle of this protocol carries every gate with its raw supervisor result, every evaluated mutant's raw "
                                           "result, the base and mutant evidence of any validated correction, the contract audit and the ledger; an INFEASIBLE "
                                           "bundle carries the executed witness, its digest, output and operation, its analysis in the constrained witness "
                                           "language and copies of the repository files that analysis resolved call origins through; a bundle without this "
                                           "field is historical and is checked for internal consistency only"),
                                  "witness_language": WITNESS_LANGUAGE}}
        self.bundle["provenance"] = build_provenance(provider.describe(), self.limits(), task.upstream)

    def limits(self) -> dict:
        """Every threshold and limit that shaped this run, recorded in one place (provenance)."""
        return {"max_turns": self.max_turns, "max_mutants": self.max_mutants, "mutation_threshold": self.mutation_threshold,
                "drift_threshold": self.drift_threshold, "mutant_workers": self.mutant_workers, "max_seal_attempts": MAX_SEAL_ATTEMPTS,
                "min_sealed_tests": MIN_SEALED_TESTS, "min_mutants_for_score": MIN_MUTANTS_FOR_SCORE,
                "min_adversarial_when_no_mutants": MIN_ADVERSARIAL_WHEN_NO_MUTANTS, "per_test_timeout_s": min(60, self.task.test_timeout),
                "test_timeout_s": self.task.test_timeout, "checkpoint_timeout_s": self.task.checkpoint_timeout,
                "arbitrate": self.arbitrate, "arbitration_apply": self.arbitration_apply, "max_corrected_tests": MAX_CORRECTED_TESTS,
                "max_mutants_for_discrimination": MAX_MUTANTS_FOR_DISCRIMINATION, "max_breaker_attempts": MAX_BREAKER_ATTEMPTS,
                "max_witnesses": MAX_WITNESSES, "witness_timeout_s": WITNESS_TIMEOUT}

    # ----------------------------------------------------------------- helpers
    def log(self, message: str, stage: str | None = None) -> None:
        if stage:
            self.bundle["stage"] = stage
        print(f"[{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {message}", flush=True)
        if self.progress:
            try:
                self.progress({"at_utc": utcnow(), "stage": self.bundle["stage"], "message": message})
            except Exception:  # noqa: BLE001 - progress sinks must never break a run
                pass

    def save(self, name: str, data) -> None:
        """Write an artifact atomically (temporary file, then rename) so a reader never sees a half-written JSON (API-08)."""
        path = self.out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            payload = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        elif isinstance(data, bytes):
            payload = data
        else:
            payload = str(data).encode("utf-8")
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(payload)
        os.replace(tmp, path)

    def existing_step(self, name: str = "existing") -> dict:
        return {"name": name, "cmd": self.task.test_command, "cwd": GUEST_REPO, "timeout": self.task.test_timeout,
                "env": self.task.guest_env()}

    def suite_steps(self, nonce: str, module: str = "test_sealed", sealed_dir: str = GUEST_SEALED_DIR, prefix: str = "sealed") -> list[dict]:
        return sealed_steps(GUEST_PYTHON, GUEST_REPO, sealed_dir, nonce, self.task.sealed_extra_paths(), self.task.guest_env(),
                            timeout=self.task.test_timeout, module_name=module, per_test_timeout=min(60, self.task.test_timeout),
                            step_prefix=prefix)

    @staticmethod
    def guest_files(files: dict[str, bytes]) -> dict[str, bytes]:
        return {f"{GUEST_REPO}/{rel}": data for rel, data in files.items()}

    def sealed_files(self, guest_dir: str, module_name: str, source: str, canary: bool = True) -> dict[str, bytes]:
        """Guest files for one model-written module run through the supervisor (module, child, canary, job)."""
        return guest_files_for(guest_dir, module_name, source, repo_dir=GUEST_REPO, extra_paths=self.task.sealed_extra_paths(),
                               canary=canary)

    def plan_suite_binding(self, snapshot: dict[str, bytes], baseline: dict) -> dict:
        """Decide how the repository's own suite is verified on the candidate. Bound (through the supervisor, one child
        per test as uid 65534, digests and nonce checked) when the repository uses unittest discovery and static
        discovery of the frozen test modules reproduces exactly the test IDs the baseline run executed. Otherwise the
        suite is stdout-parsed and every record says so (`evidence_class: "stdout"`)."""
        if self.task.test_runner != "unittest":
            return {"mode": "stdout", "reason": f"test runner {self.task.test_runner!r} is parsed from console output; only unittest suites run bound"}
        static = static_repo_tests(snapshot, self.task.test_command)
        if static is None:
            return {"mode": "stdout", "reason": "the test command is not a unittest discovery run"}
        baseline_ids = {t["id"] for t in (baseline.get("tests") or [])}
        static_ids = set(static["ids"])
        if not static_ids or static_ids != baseline_ids:
            return {"mode": "stdout", "static": static,
                    "reason": f"static discovery found {len(static_ids)} test id(s) but the baseline ran {len(baseline_ids)}; "
                              "inherited or dynamically generated tests cannot be bound"}
        return {"mode": "bound", "static": static,
                "reason": f"{len(static_ids)} statically discovered test ids in {len(static['modules'])} module(s) match the baseline run"}

    def _record_plan(self, plan: dict) -> None:
        self.bound_plan = plan
        static = plan.get("static") or {}
        self.bundle["execution"]["suite_binding"] = {
            "mode": plan["mode"], "reason": plan["reason"],
            "modules": [{"name": m["name"], "path": m["rel"], "sha256": m["sha256"], "tests": len(m["ids"])} for m in static.get("modules", [])]}

    def run_repo_suite(self, name: str, checkpoint_uuid: str, changed: dict[str, bytes], deletes: list[str],
                       heldout: dict[str, str] | None = None, include_existing: bool = True) -> dict:
        """Run test modules that live in the repository on the candidate, in a fresh disposable branch AFTER the sealed
        verification: the repository's own suite (`name="existing"`), injected held-out modules (`name="heldout"`), or
        both for the evaluation judge. Bound mode runs them through the supervisor and binds the result to the frozen
        digests and static IDs; stdout mode runs the task's test command and parses its output."""
        task = self.task
        files = self.guest_files(changed)
        plan = self.bound_plan or {"mode": "stdout", "reason": "no suite binding plan (checkpoint did not complete)"}
        mode, note = plan["mode"], plan["reason"]
        modules: list[dict] = []
        if mode == "bound" and include_existing:
            modules = [{"name": m["name"], "path": f"{GUEST_REPO}/{m['rel']}", "sha256": m["sha256"], "ids": m["ids"]}
                       for m in plan["static"]["modules"]]
        if heldout:
            for guest_rel, content in heldout.items():
                files[f"{GUEST_REPO}/{guest_rel}"] = content.encode("utf-8")
                if mode == "bound":
                    module = module_name_for(guest_rel, plan["static"]["top"])
                    try:
                        ids = static_test_ids(content, module) if module else []
                    except SyntaxError:
                        ids = []
                    if not module or not ids:
                        mode, note, modules = "stdout", f"held-out module {guest_rel} is not statically discoverable; parsed from console output", []
                        break
                    modules.append({"name": module, "path": f"{GUEST_REPO}/{guest_rel}", "sha256": sha256_text(content), "ids": ids})
        suite_dir = GUEST_HELDOUT_DIR if heldout else GUEST_SUITE_DIR
        if mode == "bound" and modules:
            nonce = new_nonce()
            files.update(repo_suite_files(suite_dir, modules, GUEST_REPO, task.sealed_extra_paths(), canary=True))
            steps = sealed_steps(GUEST_PYTHON, GUEST_REPO, suite_dir, nonce, env=task.guest_env(), timeout=task.test_timeout,
                                 per_test_timeout=min(60, task.test_timeout), step_prefix=name)
            run = self.executor.run_branch(checkpoint_uuid, files, steps, stage=name, deletes=deletes, timeout=task.test_timeout + 60)
            result, summary = self.suite_outcome(run, nonce, name)
            self.raw_results[name] = result
            binding = bind_modules(result, modules, nonce)
            parsed = {"runner": "unittest", "ran": summary["ran"], "tests": summary["tests"], "passed": summary["passed"],
                      "failing": summary["failing"], "all_passed": bool(summary["all_passed"] and binding["ok"]),
                      "summary_line": summary["summary_line"] + ("" if binding["ok"] else "; binding FAILED: " + "; ".join(binding["reasons"])[:240]),
                      "module_error": bool(summary.get("import_error")), "operation_uuid": run.operation_uuid,
                      "runner_error": run.runner_error, "evidence_class": "bound", "evidence_note": note, "binding": binding,
                      "nonce": nonce, "canary_ok": summary.get("canary_ok"),
                      "modules": [{"name": m["name"], "sha256": m["sha256"], "tests": len(m["ids"]), "ids": m["ids"]} for m in modules]}
        else:
            run = self.executor.run_branch(checkpoint_uuid, files, [self.existing_step(name)], stage=name, deletes=deletes,
                                           timeout=task.test_timeout + 60)
            parsed = self.parsed_step(run, name)
            parsed.update({"evidence_class": "stdout", "evidence_note": note, "binding": None})
        if heldout:
            parsed["files"] = sorted(heldout)
        return parsed

    def parsed_step(self, run, name: str) -> dict:
        step = run.step(name)
        if run.runner_error or step is None:
            return {"runner": self.task.test_runner, "ran": 0, "tests": [], "events": [], "passed": 0, "failing": 0,
                    "failures": 0, "errors": 1, "subtest_events": 0, "module_error": True, "all_passed": False,
                    "summary_line": f"runner error: {self.diagnostics.public_text(name, run.runner_error or 'step missing')}", "operation_uuid": run.operation_uuid,
                    "stderr_tail": _tail(run.raw_stderr_excerpt, 1500)}
        parsed = parse_test_output(self.task.test_runner, step.stdout, step.stderr, step.exit_code)
        parsed.update({"operation_uuid": run.operation_uuid, "exit_code": step.exit_code, "timed_out": step.timed_out,
                       "duration_s": step.duration_s, "stderr_tail": _tail(step.stderr, 2500), "stdout_tail": _tail(step.stdout, 2500)})
        return parsed

    def suite_outcome(self, run, nonce: str, prefix: str = "sealed") -> tuple[dict | None, dict]:
        result = read_sealed_result(run, prefix)
        summary = summarize(result)
        step = run.step(prefix)
        summary.update({"operation_uuid": run.operation_uuid, "nonce": nonce, "supervisor_exit_code": step.exit_code if step else None,
                        "runner_error": run.runner_error})
        return result, summary


    REPAIR_SUFFIX = ("\n\nYOUR PREVIOUS ANSWER WAS NOT A VALID JSON OBJECT FOR THE REQUIRED SCHEMA ({problem}). "
                     "Answer again with exactly one JSON object that matches the schema, with every required field, and nothing else.")

    def ask(self, role: str, prompt: str, schema: dict, stage: str):
        """Structured call with one repair retry on a malformed answer; transport-uncertain failures are never retried."""
        try:
            return self.provider.structured(role, prompt, schema, stage)
        except ModelError as error:
            if error.uncertain or "schema" not in str(error):
                raise
            self.log(f"{stage}: malformed answer, one repair retry ({self.diagnostics.public_text(stage, error)})")
            return self.provider.structured(role, prompt + self.REPAIR_SUFFIX.format(problem=self.diagnostics.public_text(f"{stage}-schema", error)), schema, f"{stage}-repair")

    # ----------------------------------------------------------------- lifecycle
    def run(self) -> dict:
        try:
            self._run()
        except PipelineAbort as abort:
            self.log(f"ABORT {abort.verdict}: {abort.reason}", "aborted")
            self.bundle["verdict"] = {"verdict": abort.verdict, "reasons": [abort.reason], "warnings": self.bundle["verdict"].get("warnings", [])}
        except ModelError as error:
            public = self.diagnostics.public_text(self.bundle.get("stage") or "run", error)
            self.log(f"MODEL ERROR: {public}", "error")
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [f"model provider: {public}" + (" (outcome uncertain; not retried)" if error.uncertain else "")],
                                      "warnings": []}
        except Exception as error:  # noqa: BLE001 - keep the evidence, then re-raise
            public = self.diagnostics.public_text(self.bundle.get("stage") or "run", error)
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [public], "warnings": []}
            self.finish()
            raise
        return self.finish()

    def run_baseline(self) -> dict:
        """Plain-agent baseline: the same implementation loop (model, tools, turn budget) with NONE of Attest's
        verification, sealing, breaker, drift or arbitration. It just implements and stops. Used only by the
        controlled evaluation so a plain agent and Attest share identical implementation capability and budget."""
        try:
            task = self.task
            snapshot = snapshot_repo(task.repo_dir, task.max_file_bytes)
            self.enforce_bounds(snapshot)
            self.bundle["task"] = task.frozen(snapshot)
            self.bundle["profile"]["label"] = self.profile_label
            self.log(f"baseline: frozen task {task.id} with {len(snapshot)} files", "freeze")
            checkpoint_uuid = self._checkpoint(snapshot)
            spec = {"feasible": True, "infeasibility_reason": None, "restated_task": task.statement,
                    "interface_contract": [], "acceptance_criteria": task.acceptance_criteria, "out_of_scope": [],
                    "external_references_needed": []}
            self.bundle["spec"] = spec
            workspace, finished, finish_summary, _ = self._implement_loop(spec, snapshot, checkpoint_uuid, "")
            changed, deleted = workspace.changed(), workspace.deleted()
            diff = workspace.unified_diff()
            self.save("candidate.patch", diff)
            self.final_changed, self.final_deleted = changed, deleted
            scope = workspace.scope_report()
            self.bundle["candidate"] = {"changed_paths": sorted(changed), "deleted_paths": deleted, "scope_ok": scope["ok"],
                                        "violations": scope["violations"], "diff": diff, "sha256": scope["sha256"],
                                        "implementer_finished": finished}
            self.bundle["verdict"] = {"verdict": "BASELINE", "reasons": [] if finished else ["implementer did not finish"],
                                      "warnings": [], "finished": finished, "summary": finish_summary}
        except PipelineAbort as abort:
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [abort.reason], "warnings": []}
        except ModelError as error:
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [f"model provider: {self.diagnostics.public_text(self.bundle.get('stage') or 'baseline', error)}"],
                                      "warnings": []}
        return self.finish()

    def _checkpoint(self, snapshot: dict[str, bytes]) -> str:
        """Create the retained checkpoint (optional pinned install) and assert the existing suite passes on base."""
        task = self.task
        base_image = self.executor.resolve_image(task.base_image)
        self.bundle["execution"]["base_image_uuid"] = base_image
        steps = []
        if task.install_command:
            steps.append({"name": "install", "cmd": task.install_command, "cwd": GUEST_REPO,
                          "timeout": max(60, task.checkpoint_timeout - 60), "env": task.guest_env(), "stop_on_failure": True})
        steps.append(self.existing_step())
        self.log(f"creating checkpoint from {task.base_image} ({base_image}); networking={'on' if task.checkpoint_networking else 'off'}", "checkpoint")
        checkpoint = self.executor.create_checkpoint(base_image, self.guest_files(snapshot), steps, stage="checkpoint",
                                                     timeout=task.checkpoint_timeout, networking=task.checkpoint_networking)
        install = checkpoint.step("install")
        baseline = self.parsed_step(checkpoint, "existing")
        self.bundle["execution"].update({"checkpoint_operation_uuid": checkpoint.operation_uuid,
                                         "checkpoint_image_uuid": checkpoint.result_image_uuid, "baseline": baseline})
        if not checkpoint.ok or not checkpoint.result_image_uuid:
            raise PipelineAbort("ERROR", f"checkpoint failed: {self.diagnostics.public_text('checkpoint', checkpoint.runner_error or str(checkpoint.status))}")
        if install and not install.ok:
            raise PipelineAbort("ERROR", f"dependency install failed (exit {install.exit_code})")
        if not baseline["all_passed"]:
            raise PipelineAbort("NEEDS HUMAN", f"existing tests do not pass on the unmodified repository: {baseline['summary_line']}")
        self.checkpoint_uuid = checkpoint.result_image_uuid
        self._record_plan(self.plan_suite_binding(snapshot, baseline))
        return checkpoint.result_image_uuid

    def judge_heldout(self, heldout_src: str) -> dict:
        """Independent ground-truth judge used by the evaluation: run the existing suite plus the held-out suite on the
        final candidate in a fresh branch from the checkpoint. 'correct' means both pass. Reuses the checkpoint."""
        if not self.checkpoint_uuid:
            return {"error": "no checkpoint to judge against", "correct": False}
        guest_rel = "tests/test_heldout_eval.py"
        deletes = [f"{GUEST_REPO}/{rel}" for rel in self.final_deleted]
        parsed = self.run_repo_suite("judge", self.checkpoint_uuid, self.final_changed, deletes,
                                     heldout={guest_rel: heldout_src}, include_existing=True)
        return {"operation_uuid": parsed.get("operation_uuid"), "summary_line": parsed["summary_line"], "ran": parsed["ran"],
                "passed": parsed["passed"], "failing": parsed["failing"], "correct": parsed["all_passed"],
                "runner_error": parsed.get("runner_error"), "evidence_class": parsed.get("evidence_class"),
                "heldout_sha256": sha256_text(heldout_src)}

    def finish(self) -> dict:
        self.bundle["finished_at_utc"] = utcnow()
        self.bundle["ledger"] = self.ledger.to_dict()
        self.bundle["limitations"] = self.limitations()
        self.save("ledger.json", self.bundle["ledger"])
        self.save("verify_raw.json", {"note": "raw supervisor results (per-test records, nonce, canaries, start-up hooks, digests) for every suite "
                                              "that ran under the supervisor; `attest check` recomputes the binding from them",
                                      "supervisor": SUPERVISOR_VERSION, **self.raw_results})
        write_bundle(self.out_dir, self.bundle)
        if hasattr(self.ledger, "detach_sink"):
            self.ledger.detach_sink()  # the journal is complete for this run; the manifest fixes its digest next
        self.write_manifest()
        self.log(f"verdict {self.bundle['verdict']['verdict']} -> {self.out_dir}", "finished")
        return self.bundle

    def write_manifest(self) -> dict:
        """Written last: sha256 and size of every artifact in the run directory except the manifest itself."""
        manifest = build_manifest(self.out_dir, self.run_id)
        self.save(MANIFEST_FILE, manifest)
        return manifest

    def limitations(self) -> list[str]:
        return [
            f"Profile '{self.profile_label}': inference provider {self.provider.name}; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.",
            "Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).",
            "The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.",
            "Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each "
            "failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The "
            "correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the "
            "candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its "
            "nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by "
            "an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The "
            "classification itself remains a model judgement.",
            "A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; "
            "lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` "
            "recomputes the classification from the raw results.",
            "INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on "
            "the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.",
            "Grounding runs only when the specification names external references; sources are cited, not verified for correctness.",
            "Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.",
            "Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.",
            "Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.",
            "manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial "
            "bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.",
        ]

    def _implement_loop(self, spec, snapshot, checkpoint_uuid, sources):
        """The implementation loop shared by Attest and the plain-agent baseline: identical model role, tools, turn
        budget, syntax checks, undo and test-before-finish discipline. Returns (workspace, finished, summary, transcript)."""
        task = self.task
        workspace = Workspace(snapshot, task.allowed_write_globs, task.protected_globs)
        transcript: list[dict] = []
        trajectory = self.out_dir / "trajectory.jsonl"
        finished = False
        finish_summary = None
        edited_since_test = False
        finish_nudged = False
        self.log("implementation", "implement")
        for turn in range(1, self.max_turns + 1):
            action = self.ask("implement", implement_prompt(task, spec, workspace, transcript, turn, self.max_turns, sources),
                              ACTION_SCHEMA, f"implement-{turn}").json
            # Mandatory check before finishing: untested edits are sent back once with a reminder (never loops).
            if action["action"] == "finish" and edited_since_test and not finish_nudged and turn < self.max_turns:
                finish_nudged = True
                observation = ("Before finishing, run the existing test suite once: you have edits that have not been tested "
                               "since your last change. Use run_tests now, then finish.")
            else:
                observation = self.execute_action(action, workspace, checkpoint_uuid, turn)
                if action["action"] in ("write_file", "replace_in_file", "undo"):
                    edited_since_test = True
                elif action["action"] == "run_tests":
                    edited_since_test = False
            shown = dict(action)
            if shown.get("content") and len(shown["content"]) > 300:
                shown["content"] = shown["content"][:300] + f"...[{len(action['content'])} chars written]"
            transcript.append({"turn": turn, "action": shown, "observation": observation})
            with trajectory.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"turn": turn, "action": action, "observation": observation, "at_utc": utcnow()}, ensure_ascii=False) + "\n")
            self.bundle["trajectory"]["actions"].append({"turn": turn, "action": action["action"], "path": action.get("path"),
                                                         "reason": action.get("reason"), "observation_head": observation[:160]})
            self.log(f"turn {turn}: {action['action']} {action.get('path') or ''} -> {observation.splitlines()[0][:100] if observation else ''}")
            if action["action"] == "finish" and observation.startswith("finished:"):
                finished = True
                finish_summary = action.get("summary")
                break
        self.bundle["trajectory"]["turns"] = len(transcript)
        self.bundle["trajectory"]["finished"] = finished
        return workspace, finished, finish_summary, transcript

    def enforce_bounds(self, snapshot: dict[str, bytes]) -> None:
        """Refuse, before any sandbox operation, a repository or an external task outside the documented limits."""
        problems = repository_problems(snapshot, self.task.max_file_bytes)
        if self.task.upstream:
            problems += external_policy_problems(self.task)
        if problems:
            raise PipelineAbort("ERROR", "refused before any sandbox operation: " + "; ".join(problems))

    def _run(self) -> None:
        task = self.task
        snapshot = snapshot_repo(task.repo_dir, task.max_file_bytes)
        self.enforce_bounds(snapshot)
        frozen = task.frozen(snapshot)
        self.bundle["task"] = frozen
        self.save("task.frozen.json", frozen)
        self.log(f"frozen task {task.id} with {len(snapshot)} files, spec sha256 {frozen['spec_sha256'][:12]}", "freeze")

        # Stage 1: checkpoint (optional pinned install with networking), baseline existing tests.
        base_image = self.executor.resolve_image(task.base_image)
        self.bundle["execution"]["base_image_uuid"] = base_image
        steps = []
        if task.install_command:
            steps.append({"name": "install", "cmd": task.install_command, "cwd": GUEST_REPO,
                          "timeout": max(60, task.checkpoint_timeout - 60), "env": task.guest_env(), "stop_on_failure": True})
        steps.append(self.existing_step())
        self.log(f"creating checkpoint from {task.base_image} ({base_image}); networking={'on' if task.checkpoint_networking else 'off'}", "checkpoint")
        checkpoint = self.executor.create_checkpoint(base_image, self.guest_files(snapshot), steps, stage="checkpoint",
                                                     timeout=task.checkpoint_timeout, networking=task.checkpoint_networking)
        install = checkpoint.step("install")
        self.bundle["execution"]["install"] = ({"exit_code": install.exit_code, "duration_s": install.duration_s,
                                                "stdout_tail": _tail(install.stdout, 1500), "stderr_tail": _tail(install.stderr, 1500)}
                                               if install else None)
        baseline = self.parsed_step(checkpoint, "existing")
        self.bundle["execution"].update({"checkpoint_operation_uuid": checkpoint.operation_uuid,
                                         "checkpoint_image_uuid": checkpoint.result_image_uuid,
                                         "checkpoint_chain": list(getattr(checkpoint, "chain", []) or []),  # earlier file-only operations of a chunked checkpoint
                                         "checkpoint_networking": task.checkpoint_networking, "baseline": baseline})
        self.save("baseline.json", baseline)
        if not checkpoint.ok or not checkpoint.result_image_uuid:
            raise PipelineAbort("ERROR", f"checkpoint failed: {self.diagnostics.public_text('checkpoint', checkpoint.runner_error or str(checkpoint.status))}")
        if install and not install.ok:
            raise PipelineAbort("ERROR", f"dependency install failed (exit {install.exit_code}): {_tail(install.stderr, 400)}")
        if not baseline["all_passed"]:
            raise PipelineAbort("NEEDS HUMAN", f"existing tests do not pass on the unmodified repository: {baseline['summary_line']}")
        self.log(f"checkpoint {checkpoint.result_image_uuid} ready; baseline {baseline['summary_line']} ({baseline['ran']} tests)")
        checkpoint_uuid = checkpoint.result_image_uuid
        self.checkpoint_uuid = checkpoint_uuid
        self._record_plan(self.plan_suite_binding(snapshot, baseline))
        self.log(f"suite binding: {self.bound_plan['mode']} ({self.bound_plan['reason']})")

        # Stage 2: specification and interface contract.
        self.log("specification", "spec")
        spec = self.ask("spec", spec_prompt(task, snapshot), SPEC_SCHEMA, "spec").json
        self.bundle["spec"] = spec
        self.save("spec.json", spec)
        self.log(f"spec: feasible={spec['feasible']}, {len(spec['acceptance_criteria'])} criteria, {len(spec['interface_contract'])} contract entries, "
                 f"{len(spec.get('external_references_needed') or [])} external references")
        # Stage 2a: contract audit. Conflicting requirements must be DEMONSTRATED by a witness program executed on the unmodified
        # repository before the run may end INFEASIBLE; a bare claim (the specification's or the auditor's) is a suspicion that
        # is recorded, handed to the sealer and, when the specification itself claimed infeasibility, held for a human.
        self.log("contract audit", "contract")
        audit = self.contract_audit(spec, snapshot, checkpoint_uuid)
        self.bundle["contract_audit"] = audit
        self.save("contract_audit.json", audit)
        grounded = [c for c in audit.get("conflicts") or [] if c.get("grounded")]
        demonstrated = [c for c in audit.get("conflicts") or [] if c.get("demonstrated") and not c.get("grounded")]
        claimed = [c for c in audit.get("conflicts") or [] if not c.get("demonstrated")]
        self.log(f"contract audit: {audit.get('outcome')} ({len(grounded)} grounded, {len(demonstrated)} demonstrated but not grounded, {len(claimed)} claimed only)")
        if grounded:
            first = grounded[0]
            raise PipelineAbort("INFEASIBLE", f"contract contradiction demonstrated by an executed witness in {WITNESS_LANGUAGE} on the task's own criteria "
                                              f"(requirements {', '.join(first['requirement_ids'])}): {first['summary'][:200]}; witness output: "
                                              f"{(first.get('stdout_tail') or '').strip()[:200]}")
        if demonstrated:
            # a demonstrated conflict that rests on the specification model's restatement, or on an unconstrained witness, is not a
            # proof that the requester's task is impossible (R5-03): it is held for a human with the evidence recorded
            first = demonstrated[0]
            raise PipelineAbort("NEEDS HUMAN", f"contract conflict demonstrated but not grounded ({first.get('provenance')} criteria "
                                               f"{', '.join(first['requirement_ids'])}"
                                               + ("" if first.get("witness_constrained") else f"; witness outside {WITNESS_LANGUAGE}") + f"): {first['summary'][:200]}; "
                                               "a model's restatement of the task cannot establish that the task is impossible, so a human decides whether "
                                               "the requirement conflict is real")
        if not spec["feasible"]:
            raise PipelineAbort("NEEDS HUMAN", f"the specification stage judged the task infeasible ({(spec.get('infeasibility_reason') or '')[:200]}) "
                                               "but no executed witness demonstrated a contradiction; a human decides whether the task is feasible")
        audit_hint = ""
        if claimed:
            audit_hint = ("AUDITOR'S SUSPICION (claimed, NOT demonstrated by its witness): " + " | ".join(
                f"requirements {', '.join(c['requirement_ids'])}: {c['summary'][:200]}" for c in claimed)
                + ". Write at least one sealed test that exercises exactly this interaction so the candidate is judged on it.")

        # Stage 2b: grounding of external references (Tavily), only when the specification asks for it.
        queries = list(spec.get("external_references_needed") or []) + list(task.extra.get("grounding_queries") or [])
        grounding = ground(queries, self.tavily)
        self.bundle["grounding"] = grounding
        self.save("grounding.json", grounding)
        sources = sources_text(grounding)
        if grounding["calls"]:
            self.log(f"grounding: {grounding['calls']} Tavily calls, {len(grounding['sources'])} sources", "ground")

        # Stages 3 and 4: seal acceptance tests, prove them red through the supervisor.
        feedback = None
        rejected: list[dict] = []
        sealed_src = sealed_sha = None
        expected_ids: list[str] = []
        red_summary = None
        for attempt in range(1, MAX_SEAL_ATTEMPTS + 1):
            self.log(f"sealing acceptance tests (attempt {attempt})", "seal")
            try:
                result = self.ask("seal", seal_prompt(task, spec, snapshot, feedback, sources, audit_hint), SEAL_SCHEMA, f"seal-{attempt}")
            except ModelError as error:
                if not error.uncertain:
                    raise
                feedback = None
                public = self.diagnostics.public_text(f"seal-{attempt}", error)
                rejected.append({"attempt": attempt, "reason": f"inference outcome uncertain: {public}"})
                self.log(f"seal attempt {attempt} not usable: {public}")
                continue
            candidate_src, repaired = repair_escapes(result.json["test_file"])
            if repaired:
                self.log(f"seal attempt {attempt}: repaired literal escape sequences in the returned module")
            self.save(f"sealed/test_sealed.attempt{attempt}.py", candidate_src)
            try:
                compile(candidate_src, SEALED_FILE, "exec")
                host_ids = static_test_ids(candidate_src)
            except SyntaxError as error:
                feedback = f"the module has a syntax error: {error}"
                rejected.append({"attempt": attempt, "reason": feedback})
                self.log(f"seal attempt {attempt} rejected: {feedback}")
                continue
            nonce = new_nonce()
            red_run = self.executor.run_branch(checkpoint_uuid, self.sealed_files(GUEST_SEALED_DIR, "test_sealed", candidate_src),
                                               self.suite_steps(nonce), stage=f"red-{attempt}", timeout=task.test_timeout + 60)
            red_result, summary = self.suite_outcome(red_run, nonce)
            self.save(f"red.attempt{attempt}.json", {"summary": summary, "result": red_result})
            sha = sha256_text(candidate_src)
            missing = [t["id"] for t in summary["tests"] if t["outcome"] in ("MISSING_RESULT", "FORGED", "TIMEOUT", "CRASH")]
            if red_result is None:
                feedback = "the supervisor produced no result for the sealed module (parse failure or crash); make the module import cleanly"
            elif red_result.get("nonce") != nonce or red_result.get("sealed_sha256_before") != sha:
                feedback = "sealed result binding failed on the red check (nonce or digest mismatch)"
            elif red_result.get("discovery_error"):
                feedback = f"the module could not be parsed statically: {red_result['discovery_error']}"
            elif set(red_result.get("expected_ids") or []) != set(host_ids):
                feedback = "static test discovery differs between host and guest; use plain unittest.TestCase classes with test_ methods"
            elif summary["ran"] < MIN_SEALED_TESTS:
                feedback = f"only {summary['ran']} test methods were discovered; at least {MIN_SEALED_TESTS} are required"
            elif missing:
                feedback = f"{len(missing)} tests crashed, timed out or produced no result on the unmodified code; tests must fail with assertions or exceptions, not by killing the process: {', '.join(missing)[:200]}"
            elif summary["failing"] == 0:
                feedback = "every test passed on the unmodified code; the suite must fail for behavior that is not implemented yet"
            elif (defective := test_internal_errors(summary["tests"])) and attempt < MAX_SEAL_ATTEMPTS:
                feedback = ("these tests crashed inside the test module itself on the unmodified code (" + "; ".join(defective)[:400]
                            + "); a red test must fail by asserting on the API's behaviour, not by an error in the test body. Fix them.")
            elif (gaps := coverage_gaps(result.json.get("coverage"), spec["acceptance_criteria"], host_ids)) and attempt < MAX_SEAL_ATTEMPTS:
                feedback = ("your coverage map leaves acceptance criteria without any existing test method: " + ", ".join(gaps)[:300]
                            + "; add tests for them and map every criterion to real test method names")
            else:
                sealed_src, sealed_sha, red_summary = candidate_src, sha, summary
                self.raw_results["red"] = red_result
                expected_ids = list(red_result["expected_ids"])
                gaps = coverage_gaps(result.json.get("coverage"), spec["acceptance_criteria"], host_ids)
                self.bundle["sealed_tests"] = {"path": f"sealed/{SEALED_FILE}", "sha256": sha, "test_count": summary["ran"],
                                               "declared_test_count": result.json["test_count"], "expected_ids": expected_ids, "escapes_repaired": repaired,
                                               "sealed_at_utc": utcnow(), "author_model": result.call.requested_model,
                                               "attempts": attempt, "rejected_attempts": rejected, "notes": result.json["notes"],
                                               "coverage": result.json.get("coverage"), "coverage_gaps": gaps,
                                               "coverage_note": "the map is the sealer's own claim of which test checks which criterion; gaps are criteria no test claims"}
                if gaps:
                    self.log(f"sealed suite accepted with coverage gaps (criteria without a claimed test): {', '.join(gaps)[:200]}")
                self.save(f"sealed/{SEALED_FILE}", candidate_src)
                self.log(f"sealed {summary['ran']} test methods (sha256 {sha[:12]}); red check: {summary['failing']} of {summary['ran']} failing on base, "
                         f"{summary['passed']} passing", "red")
                break
            rejected.append({"attempt": attempt, "reason": feedback, "operation_uuid": red_run.operation_uuid})
            self.log(f"seal attempt {attempt} rejected: {feedback[:160]}")
        if sealed_src is None:
            self.bundle["sealed_tests"] = {"path": None, "sha256": None, "test_count": 0, "expected_ids": [], "sealed_at_utc": None,
                                           "author_model": None, "attempts": MAX_SEAL_ATTEMPTS, "rejected_attempts": rejected, "notes": ""}
            raise PipelineAbort("NEEDS HUMAN", "could not seal a valid acceptance-test suite: " + "; ".join(r["reason"][:120] for r in rejected))
        self.bundle["red_run"] = red_summary

        # Stage 5: implementation through validated JSON actions.
        workspace, finished, finish_summary, transcript = self._implement_loop(spec, snapshot, checkpoint_uuid, sources)

        # Stage 6: candidate patch and scope policy.
        changed, deleted = workspace.changed(), workspace.deleted()
        scope = workspace.scope_report()
        diff = workspace.unified_diff()
        self.save("candidate.patch", diff)
        self.final_changed, self.final_deleted = changed, deleted
        self.bundle["candidate"] = {"changed_paths": sorted(changed), "deleted_paths": deleted, "scope_ok": scope["ok"],
                                    "violations": scope["violations"], "diff": diff, "sha256": scope["sha256"],
                                    "implementer_finished": finished}
        if not changed and not deleted:
            self.bundle["candidate"]["unfinished"] = not finished
            raise PipelineAbort("NO CHANGE", "the implementer finished without changing any file" if finished else
                                f"unfinished: the turn budget ({self.max_turns} turns) was exhausted without a patch; the implementer neither finished nor changed a file")
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        gates: dict[str, dict] = {}
        warnings: list[str] = []

        # Stage 6b: static tamper scan of the added lines (warnings, never a gate).
        tamper = scan_diff(diff)
        self.bundle["candidate"]["tamper_scan"] = tamper
        self.save("tamper_scan.json", tamper)
        if tamper["flagged"]:
            warnings.append(f"static tamper scan: {tamper['summary']}; review the patch before trusting self-reported results")
            self.log(f"tamper scan: {tamper['summary']}")

        # Stage 7: fresh-branch verification bound to the sealed suite. ORDER RULE: the sealed supervisor is the only
        # step of its branch, so nothing that imports candidate code runs ahead of it in the same operation.
        self.log("verification", "verify")
        verification = self.verify_candidate(changed, deletes, sealed_src, sealed_sha, expected_ids, checkpoint_uuid)
        verify_run, sealed_result, sealed_summary, binding = (verification["run"], verification["result"], verification["summary"], verification["binding"])
        self.raw_results["sealed"] = sealed_result
        self.log(f"verify: sealed {sealed_summary['summary_line']}; binding {'ok' if binding['ok'] else 'FAILED: ' + '; '.join(binding['reasons'])[:200]}")

        # Stage 7a: the repository's own suite on the candidate, in its own disposable branch after the supervisor.
        existing = self.run_repo_suite("existing", checkpoint_uuid, changed, deletes)
        self.log(f"existing suite ({existing['evidence_class']}): {existing['summary_line']} ({existing['passed']}/{existing['ran']})")
        self.bundle["verification"] = {"operation_uuid": verify_run.operation_uuid, "status": verify_run.status,
                                       "order": list(VERIFICATION_ORDER), "sealed_sha256_injected": sealed_sha,
                                       "expected_ids": expected_ids, "existing": existing, "sealed": sealed_summary,
                                       "binding": binding, "heldout": None, "corrected": None}

        # Gates and the reasons that explain them are built side by side; `blame` keeps every reason attached to the gate
        # it came from, so a gate re-run on a validated correction can retire exactly its own reasons.
        # `gates` and `warnings` were created before the tamper scan (stage 6b) and already hold its warning
        blame: dict[str, list[str]] = {}
        general: list[str] = []
        if not finished:
            general.append(f"implementer did not finish within {self.max_turns} turns")
        if not scope["ok"]:
            general.append("scope policy violated: " + "; ".join(scope["violations"]))
        if verify_run.runner_error:
            general.append(f"verification run failed: {verify_run.runner_error}")
        gates["existing_suite"] = {"ok": existing["all_passed"], "detail": existing["summary_line"], "evidence_class": existing["evidence_class"]}
        if not existing["all_passed"]:
            blame["existing_suite"] = [f"existing test suite failed on the candidate: {existing['summary_line']}"]
        gates["sealed_binding"] = {"ok": binding["ok"], "detail": "; ".join(binding["reasons"]) or "all checks pass", "evidence_class": "bound"}
        blame["sealed_binding"] = list(binding["reasons"])
        if existing["evidence_class"] == "stdout":
            warnings.append(f"existing suite evidence is parsed console output ({existing['evidence_note']}); the sealed, mutation and adversarial gates are bound")

        # Stage 7b: held-out tests (for example the upstream PR's own tests), separate branch, GATE when configured.
        if task.heldout_tests:
            try:
                heldout = self.run_repo_suite("heldout", checkpoint_uuid, changed, deletes, heldout=task.heldout_tests, include_existing=False)
            except Exception as error:  # noqa: BLE001 - uncertain spawn: gate fails with the reason, no replay
                heldout = {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False, "module_error": True,
                           "summary_line": f"held-out branch could not be executed: {self.diagnostics.public_text('heldout', error)}",
                           "operation_uuid": None, "evidence_class": (self.bound_plan or {}).get("mode", "stdout"),
                           "evidence_note": "branch did not run", "files": sorted(task.heldout_tests)}
            self.bundle["verification"]["heldout"] = heldout
            failing_ids = [t["id"] for t in heldout["tests"] if t["outcome"] != "ok"]
            gates["heldout_suite"] = {"ok": heldout["all_passed"], "detail": heldout["summary_line"], "failing": failing_ids,
                                      "evidence_class": heldout["evidence_class"]}
            if not heldout["all_passed"]:
                blame["heldout_suite"] = [f"held-out tests failed: {heldout['failing']} of {heldout['ran']} ({', '.join(failing_ids)[:300]}); "
                                          "resolve the failures or the contract disagreement before this patch can be verified"]
            self.log(f"held-out suite ({heldout['evidence_class']}): {heldout['summary_line']} ({heldout['passed']}/{heldout['ran']})", "heldout")
        self.save("verify.json", self.bundle["verification"])

        # Stage 8: breaker pass (mutants + model-written adversarial tests) only when the sealed suite passed.
        if binding["ok"] and existing["all_passed"]:
            self.log("breaker pass", "break")
            breaker = self.breaker_pass(snapshot, changed, deleted, sealed_src, sealed_sha, checkpoint_uuid, spec, diff, expected_ids, sources)
            self.bundle["breaker"] = breaker
            self.save("breaker.json", breaker)
            self.breaker_gates(breaker, gates, blame, warnings)
        else:
            gates["mutation"] = {"ok": False, "detail": "not run: verification did not pass", "skipped": True, "evidence_class": "bound"}
            gates["adversarial_tests"] = {"ok": False, "detail": "not run: verification did not pass", "skipped": True, "evidence_class": "bound"}

        # Stage 9: drift audit over the whole action trail and the diff.
        self.log("drift audit", "audit")
        try:
            drift = self.ask("audit", drift_prompt(task, spec, diff, self.bundle["trajectory"]["actions"], finish_summary),
                             DRIFT_SCHEMA, "drift-audit").json
            score = float(drift.get("drift_score") or 0.0)
            drift["threshold"] = self.drift_threshold
            self.bundle["drift"] = drift
            self.save("drift.json", drift)
            if score >= self.drift_threshold:
                blame["drift_audit"] = [f"drift audit score {score:.2f} ({drift.get('assessment')}): {drift.get('summary', '')[:200]}"]
                gates["drift_audit"] = {"ok": False, "detail": f"score {score}", "evidence_class": "model"}
            else:
                gates["drift_audit"] = {"ok": True, "detail": f"score {score} ({drift.get('assessment')})", "evidence_class": "model"}
                if score >= 0.3 or drift.get("scope_widened") or drift.get("unsupported_claims"):
                    warnings.append(f"drift audit: score {score:.2f}, widened {len(drift.get('scope_widened') or [])}, unsupported claims {len(drift.get('unsupported_claims') or [])}")
            self.log(f"drift audit: score {score} ({drift.get('assessment')})")
        except ModelError as error:
            public = self.diagnostics.public_text("drift-audit", error)
            self.bundle["drift"] = {"error": public}
            gates["drift_audit"] = {"ok": False, "detail": f"audit call failed: {public}", "evidence_class": "model"}
            blame["drift_audit"] = [f"drift audit unavailable: {public}"]

        def decide() -> tuple[str, list[str], dict]:
            """The recorded reasons (general first, then per gate in the fixed gate order) and the pure derivation; the two
            are built independently and must agree, otherwise the run fails closed."""
            ordered = list(general)
            for name in ("existing_suite", "sealed_binding", "heldout_suite", "mutation", "adversarial_tests", "drift_audit"):
                ordered.extend(blame.get(name) or [])
            for name in blame:
                if name not in ("existing_suite", "sealed_binding", "heldout_suite", "mutation", "adversarial_tests", "drift_audit"):
                    ordered.extend(blame[name])
            verdict = "VERIFIED" if not ordered else "NEEDS HUMAN"
            derivation = derive(gates, self.bundle["candidate"], gates["sealed_binding"]["ok"])
            if derivation["verdict"] != verdict:
                ordered.append(f"verdict derivation inconsistent: the gates derive {derivation['verdict']} but the recorded reasons give {verdict}; failing closed")
                verdict = "NEEDS HUMAN"
            return verdict, ordered, derivation

        self.bundle["gates"] = gates
        verdict, reasons, derivation = decide()
        original = {"verdict": verdict, "reasons": list(reasons), "gates": json.loads(json.dumps(gates))}

        # Stage 10: arbitration of model-generated test failures. The arbiter classifies each failing sealed or adversarial
        # test (implementation bug, test defect, contract dispute) and offers a corrected module for pure test defects. A
        # correction counts only after mechanical validation (same test set, only the failing tests changed, passes on the
        # candidate, still discriminates on the base or a mutant); a validated correction RE-RUNS the affected gate, and the
        # verdict is derived again from the gates. A sealed test that failed by assertion is never overridden: the arbiter's
        # view is recorded for the human, the hold stands. Original tests, results and reasons are preserved in the bundle.
        if verdict == "NEEDS HUMAN" and self.arbitrate:
            arb = self.arbitrate_failures(spec, diff, sealed_src, sealed_sha, expected_ids, checkpoint_uuid,
                                          changed, deleted, gates, binding, sealed_summary, finished, scope["ok"])
            if arb:
                applied: list[dict] = []
                if self.arbitration_apply:
                    for module in arb["modules"]:
                        if not module.get("validated"):
                            continue
                        corrected = module["corrected"]
                        if module["module"] == "adversarial":
                            adversarial = self.bundle["breaker"]["adversarial"]
                            adversarial["corrected"] = corrected
                            gates["adversarial_tests"] = {
                                "ok": True, "evidence_class": "bound", "corrected": True,
                                "detail": (f"{corrected['summary']['summary_line']} on the corrected module ({len(corrected['changed_tests'])} test(s) corrected, "
                                           f"validated: {corrected['discrimination']}); original failures kept in E3"),
                                "original_failing": list((gates.get("adversarial_tests") or {}).get("failing") or []),
                                "original_detail": (gates.get("adversarial_tests") or {}).get("detail")}
                            blame["adversarial_tests"] = []
                            applied.append({"gate": "adversarial_tests", "module": "adversarial", "corrected_sha256": corrected["sha256"],
                                            "changed_tests": corrected["changed_tests"], "discrimination": corrected["discrimination"]})
                            self.save("breaker.json", self.bundle["breaker"])
                            self.log(f"arbitration: adversarial gate re-run on the validated correction: {corrected['summary']['summary_line']}", "arbitrate")
                        elif module["module"] == "sealed":
                            # the candidate re-run of the corrected sealed suite IS the re-verification (supervisor, nonce, digest,
                            # canaries); the breaker then runs against the corrected suite, since it was skipped before
                            self.bundle["verification"]["corrected"] = corrected
                            self.bundle["verification"]["heldout_note"] = "held-out and existing suites were not re-run: they do not depend on the sealed module"
                            gates["sealed_binding"] = {
                                "ok": True, "evidence_class": "bound", "corrected": True,
                                "detail": (f"{corrected['summary']['summary_line']} on the corrected sealed module ({len(corrected['changed_tests'])} test(s) corrected, "
                                           f"validated: {corrected['discrimination']}); the original failure is kept in E1"),
                                "original_detail": (gates.get("sealed_binding") or {}).get("detail")}
                            blame["sealed_binding"] = []
                            applied.append({"gate": "sealed_binding", "module": "sealed", "corrected_sha256": corrected["sha256"],
                                            "changed_tests": corrected["changed_tests"], "discrimination": corrected["discrimination"]})
                            self.save("verify.json", self.bundle["verification"])
                            if existing["all_passed"]:
                                corrected_src = (self.out_dir / corrected["path"]).read_text(encoding="utf-8")
                                self.log("breaker pass on the corrected sealed suite", "break")
                                breaker = self.breaker_pass(snapshot, changed, deleted, corrected_src, corrected["sha256"], checkpoint_uuid, spec, diff,
                                                            corrected["expected_ids"], sources)
                                breaker["after_sealed_correction"] = True
                                self.bundle["breaker"] = breaker
                                self.save("breaker.json", breaker)
                                for name in ("mutation", "adversarial_tests"):
                                    gates.pop(name, None)
                                    blame.pop(name, None)
                                self.breaker_gates(breaker, gates, blame, warnings)
                                applied[-1]["breaker_rerun"] = True
                                self.log(f"arbitration: sealed gate re-run on the validated correction; mutation {gates['mutation'].get('detail')}; "
                                         f"adversarial {gates['adversarial_tests'].get('detail')}", "arbitrate")
                arb["applied_to_gates"] = applied
                self.bundle["arbitration"] = arb
                self.save("arbitration.json", arb)
                warnings.append(f"arbitration ({'validated corrections re-run their gates' if self.arbitration_apply else 'advisory'}): {arb['headline']}")
                self.log(f"arbitration: {arb['headline']}", "arbitrate")
                if applied:
                    self.bundle["gates"] = gates
                    verdict, reasons, derivation = decide()
                    self.bundle["verdict"] = {"verdict": verdict, "reasons": reasons, "warnings": warnings, "derivation": derivation,
                                              "corrections": applied, "before_corrections": original}
                    return
        self.bundle["verdict"] = {"verdict": verdict, "reasons": reasons, "warnings": warnings, "derivation": derivation}

    def verify_candidate(self, changed, deletes, sealed_src, sealed_sha, expected_ids, checkpoint_uuid, stage: str = "verify") -> dict:
        """One fresh disposable branch: the sealed supervisor as the FIRST step, bound to the module proven red."""
        nonce = new_nonce()
        files = self.guest_files(changed)
        files.update(self.sealed_files(GUEST_SEALED_DIR, "test_sealed", sealed_src))
        verify_steps = self.suite_steps(nonce)
        if not is_supervisor_step(verify_steps[0]):
            raise PipelineAbort("ERROR", "verification order violated: the sealed supervisor must be the first step of the verify branch")
        run = self.executor.run_branch(checkpoint_uuid, files, verify_steps, stage=stage, deletes=deletes, timeout=self.task.test_timeout + 60)
        result, summary = self.suite_outcome(run, nonce)
        binding = bind_verification(result, expected_ids, sealed_sha, nonce)
        return {"run": run, "result": result, "summary": summary, "binding": binding, "nonce": nonce}

    def breaker_gates(self, breaker: dict, gates: dict, blame: dict, warnings: list[str]) -> None:
        """Mutation and adversarial gates from a breaker record, with their reasons attached to the gate they belong to."""
        mutation = breaker["mutation"]
        generated, evaluated, unknown = mutation["generated"], mutation["evaluated"], mutation["unknown"]
        adversarial = breaker["adversarial"]
        adversarial_ran = 0 if adversarial.get("unusable") else int((adversarial.get("summary") or {}).get("ran") or 0)
        if generated == 0 and adversarial_ran >= MIN_ADVERSARIAL_WHEN_NO_MUTANTS:
            # No mutable sites on the changed lines (for example only data tables or simple additions): nothing the
            # mutation gate can detect, so the adversarial suite carries the structural load and the verdict says so.
            gates["mutation"] = {"ok": True, "detail": f"no mutable sites on the changed lines; the adversarial suite ({adversarial_ran} tests) carries the load",
                                 "evidence_class": "bound", "weak": True}
            warnings.append(f"mutation gate: no mutable sites were generated on the changed lines; only the adversarial suite ({adversarial_ran} tests) tests the patch structurally")
        elif generated == 0:
            gates["mutation"] = {"ok": False, "detail": f"no mutable sites on the changed lines and only {adversarial_ran} adversarial test(s)", "evidence_class": "bound"}
            blame["mutation"] = [f"mutation gate: no mutable sites were generated on the changed lines and the adversarial suite has only {adversarial_ran} test(s) "
                                 f"(fewer than {MIN_ADVERSARIAL_WHEN_NO_MUTANTS}); nothing structural tests this patch, so it cannot be VERIFIED"]
        elif evaluated == 0:
            gates["mutation"] = {"ok": False, "detail": f"all {generated} mutants unknown (could not be evaluated)", "evidence_class": "bound"}
            blame["mutation"] = [f"mutation gate could not run: all {generated} mutants were unknown (sandbox could not evaluate them); "
                                 "a verdict cannot be VERIFIED without a mutation score"]
        elif unknown > 0 and evaluated < MIN_MUTANTS_FOR_SCORE:
            gates["mutation"] = {"ok": False, "detail": f"only {evaluated} of {generated} mutants evaluated ({unknown} unknown)", "evidence_class": "bound"}
            blame["mutation"] = [f"mutation gate incomplete: only {evaluated} of {generated} mutants could be evaluated "
                                 f"({unknown} unknown); too few to score, so the result is not trustworthy"]
        elif mutation["score"] < self.mutation_threshold:
            blame["mutation"] = [f"mutation score {mutation['score']:.2f} below {self.mutation_threshold:.2f}: {mutation['survived']} of {evaluated} mutants survived the sealed suite"]
            gates["mutation"] = {"ok": False, "detail": f"score {mutation['score']}", "evidence_class": "bound"}
        else:
            gates["mutation"] = {"ok": True, "detail": f"score {mutation['score']} on {evaluated} mutants", "evidence_class": "bound"}
            if evaluated < MIN_MUTANTS_FOR_SCORE:
                warnings.append(f"only {evaluated} mutants evaluated (all killed); mutation score is weak evidence")
            if unknown:
                warnings.append(f"{unknown} mutant(s) were unknown and excluded from the score")
        if adversarial.get("unusable"):
            gates["adversarial_tests"] = {"ok": False, "detail": adversarial["unusable"][:160], "evidence_class": "bound"}
            blame["adversarial_tests"] = [f"model-written adversarial tests could not be produced: {adversarial['unusable'][:160]}; rerun the breaker stage or review manually"]
        elif adversarial["summary"]["all_passed"] and adversarial["binding"]["ok"]:
            gates["adversarial_tests"] = {"ok": True, "detail": adversarial["summary"]["summary_line"], "evidence_class": "bound"}
        else:
            failing_ids = [t["id"] for t in adversarial["summary"]["tests"] if t["outcome"] != "ok"]
            gates["adversarial_tests"] = {"ok": False, "detail": adversarial["summary"]["summary_line"], "failing": failing_ids, "evidence_class": "bound"}
            reasons = []
            if not adversarial["binding"]["ok"]:
                reasons.append("adversarial suite binding failed: " + "; ".join(adversarial["binding"]["reasons"])[:300])
            reasons.append(f"model-written adversarial tests failed: {adversarial['summary']['failing']} of {adversarial['summary']['ran']} "
                           f"({', '.join(failing_ids)[:300]}); each failure is a bug or a contract disagreement to resolve")
            blame["adversarial_tests"] = reasons

    # ----------------------------------------------------------------- contract audit
    def contract_audit(self, spec: dict, snapshot: dict[str, bytes], checkpoint_uuid: str) -> dict:
        """Ask the auditor for requirement conflicts and EXECUTE every witness it offers on the unmodified checkpoint. A
        conflict counts as demonstrated only when its witness exits with WITNESS_EXIT_CODE and prints the marker line; the
        program, its output and the operation id are recorded so a reader can judge the demonstration."""
        record = {"model": None, "consistent": None, "notes": "", "conflicts": [], "outcome": "not run", "error": None,
                  "rule": (f"a conflict is demonstrated only when it names existing criteria and its witness program, run on the unmodified "
                           f"repository in a disposable sandbox branch, prints a line starting with {WITNESS_MARKER!r} that names at least one of "
                           f"them and exits with code {WITNESS_EXIT_CODE}; it is GROUNDED, and may end the run as infeasible, only when every named "
                           f"requirement is an authoritative task criterion (TC) and the witness conforms to the constrained witness language "
                           f"{WITNESS_LANGUAGE} (a positive grammar: literal inputs, allowed built-ins and standard-library functions, and functions "
                           "or classes the frozen repository defines, every call origin resolved statically; enforced mechanically here and again by "
                           "attest check); a demonstrated conflict that involves a derived criterion (AC) or a witness outside the language is held "
                           "for a human; a claimed-only conflict never ends a run; whether the witness's inputs and comparison demonstrate that the "
                           "criteria cannot all hold is the model's reasoning, recorded with its execution, not a formal proof of impossibility")}
        try:
            answer = self.ask("audit", contract_audit_prompt(self.task, spec, snapshot), CONTRACT_AUDIT_SCHEMA, "contract-audit")
        except ModelError as error:
            if error.uncertain:
                raise
            record.update({"error": f"audit call failed: {self.diagnostics.public_text('contract-audit', error)}", "outcome": "unavailable"})
            return record
        record["model"] = answer.call.requested_model
        record["consistent"] = bool(answer.json.get("consistent"))
        record["notes"] = answer.json.get("notes") or ""
        conflicts = list(answer.json.get("conflicts") or [])[:MAX_WITNESSES]
        task_ids = {f"TC{i}" for i in range(1, len(self.task.acceptance_criteria or []) + 1)}
        derived_ids = {f"AC{i}" for i in range(1, len(spec.get("acceptance_criteria") or []) + 1)}
        record["requirement_ids_known"] = {"task": sorted(task_ids, key=lambda s: int(s[2:])), "derived": sorted(derived_ids, key=lambda s: int(s[2:]))}
        record["input_domain"] = WITNESS_INPUT_DOMAIN
        record["witness_language"] = WITNESS_LANGUAGE
        copied: set[str] = set()
        for index, conflict in enumerate(conflicts, 1):
            witness, _ = repair_escapes(conflict.get("witness") or "")
            ids = [str(i).strip() for i in (conflict.get("requirement_ids") or []) if str(i).strip()]
            provenance = requirement_provenance(ids, task_ids, derived_ids)
            entry = {"requirement_ids": ids, "provenance": provenance, "summary": (conflict.get("summary") or "")[:500],
                     "witness_path": None, "witness_sha256": None, "witness_constrained": None, "constraint_problems": [], "witness_language": None,
                     "exit_code": None, "timed_out": None, "stdout_tail": "", "stderr_tail": "",
                     "operation_uuid": None, "demonstrated": False, "grounded": False, "status": "no witness"}
            if provenance == "unknown":
                # a conflict must name real criteria (authoritative TC ids or derived AC ids); a witness for requirements that do not
                # exist is a claim about nothing
                unknown_ids = [i for i in ids if i not in task_ids and i not in derived_ids]
                entry["status"] = ("the conflict names no requirement" if not ids else "the conflict names unknown requirement id(s): " + ", ".join(unknown_ids)[:120]) \
                    + "; recorded as claimed only, the witness was not executed"
                record["conflicts"].append(entry)
                self.log(f"contract audit: conflict {index}: {entry['status']}")
                continue
            if witness.strip():
                # the constrained witness language (R6-1): a positive grammar whose call origins are resolved against the frozen
                # repository; the repository files the resolution read are kept in the bundle so that attest check repeats it offline
                analysis = analyze_witness(witness, Repository.from_snapshot(snapshot, self.task.python_paths))
                entry["witness_language"] = analysis
                entry["constraint_problems"] = analysis["problems"]
                entry["witness_constrained"] = bool(analysis["conforms"])
                for path in analysis["repository_files"]:
                    if path not in copied and path in snapshot:
                        self.save(f"{REPOSITORY_COPY_DIR}/{path}", snapshot[path])
                        copied.add(path)
                try:
                    compile(witness, f"witness_{index}.py", "exec")
                except SyntaxError as error:
                    entry["status"] = f"witness does not compile: {error.msg} at line {error.lineno}"
                    record["conflicts"].append(entry)
                    continue
                self.save(f"contract_audit/witness_{index}.py", witness)
                entry["witness_path"] = f"contract_audit/witness_{index}.py"
                entry["witness_sha256"] = sha256_text(witness)
                guest_path = f"{GUEST_AUDIT_DIR}/witness_{index}.py"
                steps = [{"name": f"witness-{index}", "cmd": [GUEST_PYTHON, guest_path], "cwd": GUEST_REPO, "timeout": WITNESS_TIMEOUT,
                          "env": self.task.guest_env()}]
                try:
                    run = self.executor.run_branch(checkpoint_uuid, {guest_path: witness.encode("utf-8")}, steps, stage=f"witness-{index}",
                                                   timeout=WITNESS_TIMEOUT + 60)
                except Exception as error:  # noqa: BLE001 - an uncertain spawn is recorded, never replayed
                    entry["status"] = f"witness could not be executed: {self.diagnostics.public_text(f'witness-{index}', error)}"
                    record["conflicts"].append(entry)
                    continue
                step = run.step(f"witness-{index}")
                entry["operation_uuid"] = run.operation_uuid
                if run.runner_error or step is None:
                    entry["status"] = f"witness run failed: {run.runner_error or 'step missing'}"
                else:
                    entry.update({"exit_code": step.exit_code, "timed_out": step.timed_out, "stdout_tail": _tail(step.stdout, 1500),
                                  "stderr_tail": _tail(step.stderr, 1000)})
                    marker_lines = [line for line in step.stdout.splitlines() if line.startswith(WITNESS_MARKER)]
                    marker = bool(marker_lines)
                    # the marker line must name at least one of the requirements the conflict claims, so the printed observation is
                    # tied to the claim it is said to demonstrate (a bare marker with an unrelated or empty line is not a demonstration)
                    names_claim = any(any(re.search(rf"(?<![A-Za-z0-9]){re.escape(i)}(?![0-9])", line) for i in ids) for line in marker_lines)
                    if step.timed_out:
                        entry["status"] = "witness timed out"
                    elif step.exit_code == WITNESS_EXIT_CODE and marker and names_claim:
                        entry["demonstrated"] = True
                        # GROUNDED (R5-03): every requirement is the requester's own, and the witness is constrained to the input domain
                        # and the unchanged code; only a grounded conflict may end the run as infeasible, anything else is a hold
                        entry["grounded"] = provenance == "task" and bool(entry["witness_constrained"])
                        if entry["grounded"]:
                            entry["status"] = f"demonstrated and grounded (authoritative criteria, witness in {WITNESS_LANGUAGE})"
                        elif provenance != "task":
                            entry["status"] = f"demonstrated on {provenance} criteria (a model's restatement is involved); held for a human, not infeasible"
                        else:
                            entry["status"] = (f"demonstrated by a witness outside the constrained witness language {WITNESS_LANGUAGE} ("
                                               + "; ".join(entry["constraint_problems"])[:200] + "); held for a human, not infeasible")
                    elif step.exit_code == WITNESS_EXIT_CODE and marker:
                        entry["status"] = "marker line does not name any of the claimed requirements; recorded as claimed only"
                    elif step.exit_code == 0:
                        entry["status"] = "not demonstrated (the witness reported it could not show the conflict)"
                    else:
                        entry["status"] = f"broken witness (exit {step.exit_code}" + ("" if marker else ", no marker line") + ")"
            record["conflicts"].append(entry)
            self.log(f"contract audit: conflict {index} ({', '.join(entry['requirement_ids'])}): {entry['status']}")
        if any(c["grounded"] for c in record["conflicts"]):
            record["outcome"] = "contradiction demonstrated"
        elif any(c["demonstrated"] for c in record["conflicts"]):
            record["outcome"] = "conflict demonstrated on derived criteria or by an unconstrained witness"
        elif record["conflicts"]:
            record["outcome"] = "conflicts claimed, none demonstrated"
        elif record["consistent"]:
            record["outcome"] = "consistent"
        else:
            record["outcome"] = "inconsistent claimed without a witness"
        return record

    # ----------------------------------------------------------------- breaker
    def breaker_pass(self, snapshot, changed, deleted, sealed_src, sealed_sha, checkpoint_uuid, spec, diff, expected_ids, sources) -> dict:
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        mutants = generate_mutants(snapshot, changed, max_mutants=self.max_mutants)
        self.log(f"breaker: {len(mutants)} mutants of changed lines; running in parallel branches (workers={self.mutant_workers})")

        raw_mutants: dict = {}

        def run_mutant(mutant):
            files = {f"{GUEST_REPO}/{rel}": data for rel, data in changed.items()}
            files[f"{GUEST_REPO}/{mutant.path}"] = mutant.source.encode("utf-8")
            files.update(self.sealed_files(GUEST_SEALED_DIR, "test_sealed", sealed_src, canary=False))
            nonce = new_nonce()
            base = {"id": mutant.id, "path": mutant.path, "lineno": mutant.lineno, "operator": mutant.operator, "description": mutant.description,
                    "nonce": nonce}
            try:
                run = self.executor.run_branch(checkpoint_uuid, files, self.suite_steps(nonce), stage=f"mutant-{mutant.id}",
                                               deletes=deletes, timeout=self.task.test_timeout + 60)
            except Exception as error:  # noqa: BLE001 - an uncertain or failed spawn makes this mutant unknown, never replayed
                return {**base, "status": "unknown", "operation_uuid": None, "failing_methods": 0, "killed_by": [],
                        "evidence": "no execution", "error": self.diagnostics.public_text(f"mutant-{mutant.id}", error)}
            result, summary = self.suite_outcome(run, nonce)
            raw_mutants[mutant.id] = result
            binding = bind_verification(result, expected_ids, sealed_sha, nonce, canary=False)
            status, evidence, killed_by = classify_mutant_run(result, binding, expected_ids)
            return {**base, "status": status, "operation_uuid": run.operation_uuid, "failing_methods": len(killed_by), "killed_by": killed_by[:5],
                    "evidence": evidence, "binding_ok": binding["ok"], "structural_problems": structural_problems(binding, result)}

        results = []
        if mutants:
            with ThreadPoolExecutor(max_workers=max(1, min(self.mutant_workers, len(mutants)))) as pool:
                results = list(pool.map(run_mutant, mutants))
        self.raw_results["mutants"] = raw_mutants  # every evaluated mutant's raw supervisor result, so `attest check` can reclassify it
        killed = sum(1 for r in results if r["status"] == "killed")
        survived = sum(1 for r in results if r["status"] == "survived")
        unknown = sum(1 for r in results if r["status"] == "unknown")
        evaluated = killed + survived
        score = round(killed / evaluated, 3) if evaluated else None
        self.log(f"breaker: killed {killed}, survived {survived}, unknown {unknown}, mutation score {score}")
        for mutant in mutants:
            self.save(f"mutants_{mutant.id}.py", mutant.source)
        mutation = {"generated": len(mutants), "evaluated": evaluated, "killed": killed, "survived": survived, "unknown": unknown,
                    "score": score, "threshold": self.mutation_threshold, "mutants": results, "policy": MUTANT_POLICY}

        # Model-written adversarial tests, run through the same supervisor in their own directory (one feedback retry).
        adversarial: dict = {}
        try:
            feedback = None
            src = None
            host_ids: list[str] = []
            authored = None
            escalated = False
            for attempt in range(1, MAX_BREAKER_ATTEMPTS + 1):
                role = "break" if attempt < MAX_BREAKER_ATTEMPTS else "arbitrate"  # the last attempt escalates to the stronger model
                escalated = role != "break"
                authored = self.ask(role, breaker_prompt(self.task, spec, diff, [i.split(".")[-1] for i in expected_ids], sources, feedback,
                                                         per_test_timeout=min(60, self.task.test_timeout)),
                                    BREAKER_SCHEMA, f"break-tests-{attempt}" + ("-escalated" if escalated else ""))
                self.save(f"breaker_response.attempt{attempt}.json", {"json": authored.json, "text_head": (authored.text or "")[:4000]})
                candidate, repaired = repair_escapes(authored.json.get("test_file") or "")
                self.save(f"breaker_tests.attempt{attempt}.py", candidate)
                try:
                    compile(candidate, "test_breaker.py", "exec")
                    ids = static_test_ids(candidate, "test_breaker") if "unittest" in candidate else []
                except SyntaxError as error:
                    feedback = (f"the module has a syntax error: {error.msg} at line {error.lineno}: {(error.text or '').strip()[:120]!r}; "
                                "return the complete module source as the JSON string test_file, with every string literal and bracket closed")
                    self.log(f"breaker tests attempt {attempt} rejected: {feedback[:120]}")
                    continue
                if len(ids) < 3:
                    feedback = (f"the answer contained {len(ids)} discoverable unittest.TestCase test methods in {len(candidate)} characters of test_file; "
                                "test_file must be the complete Python module source (starting with `import unittest`) with at least 6 test methods")
                    self.log(f"breaker tests attempt {attempt} rejected: {feedback[:120]}")
                    continue
                src, host_ids = candidate, ids
                break
            if src is None:
                adversarial = {"unusable": feedback or "no module produced", "attempts": MAX_BREAKER_ATTEMPTS, "escalated": escalated,
                               "summary": {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False,
                                           "summary_line": f"no usable adversarial module after {MAX_BREAKER_ATTEMPTS} attempts (the last by the arbiter's model)"},
                               "binding": {"ok": False, "checks": {}, "reasons": [feedback or "no module"]}}
            else:
                self.save("breaker_tests.py", src)
                nonce = new_nonce()
                files = {f"{GUEST_REPO}/{rel}": data for rel, data in changed.items()}
                files.update(self.sealed_files(GUEST_BREAKER_DIR, "test_breaker", src))
                try:
                    run = self.executor.run_branch(checkpoint_uuid, files, self.suite_steps(nonce, "test_breaker", GUEST_BREAKER_DIR, "breaker"),
                                                   stage="breaker-tests", deletes=deletes, timeout=self.task.test_timeout + 60)
                except Exception as error:  # noqa: BLE001 - uncertain spawn: the adversarial stage is unusable, not replayed
                    # classified and recorded privately here, as a sandbox failure; the ModelError below carries only the public text
                    raise ModelError(f"adversarial branch could not be executed: {self.diagnostics.public_text('break-tests-sandbox', error)}") from None
                result, summary = self.suite_outcome(run, nonce, "breaker")
                self.raw_results["adversarial"] = result
                binding = bind_verification(result, host_ids, sha256_text(src), nonce)
                adversarial = {"sha256": sha256_text(src), "author_model": authored.call.requested_model, "author_role": authored.call.role,
                               "attempts": attempt, "escalated": escalated,
                               "expected_ids": host_ids, "summary": summary, "binding": binding, "notes": authored.json.get("notes", ""),
                               "operation_uuid": run.operation_uuid}
                self.log(f"breaker tests: {summary['summary_line']}; binding {'ok' if binding['ok'] else 'FAILED'}")
        except ModelError as error:
            public = self.diagnostics.public_text("break-tests", error)
            adversarial = {"unusable": f"adversarial test authoring failed: {public}",
                           "summary": {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False, "summary_line": f"authoring failed: {public}"},
                           "binding": {"ok": False, "checks": {}, "reasons": [public]}}
        return {"mutation": mutation, "adversarial": adversarial}

    # ----------------------------------------------------------------- arbitration
    def arbitrate_failures(self, spec, diff, sealed_src, sealed_sha, expected_ids, checkpoint_uuid, changed, deleted,
                           gates, binding, sealed_summary, finished, scope_ok) -> dict | None:
        """Arbitrate a NEEDS HUMAN whose only failing gates are model-generated tests (sealed and/or adversarial).
        Returns None when the failure is not confined to generated tests (a structural, held-out, mutation, drift,
        scope or unfinished failure is never arbitrated: those stay with the human)."""
        # Gates that were skipped because verification did not pass are not independent failures to arbitrate around.
        failed = {name for name, g in gates.items() if not g.get("ok") and not g.get("skipped")}
        if not finished or not scope_ok or not failed or (failed - {"sealed_binding", "adversarial_tests"}):
            return None
        modules = []
        skipped: list[str] = []

        def eligible(label: str, module_binding: dict, raw: dict | None, tests: list[dict]) -> list[dict] | None:
            # The same structural filter for both generated modules (CORE-01): a plain test failure legitimately makes the child
            # exit 1 and a supervisor-observed timeout is a recorded fact, so neither is tampering; every other failing binding
            # check (nonce, digest, isolation, crash, missing/forged/mismatched result, discovery, id set, canary, start-up
            # hook, cleanup) means the evidence cannot be trusted, and untrusted evidence is never turned into a "test defect".
            problems = structural_problems(module_binding, raw)
            if problems:
                skipped.append(f"{label}: untrusted execution evidence ({', '.join(problems)[:160]}) is never arbitrated")
                return None
            classes = outcome_classes(raw)
            untrusted = [t["id"] for t in tests if t["outcome"] != "ok" and classes.get(t["id"], "untrusted") == "untrusted"]
            if untrusted:
                skipped.append(f"{label}: untrusted per-test record(s) ({', '.join(i.split('.')[-1] for i in untrusted)[:160]}) are never arbitrated")
                return None
            return [t for t in tests if classes.get(t["id"]) in ("red", "timeout")]

        if "sealed_binding" in failed:
            sealed_fail = eligible("sealed", binding, self.raw_results.get("sealed"), sealed_summary.get("tests", []))
            if sealed_fail:
                modules.append(("sealed", "test_sealed", GUEST_SEALED_DIR, sealed_src, sealed_fail))
        adversarial = (self.bundle.get("breaker") or {}).get("adversarial") or {}
        if "adversarial_tests" in failed and not adversarial.get("unusable"):
            adv_fail = eligible("adversarial", adversarial.get("binding") or {}, self.raw_results.get("adversarial"),
                                (adversarial.get("summary") or {}).get("tests", []))
            adv_src = None
            adv_path = self.out_dir / "breaker_tests.py"
            if adv_path.is_file():
                adv_src = adv_path.read_text(encoding="utf-8")
            if adv_fail and adv_src:
                modules.append(("adversarial", "test_breaker", GUEST_BREAKER_DIR, adv_src, adv_fail))
        if not modules:
            if skipped:
                counts = {k: 0 for k in ("implementation_bug", "test_defect", "contract_dispute")}
                self.log("arbitration not attempted: " + "; ".join(skipped), "arbitrate")
                return {"applied": self.arbitration_apply, "validated_modules": [], "cleared": False, "all_corrected": False, "counts": counts,
                        "headline": "not attempted: " + "; ".join(skipped), "modules": [], "skipped": skipped, "rule": ARBITRATION_RULE,
                        "note": "lost, forged, mismatched, crashed or non-isolated execution evidence is never classified as a test defect; the hold stands"}
            return None
        self.log("arbitration: classifying model-generated test failures", "arbitrate")
        results = []
        for label, module_name, guest_dir, module_src, failing in modules:
            results.append(self.arbitrate_module(label, module_name, guest_dir, module_src, failing, spec, diff,
                                                 checkpoint_uuid, changed, deleted))
        every_class = [c for r in results for c in r["classifications"]]
        counts = {k: sum(1 for c in every_class if c["classification"] == k)
                  for k in ("implementation_bug", "test_defect", "contract_dispute")}
        validated = [r["module"] for r in results if r.get("validated")]
        all_corrected = bool(results) and all(r.get("cleared_module") for r in results)
        if results and all(r.get("validated") for r in results):
            headline = (f"all {counts['test_defect']} failing generated test(s) classified as test defects; the corrected tests pass on the "
                        f"candidate and discriminate ({'; '.join(r['corrected']['discrimination'] for r in results)}); the affected gate(s) are re-run "
                        "on the corrected modules")
        elif any(r.get("sealed_assertion_hold") for r in results):
            headline = (f"{counts['test_defect']} failing sealed test(s) classified as test defects and the correction was validated by execution, "
                        "but a sealed test that failed by assertion or by an exception, whatever its origin, is never overridden: the "
                        "hold stands for a human (the arbiter's view and the corrected tests are recorded)")
        elif all_corrected:
            headline = (f"all {counts['test_defect']} failing generated test(s) classified as test defects and the corrected tests pass on the "
                        "candidate, but the correction did not meet the validation rule ("
                        + "; ".join((r.get("error") or "not validated") for r in results if not r.get("validated")) + "); the hold stands")
        elif counts["implementation_bug"]:
            headline = f"{counts['implementation_bug']} failing test(s) indicate a real implementation bug; human review required"
        elif counts["contract_dispute"]:
            headline = f"{counts['contract_dispute']} failing test(s) are contract disputes; a human must decide"
        else:
            headline = "generated-test failures could not be cleared by arbitration; human review required"
        return {"applied": self.arbitration_apply, "validated_modules": validated, "cleared": bool(validated) and self.arbitration_apply,
                "all_corrected": all_corrected, "counts": counts, "headline": headline, "modules": results, "rule": ARBITRATION_RULE,
                "note": "original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate"}

    def arbitrate_module(self, label, module_name, guest_dir, module_src, failing, spec, diff, checkpoint_uuid,
                         changed, deleted) -> dict:
        record = {"module": label, "classifications": [], "corrected_notes": "", "corrected_module": None,
                  "candidate_rerun": None, "base_rerun": None, "mutant_reruns": [], "cleared_module": False, "validated": False,
                  "corrected": None, "sealed_assertion_hold": False, "error": None}
        try:
            answer = self.ask("arbitrate", arbitrate_prompt(self.task, spec, diff, module_src, module_name, failing),
                              ARBITRATION_SCHEMA, f"arbitrate-{label}").json
        except ModelError as error:
            record["error"] = f"arbiter call failed: {self.diagnostics.public_text(f'arbitrate-{label}', error)}"
            return record
        record["classifications"] = answer.get("classifications") or []
        record["corrected_notes"] = answer.get("corrected_notes", "")
        failing_ids = {f["id"] for f in failing}
        # Exactly one classification per failing test (CORE-05): an answer about other tests says nothing about these.
        id_problems, by_id = classification_problems(record["classifications"], failing_ids)
        record["classification_ids_ok"] = not id_problems
        if id_problems:
            record["error"] = "classification ids do not match the failing tests: " + "; ".join(id_problems)[:300]
            return record
        all_defect = all(c.get("classification") == "test_defect" for c in by_id.values())
        corrected, _ = repair_escapes(answer.get("corrected_module") or "")
        if not (all_defect and corrected.strip()):
            return record  # a real bug or a dispute, or no correction offered: nothing to re-verify
        try:
            compile(corrected, f"{module_name}.py", "exec")
            corrected_ids = static_test_ids(corrected, module_name)
            # Mechanical constraints on the correction, independent of the arbiter's opinion (CORE-05): same test set, only
            # the failing tests' bodies changed, additive non-colliding imports only, class metadata and helpers untouched.
            problems, changed_tests = correction_problems(module_src, corrected, module_name, failing_ids, MAX_CORRECTED_TESTS)
        except SyntaxError as error:
            record["error"] = f"corrected module has a syntax error: {error}"
            return record
        record["scope_problems"] = problems
        if problems:
            record["error"] = "correction rejected whole: " + "; ".join(problems)[:400]
            return record
        disagreeing = sorted(f["id"] for f in failing if oracle_disagreement(f))
        if label == "sealed" and disagreeing:
            # the pre-registered oracle disagreed with the candidate (an assertion failed or an exception was raised, whatever its
            # origin); whether the oracle or the candidate is wrong is a judgement, and execution cannot settle it (each side passes
            # its own test), so it stays with the human; only a test the supervisor killed at its timeout leaves the oracle undisputed
            record["sealed_assertion_hold"] = True
            record["sealed_disagreeing_tests"] = disagreeing
        record["corrected_module"] = f"arbitration/{label}_corrected.py"
        self.save(f"arbitration/{label}_corrected.py", corrected)
        corrected_sha = sha256_text(corrected)
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        # Re-run the corrected tests on the CANDIDATE under the supervisor: a genuine test defect, once corrected, must pass.
        nonce = new_nonce()
        files = self.guest_files(changed)
        files.update(self.sealed_files(guest_dir, module_name, corrected))
        try:
            run = self.executor.run_branch(checkpoint_uuid, files, self.suite_steps(nonce, module_name, guest_dir, "arb"),
                                           stage=f"arbitrate-{label}-candidate", deletes=deletes, timeout=self.task.test_timeout + 60)
            result, summary = self.suite_outcome(run, nonce, "arb")
            cand_binding = bind_verification(result, corrected_ids, corrected_sha, nonce)
            record["candidate_rerun"] = {"summary_line": summary["summary_line"], "all_passed": summary["all_passed"],
                                         "binding_ok": cand_binding["ok"], "operation_uuid": run.operation_uuid}
            candidate_ok = summary["all_passed"] and cand_binding["ok"]
        except Exception as error:  # noqa: BLE001
            record["error"] = f"candidate re-run failed: {self.diagnostics.public_text(f'arbitrate-{label}-candidate', error)}"
            return record
        # The corrected tests must still DISCRIMINATE: fail on the unmodified base (every corrected sealed test must, since the
        # red check is the sealed suite's defining property), or, for a module that legitimately passes on the base (a refactor
        # that preserves behaviour), be caught by at least one mutant of the patch. Only AUTHENTIC red results count (CORE-01):
        # the base run must be structurally sound and every corrected test must have an exit-1 FAIL/ERROR report bound to the
        # nonce; a lost, forged, crashed or timed-out record is never "red".
        discrimination = None
        nonce_b = new_nonce()
        try:
            run_b = self.executor.run_branch(checkpoint_uuid, self.sealed_files(guest_dir, module_name, corrected),
                                             self.suite_steps(nonce_b, module_name, guest_dir, "arbbase"),
                                             stage=f"arbitrate-{label}-base", timeout=self.task.test_timeout + 60)
            result_b, summary_b = self.suite_outcome(run_b, nonce_b, "arbbase")
        except Exception as error:  # noqa: BLE001
            record["error"] = f"base re-run failed: {self.diagnostics.public_text(f'arbitrate-{label}-base', error)}"
            return record
        self.raw_results[f"{label}_corrected_base"] = result_b
        record["base_rerun"] = base_discrimination(result_b, summary_b, corrected_ids, corrected_sha, nonce_b, sorted(changed_tests), label)
        record["base_rerun"]["operation_uuid"] = run_b.operation_uuid
        discrimination = record["base_rerun"].get("discrimination")
        if record["base_rerun"].get("untrusted"):
            record["error"] = "base re-run evidence untrusted: " + record["base_rerun"]["untrusted"]
        elif discrimination is None and label == "adversarial":
            discrimination = self.mutant_discrimination(record, module_name, guest_dir, corrected, corrected_ids, corrected_sha, changed, deletes,
                                                        checkpoint_uuid, changed_tests)
        if discrimination is None and not record.get("error"):
            record["error"] = ("corrected tests do not discriminate: they pass on the unmodified base"
                               + (" and no validly killed mutant of the patch is caught by them" if label == "adversarial" else "; a sealed test must fail on the base"))
        record["cleared_module"] = bool(candidate_ok and discrimination)
        record["validated"] = bool(candidate_ok and discrimination and not record["sealed_assertion_hold"])
        if record["validated"] or record["cleared_module"]:
            self.raw_results[f"{label}_corrected"] = result
            record["corrected"] = {"path": record["corrected_module"], "sha256": corrected_sha, "expected_ids": corrected_ids,
                                   "changed_tests": sorted(changed_tests), "summary": summary, "binding": cand_binding, "nonce": nonce,
                                   "operation_uuid": run.operation_uuid, "discrimination": discrimination,
                                   "base_rerun": record["base_rerun"], "mutant_reruns": record["mutant_reruns"],
                                   "original_sha256": sha256_text(module_src), "original_failing": sorted(failing_ids)}
        return record

    def mutant_discrimination(self, record, module_name, guest_dir, corrected, corrected_ids, corrected_sha, changed, deletes, checkpoint_uuid,
                              changed_tests) -> str | None:
        """For a corrected adversarial module that passes on the base: run it against up to MAX_MUTANTS_FOR_DISCRIMINATION mutants
        that the sealed suite validly killed; it discriminates when at least one mutant makes a corrected test fail with an
        authentic result under a structurally sound run (CORE-01). Every re-run's raw result is kept for `attest check`."""
        mutants = [m for m in ((self.bundle.get("breaker") or {}).get("mutation") or {}).get("mutants") or [] if m.get("status") == "killed"]
        raw = self.raw_results.setdefault("adversarial_corrected_mutants", {})
        for mutant in mutants[:MAX_MUTANTS_FOR_DISCRIMINATION]:
            source_path = self.out_dir / f"mutants_{mutant['id']}.py"
            if not source_path.is_file():
                continue
            files = {f"{GUEST_REPO}/{rel}": data for rel, data in changed.items()}
            files[f"{GUEST_REPO}/{mutant['path']}"] = source_path.read_bytes()
            files.update(self.sealed_files(guest_dir, module_name, corrected, canary=False))
            nonce = new_nonce()
            try:
                run = self.executor.run_branch(checkpoint_uuid, files, self.suite_steps(nonce, module_name, guest_dir, "arbmut"),
                                               stage=f"arbitrate-adversarial-{mutant['id']}", deletes=deletes, timeout=self.task.test_timeout + 60)
                result_m, summary = self.suite_outcome(run, nonce, "arbmut")
            except Exception as error:  # noqa: BLE001 - an uncertain spawn makes this mutant unknown, never replayed
                record["mutant_reruns"].append({"mutant": mutant["id"], "error": self.diagnostics.public_text(f"arbitrate-adversarial-{mutant['id']}", error)})
                continue
            raw[mutant["id"]] = result_m
            entry = mutant_rerun_discrimination(result_m, summary, corrected_ids, corrected_sha, nonce, sorted(changed_tests))
            entry.update({"mutant": mutant["id"], "description": mutant.get("description"), "operation_uuid": run.operation_uuid})
            record["mutant_reruns"].append(entry)
            if entry["corrected_tests_failing"]:
                return (f"corrected test(s) {', '.join(t.split('.')[-1] for t in entry['corrected_tests_failing'])} catch mutant {mutant['id']} "
                        f"({mutant.get('description')}) with authentic results")
        return None

    # ----------------------------------------------------------------- actions
    @staticmethod
    def _syntax_note(workspace: Workspace, rel: str) -> str:
        if not rel.endswith(".py"):
            return ""
        try:
            compile(workspace.files[rel].decode("utf-8", "replace"), rel, "exec")
        except SyntaxError as error:
            return (f"\nSYNTAX ERROR after this edit: {error.msg} at line {error.lineno}. The file does not parse. "
                    "Fix it with another edit or use `undo` to revert this change before continuing.")
        return ""

    def execute_action(self, action: dict, workspace: Workspace, checkpoint: str, turn: int) -> str:
        kind = action["action"]
        deletes = [f"{GUEST_REPO}/{p}" for p in workspace.deleted()]
        try:
            if kind == "list_files":
                return "\n".join(workspace.list_files())
            if kind == "read_file":
                if not action.get("path"):
                    return "INVALID ACTION: read_file needs path"
                return workspace.read(action["path"], start_line=action.get("start_line"), end_line=action.get("end_line"))
            if kind == "search":
                if not action.get("find"):
                    return "INVALID ACTION: search needs find (a symbol or literal snippet, or re:<regular expression>); path is optional"
                return workspace.search(action["find"], action.get("path"))
            if kind == "replace_in_file":
                if not action.get("path") or action.get("find") is None or action.get("replace") is None:
                    return "INVALID ACTION: replace_in_file needs path, find and replace"
                rel = workspace.replace(action["path"], action["find"], action["replace"])
                return f"replaced one occurrence in {rel}; the file is now {len(workspace.files[rel])} bytes" + self._syntax_note(workspace, rel)
            if kind == "write_file":
                if not action.get("path") or action.get("content") is None:
                    return "INVALID ACTION: write_file needs path and the complete content"
                rel = workspace.write(action["path"], action["content"])
                return f"wrote {rel} ({len(action['content'].encode('utf-8'))} bytes)" + self._syntax_note(workspace, rel)
            if kind == "undo":
                rel = workspace.undo()
                return f"reverted the last edit to {rel}" if rel else "nothing to undo"
            if kind == "run_tests":
                run = self.executor.run_branch(checkpoint, self.guest_files(workspace.changed()), [self.existing_step()],
                                               stage=f"impl-tests-{turn}", deletes=deletes, timeout=self.task.test_timeout + 60)
                parsed = self.parsed_step(run, "existing")
                failing = [f"{t['id']}: {t['outcome']}" for t in parsed["tests"] if t["outcome"] != "ok"]
                return (f"existing test suite: {parsed['summary_line']} (ran {parsed['ran']}, passed {parsed['passed']}, exit {parsed.get('exit_code')})\n"
                        + ("failing: " + ", ".join(failing)[:1500] + "\n" if failing else "")
                        + _tail(parsed.get("stdout_tail", "") if self.task.test_runner == "pytest" else parsed.get("stderr_tail", ""), 3000))
            if kind == "run_python":
                if not action.get("code"):
                    return "INVALID ACTION: run_python needs code"
                run = self.executor.run_branch(checkpoint, self.guest_files(workspace.changed()),
                                               [{"name": "python", "cmd": [GUEST_PYTHON, "-c", action["code"]], "cwd": GUEST_REPO,
                                                 "timeout": 60, "env": self.task.guest_env()}],
                                               stage=f"impl-python-{turn}", deletes=deletes, timeout=90)
                step = run.step("python")
                if run.runner_error or step is None:
                    return f"sandbox run failed: {self.diagnostics.public_text(f'impl-python-{turn}', run.runner_error)}"
                note = ""
                if re.search(r"write_text|write_bytes|open\([^)]*['\"](w|a|r\+)|shutil\.|os\.(rename|replace|remove)", action["code"]):
                    note = ("NOTE: this snippet wrote files, but run_python executes in a throwaway sandbox branch and those changes are DISCARDED. "
                            "Use replace_in_file or write_file to change the repository.\n")
                return f"{note}exit {step.exit_code}{' (timed out)' if step.timed_out else ''}\nstdout:\n{_tail(step.stdout, 2000)}\nstderr:\n{_tail(step.stderr, 1500)}"
            if kind == "finish":
                return "finished: " + (action.get("summary") or "")
            return f"INVALID ACTION: unknown action {kind}"
        except PolicyViolation as error:
            return f"REJECTED by write policy: {error}"
        except FileNotFoundError as error:
            return f"no such file: {error}"
