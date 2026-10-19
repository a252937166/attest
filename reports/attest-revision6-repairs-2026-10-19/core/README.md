# Item 1 (R5-03 continued): the constrained witness language attest-witness/1 (19 October 2026)

Finding (revision-6 review, `reports/attest-revision6-review-2026-10-19/core-review.md`): the revision-6 constraint was a list of
forbidden spellings (`witness_constraint_problems` checked the immediate call name). A witness that imported
`from builtins import type as make_type` built a dynamic `str` subclass with an overridden `__len__` while the check returned no
problem, and `Pipeline.contract_audit` then marked the conflict constrained and grounded, the input of the INFEASIBLE branch. The
offline checker reused the same helper.

Offline work: no provider call, no sandbox operation, no production request. The review folder and every earlier record are
unchanged.

## What changed

- `attest/core/witness.py` (new): the language `attest-witness/1`, a POSITIVE grammar. Anything it does not name is outside it.
  - Statements: imports, assignments to names or items, expression statements, if/elif/else, for, while,
    try/except/else/finally, assert, raise, pass, break, continue. Function, class and lambda definitions, `with`, `del`,
    `global`, `match` and assignment expressions are outside.
  - Imports: `sys` (exit, stdout, stderr, maxsize), `itertools`, `math`, `string` and `json` (each with a fixed list of names),
    and the frozen repository's own modules. Relative and star imports are outside. A standard-library module that the
    repository shadows with its own file is refused.
  - Repository names: `Repository.resolve` follows the repository's own source (explicit re-exports, star imports with or
    without a literal `__all__`, same-module aliases, submodules, `python_paths` roots) and accepts only a name that resolves to a
    function or class the repository defines. A re-export of anything else (for example `typing.NamedTuple` or the
    `collections` module), a conditional or repeated binding, an alias of a built-in, an unreadable file or a resolution deeper
    than 8 steps is unresolved.
  - Calls: an allowed built-in by its own name; an allowed standard-library function or a resolved repository function or class
    by its imported name or module attribute; a method of a built-in value (str, bytes, numbers, list, tuple, dict, set, range,
    `args` of an exception). A call through a value held in a variable, a subscript, a call result or any other computed
    expression is outside, and so is a callable passed where a built-in calls it back (`map`, `filter`, `sorted(key=)`,
    `min/max(key=)`, `iter(callable, sentinel)`, the itertools callbacks, the json hooks, `list.sort(key=)`) unless its own
    origin is resolved.
  - Names: every name must be bound by the witness or be an allowed built-in; `type`, `object`, `getattr`, `vars`, `globals`,
    `exec`, `eval`, `compile`, `__import__`, `__builtins__` and every other name outside the list are outside the language.
    Attributes whose names start with an underscore are outside.
  - `analyze_witness(source, repository)` returns `conforms`, every problem, the resolved origin of every import and repository
    attribute, and the repository files the resolution read with their sha256.
- `attest/core/pipeline.py`: `contract_audit` analyses every witness against `Repository.from_snapshot(snapshot,
  task.python_paths)`, records the analysis per conflict (`witness_language`), sets `witness_constrained` from it, and copies the
  repository files the resolution read into `contract_audit/repository/<path>`. `grounded` = every requirement is a TC id and the
  witness conforms. A demonstrated task-provenance conflict outside the language is held: status "demonstrated by a witness outside
  the constrained witness language attest-witness/1 (...); held for a human, not infeasible", verdict NEEDS HUMAN with reason
  class `contract_conflict_held`. `witness_constraint_problems(source, repository=None)` stays as a thin wrapper.
- `attest/core/prompts.py`: the audit prompt states the language (`witness.language_summary()`, generated from the same constants
  the analyser uses, so the two cannot drift).
