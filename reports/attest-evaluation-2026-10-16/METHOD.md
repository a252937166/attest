# Controlled evaluation: plain agent vs Attest — method

## Question

Does Attest's verification layer change outcomes versus a plain agent that uses the **same** implementation model and
tools? Specifically, does it avoid shipping broken code (false acceptance), and at what cost in money, latency and false
rejection?

## Design

- **Frozen task suite** (`examples/eval/SUITE.json`): five distinct Python tasks, each a small repo with a working helper
  (so the existing suite passes on the unmodified code) and a target stub (so the independent held-out suite fails on it):
  `roman-to-numeral`, `rle-encode`, `balanced-brackets`, `durationkit-units-001`, `semver-is-compatible-pr368-v2`
  (the last two are multi-file; semver is the real python-semver repo with pinned pytest).
- **Two systems, identical implementation capability.**
  - *Baseline (plain agent):* the same implementation loop — same Nebius model for the `implement` role, the same tools
    (read/edit/run_tests/run_python in a Nebius Sandbox), the same turn budget, the same syntax-check/undo/test-before-finish
    discipline — with **none** of Attest's spec, sealing, verification, breaker, drift or arbitration stages. It implements
    and stops.
  - *Attest:* the full pipeline, same `implement` model.
- **Same budget.** Both run under the same per-run USD cap ($0.50); Attest pays its spec/seal/breaker/drift/arbitration
  overhead out of that cap.
- **Independent judge.** Both final patches are judged by the **same** held-out suite (the task's `heldout.py`, run together
  with the existing suite in a fresh sandbox branch from the checkpoint). `held_out_correct` = both pass. The judge is the
  objective ground truth; it is not shown to either system.
- **Confusion against ground truth.** For each run: `true_accept` (accepted and correct), `false_accept` (accepted but
  incorrect — *shipped broken code*), `false_reject` (not accepted but correct), `true_reject` (not accepted and incorrect),
  `infra_error`. The baseline "accepts" whatever it finishes (a plain agent ships whatever it produced); Attest accepts only
  a `VERIFIED` verdict.
- **All attempts retained** under `runs/`. Transient infrastructure failures (TLS resets on the sandbox or inference API) are
  recorded as `infra_error`, not hidden.

## Commands

```
python3 scripts/make_eval_suite.py                 # (re)write the frozen suite
python3 scripts/run_evaluation.py --provider nebius --workers 1 --usd-cap 0.5 \
        --out reports/attest-evaluation-2026-10-16
```

## Honest reading guide

- `false_accept` is the metric that matters most: a plain agent has no gate, so any wrong patch it finishes is shipped. The
  held-out suite is the referee.
- A `false_reject` is only a cost if the held-out suite is itself complete. Where Attest's breaker finds an edge case the
  held-out suite does not cover, a "false reject" by this harness is really Attest catching a bug the ground-truth judge
  missed — those cases are called out individually in `README.md`, not hidden in the aggregate.
- Attest's extra cost and latency are the price of the evidence and the gate; both are reported.
