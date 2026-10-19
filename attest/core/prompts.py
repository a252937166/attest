"""Prompts and JSON schemas for the specification, sealing and implementation stages."""

from __future__ import annotations

import json

SPEC_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "feasible": {"type": "boolean"},
        "infeasibility_reason": {"type": ["string", "null"]},
        "restated_task": {"type": "string"},
        "interface_contract": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": False,
                      "properties": {"name": {"type": "string"}, "signature": {"type": "string"},
                                     "behavior": {"type": "string"}, "error_cases": {"type": "array", "items": {"type": "string"}}},
                      "required": ["name", "signature", "behavior", "error_cases"]}},
        "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
        "external_references_needed": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["feasible", "infeasibility_reason", "restated_task", "interface_contract", "acceptance_criteria", "out_of_scope",
                 "external_references_needed"],
}

DRIFT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "drift_score": {"type": "number"},
        "assessment": {"type": "string", "enum": ["aligned", "narrowed", "widened", "off_target"]},
        "scope_narrowed": {"type": "array", "items": {"type": "string"}},
        "scope_widened": {"type": "array", "items": {"type": "string"}},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["drift_score", "assessment", "scope_narrowed", "scope_widened", "unsupported_claims", "summary"],
}

SEAL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "test_file": {"type": "string"}, "test_count": {"type": "integer"}, "notes": {"type": "string"},
        # which test methods cover which acceptance criterion (1-based index into the contract's list); the pipeline checks
        # that every criterion is claimed by at least one existing test method and records the gaps
        "coverage": {"type": "array",
                     "items": {"type": "object", "additionalProperties": False,
                               "properties": {"criterion": {"type": "integer"}, "tests": {"type": "array", "items": {"type": "string"}}},
                               "required": ["criterion", "tests"]}},
    },
    "required": ["test_file", "test_count", "notes", "coverage"],
}
BREAKER_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"test_file": {"type": "string"}, "test_count": {"type": "integer"}, "notes": {"type": "string"}},
    "required": ["test_file", "test_count", "notes"],
}

# Contract audit (19 Oct 2026): a model looks for requirements that no implementation confined to the write scope can
# satisfy, and must back every claim with a WITNESS PROGRAM that is executed on the unmodified repository. A claim without a
# demonstrating witness is recorded as a suspicion, never as a verdict.
CONTRACT_AUDIT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "consistent": {"type": "boolean"},
        "conflicts": {"type": "array",
                      "items": {"type": "object", "additionalProperties": False,
                                "properties": {"requirement_ids": {"type": "array", "items": {"type": "string"}},
                                               "summary": {"type": "string"},
                                               "witness": {"type": "string"}},
                                "required": ["requirement_ids", "summary", "witness"]}},
        "notes": {"type": "string"},
    },
    "required": ["consistent", "conflicts", "notes"],
}
WITNESS_MARKER = "CONTRADICTION"
WITNESS_EXIT_CODE = 3

ARBITRATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "classifications": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": False,
                      "properties": {"test_id": {"type": "string"},
                                     "classification": {"type": "string", "enum": ["implementation_bug", "test_defect", "contract_dispute"]},
                                     "defect_kind": {"type": ["string", "null"],
                                                     "enum": ["wrong_expectation", "unspecified_behavior", "excessive_workload",
                                                              "python_incompatibility", "other", None]},
                                     "rationale": {"type": "string"}, "contract_basis": {"type": "string"}},
                      # strict structured output (the gateway and Token Factory) requires every property to be listed as
                      # required; optional fields are expressed as nullable, never by omission from `required`
                      "required": ["test_id", "classification", "defect_kind", "rationale", "contract_basis"]}},
        "corrected_module": {"type": ["string", "null"]},
        "corrected_notes": {"type": "string"},
    },
    "required": ["classifications", "corrected_module", "corrected_notes"],
}

ACTIONS = ["list_files", "read_file", "search", "replace_in_file", "write_file", "run_tests", "run_python", "undo", "finish"]
ACTION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "action": {"type": "string", "enum": ACTIONS},
        "path": {"type": ["string", "null"]},
        "content": {"type": ["string", "null"]},
        "find": {"type": ["string", "null"]},
        "replace": {"type": ["string", "null"]},
        "start_line": {"type": ["integer", "null"]},
        "end_line": {"type": ["integer", "null"]},
        "code": {"type": ["string", "null"]},
        "reason": {"type": "string"},
        "summary": {"type": ["string", "null"]},
    },
    "required": ["action", "path", "content", "find", "replace", "start_line", "end_line", "code", "reason", "summary"],
}


