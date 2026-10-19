# Attest pilot: verify a change to your own repository

Attest is an evidence-gated coding agent. You give it a repository, a pinned commit and a precise request; it writes
sealed acceptance tests before any code exists, implements the change in a sandbox, then tries to break the result
(mutation check, adversarial tests, drift audit) and hands you a Proof Bundle whose verdict you can re-check offline.
This pilot runs the whole workflow from the command line on a public GitHub repository of your choice. Nothing runs on
your machine except the CLI itself: every test and every patch executes inside a Nebius Token Factory sandbox, and the
inference uses NVIDIA Nemotron models on Nebius Token Factory under your own API key.

Time to a first Proof Bundle: about 30 minutes once you know which change you want, of which 5 to 10 minutes are the run
itself. Writing a precise statement from an unfamiliar repository takes longer than every tool step together; budget for it.

## 0. What you need

| Item | Why |
| --- | --- |
| Python 3.12 (`python3 --version`) | the CLI is standard-library Python; `pip install -e ".[dev]"` adds `jsonschema` (with its dependencies) and `certifi` |
| A Nebius Token Factory API key and project id | Sandboxes (a beta service; Nebius's console says beta runs are free, which this project has not reconciled against an invoice) and Nemotron inference (paid, capped by `--usd-cap`, default $0.50 per run); both are billed by Nebius separately |
| A public GitHub repository, Python, `unittest` or `pytest`, under 2,000 files and 25 MB | the pilot's supported scope |
| The 40-character sha of the commit to start from | Attest only works on pinned commits |

Set both credentials in your shell only (they are never written to artifacts). Both are required by `preflight` and `run`;
without them the commands stop with a one-line message naming the missing variable:

```bash
export NEBIUS_API_KEY="..."              # from the Token Factory console
export NEBIUS_PROJECT_ID="aiproject-..."  # the project id shown in the console, not a key
```

Every command below passes `--provider nebius` explicitly. The CLI's default profile is the project team's internal
development gateway, which is not available to pilot users; leaving the flag out fails with a message about a missing
`CODEX_API_KEY`.

## 1. Install and preflight

```bash
git clone <this repository> attest && cd attest
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m attest preflight --provider nebius
```

Preflight prints one JSON object: `sandboxes` (your permissions, limits and the resolved `python:3.12-slim` image uuid),
`nebius` (the Nemotron models per role and the per-run cap) and an empty `ledger`. If it fails, stop here and send us the
output (the tool never prints a key).

## 2. Import the repository at a pinned commit

```bash
python -m attest import \
  --github https://github.com/<owner>/<repo> --commit <40-char sha> \
  --id <task-id> --out tasks \
  --runner pytest \
  --write-glob 'src/<package>/**' \
  --python-path src \
  --import-hint 'from <package> import <name>   (package lives in src/<package>)' \
  --pin pytest==8.3.3 --pin pluggy==1.5.0 --pin iniconfig==2.0.0 --pin packaging==24.1 \
  --statement-file statement.txt --criteria-file criteria.txt
```

Everything in angle brackets is a placeholder; `<task-id>` also names the directory `tasks/<task-id>/`. Exit codes: 0
imported, 2 refused (the message names the limit), 3 imported but `task.json` has policy problems listed in the output.

A complete example is in this repository: `examples/semver-long-prerelease-pr488/` was imported from python-semver at
commit `887d057e66b7fdfe0adf5a206ac810766b5af938` with the statement and criteria you can read in its `task.json`, the
upstream pull request's tests as `heldout_test_pr488.py`, the write scope `src/semver/**`, the pins above, and the
import hint `from semver import Version   (package lives in src/semver; the class is semver.version.Version)`.

What the import does and refuses:

- downloads exactly that commit, keeps regular files only (links inside the repository become copies, links outside are
  listed and dropped), records the tarball digest and a tree digest in `tasks/my-task/SOURCE.json`;
- refuses, before anything else happens, a repository over 2,000 files or 25 MB, a file over 200 KB (raise with
  `--max-file-bytes`, hard cap 1 MB), a branch or tag instead of a sha, a whole-repository write scope, an unprotected
  test or packaging file, an unpinned dependency, a test timeout over 300 s. Every refusal names the limit;
- writes `tasks/<task-id>/task.json`: your statement, your acceptance criteria, the write scope, the protected files, the
  pinned install that runs once at checkpoint time (the only networked operation), and `upstream` with the URL and commit;
- prints what it recorded (write scope, protected files, test command, install, held-out files), anything it skipped, the
  policy problems if any, and which fields are still empty.

Protected by default (unless you pass your own `--protect` list): `tests/**`, `test/**`, `setup.py`, `setup.cfg`,
`pyproject.toml`, `requirements*.txt`, `requirements/**`, `*.lock`, `poetry.lock`, `Pipfile`, `Pipfile.lock`, `tox.ini`,
`noxfile.py`, `MANIFEST.in`, `Makefile`, `.github/**`. The implementer can only write inside `--write-glob`.

Runner: choose `--runner unittest` whenever the repository's tests are `unittest.TestCase` classes, even if the project
itself runs them through pytest (many do): the repository's own suite then runs through the same supervisor as the sealed
tests (one process per test, bound to digests and a nonce) and needs no pins. Choose `pytest` only for suites that need
pytest features (fixtures, parametrize); such a suite is run with the task's test command and judged from its console
output, which the Proof Bundle labels `evidence_class: stdout` with a warning. The sealed, mutation and adversarial gates
are bound either way.

Pins: the sandbox image is bare `python:3.12-slim`, so the test runner itself must be installed. The four pins above are
pytest 8.3.3 and its three dependencies; `--runner unittest` needs no pins. Add your repository's runtime dependencies
the same way, each as `name==version` (an unpinned name is refused). The install runs once, with networking, when the
checkpoint is created; tests never have network access.

`statement.txt` and `criteria.txt` are read relative to your current directory (the checkout root in these commands);
they are yours to keep, so commit them next to `tasks/<task-id>/` if you want to reproduce the run. `statement.txt` is one
paragraph saying exactly what must change and what must not; `criteria.txt` has one testable
sentence per line (a criterion may name standard-library modules; "the existing tests still pass" is a good last line).
Precision here is what the sealed tests are written from: an ambiguous statement produces an ambiguous test suite, and
the run ends in `NEEDS HUMAN` instead of `VERIFIED`. Say which behaviours are unspecified when you do not care about them.
`--import-hint` is free text shown to the test authors and the implementer, typically the import line a test would use
plus where the package lives. To import again after changing the statement, delete `tasks/<task-id>/` first; the tarball
is downloaded again.

Optional: a held-out suite the implementer never sees (`--heldout tests/test_heldout.py=heldout.py`), for example the
tests of the upstream pull request that fixed the issue.

## 3. Run

```bash
python -m attest run --task tasks/<task-id>/task.json --out runs --provider nebius --usd-cap 0.5
```

The run prints every stage with UTC timestamps: checkpoint, specification, sealing (a count of how many sealed tests
fail on your unmodified code; the tests themselves are in `runs/.../sealed/test_sealed.py` and the per-test record in
`red.attempt1.json`), implementation turns (at most 12 for an imported repository), verification, the breaker pass, the
drift audit and, when a generated test fails, the arbiter's classification. The exit code is 0 for `VERIFIED` and 2
otherwise; when you start the run in the background, read the verdict from `PROOF.md` or `proof_bundle.json`. The Proof
Bundle is in `runs/<task-id>-<timestamp>/`: `PROOF.md` first, then `proof_bundle.json`, the sealed tests, the candidate
patch, the breaker tests and every supervisor record.

Verdicts: `VERIFIED` (every gate passed; a gate may have been re-run on a corrected generated test after the correction was
validated by execution, which the bundle says), `NEEDS HUMAN` (a gate failed; the reasons name it; a sealed test that failed by assertion or by any exception always holds, even when the arbiter calls it defective; only a test the supervisor killed at its timeout can be corrected), `INFEASIBLE` (the contract auditor's witness program,
executed on your unmodified repository, demonstrated that your own acceptance criteria contradict each other; since
revision 6 the conflict must name only your criteria, and since revision 7 the witness must be written in the constrained
witness language `attest-witness/1` (literal inputs, allowed built-ins and standard-library functions, and the functions and
classes your repository defines, every call origin checked), otherwise the run is held as `NEEDS HUMAN` with reason class
`contract_conflict_held`; the program and its
output are in `contract_audit/`), `NO CHANGE` (no patch was produced: the implementer finished without editing, or ran out
of turns, which the bundle reports as unfinished), `ERROR` (infrastructure; nothing was retried).

## 4. Check the bundle offline

```bash
python -m attest check runs/<task-id>-<timestamp>
```

Exit code 0 when everything agrees, 1 on any mismatch. This recomputes every artifact digest, the sealed and adversarial bindings from the raw supervisor records, the ledger
totals and the gate-to-verdict rule, and re-renders `PROOF.md`. It is an integrity and consistency check, not a
signature and not independent proof of execution; the operation ids in the bundle are what the sandbox service records.

## 5. Limits of the pilot

- Python 3.12, `unittest` or `pytest`, pure-Python dependencies installable from pinned requirements at checkpoint time.
- No network at test time; no services, databases, GUIs or system packages.
- One task per run; the implementer writes only inside `allowed_write_globs`.
- Per run: at most 12 implementer turns, 12 mutants, 180 s per test suite (300 s maximum), `--usd-cap` dollars.
- Model-written tests can be wrong. A `NEEDS HUMAN` with an arbiter classification of `test_defect` means the hold came
  from the test, not from your code; the corrected test and its re-runs are in the bundle.
- The mutation gate needs at least 4 one-line mutants of the changed lines that could be evaluated. A one- or two-line fix
  yields about that many, so a single sandbox operation that ends uncertain (recorded as an `unknown` mutant, never
  replayed) holds the verdict as `NEEDS HUMAN` with the reason "mutation gate incomplete". That is an infrastructure gap,
  not a finding against your patch: run the task again; the unknown mutant and its error are in `breaker.json`.

## 6. Send feedback

Copy `PILOT_FEEDBACK.md`, fill it in and send it back with the run directory zipped (`runs/<task-id>-<timestamp>`; it
contains no credentials). Ten minutes of notes on where the instructions were unclear are worth more to us than a
polished report.