- `attest/core/check.py`: for an INFEASIBLE verdict under protocol 3 or later, the checker repeats the analysis from the witness
  file and `Repository.from_bundle` (a repository copy is read only when its sha256 equals the frozen task's digest of that path)
  and never trusts a recorded `grounded` or `witness_constrained` flag. Under protocol 4 it also requires a conforming recorded
  analysis whose repository-file list equals the re-derived one, and a new check `witness_language_rederived` compares every
  conflict's recorded analysis with a fresh one, whatever the verdict.
- `attest/core/verdict.py`: `EVIDENCE_PROTOCOL_VERSION = 4`; the bundle's protocol note names the language and the copies.
- `attest/core/exhibits.py`: the hold explanation names the language and its first problems.

## Mechanical enforcement versus the limits of model reasoning

Enforced mechanically, in the pipeline before the verdict and again by `attest check`: how a witness builds its inputs (literals,
containers, comprehensions and values computed from them by allowed calls), which code it may call (allowed built-ins, a short
list of standard-library functions, functions and classes the frozen repository defines, methods of built-in values), and which
modules it may import. A witness cannot construct a subclass of a built-in type, a dynamic type or an object with overridden
special methods except by calling code the repository itself defines.

Not established by the language: that the witness's inputs and comparison demonstrate that the named criteria cannot all hold.
That link is the auditor model's reasoning. Attest records the program, its execution and its output; a grounded verdict reads
"demonstrated by an executed witness", never "proven impossible". The marker line and exit code show what the program printed,
not that what it printed is true.

## Acceptance (negative cases next to positive controls)

`tests/test_audit_core.py::R61WitnessLanguage`, with the updated `R503GroundedInfeasibility` and `WitnessValidation` and the
verification suite's contract tests; output in `unittest-witness-language.txt` (13 tests, all passing).

| Test | Negative cases | Positive control |
| --- | --- | --- |
| `test_every_bypass_program_is_outside_the_language_with_a_named_reason` | 27 programs, each with its expected reason: imported aliases (the review's `from builtins import type as make_type`, `import builtins as b`, aliases of `exec` and `eval`, `types.new_class` imported or as a module attribute, `operator.attrgetter`, `collections.namedtuple`, `typing.NamedTuple`, `enum.Enum`); assigned aliases (`make = type`, `ev = eval`, an alias of a repository function, a reassigned imported name, a callable held in a dict); indirect factories and calls (`(0).__class__.__class__`, `str('x').__class__`, a generator frame's `f_builtins`, `sys.modules`, `getattr`, `vars`, `__builtins__`, `__import__`, `map` over a value-held callable, `sorted` with a lambda key, which is also reported as a lambda definition); class and function definitions | |
| `test_repository_names_resolve_only_to_definitions_of_the_repository` | a synthetic repository: re-exported `typing.NamedTuple`, re-exported `collections` module, a repository alias `make = type`, a conditionally defined function, a factory returned by repository code and then called, the same factory passed to `map`; a repository `json.py` shadowing the standard-library module | a repository function resolves through the package's star import to `pkg/core.py`; a name that merely spells `type` but is bound to `itertools.groupby` is analysed by its origin and conforms |
| `test_literal_input_witnesses_conform_and_record_their_origins` | | the fake auditor's grounded witness and a richer witness (itertools, comprehensions, try/except with `repr`, f-strings, `str.partition`, `sorted(key=str.lower)`) conform, with `parse_duration` resolved through `durationkit/__init__.py` to `durationkit/parse.py` |
| `test_the_contract_audit_holds_every_bypass_and_grounds_only_the_literal_witness` | the real `contract_audit` with a controlled executor that demonstrates every witness (exit 3, marker naming TC1): all 27 bypass programs are demonstrated, task provenance, not constrained, not grounded, status "outside the constrained witness language" | the literal witness is grounded, outcome "contradiction demonstrated", and its two repository files are copied into the run directory |
| `test_the_reviews_program_end_to_end_is_held_and_never_checks_as_infeasible` | the whole pipeline with the review's program: NEEDS HUMAN, `contract_conflict_held`, the explanation names the language; a forger who flips the verdict to INFEASIBLE and the flags to grounded and conforming fails `required_evidence` ("outside the constrained witness language attest-witness/1") and `witness_language_rederived` | the held bundle itself checks complete |
| `test_the_checker_re_derives_grounding_from_the_witness_and_the_repository_copies` | on a genuine grounded bundle: (a) the witness file swapped for the review's program with every record left claiming conformance; (b) a repository copy that differs from the frozen file; (c) the copies deleted; (d) the swapped bundle downgraded to protocol 3; (e) a recorded file list that hides a file the resolution reads; each fails `required_evidence` with the named reason | the genuine bundle is INFEASIBLE and fully verified under protocol 4 |
| `R503GroundedInfeasibility::test_recorded_witnesses_classify_as_the_review_argued` | the recorded kvparse witness (defines a class and functions) and the recorded revision-5 rle witness (calls `type()`, reads `__name__`; it passed the old blacklist) are outside the language | the recorded revision-6 rle witness, literal inputs and the repository's own `decode`, conforms against the frozen rle repository |

The review's own reproduction, re-run from a documented copy (`review-repro/core-repro.py`, one line changed to take the project
root from the environment because the copy sits two levels deeper; original digests in `review-repro/sha256-originals.txt`;
output `review-repro/core-repro-rerun.txt`, results `review-repro/core-repro-results.json`): the alias program now reports three
problems (the `builtins` import, the `__int__` attribute, the call of `Z`, a value), and the actual `contract_audit` records
`demonstrated: true, provenance: task, witness_constrained: false, grounded: false` with the status "demonstrated by a witness
outside the constrained witness language attest-witness/1 (...); held for a human, not infeasible". Its R5-02 part is unchanged:
the protocol-3 positive control passes and the joint deletion fails with `gates_match_stage_records` and `required_evidence`.

## Remaining limitations

- The analysis is static and rests on the repository's own source: a repository that binds names through `globals()`,
  `setattr` or import hooks, or a pinned dependency on the guest path that shadows a resolved repository module, is outside what
  it can see. Values computed by the repository's own code (including instances of classes the repository defines) are inside
  the input domain by the rule, and a callable returned by repository code is traced only where the witness calls it or passes
  it to a known callback position, not inside other repository functions.
- Attribute access on repository objects (for example `version.major`) is outside the language, so a witness for a class-based
  interface can only hold the run; that is conservative, never permissive.
- A protocol-3 INFEASIBLE bundle keeps no repository copies, so a protocol-3 witness that imports repository code cannot be
  re-established offline; no such bundle has been recorded.
- The language says nothing about whether a witness's demonstration is sound (see above); that is the documented limit of model
  reasoning, recorded with the execution.