def _tree(files: dict[str, bytes]) -> str:
    return "\n".join(f"- {path} ({len(data)} bytes)" for path, data in sorted(files.items()))


def _outline(source: bytes, limit: int = 80) -> list[str]:
    """`def` and `class` lines of a Python source with their line numbers (a map for navigating a long file)."""
    lines = []
    for number, raw in enumerate(source.decode("utf-8", "replace").splitlines(), 1):
        stripped = raw.lstrip()
        if stripped.startswith(("def ", "class ", "async def ")):
            lines.append(f"{number}: {raw.rstrip()[:110]}")
            if len(lines) >= limit:
                lines.append("... (outline truncated)")
                break
    return lines


def _tree_with_outlines(files: dict[str, bytes], focus: list[str] | None, budget: int = 6_000) -> str:
    """The tree, plus a def/class outline (with line numbers) for the Python files the task may change, so the implementer
    can jump to a symbol instead of paging through a long file."""
    parts = [_tree(files)]
    used = 0
    for path, data in sorted(files.items()):
        if not path.endswith(".py") or not _focused(path, focus or ["**"]):
            continue
        outline = _outline(data)
        if not outline:
            continue
        block = f"\nOUTLINE OF {path} ({len(data.decode('utf-8', 'replace').splitlines())} lines; line: definition):\n" + "\n".join(outline)
        if used + len(block) > budget:
            parts.append(f"\n(outline of {path} omitted: prompt size budget; use search to locate symbols)")
            continue
        used += len(block)
        parts.append(block)
    return "\n".join(parts)


def _focused(path: str, patterns: list[str]) -> bool:
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern) or (pattern.endswith("/**") and path.startswith(pattern[:-3] + "/")):
            return True
    return False


def _dump_files(files: dict[str, bytes], focus: list[str] | None = None, limit: int = 40_000, excerpt: int = 1_200,
                total: int = 90_000) -> str:
    """Full text for files the task may change (focus), short excerpts for the rest, bounded overall."""
    parts = []
    used = 0
    ordered = sorted(files.items(), key=lambda kv: (not _focused(kv[0], focus or ["**"]), kv[0]))
    for path, data in ordered:
        text = data.decode("utf-8", "replace")
        cap = limit if _focused(path, focus or ["**"]) else excerpt
        if len(text) > cap:
            text = text[:cap] + f"\n...[{len(text) - cap} more chars not shown]..."
        if used + len(text) > total:
            parts.append(f"### {path}\n(omitted: prompt size budget reached)")
            continue
        used += len(text)
        parts.append(f"### {path}\n```\n{text}\n```")
    return "\n\n".join(parts)


def spec_prompt(task, snapshot: dict[str, bytes]) -> str:
    return f"""You are the SPECIFICATION stage of Attest, an evidence-gated coding agent.
Your output is a contract that an independent test author and an independent implementer will both follow.
Do not write implementation code. Be precise, testable and complete; resolve ambiguities explicitly.

TASK TITLE: {task.title}

TASK STATEMENT:
{task.statement}

ACCEPTANCE CRITERIA GIVEN BY THE REQUESTER:
{json.dumps(task.acceptance_criteria, indent=2)}

IMPORT HINT: {task.import_hint or "(none)"}

REPOSITORY TREE:
{_tree(snapshot)}

REPOSITORY FILES (full text for files the implementer may change, excerpts for the rest):
{_dump_files(snapshot, task.allowed_write_globs)}

Produce JSON with:
- feasible: false only if the task contradicts the code base or cannot be verified by tests; then give infeasibility_reason.
- restated_task: one paragraph in your own words.
- interface_contract: every public function or class the task touches, with exact signature, behavior and error_cases (exception type + condition).
- acceptance_criteria: numbered, independently testable statements covering normal cases, edge cases and errors. Keep existing behavior that must be preserved as explicit criteria.
- out_of_scope: what the implementer must not change.
- external_references_needed: search queries for live documentation of third-party libraries, APIs or standards the task
  depends on (for example a changed SDK signature). Empty when the task only concerns code in this repository.
"""


