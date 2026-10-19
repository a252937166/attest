# Evaluation results: revision7-3 (codex)

Registered 2026-10-19T14:43:54.706090+00:00; finished 2026-10-19T14:51:37.044048+00:00; complete: True; stopped: a transport-uncertain operation occurred; the batch stopped without replaying anything.
Systems ['attest'], 2 tasks, 1 attempt(s) per cell, 2 cells scheduled, 2 completed, 0 not run.
Provenance: commit `none`, package `f836cfd0154faa87`, harness `5af2b4989b2b93db`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none; provider profile: provider=codex_gateway; roles arbitrate=gpt-6-astra:medium audit=gpt-6-astra:low break=gpt-6-sol:medium implement=gpt-6-sol:medium seal=gpt-6-sol:medium spec=gpt-6-astra:low summary=gpt-6-luna:low; base_url_sha256=68e25b464500800e.
Budget: committed $0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | durationkit-units-001 | attest | 1 | completed | ERROR | not correct | infra_error | 4 | 0.0 | 419.5 s | f836cfd0 |
| 1 | kvparse-refactor-001 | attest | 1 | completed | ERROR | not judged | infra_error | 6 | 0.0 | 462.2 s | f836cfd0 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (hold without a patch on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0.0 | 440.9 s |
Starting committed total of this process: $0 = $0 from 0 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-19T14:43:54.709640+00:00).


## Reasons recorded for every non-accepted cell

- cell 0 (durationkit-units-001, attest): model provider: the inference outcome is uncertain (transport failure); the request was not retried [ref 40c2bd57] (outcome uncertain; not retried)
- cell 1 (kvparse-refactor-001, attest): SandboxError: spawn outcome uncertain (URLError: <urlopen error _ssl.c:983: The handshake operation timed out>); inspect account operations, do not replay

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks a hold that produced no patch (an INFEASIBLE verdict, or a NEEDS HUMAN hold with no patch) on a task whose held-out suite is satisfiable (a wrong refusal); the same hold on a task marked `unsatisfiable` is a `true_reject`. A NEEDS HUMAN hold that did produce a patch is judged on that patch. A task is an invalid comparison when any of its cells ran another revision, provider, limit or effective provider profile (models per role, reasoning effort, sampling) than the registered one. Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
