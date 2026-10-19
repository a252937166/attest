# Evaluation results: revision6 (codex)

Registered 2026-10-19T10:39:54.943877+00:00; finished 2026-10-19T10:51:39.140793+00:00; complete: True; stopped: no.
Systems ['attest'], 3 tasks, 1 attempt(s) per cell, 3 cells scheduled, 3 completed, 0 not run.
Provenance: commit `none`, package `b11ec0658845e54d`, harness `5af2b4989b2b93db`, examples `6db7a2e937d6e5d4`; snapshot intact at end: True; invalid comparisons: none; provider profile: provider=codex_gateway; roles arbitrate=gpt-6-astra:medium audit=gpt-6-astra:low break=gpt-6-sol:medium implement=gpt-6-sol:medium seal=gpt-6-sol:medium spec=gpt-6-astra:low summary=gpt-6-luna:low; base_url_sha256=68e25b464500800e.
Budget: committed $0 of an approved None (per-run cap $0.5).

## Every scheduled cell

| # | Task | System | Attempt | Status | Verdict | Judge | Label | Calls | USD committed | Wall | Revision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | rle-encode | attest | 1 | completed | NEEDS HUMAN | not correct | true_reject | 2 | 0.0 | 159.1 s | b11ec065 |
| 1 | durationkit-units-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.0 | 679.6 s | b11ec065 |
| 2 | kvparse-refactor-001 | attest | 1 | completed | VERIFIED | correct | true_accept | 11 | 0.0 | 527.9 s | b11ec065 |

## Summary per system

| System | Scheduled | Completed | True accept | False accept (shipped broken) | False reject (held correct) | True reject | False refusal (hold without a patch on a satisfiable task) | No patch (unfinished) | Infra error | Not run | Needs human | USD committed | Mean wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attest | 3 | 3 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0.0 | 455.5 s |
Starting committed total of this process: $0 = $0 from 0 completed row(s) + $0 from 0 run director(ies) no row owns (rebuilt from disk at 2026-10-19T10:39:54.944552+00:00).


## Reasons recorded for every non-accepted cell

- cell 0 (rle-encode, attest): contract conflict demonstrated but not grounded (mixed criteria TC5, AC8, AC12): For input 'a1', AC8 requires 'a111', but the decoder preserved by AC12 returns 111 copies of 'a', violating TC5.; a model's restatement of 

Pacing: gateway status: hourly request counting not enforced; rejections 0; waits 0.

Ground truth: the independent held-out suite of each task (for a task marked `unsatisfiable`, no patch counts as correct and a hold is the right outcome). `no_patch` marks a cell that produced no patch at all (an unfinished task, neither a rejection nor an acceptance); `false_refusal` marks a hold that produced no patch (an INFEASIBLE verdict, or a NEEDS HUMAN hold with no patch) on a task whose held-out suite is satisfiable (a wrong refusal); the same hold on a task marked `unsatisfiable` is a `true_reject`. A NEEDS HUMAN hold that did produce a patch is judged on that patch. A task is an invalid comparison when any of its cells ran another revision, provider, limit or effective provider profile (models per role, reasoning effort, sampling) than the registered one. Infrastructure errors and not-run cells stay in the table; nothing was merged or selected.