def numbered_criteria(criteria: list[str], prefix: str = "AC") -> str:
    return "\n".join(f"{prefix}{i}: {text}" for i, text in enumerate(criteria, 1)) or "(none)"


WITNESS_INPUT_DOMAIN = ("the input domain of a witness is the set of values the task names or implies: literals of the built-in types the "
                        "task's statement and criteria use (plain str, int, list, dict, bytes, None and so on) and values computed from them "
                        "by the unchanged repository code; instances of subclasses of built-in types, objects with overridden special methods "
                        "and other adversarial values are OUTSIDE the domain unless the task names them explicitly")


def contract_audit_prompt(task, spec: dict, snapshot: dict[str, bytes]) -> str:
    """Ask for requirement conflicts that no implementation within the write scope can resolve, each backed by a witness program."""
    lead = ""
    if not spec.get("feasible", True):
        lead = (f"\nTHE SPECIFICATION STAGE ALREADY JUDGED THE TASK INFEASIBLE, SAYING: {spec.get('infeasibility_reason')}\n"
                "Treat that as a claim to test, not as a fact: either demonstrate it with a witness or report that it could not be demonstrated.\n")
    return f"""You are the CONTRACT AUDITOR of Attest. Before any code is written, you check whether the frozen contract below can be
satisfied at all by an implementation that may change only the files in the write scope. A contract is unsatisfiable when two
of its requirements cannot both hold for some concrete input, or when a requirement conflicts with code outside the write scope
(or code the contract says must stay unchanged). Typical cases: a round trip through an unchanged inverse function that cannot
represent every input; two acceptance criteria that demand different outputs for the same input; an error case that contradicts
a normal case; a requirement that a fixed caller makes impossible.
{lead}
TASK STATEMENT (authoritative, written by the requester):
{task.statement}

AUTHORITATIVE TASK CRITERIA (the requester's own acceptance criteria, referenced by id TCn):
{numbered_criteria(task.acceptance_criteria, "TC")}

RESTATED TASK (derived by the specification stage, a model):
{spec["restated_task"]}

INTERFACE CONTRACT (derived):
{json.dumps(spec["interface_contract"], indent=2)}

DERIVED ACCEPTANCE CRITERIA (written by the specification stage, referenced by id ACn):
{numbered_criteria(spec["acceptance_criteria"])}

OUT OF SCOPE (must not change): {json.dumps(spec.get("out_of_scope") or [])}
WRITE SCOPE (the only files an implementation may change): {json.dumps(task.allowed_write_globs)}
IMPORT HINT: {task.import_hint or "(none)"}

REPOSITORY BEFORE ANY CHANGE (full text for files in the write scope, excerpts for the rest):
{_dump_files(snapshot, task.allowed_write_globs)}

PROVENANCE RULE. Name the requirements a conflict rests on by id. Only a conflict whose every requirement is an AUTHORITATIVE
task criterion (TC ids) can end the run as infeasible; a conflict that involves a derived criterion (AC ids), or mixes both, is
recorded and HELD FOR A HUMAN, because a model's restatement cannot establish that the requester's task is impossible. Do not
restate a TC as an AC to make a conflict look authoritative: cite the TC.

INPUT DOMAIN RULE. {WITNESS_INPUT_DOMAIN}. A witness that needs a value outside the domain demonstrates nothing about the task.

For EVERY conflict you report you must supply a WITNESS PROGRAM, because a claim without an executed demonstration is recorded
as a suspicion and does not stop the run. The witness is a standalone Python 3.12 program (standard library only, no network,
no file writes, under 20 seconds) that will be executed in the repository root of the UNMODIFIED repository (the write-scope
files are still in their original state, so a function to be implemented may be a stub or missing: do not call it). It must:
- be CONSTRAINED: it may not define any function, class or lambda, may not create types with type(name, bases, dict), may not
  use exec, eval, compile or __import__; it may only import the standard library and the repository's unchanged modules, build
  values of the input domain, call the unchanged code and compare. In particular it must not implement its own version of the
  function the task asks for and treat that version's output as "required": a required value must follow from a criterion's
  stated rule or example (a literal the criterion states, or the unchanged inverse/reference function the criterion names);
- compute something from the fixed code or the contract itself (for example call the unchanged inverse function on candidate
  outputs, enumerate every possible output up to a stated bound, or evaluate the two criteria on the same concrete input) that
  shows the requirements cannot all hold for a concrete input it names;
- print exactly one line starting with `{WITNESS_MARKER} <requirement ids>: <one-sentence explanation naming the input>` and exit
  with code {WITNESS_EXIT_CODE} when the conflict is demonstrated; print `NOT DEMONSTRATED: <reason>` and exit with code 0 when
  it could not demonstrate it (an exit code other than 0 or {WITNESS_EXIT_CODE}, or a traceback, counts as a broken witness);
- never fake the demonstration: the printed line must follow from the computation (an exhaustive bounded search must state its
  bound; a direct evaluation must show both values).
Report at most 3 conflicts. If the contract is consistent, return consistent=true and an empty conflicts list.
Return JSON: consistent, conflicts (requirement_ids, summary, witness = the complete program source), notes (one or two sentences).
"""


