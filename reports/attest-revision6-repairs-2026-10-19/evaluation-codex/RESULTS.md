# Evaluation results: revision7 (codex)

Registered 2026-10-19T14:23:03.659852+00:00; finished 2026-10-19T14:33:35.607731+00:00; complete: True; stopped: a transport-uncertain operation occurred; the batch stopped without replaying anything.
Systems ['attest'], 4 tasks, 1 attempt(s) per cell, 4 cells scheduled, 3 completed, 1 not run.
Provenance: commit `none`, package `f836cfd0154faa87`, harness `5af2b4989b2b93db`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none; provider profile: provider=codex_gateway; roles arbitrate=gpt-6-astra:medium audit=gpt-6-astra:low break=gpt-6-sol:medium implement=gpt-6-sol:medium seal=gpt-6-sol:medium spec=gpt-6-astra:low summary=gpt-6-luna:low; base_url_sha256=68e25b464500800e.
Budget: committed $0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | rle-encode | attest | 1 | completed | INFEASIBLE | not correct | true_reject | 2 | 0.0 | 177.0 s | f836cfd0 |
| 1 | balanced-brackets | attest | 1 | completed | VERIFIED | correct | true_accept | 10 | 0.0 | 619.5 s | f836cfd0 |
| 2 | durationkit-units-001 | attest | 1 | completed | ERROR | not judged | infra_error | 6 | 0.0 | 335.6 s | f836cfd0 |
| 3 | kvparse-refactor-001 | attest | 1 | not_run | - | not judged | not_run | - | - | - | - |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (hold without a patch on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 4 | 3 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0.0 | 377.4 s |
Starting committed total of this process: $0 = $0 from 0 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-19T14:23:03.661905+00:00).


## Reasons recorded for every non-accepted cell

- cell 0 (rle-encode, attest): contract contradiction demonstrated by an executed witness in attest-witness/1 on the task's own criteria (requirements TC5): TC5 conflicts with the authoritative task's mandatory encoding format and unchanged decode: in
- cell 2 (durationkit-units-001, attest): SandboxError: spawn outcome uncertain (URLError: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1000)>); inspect account operations, do not replay

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks a hold that produced no patch (an INFEASIBLE verdict, or a NEEDS HUMAN hold with no patch) on a task whose held-out suite is satisfiable (a wrong refusal); the same hold on a task marked `unsatisfiable` is a `true_reject`. A NEEDS HUMAN hold that did produce a patch is judged on that patch. A task is an invalid comparison when any of its cells ran another revision, provider, limit or effective provider profile (models per role, reasoning effort, sampling) than the registered one. Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
