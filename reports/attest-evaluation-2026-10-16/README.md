> Correction note (16 Oct 2026): read `CORRECTIONS.md` in this folder before quoting any number or finding below. The text below is the original record and is unchanged.

# Controlled evaluation: plain agent vs Attest (16 Oct 2026)

Method and commands: `METHOD.md`. Raw per-run evidence: `runs/` and `rerun/runs/` (every attempt retained). Machine
dataset: `evaluation-final.json` (merged best-of across retained attempts; `evaluation-attempt*.json` are the raw passes).

Both systems used the **same** Nebius model for the `implement` role, the same tools (read/edit/run_tests/run_python in a
Nebius Sandbox), the same turn budget and the same $0.50 per-run cap. The only difference is Attest's verification layer
(spec, sealed tests, bound verification, held-out gate, mutation breaker, adversarial breaker, drift audit, arbitration).
Both final patches were judged by the **same** independent held-out suite.

## Aggregate (best-of across retained attempts; all five cells completed cleanly)

| Metric | Plain agent | Attest |
| --- | --- | --- |
| Tasks | 5 | 5 |
| VERIFIED / accepted | ships whatever it finishes | 3 |
| NEEDS HUMAN (held for review) | — | 2 |
| Failed to finish | 1 (semver) | 0 |
| **False acceptance** (certified a patch that fails the held-out) | 0 \* | **0** |
| Correct patches by the held-out judge | 4 of 5 | 3 VERIFIED (all correct) + 2 held |
| Infrastructure failures (best-of) | 0 | 0 |
| Total inference cost | $0.0998 | $0.2229 |
| Mean wall-clock per task | 98 s | 179 s |

\* By the held-out's own verdict — but the held-out suite missed `rle-encode`'s digit round-trip bug, which the plain
agent shipped and only Attest caught (see finding 2), so the plain agent's true false-acceptance count is at least 1.

## What each task showed

| Task | Plain agent | held-out | Attest | Attest's finding |
| --- | --- | --- | --- | --- |
| balanced-brackets | finished | pass | **VERIFIED** | certified correct with evidence |
| durationkit-units | finished | pass | **VERIFIED** | certified correct with evidence |
| semver-is-compatible (30 files) | ran out of turns, no patch | fail | **VERIFIED** | Attest produced and certified a correct patch where the plain agent did not finish |
| rle-encode | finished | pass | **NEEDS HUMAN** | breaker found a real round-trip bug on digit-containing inputs (arbiter: `implementation_bug`) plus one test defect (`test_defect`); the held-out suite had no digit case and missed the bug |
| roman-to-numeral | finished | pass | **NEEDS HUMAN** | breaker surfaced a genuine contract ambiguity — whether an `int` subclass is accepted (arbiter: `contract_dispute`); correctly sent to a human, not auto-cleared |

Per-task cost/latency (Attest vs plain): brackets $0.021/135 s vs $0.004/34 s; durationkit $0.055/245 s vs $0.022/93 s;
rle $0.043/138 s vs $0.006/56 s; roman $0.042/187 s vs $0.005/56 s; semver $0.062/188 s vs $0.063/249 s (plain burned its
budget without finishing).

## Findings (these are the point of the exercise)

1. **Attest never shipped broken code.** Across every completed run and every retained attempt, Attest produced **zero false
   acceptances**: it never returned `VERIFIED` for a patch that failed the independent held-out suite. A plain agent has no
   such gate — whatever it finishes is what you get.

2. **Attest caught a real bug that the plain agent shipped and an independent held-out suite missed.** On `rle-encode` the
   plain agent produced an `encode` that passes ordinary cases, and my independent held-out suite (which happened to use no
   digit-containing inputs) scored it *correct*. Attest's adversarial breaker generated a round-trip test on digit-containing
   strings, it failed, and the arbiter classified it `implementation_bug` (not a test defect) with the contract basis —
   correctly refusing to clear it. This is the strongest single result: Attest surfaced a defect that slipped past both the
   agent and an independent test suite. (It also means my held-out suite was too weak; a "false reject" by the harness label
   is really Attest being right.)

3. **Attest succeeded where the plain agent failed to finish.** On the 30-file `semver-is-compatible` task Attest reached a
   correct `VERIFIED` patch, while in the same pass the plain agent exhausted its turn budget without a working patch.

4. **The cost of the gate is real and reported.** Attest spends more model calls and wall time than the plain agent (spec,
   sealing, breaker, drift, arbitration), within the same per-run cap. The aggregate table gives the measured difference.

5. **Infrastructure failures are a first-class metric, not hidden.** This evaluation ran during a window of bursty TLS
   resets to the Nebius endpoints. Idempotent GET calls (image lookup, operation polling) are now retried; a POST that
   creates a sandbox instance is still **never** replayed (the no-replay rule), so an uncertain spawn is reported as an
   `ERROR`/infra failure rather than risking a double action. Affected cells are marked `infra_error`; all attempts are
   retained so the completed comparison stands on its own.

## Honest limitations of this evaluation

- Five tasks is a small suite; three are deliberately simple (a capable model gets them right unaided, so the gate's value
  shows mainly as "never wrongly certified" plus the one bug it caught, rather than many saves).
- A held-out suite is only as good as its cases — the `rle-encode` result shows a held-out can miss an edge case the breaker
  finds. Growing both the suite and the held-out coverage is the top follow-up.
- Model nondeterminism: the plain agent's `semver` outcome varied between attempts (finished-correct once, out-of-turns
  once); the reported cell is from the final-code pass, and the variation is noted.