def seal_prompt(task, spec: dict, snapshot: dict[str, bytes], feedback: str | None, sources: str = "", audit_hint: str = "") -> str:
    feedback_block = f"\nPREVIOUS ATTEMPT WAS REJECTED. REASON: {feedback}\nFix that problem in this attempt.\n" if feedback else ""
    feedback_block += ("\n" + sources + "\n") if sources else ""
    feedback_block += ("\n" + audit_hint + "\n") if audit_hint else ""
    return f"""You are an INDEPENDENT ACCEPTANCE TEST AUTHOR for Attest. You have not seen and will not see the implementation.
You have NO filesystem and NO tools: do not try to create or edit files; return the complete module source as the JSON string `test_file`.
Write the sealed acceptance tests that decide whether an implementation of the contract below is correct.
The implementer never sees these tests; they are run on the unmodified code first (they must fail there) and on the candidate afterwards.

CONTRACT (restated task):
{spec["restated_task"]}

INTERFACE CONTRACT:
{json.dumps(spec["interface_contract"], indent=2)}

ACCEPTANCE CRITERIA (referenced by id in your coverage map):
{numbered_criteria(spec["acceptance_criteria"])}

IMPORT HINT: {task.import_hint or "(none)"}
{feedback_block}
READ-ONLY VIEW OF THE CURRENT REPOSITORY (before any change; full text for the files under change, excerpts for the rest):
{_dump_files(snapshot, task.allowed_write_globs)}

Rules for the test module:
0. Python 3.12 only: exceptions have no `.message` attribute (use `str(cm.exception)`), use `assertRaises(...) as cm`, never
   `assertRaisesRegexp`; do not run doctests or inspect the code under test's source; each test must call the public API directly.
1. Python standard library only; a single module that must be importable as `import test_sealed`; use unittest.TestCase classes.
2. Import the public API exactly as the import hint and contract describe. Do not import private names.
3. One behavior per test method, with descriptive names. Cover EVERY acceptance criterion, including error cases (use assertRaises with the exact exception type).
   Assert the exception TYPE only: never assert on exception message text (no assertIn/assertEqual on str(cm.exception)) unless an
   acceptance criterion quotes the exact message, because messages are implementation wording, not behaviour.
   For a criterion that relates two operations (a round trip, an inverse, consistency between functions), test it on inputs that
   stress the relation, in particular inputs containing the characters or values the other operation treats specially, not only
   on friendly inputs.
4. Include at least 10 tests. Tests for behavior that is not implemented yet must fail on the current code.
5. Do not depend on the file system, network, randomness, or the current time. No print statements.
6. Do not include an `if __name__ == "__main__"` block; the runner handles execution.
Return JSON: test_file (the full module source), test_count, notes (one line on coverage decisions), coverage (one entry per
acceptance criterion: its number and the test method names that check it; a criterion with no test is a gap you must close).
"""


