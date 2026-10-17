"""One task, end to end: freeze, checkpoint, spec, ground, seal, red, implement, verify, hold out, break, audit, attest.

Verdict rule: VERIFIED only when every gate holds; any failed gate yields NEEDS HUMAN with the exact reasons; infrastructure
failures yield ERROR. Held-out failures, surviving mutants beyond the threshold, failing model-written adversarial tests and
high drift all block VERIFIED.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..ledger import Ledger, utcnow
from ..models.base import ModelError
from .external import LIMITS as EXTERNAL_LIMITS, external_policy_problems, repository_problems
from .grounding import ground, sources_text
from .mutate import generate_mutants
from .prompts import (ACTION_SCHEMA, ARBITRATION_SCHEMA, BREAKER_SCHEMA, DRIFT_SCHEMA, SEAL_SCHEMA, SPEC_SCHEMA,
                      arbitrate_prompt, breaker_prompt, drift_prompt, implement_prompt, seal_prompt, spec_prompt)
from .manifest import MANIFEST_FILE, build_manifest
from .proof import write_bundle
from .provenance import build_provenance
from .sealed import (BAD_OUTCOMES, SEALED_FILE, SUPERVISOR_VERSION, bind_modules, bind_verification, guest_files_for, is_supervisor_step,
                     module_name_for, new_nonce, read_sealed_result, repair_escapes, repo_suite_files, sealed_steps, sha256_text,
                     static_repo_tests, static_test_ids, summarize)
from .tamper import scan_diff
from .task import GUEST_PYTHON, GUEST_REPO, GUEST_SEALED_DIR, TaskSpec
from .testparse import parse_test_output
from .verdict import derive
from .workspace import PolicyViolation, Workspace, snapshot_repo

GUEST_BREAKER_DIR = "/tmp/breaker"
GUEST_SUITE_DIR = "/tmp/attest_suite"      # verifier files for the repository's own suite run through the supervisor
GUEST_HELDOUT_DIR = "/tmp/attest_heldout"  # verifier files for held-out modules run through the supervisor
MAX_SEAL_ATTEMPTS = 3
MIN_SEALED_TESTS = 5
MIN_MUTANTS_FOR_SCORE = 4
MIN_ADVERSARIAL_WHEN_NO_MUTANTS = 6  # a patch with no mutable sites passes the mutation gate only with a real adversarial suite
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


# Exception types that, raised in the last frame of the test module itself, mean the test body is broken rather than the
# behaviour missing (an unimplemented API raises inside the repository, or AttributeError/NotImplementedError, which are not here).
TEST_INTERNAL_EXCEPTIONS = ("ValueError: too many values to unpack", "ValueError: not enough values to unpack", "NameError:",
                            "UnboundLocalError:", "ZeroDivisionError:", "IndentationError:", "SyntaxError:")


def test_internal_errors(tests: list[dict], module_file: str = f"/{SEALED_FILE}") -> list[str]:
    """Sealed tests whose red failure is an error raised by the test module's own code (traceback's last frame in the test
    file and an exception that cannot come from calling an unimplemented API). Returned as `name: exception` strings."""
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


class Pipeline:
    def __init__(self, task: TaskSpec, provider, executor, ledger: Ledger, out_dir: Path, max_turns: int = 12,
                 max_mutants: int = 12, mutation_threshold: float = 0.5, mutant_workers: int = 8,
                 drift_threshold: float = 0.6, tavily=None, profile_label: str = "development", progress=None,
                 arbitrate: bool = True, arbitration_apply: bool = False, run_id: str | None = None):
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
        self.started_at = utcnow()
        self.bundle: dict = {
            "run_id": self.run_id, "started_at_utc": self.started_at, "finished_at_utc": None,
            "profile": {"label": profile_label, "provider": provider.describe(), "executor": executor.describe()},
            "provenance": None, "task": None, "execution": {}, "spec": None, "grounding": None, "sealed_tests": None, "red_run": None,
            "trajectory": {"turns": 0, "actions": [], "path": "trajectory.jsonl", "finished": False},
            "candidate": {"changed_paths": [], "deleted_paths": [], "scope_ok": None, "violations": [], "diff": "", "sha256": {}},
            "verification": None, "breaker": None, "drift": None, "arbitration": None, "gates": {},
            "verdict": {"verdict": "ERROR", "reasons": [], "warnings": []}, "ledger": None, "limitations": [], "stage": "created"}
        self.bundle["provenance"] = build_provenance(provider.describe(), self.limits(), task.upstream)

    def limits(self) -> dict:
        """Every threshold and limit that shaped this run, recorded in one place (provenance)."""
        return {"max_turns": self.max_turns, "max_mutants": self.max_mutants, "mutation_threshold": self.mutation_threshold,
                "drift_threshold": self.drift_threshold, "mutant_workers": self.mutant_workers, "max_seal_attempts": MAX_SEAL_ATTEMPTS,
                "min_sealed_tests": MIN_SEALED_TESTS, "min_mutants_for_score": MIN_MUTANTS_FOR_SCORE,
                "min_adversarial_when_no_mutants": MIN_ADVERSARIAL_WHEN_NO_MUTANTS, "per_test_timeout_s": min(60, self.task.test_timeout),
                "test_timeout_s": self.task.test_timeout, "checkpoint_timeout_s": self.task.checkpoint_timeout,
                "arbitrate": self.arbitrate, "arbitration_apply": self.arbitration_apply}

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
        path = self.out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (dict, list)):
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        elif isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(str(data), encoding="utf-8")

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
                    "summary_line": f"runner error: {run.runner_error or 'step missing'}", "operation_uuid": run.operation_uuid,
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
            self.log(f"{stage}: malformed answer, one repair retry ({str(error)[:120]})")
            return self.provider.structured(role, prompt + self.REPAIR_SUFFIX.format(problem=str(error)[:160]), schema, f"{stage}-repair")

    # ----------------------------------------------------------------- lifecycle
    def run(self) -> dict:
        try:
            self._run()
        except PipelineAbort as abort:
            self.log(f"ABORT {abort.verdict}: {abort.reason}", "aborted")
            self.bundle["verdict"] = {"verdict": abort.verdict, "reasons": [abort.reason], "warnings": self.bundle["verdict"].get("warnings", [])}
        except ModelError as error:
            self.log(f"MODEL ERROR: {error}", "error")
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [f"model provider: {error}" + (" (outcome uncertain; not retried)" if error.uncertain else "")], "warnings": []}
        except Exception as error:  # noqa: BLE001 - keep the evidence, then re-raise
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [f"{type(error).__name__}: {str(error)[:300]}"], "warnings": []}
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
            self.bundle["verdict"] = {"verdict": "ERROR", "reasons": [f"model provider: {error}"], "warnings": []}
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
            raise PipelineAbort("ERROR", f"checkpoint failed: {checkpoint.runner_error or checkpoint.status}")
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
            "Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then "
            "classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and "
            "re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never "
            "clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.",
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
            raise PipelineAbort("ERROR", f"checkpoint failed: {checkpoint.runner_error or checkpoint.status}")
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
        if not spec["feasible"]:
            raise PipelineAbort("INFEASIBLE", spec.get("infeasibility_reason") or "specification judged the task infeasible")

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
                result = self.ask("seal", seal_prompt(task, spec, snapshot, feedback, sources), SEAL_SCHEMA, f"seal-{attempt}")
            except ModelError as error:
                if not error.uncertain:
                    raise
                feedback = None
                rejected.append({"attempt": attempt, "reason": f"inference outcome uncertain: {error}"})
                self.log(f"seal attempt {attempt} not usable: {str(error)[:160]}")
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
            else:
                sealed_src, sealed_sha, red_summary = candidate_src, sha, summary
                self.raw_results["red"] = red_result
                expected_ids = list(red_result["expected_ids"])
                self.bundle["sealed_tests"] = {"path": f"sealed/{SEALED_FILE}", "sha256": sha, "test_count": summary["ran"],
                                               "declared_test_count": result.json["test_count"], "expected_ids": expected_ids, "escapes_repaired": repaired,
                                               "sealed_at_utc": utcnow(), "author_model": result.call.requested_model,
                                               "attempts": attempt, "rejected_attempts": rejected, "notes": result.json["notes"]}
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
            raise PipelineAbort("NO CHANGE", "the implementer finished without changing any file" if finished else "turn budget exhausted without changes")
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        gates: dict[str, dict] = {}
        reasons: list[str] = []
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
        nonce = new_nonce()
        files = self.guest_files(changed)
        files.update(self.sealed_files(GUEST_SEALED_DIR, "test_sealed", sealed_src))
        verify_steps = self.suite_steps(nonce)
        if not is_supervisor_step(verify_steps[0]):
            raise PipelineAbort("ERROR", "verification order violated: the sealed supervisor must be the first step of the verify branch")
        verify_run = self.executor.run_branch(checkpoint_uuid, files, verify_steps, stage="verify", deletes=deletes,
                                              timeout=task.test_timeout + 60)
        sealed_result, sealed_summary = self.suite_outcome(verify_run, nonce)
        self.raw_results["sealed"] = sealed_result
        binding = bind_verification(sealed_result, expected_ids, sealed_sha, nonce)
        self.log(f"verify: sealed {sealed_summary['summary_line']}; binding {'ok' if binding['ok'] else 'FAILED: ' + '; '.join(binding['reasons'])[:200]}")

        # Stage 7a: the repository's own suite on the candidate, in its own disposable branch after the supervisor.
        existing = self.run_repo_suite("existing", checkpoint_uuid, changed, deletes)
        self.log(f"existing suite ({existing['evidence_class']}): {existing['summary_line']} ({existing['passed']}/{existing['ran']})")
        self.bundle["verification"] = {"operation_uuid": verify_run.operation_uuid, "status": verify_run.status,
                                       "order": list(VERIFICATION_ORDER), "sealed_sha256_injected": sealed_sha,
                                       "expected_ids": expected_ids, "existing": existing, "sealed": sealed_summary,
                                       "binding": binding, "heldout": None}

        if not finished:
            reasons.append(f"implementer did not finish within {self.max_turns} turns")
        if not scope["ok"]:
            reasons.append("scope policy violated: " + "; ".join(scope["violations"]))
        if verify_run.runner_error:
            reasons.append(f"verification run failed: {verify_run.runner_error}")
        if not existing["all_passed"]:
            reasons.append(f"existing test suite failed on the candidate: {existing['summary_line']}")
        reasons.extend(binding["reasons"])
        gates["existing_suite"] = {"ok": existing["all_passed"], "detail": existing["summary_line"], "evidence_class": existing["evidence_class"]}
        gates["sealed_binding"] = {"ok": binding["ok"], "detail": "; ".join(binding["reasons"]) or "all checks pass", "evidence_class": "bound"}
        if existing["evidence_class"] == "stdout":
            warnings.append(f"existing suite evidence is parsed console output ({existing['evidence_note']}); the sealed, mutation and adversarial gates are bound")

        # Stage 7b: held-out tests (for example the upstream PR's own tests), separate branch, GATE when configured.
        if task.heldout_tests:
            try:
                heldout = self.run_repo_suite("heldout", checkpoint_uuid, changed, deletes, heldout=task.heldout_tests, include_existing=False)
            except Exception as error:  # noqa: BLE001 - uncertain spawn: gate fails with the reason, no replay
                heldout = {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False, "module_error": True,
                           "summary_line": f"held-out branch could not be executed: {type(error).__name__}: {str(error)[:160]}",
                           "operation_uuid": None, "evidence_class": (self.bound_plan or {}).get("mode", "stdout"),
                           "evidence_note": "branch did not run", "files": sorted(task.heldout_tests)}
            self.bundle["verification"]["heldout"] = heldout
            failing_ids = [t["id"] for t in heldout["tests"] if t["outcome"] != "ok"]
            gates["heldout_suite"] = {"ok": heldout["all_passed"], "detail": heldout["summary_line"], "failing": failing_ids,
                                      "evidence_class": heldout["evidence_class"]}
            if not heldout["all_passed"]:
                reasons.append(f"held-out tests failed: {heldout['failing']} of {heldout['ran']} ({', '.join(failing_ids)[:300]}); "
                               "resolve the failures or the contract disagreement before this patch can be verified")
            self.log(f"held-out suite ({heldout['evidence_class']}): {heldout['summary_line']} ({heldout['passed']}/{heldout['ran']})", "heldout")
        self.save("verify.json", self.bundle["verification"])

        # Stage 8: breaker pass (mutants + model-written adversarial tests) only when the sealed suite passed.
        if binding["ok"] and existing["all_passed"]:
            self.log("breaker pass", "break")
            breaker = self.breaker_pass(snapshot, changed, deleted, sealed_src, sealed_sha, checkpoint_uuid, spec, diff, expected_ids, sources)
            self.bundle["breaker"] = breaker
            self.save("breaker.json", breaker)
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
                reasons.append(f"mutation gate: no mutable sites were generated on the changed lines and the adversarial suite has only {adversarial_ran} test(s) "
                               f"(fewer than {MIN_ADVERSARIAL_WHEN_NO_MUTANTS}); nothing structural tests this patch, so it cannot be VERIFIED")
            elif evaluated == 0:
                gates["mutation"] = {"ok": False, "detail": f"all {generated} mutants unknown (could not be evaluated)", "evidence_class": "bound"}
                reasons.append(f"mutation gate could not run: all {generated} mutants were unknown (sandbox could not evaluate them); "
                               "a verdict cannot be VERIFIED without a mutation score")
            elif unknown > 0 and evaluated < MIN_MUTANTS_FOR_SCORE:
                gates["mutation"] = {"ok": False, "detail": f"only {evaluated} of {generated} mutants evaluated ({unknown} unknown)", "evidence_class": "bound"}
                reasons.append(f"mutation gate incomplete: only {evaluated} of {generated} mutants could be evaluated "
                               f"({unknown} unknown); too few to score, so the result is not trustworthy")
            elif mutation["score"] < self.mutation_threshold:
                reasons.append(f"mutation score {mutation['score']:.2f} below {self.mutation_threshold:.2f}: {mutation['survived']} of {evaluated} mutants survived the sealed suite")
                gates["mutation"] = {"ok": False, "detail": f"score {mutation['score']}", "evidence_class": "bound"}
            else:
                gates["mutation"] = {"ok": True, "detail": f"score {mutation['score']} on {evaluated} mutants", "evidence_class": "bound"}
                if evaluated < MIN_MUTANTS_FOR_SCORE:
                    warnings.append(f"only {evaluated} mutants evaluated (all killed); mutation score is weak evidence")
                if unknown:
                    warnings.append(f"{unknown} mutant(s) were unknown and excluded from the score")
            if adversarial.get("unusable"):
                gates["adversarial_tests"] = {"ok": False, "detail": adversarial["unusable"][:160], "evidence_class": "bound"}
                reasons.append(f"model-written adversarial tests could not be produced: {adversarial['unusable'][:160]}; rerun the breaker stage or review manually")
            elif adversarial["summary"]["all_passed"] and adversarial["binding"]["ok"]:
                gates["adversarial_tests"] = {"ok": True, "detail": adversarial["summary"]["summary_line"], "evidence_class": "bound"}
            else:
                failing_ids = [t["id"] for t in adversarial["summary"]["tests"] if t["outcome"] != "ok"]
                gates["adversarial_tests"] = {"ok": False, "detail": adversarial["summary"]["summary_line"], "failing": failing_ids, "evidence_class": "bound"}
                if not adversarial["binding"]["ok"]:
                    reasons.append("adversarial suite binding failed: " + "; ".join(adversarial["binding"]["reasons"])[:300])
                reasons.append(f"model-written adversarial tests failed: {adversarial['summary']['failing']} of {adversarial['summary']['ran']} "
                               f"({', '.join(failing_ids)[:300]}); each failure is a bug or a contract disagreement to resolve")
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
                reasons.append(f"drift audit score {score:.2f} ({drift.get('assessment')}): {drift.get('summary', '')[:200]}")
                gates["drift_audit"] = {"ok": False, "detail": f"score {score}", "evidence_class": "model"}
            else:
                gates["drift_audit"] = {"ok": True, "detail": f"score {score} ({drift.get('assessment')})", "evidence_class": "model"}
                if score >= 0.3 or drift.get("scope_widened") or drift.get("unsupported_claims"):
                    warnings.append(f"drift audit: score {score:.2f}, widened {len(drift.get('scope_widened') or [])}, unsupported claims {len(drift.get('unsupported_claims') or [])}")
            self.log(f"drift audit: score {score} ({drift.get('assessment')})")
        except ModelError as error:
            self.bundle["drift"] = {"error": str(error)}
            gates["drift_audit"] = {"ok": False, "detail": f"audit call failed: {error}", "evidence_class": "model"}
            reasons.append(f"drift audit unavailable: {error}")

        self.bundle["gates"] = gates
        verdict = "VERIFIED" if not reasons else "NEEDS HUMAN"
        # The same pure rule `attest check` re-derives offline. Reasons and gates are built side by side; if they ever
        # disagree the run fails closed and records the discrepancy instead of trusting either side.
        derivation = derive(gates, self.bundle["candidate"], binding["ok"])
        if derivation["verdict"] != verdict:
            reasons.append(f"verdict derivation inconsistent: the gates derive {derivation['verdict']} but the recorded reasons give {verdict}; failing closed")
            verdict = "NEEDS HUMAN"

        # Stage 10: arbitration of model-generated test failures. Advisory by default: it classifies each failing sealed
        # or adversarial test as an implementation bug, a test defect or a contract dispute, and for pure test defects it
        # produces a corrected module and re-verifies it (must pass on the candidate and still fail on the base). The
        # original tests, results and reasons are preserved; the verdict only changes when apply mode is explicitly on.
        if verdict == "NEEDS HUMAN" and self.arbitrate:
            arb = self.arbitrate_failures(spec, diff, sealed_src, sealed_sha, expected_ids, checkpoint_uuid,
                                          changed, deleted, gates, binding, sealed_summary, finished, scope["ok"])
            if arb:
                self.bundle["arbitration"] = arb
                self.save("arbitration.json", arb)
                warnings.append(f"arbitration ({'advisory' if not self.arbitration_apply else 'apply'}): {arb['headline']}")
                self.log(f"arbitration: {arb['headline']}", "arbitrate")
                if self.arbitration_apply and arb.get("cleared"):
                    self.bundle["verdict"] = {"verdict": "VERIFIED", "reasons": [], "warnings": warnings,
                                              "superseded_reasons": reasons, "cleared_by_arbitration": True,
                                              "derivation": derive(gates, self.bundle["candidate"], binding["ok"], arb, apply=True)}
                    return
        self.bundle["verdict"] = {"verdict": verdict, "reasons": reasons, "warnings": warnings, "derivation": derivation}

    # ----------------------------------------------------------------- breaker
    def breaker_pass(self, snapshot, changed, deleted, sealed_src, sealed_sha, checkpoint_uuid, spec, diff, expected_ids, sources) -> dict:
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        mutants = generate_mutants(snapshot, changed, max_mutants=self.max_mutants)
        self.log(f"breaker: {len(mutants)} mutants of changed lines; running in parallel branches (workers={self.mutant_workers})")

        def run_mutant(mutant):
            files = {f"{GUEST_REPO}/{rel}": data for rel, data in changed.items()}
            files[f"{GUEST_REPO}/{mutant.path}"] = mutant.source.encode("utf-8")
            files.update(self.sealed_files(GUEST_SEALED_DIR, "test_sealed", sealed_src, canary=False))
            nonce = new_nonce()
            try:
                run = self.executor.run_branch(checkpoint_uuid, files, self.suite_steps(nonce), stage=f"mutant-{mutant.id}",
                                               deletes=deletes, timeout=self.task.test_timeout + 60)
            except Exception as error:  # noqa: BLE001 - an uncertain or failed spawn makes this mutant unknown, never replayed
                return {"id": mutant.id, "path": mutant.path, "lineno": mutant.lineno, "operator": mutant.operator,
                        "description": mutant.description, "status": "unknown", "operation_uuid": None, "failing_methods": 0,
                        "killed_by": [], "error": f"{type(error).__name__}: {str(error)[:200]}"}
            result, summary = self.suite_outcome(run, nonce)
            binding = bind_verification(result, expected_ids, sealed_sha, nonce, canary=False)
            if result is None or not binding["checks"].get("nonce_matches") or not binding["checks"].get("sealed_file_unchanged_after"):
                status = "unknown"
            elif summary["failing"] > 0 or not binding["checks"].get("static_ids_match_red"):
                status = "killed"
            else:
                status = "survived"
            return {"id": mutant.id, "path": mutant.path, "lineno": mutant.lineno, "operator": mutant.operator,
                    "description": mutant.description, "status": status, "operation_uuid": run.operation_uuid,
                    "failing_methods": summary["failing"], "killed_by": [t["id"] for t in summary["tests"] if t["outcome"] != "ok"][:5]}

        results = []
        if mutants:
            with ThreadPoolExecutor(max_workers=max(1, min(self.mutant_workers, len(mutants)))) as pool:
                results = list(pool.map(run_mutant, mutants))
        killed = sum(1 for r in results if r["status"] == "killed")
        survived = sum(1 for r in results if r["status"] == "survived")
        unknown = sum(1 for r in results if r["status"] == "unknown")
        evaluated = killed + survived
        score = round(killed / evaluated, 3) if evaluated else None
        self.log(f"breaker: killed {killed}, survived {survived}, unknown {unknown}, mutation score {score}")
        for mutant in mutants:
            self.save(f"mutants_{mutant.id}.py", mutant.source)
        mutation = {"generated": len(mutants), "evaluated": evaluated, "killed": killed, "survived": survived, "unknown": unknown,
                    "score": score, "threshold": self.mutation_threshold, "mutants": results}

        # Model-written adversarial tests, run through the same supervisor in their own directory (one feedback retry).
        adversarial: dict = {}
        try:
            feedback = None
            src = None
            host_ids: list[str] = []
            authored = None
            for attempt in (1, 2):
                authored = self.ask("break", breaker_prompt(self.task, spec, diff, [i.split(".")[-1] for i in expected_ids], sources, feedback,
                                                           per_test_timeout=min(60, self.task.test_timeout)),
                                    BREAKER_SCHEMA, f"break-tests-{attempt}")
                self.save(f"breaker_response.attempt{attempt}.json", {"json": authored.json, "text_head": (authored.text or "")[:4000]})
                candidate, repaired = repair_escapes(authored.json.get("test_file") or "")
                self.save(f"breaker_tests.attempt{attempt}.py", candidate)
                try:
                    compile(candidate, "test_breaker.py", "exec")
                    ids = static_test_ids(candidate, "test_breaker") if "unittest" in candidate else []
                except SyntaxError as error:
                    feedback = f"the module has a syntax error: {error}"
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
                adversarial = {"unusable": feedback or "no module produced",
                               "summary": {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False, "summary_line": "no usable adversarial module after 2 attempts"},
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
                    raise ModelError(f"adversarial branch could not be executed: {type(error).__name__}: {str(error)[:160]}") from None
                result, summary = self.suite_outcome(run, nonce, "breaker")
                self.raw_results["adversarial"] = result
                binding = bind_verification(result, host_ids, sha256_text(src), nonce)
                adversarial = {"sha256": sha256_text(src), "author_model": authored.call.requested_model,
                               "expected_ids": host_ids, "summary": summary, "binding": binding, "notes": authored.json.get("notes", ""),
                               "operation_uuid": run.operation_uuid}
                self.log(f"breaker tests: {summary['summary_line']}; binding {'ok' if binding['ok'] else 'FAILED'}")
        except ModelError as error:
            adversarial = {"unusable": f"adversarial test authoring failed: {error}",
                           "summary": {"ran": 0, "tests": [], "passed": 0, "failing": 0, "all_passed": False, "summary_line": f"authoring failed: {str(error)[:120]}"},
                           "binding": {"ok": False, "checks": {}, "reasons": [str(error)]}}
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
        if "sealed_binding" in failed:
            # A plain test failure legitimately makes the child exit 1, so a nonzero exit alongside a FAIL/ERROR outcome is
            # NOT tampering. Only the integrity signals (nonce, digest, isolation, signal, timeout, missing/forged, discovery,
            # id set) block arbitration; those are still caught by no_signal, no_timeout, no_missing_or_forged_result, etc.
            benign = {"all_expected_pass", "no_nonzero_exit"}
            structural = [k for k, v in binding.get("checks", {}).items() if not v and k not in benign]
            if structural:  # tamper, forgery, crash, timeout or lost isolation is never a "test defect"
                return None
        modules = []
        if "sealed_binding" in failed:
            sealed_fail = [t for t in sealed_summary.get("tests", []) if t["outcome"] in ("FAIL", "ERROR")]
            if sealed_fail:
                modules.append(("sealed", "test_sealed", GUEST_SEALED_DIR, sealed_src, sealed_fail, True))
        adversarial = (self.bundle.get("breaker") or {}).get("adversarial") or {}
        if "adversarial_tests" in failed and not adversarial.get("unusable"):
            adv_fail = [t for t in (adversarial.get("summary") or {}).get("tests", []) if t["outcome"] != "ok"]
            adv_src = None
            adv_path = self.out_dir / "breaker_tests.py"
            if adv_path.is_file():
                adv_src = adv_path.read_text(encoding="utf-8")
            if adv_fail and adv_src:
                # base_check=True since 17 Oct 2026: a corrected adversarial module must also still fail on the unmodified
                # base, so the record shows the corrected tests discriminate (they are not satisfied by the stub)
                modules.append(("adversarial", "test_breaker", GUEST_BREAKER_DIR, adv_src, adv_fail, True))
        if not modules:
            return None
        self.log("arbitration: classifying model-generated test failures", "arbitrate")
        results = []
        for label, module_name, guest_dir, module_src, failing, base_check in modules:
            results.append(self.arbitrate_module(label, module_name, guest_dir, module_src, failing, spec, diff,
                                                 checkpoint_uuid, changed, deleted, base_check))
        every_class = [c for r in results for c in r["classifications"]]
        counts = {k: sum(1 for c in every_class if c["classification"] == k)
                  for k in ("implementation_bug", "test_defect", "contract_dispute")}
        # Clearing is only sound when the mutation gate actually ran and passed on a passing suite. If the sealed suite
        # itself failed, the breaker was skipped, so there is no mutation score and arbitration stays advisory only.
        mutation_ran_ok = gates.get("mutation", {}).get("ok") and not gates.get("mutation", {}).get("skipped")
        cleared = bool(results) and mutation_ran_ok and all(r.get("cleared_module") for r in results)
        all_corrected = bool(results) and all(r.get("cleared_module") for r in results)
        if cleared:
            headline = (f"all {counts['test_defect']} failing generated test(s) classified as test defects; corrected tests "
                        "pass on the candidate and still fail on the base — candidate not falsified by these tests")
        elif all_corrected:
            headline = (f"all {counts['test_defect']} failing generated test(s) classified as test defects; corrected tests pass on the "
                        "candidate and still fail on the base, but the sealed failure skipped the mutation check, so there is no mutation score "
                        "and the verdict is not cleared; a rerun seals fresh tests")
        elif counts["implementation_bug"]:
            headline = f"{counts['implementation_bug']} failing test(s) indicate a real implementation bug; human review required"
        elif counts["contract_dispute"]:
            headline = f"{counts['contract_dispute']} failing test(s) are contract disputes; a human must decide"
        else:
            headline = "generated-test failures could not be cleared by arbitration; human review required"
        return {"applied": self.arbitration_apply, "cleared": cleared, "all_corrected": all_corrected, "mutation_ran_ok": bool(mutation_ran_ok),
                "counts": counts, "headline": headline,
                "modules": results, "note": "original tests, results and reasons are preserved unchanged; arbitration is "
                "advisory unless apply mode is on, and never flips an implementation bug or contract dispute"}

    def arbitrate_module(self, label, module_name, guest_dir, module_src, failing, spec, diff, checkpoint_uuid,
                         changed, deleted, base_check) -> dict:
        record = {"module": label, "classifications": [], "corrected_notes": "", "corrected_module": None,
                  "candidate_rerun": None, "base_rerun": None, "cleared_module": False, "error": None}
        try:
            answer = self.ask("arbitrate", arbitrate_prompt(self.task, spec, diff, module_src, module_name, failing),
                              ARBITRATION_SCHEMA, f"arbitrate-{label}").json
        except ModelError as error:
            record["error"] = f"arbiter call failed: {error}"
            return record
        record["classifications"] = answer.get("classifications") or []
        record["corrected_notes"] = answer.get("corrected_notes", "")
        all_defect = bool(record["classifications"]) and all(c["classification"] == "test_defect" for c in record["classifications"])
        corrected, _ = repair_escapes(answer.get("corrected_module") or "")
        if not (all_defect and corrected.strip()):
            return record  # a real bug or a dispute, or no correction offered: nothing to re-verify
        try:
            compile(corrected, f"{module_name}.py", "exec")
            corrected_ids = static_test_ids(corrected, module_name)
        except SyntaxError as error:
            record["error"] = f"corrected module has a syntax error: {error}"
            return record
        if len(corrected_ids) < 1:
            record["error"] = "corrected module exposed no tests"
            return record
        record["corrected_module"] = f"arbitration/{label}_corrected.py"
        self.save(f"arbitration/{label}_corrected.py", corrected)
        corrected_sha = sha256_text(corrected)
        deletes = [f"{GUEST_REPO}/{rel}" for rel in deleted]
        # Re-run the corrected tests on the CANDIDATE: a genuine test defect, once corrected, must pass.
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
            record["error"] = f"candidate re-run failed: {type(error).__name__}: {str(error)[:160]}"
            return record
        base_ok = True
        if base_check:
            # The corrected tests must STILL fail on the unmodified base, or they no longer discriminate (anti-abuse).
            nonce_b = new_nonce()
            try:
                run_b = self.executor.run_branch(checkpoint_uuid, self.sealed_files(guest_dir, module_name, corrected),
                                                 self.suite_steps(nonce_b, module_name, guest_dir, "arbbase"),
                                                 stage=f"arbitrate-{label}-base", timeout=self.task.test_timeout + 60)
                _, summary_b = self.suite_outcome(run_b, nonce_b, "arbbase")
                record["base_rerun"] = {"summary_line": summary_b["summary_line"], "failing": summary_b["failing"],
                                        "operation_uuid": run_b.operation_uuid}
                base_ok = summary_b["failing"] > 0  # must still fail on base
            except Exception as error:  # noqa: BLE001
                record["error"] = f"base re-run failed: {type(error).__name__}: {str(error)[:160]}"
                return record
        record["cleared_module"] = bool(candidate_ok and base_ok)
        return record

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
                    return f"sandbox run failed: {run.runner_error}"
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