def implement_prompt(task, spec: dict, workspace, transcript: list[dict], turn: int, max_turns: int, sources: str = "") -> str:
    history = []
    recent = transcript[-8:]
    for index, entry in enumerate(recent):
        observation = entry["observation"]
        cap = 24_000 if index == len(recent) - 1 else 1_500
        if len(observation) > cap:
            observation = observation[:cap] + f"\n...[{len(observation) - cap} more chars; re-read if needed]..."
        history.append(f"TURN {entry['turn']} ACTION: {json.dumps(entry['action'])}\nOBSERVATION:\n{observation}")
    older = len(transcript) - 8
    prefix = f"({older} earlier turns omitted: {', '.join(e['action']['action'] for e in transcript[:older])})\n" if older > 0 else ""
    remaining = max_turns - turn
    nudge = ""
    if remaining <= 3:
        nudge = (f"\nBUDGET WARNING: only {remaining} turn(s) remain. If the code is written, run the existing tests once and "
                 "then finish; do not start new exploration.\n")
    reads_in_a_row = 0
    for entry in reversed(transcript):
        if entry["action"]["action"] in ("read_file", "list_files", "search"):
            reads_in_a_row += 1
        else:
            break
    if reads_in_a_row >= 3:
        nudge += (f"\nNAVIGATION WARNING: your last {reads_in_a_row} turns only read or searched and changed nothing. Use `search` with the "
                  "symbol name to get its exact line, read that range once, then edit with replace_in_file. Do not page through a file.\n")
    return f"""You are the IMPLEMENTER stage of Attest. You change the repository so that it satisfies the contract.
Hidden acceptance tests written by an independent author will be run on your final code; you cannot see them, so implement the whole contract faithfully, including error cases.
You act through ONE JSON action per turn. Turn {turn} of {max_turns}. Finish early when done.{nudge}

RESTATED TASK:
{spec["restated_task"]}

INTERFACE CONTRACT:
{json.dumps(spec["interface_contract"], indent=2)}

ACCEPTANCE CRITERIA:
{json.dumps(spec["acceptance_criteria"], indent=2)}

OUT OF SCOPE (do not change): {json.dumps(spec["out_of_scope"])}
{sources}
WRITE SCOPE: only files matching {task.allowed_write_globs}; files matching {task.protected_globs} are protected and any attempt is rejected.
REPOSITORY TREE (current workspace), with a def/class outline of the files you may change:
{_tree_with_outlines(workspace.files, task.allowed_write_globs)}

ACTIONS (set unused fields to null):
- list_files: show the tree.
- read_file: path (+ optional start_line/end_line) -> file content with line numbers of the range. Large files are truncated; read ranges.
- search: find (a symbol name or a literal snippet, matched exactly; prefix it with `re:` for a regular expression, which runs under a 2-second limit) + optional path (null = the whole tree) -> every matching line with its file and line number. USE THIS TO LOCATE A FUNCTION OR CLASS; it costs one turn and replaces paging through a file.
- replace_in_file: path + find + replace. PREFERRED WAY TO EDIT. `find` must be an exact, unique snippet of the current file (copy it verbatim, including indentation); it is replaced once by `replace`.
- write_file: path + content for NEW files or complete rewrites of small files (content must be the COMPLETE file).
- run_tests: runs the repository's existing test suite in a throwaway sandbox branch with your current changes.
- run_python: code -> runs a Python snippet in a throwaway sandbox branch with your current changes (cwd is the repository root). File changes made by the snippet are DISCARDED; only replace_in_file and write_file change the repository.
- undo: revert your most recent write_file or replace_in_file (use this to roll back an edit that broke the file instead of patching over it).
- finish: summary -> ends implementation; your current workspace becomes the candidate patch.
Every action needs a one-sentence reason. Edit first, then verify; do not spend turns re-reading what you already saw.
Locate before you read: the outline above and `search` give you the line of any symbol, so one ranged read_file is enough.
After you write or replace code it is syntax-checked immediately and any error is reported to you; fix or `undo` it before moving on.
Before you `finish`, run the existing test suite at least once after your last edit; a finish while there are untested edits is sent back to you once with a reminder.

{prefix}{chr(10).join(history) if history else "(no previous turns)"}

Return the next action as JSON.
"""


def breaker_prompt(task, spec: dict, diff: str, sealed_test_names: list[str], sources: str = "", feedback: str | None = None,
                   per_test_timeout: int = 60) -> str:
    feedback_block = f"\nYOUR PREVIOUS ANSWER WAS REJECTED: {feedback}\nReturn the complete module source text inside the JSON field this time.\n" if feedback else ""
    return f"""{feedback_block}You are the BREAKER stage of Attest. You have NO filesystem and NO tools: do not try to create, open or edit any file;
put the complete Python source of the test module into the JSON field `test_file` as a string. A candidate patch has passed its sealed acceptance tests. Your job is to try to
falsify it: write additional adversarial tests that a correct implementation of the contract must pass but a sloppy one
would fail. Think about boundaries, empty and extreme inputs, type edge cases, error paths, invariants that must hold,
interactions with existing behavior, and anything the sealed tests (names below) did not obviously cover. For a requirement
that relates two operations (a round trip, an inverse, consistency between functions) include inputs that stress the relation,
in particular inputs containing the characters or values the other operation treats specially.

RESTATED TASK:
{spec["restated_task"]}

INTERFACE CONTRACT:
{json.dumps(spec["interface_contract"], indent=2)}

ACCEPTANCE CRITERIA:
{json.dumps(spec["acceptance_criteria"], indent=2)}

IMPORT HINT: {task.import_hint or "(none)"}
{sources}
SEALED TEST NAMES ALREADY COVERED (do not duplicate them):
{json.dumps(sealed_test_names, indent=2)}

CANDIDATE DIFF:
```diff
{diff[:30000]}
```

Rules: Python 3.12 standard library only (exceptions have no `.message`; use `str(cm.exception)`); a single module importable as
`import test_breaker`; unittest.TestCase classes; at least 6 and at most 20 tests; every test must call the public API directly
and follow from the contract above (a failure must mean a bug or a contract disagreement, never a preference); do not run
doctests, parse source code or depend on the file system, network, randomness or time; no print statements; no `__main__` block.
Scope rules: test only behaviour the contract states. Where the contract says a behaviour is unspecified, out of scope or
not required, do not test it. Assert exception types, never exception message text, unless the contract quotes the exact
message. Test by value: never use subclasses or wrapper objects that override operators, comparisons
or other dunder methods to sabotage the implementation; such tests check implementation strategy, not the contract.
Workload budget: each test runs alone in its own process on a small sandbox VM with a hard limit of {per_test_timeout} seconds;
keep every test's work small (at most a few hundred cases per test, inputs under about 10,000 characters, no sleeps or
busy loops). A test that exceeds the budget is recorded as a failure of the test, not as a finding against the candidate.
Return JSON: test_file, test_count, notes (one line on what you targeted).
"""


def arbitrate_prompt(task, spec: dict, diff: str, module_source: str, module_name: str, failing: list[dict]) -> str:
    """Independent arbitration of generated tests that failed on a candidate that passed every structural check."""
    def _failure_text(f: dict) -> str:
        text = (f.get("failure_tail") or f.get("captured_tail") or "(no captured output)")[:1500]
        if f.get("outcome") == "TIMEOUT" or f.get("timed_out"):
            text = (f"TIMEOUT: the test did not finish within the per-test budget ({f.get('duration_s') or '?'} s elapsed) and was killed. "
                    "No assertion failed.\n" + text)
        return text

    failing_block = "\n\n".join(f"FAILING TEST `{f.get('id')}` (outcome {f.get('outcome')}):\n{_failure_text(f)}" for f in failing)
    return f"""You are the ARBITER of Attest. A candidate patch passed every structural check (it compiled, the existing suite
and the held-out suite passed, the sealed file was untampered, mutation and drift gates passed) but one or more
MODEL-GENERATED tests failed on it. Model-generated tests are sometimes wrong. Your job is to decide, for each failing
test, whether the failure means a real defect in the candidate or a defect in the test itself. Be impartial: do not favor
the candidate, and do not favor the test. Judge only against the contract below.

Classify each failing test as exactly one of:
- implementation_bug: the test correctly encodes the contract and the candidate genuinely violates it. The candidate is wrong.
- test_defect: the test is wrong or impossible in Python 3.12 (for example `exception.message`, a nonexistent attribute,
  a doctest/inspection of source, an assertion on exact wording or documentation the contract never required), or it checks
  behavior the contract does not specify as a hard requirement. The candidate is not shown to be wrong by this test.
- contract_dispute: the test checks a plausible behavior that the contract neither requires nor forbids; reasonable people
  could disagree. This needs a human decision.

Classification guidance:
- A test whose expected value is arithmetically or logically wrong under the contract is a test_defect (defect_kind
  wrong_expectation); the correction fixes the expectation from the contract, never from the candidate's output.
- A test that depends on behavior the contract marks unspecified, out of scope or not required, or that drives the
  implementation through subclasses or wrapper objects with overridden operators, comparisons or other dunder methods, tests
  implementation strategy rather than the contract: test_defect with defect_kind unspecified_behavior, unless the contract
  explicitly requires that behavior (then implementation_bug) or is genuinely silent on a behavior a requester would plausibly
  require (then contract_dispute).
- A TIMEOUT outcome means the test did not finish within its budget; no assertion failed. If the oracle is correct and only
  the amount of work is excessive, classify test_defect with defect_kind excessive_workload and reduce the workload in the
  correction while keeping the oracle. If the timeout plausibly comes from the candidate (an infinite loop on a valid input),
  classify implementation_bug and say which input.
- Python 3.12 incompatibilities in the test itself are test_defect with defect_kind python_incompatibility.
Set defect_kind to null for implementation_bug and contract_dispute (the field is always present).

Then, ONLY IF every failing test is a test_defect, return `corrected_module`: the COMPLETE corrected Python source of the
test module (importable as `import {module_name}`, unittest.TestCase classes, Python 3.12 standard library only, no
`__main__` block, no doctests, no source inspection). Fix each defective test so it faithfully encodes the contract (keep
the tests that were already fine unchanged). If any test is an implementation_bug or a contract_dispute, set
`corrected_module` to null — do not try to make a buggy candidate pass. Never change a test's expected values just to match
the candidate's output; a corrected test must still follow from the contract and must still fail on an unimplemented version.
Return exactly one classification per failing test, using the test ids exactly as given above (no other tests, no duplicates);
an answer whose classifications do not cover exactly the failing tests is rejected. The correction is checked mechanically
before it counts: it must keep every test method (same class and method names, none added or removed), change only the
BODIES of the methods that failed (new import statements may be added, but no existing import, class base, decorator, method
signature, helper or module-level statement may change), and the corrected tests must pass on the candidate and still
discriminate (fail on the unmodified base, or be caught by a mutant of the patch). A correction that touches a passing test,
drops a test or changes anything outside the failing bodies is rejected whole. For the SEALED module, a test that failed by
assertion or by an exception is never overridden by your classification: your correction is recorded for the human and the
hold stands; only a sealed test the supervisor killed at its timeout can be corrected and re-run.

ORIGINAL TASK STATEMENT:
{task.statement}

RESTATED TASK AND CONTRACT:
{spec["restated_task"]}
{json.dumps(spec["interface_contract"], indent=2)}

ACCEPTANCE CRITERIA:
{json.dumps(spec["acceptance_criteria"], indent=2)}

OUT OF SCOPE: {json.dumps(spec["out_of_scope"])}

CANDIDATE DIFF:
```diff
{diff[:16000]}
```

THE GENERATED TEST MODULE (`{module_name}`) THAT PRODUCED THESE FAILURES:
```python
{module_source[:24000]}
```

FAILURES:
{failing_block}

Return JSON: classifications (one entry per failing test id above), corrected_module (full corrected source or null),
corrected_notes (one or two sentences on what you changed and the contract basis, or why no correction is possible).
"""


def drift_prompt(task, spec: dict, diff: str, actions: list[dict], finish_summary: str | None) -> str:
    trail = "\n".join(f"turn {a['turn']}: {a['action']} {a.get('path') or ''} | reason: {(a.get('reason') or '')[:160]} | observed: {(a.get('observation_head') or '')[:120]}"
                       for a in actions)
    return f"""You are the DRIFT AUDITOR of Attest. Compare what was asked with what was done. You see the task, the contract, the
implementer's full action trail and the final diff. Answer three questions: does the diff solve the stated task; where did the
scope narrow (something required was skipped or weakened) or widen (something not asked for was added or changed); and which
claims in the implementer's own messages are unsupported by the observed tool output.

ORIGINAL TASK STATEMENT:
{task.statement}

RESTATED TASK AND CONTRACT:
{spec["restated_task"]}
{json.dumps(spec["interface_contract"], indent=2)}

ACCEPTANCE CRITERIA:
{json.dumps(spec["acceptance_criteria"], indent=2)}

OUT OF SCOPE: {json.dumps(spec["out_of_scope"])}

ACTION TRAIL:
{trail}

IMPLEMENTER'S FINAL SUMMARY: {finish_summary or "(none)"}

FINAL DIFF:
```diff
{diff[:30000]}
```

Return JSON: drift_score between 0.0 (fully aligned) and 1.0 (off target); assessment; scope_narrowed; scope_widened;
unsupported_claims (quote the claim); summary (two sentences). Be concrete; cite line content from the diff.
"""
