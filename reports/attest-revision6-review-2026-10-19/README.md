# Revision 6 independent closure check — 19 October 2026

**Disposition: six of the seven revision-5 follow-up items pass this scoped check; R5-03 remains partial. Two additional release follow-ups are still open: strict request validation after the paid verification incident, and a final-tree regression test that currently fails. Do not describe revision 6 as fully closed or its current complete suite as all passing.**

Only review artifacts were added. Product code/tests, prior reports and run records were not modified. This review issued public GETs only and performed offline tests with fakes; it did not issue a production POST, use credentials, invoke paid providers/Sandboxes, restart services or deploy changes.

## Independent observations

- Full suite: **352 tests, 1 failure, 0 errors, 0 skips**, 88.64 seconds. Therefore 351 passed on the reviewed final tree.
- Live read-only check around 11:18 UTC: version **0.6.0**, healthy/ready worker, idle, queue zero, no active reservations; served HTML/JS/CSS match local files.
- Package digest: `b11ec0658845e54d8917ac7a1cdbb32dddd1d16232fa0f377b08971a711837e9`, 36 sources, matching the revision-6 pin.
- Three recorded revision-6 bundles are accepted with protocol-3 complete-evidence status and no checker warnings. Semantic outcomes: durationkit and kvparse VERIFIED; rle-encode NEEDS HUMAN on mixed task/derived criteria. The safe hold is a documented tradeoff, not a new failure to implement a satisfiable task.
- The seven recorded revision-5 bundles are also accepted; two old INFEASIBLE bundles now carry one warning each. Integrity/completeness acceptance does not establish semantic correctness.
- Public list: 40 rows. The added incident row is interrupted/error, has 16 model calls and committed cost `$0.055226`; no open reservations remain. Disk headroom is 1,126 MB / 8.15%.
- Local `dist/public` remains clean at records commit `a2d95a0`, code `da00f41`, pin `25dd5f6`; nothing was pushed by this review.

## Closure of the seven scoped items

| Item | Result | Evidence boundary |
|---|---|---|
| R5-01 partial settlement framing | Closed for the reported sequence | Readback/tail repair preserves both reservations; recovered $0.07 conservatively covers $0.06 in-memory total. Failure to repair/read back prevents dispatch. |
| R5-02 mandatory stage evidence | Closed for the joint omission | Independent protocol-3 copy with existing-stage/raw deletion now has named errors and no complete/fully-verified status; positive original passes. |
| R5-03 grounded/constrained infeasibility | **Partial** | Authoritative/derived criterion separation is present, but the mechanical constraint permits aliased dynamic type construction; details below. |
| R5-04 public diagnostics | Closed for newly generated tested carriers | Fixed public vocabulary and a private sidecar cover the pipeline/providers/journal/download paths exercised by targeted tests. Historical evidence and raw supervisor status retain documented limits. |
| R5-05 actual entry-point call cap | Closed | CLI and console construct the paid provider with 22 by default; call 23 is refused before fake transport dispatch. |
| R5-06 effective provider profile | Closed within current-profile schedules | Effective roles, effort and sampling are registered and checked at resume/cell/comparison boundaries. Old schedules without a profile require fresh registration. |
| R5-07 master token in download URLs | Closed | Master query tokens are ignored; run-scoped, expiring tickets authorize only the matching download routes and no POST/admin privileges. |

Focused accounting closure tests: 14 passed. Focused API/diagnostics/ticket tests: 20 passed. These scoped successes do not override the whole-suite failure below.

## Remaining work

### 1. R5-03: mechanical witness restriction can be bypassed

`attest/core/pipeline.py:255–278` rejects direct `type(...)` calls and explicit class/function definitions, but checks the syntactic call name instead of its origin. A benign toy using `from builtins import type as make_type` creates the forbidden string subclass while `witness_constraint_problems` returns no problems. The actual contract-audit method with controlled execution records consequently marks it constrained and grounded. `attest/core/check.py:170` reuses the same helper.

This is a failure of the stated mechanical restriction, separate from the admitted limitation that model reasoning cannot prove arbitrary task impossibility. No claim is made that a real recorded batch used this bypass.

**Repair:** use a small positive witness language/allowlist with validated call origins and literal input construction, or keep unsupported witnesses on NEEDS HUMAN. Do not rely on adding one more banned alias to a blacklist. Require aliases/dynamic factories/imported helpers to be rejected or explicitly proven safe, and re-run the exact negative case alongside a valid literal witness.

See [core review](core-review.md), [bounded reproduction](core-repro.py) and [results](core-repro-results.json).

### 2. Paid verification incident: strict request validation is still not deployed

`attest/app/server.py:140–143` still declares `provider: str = "nebius"` and does not forbid unknown fields. The exact incident-shaped request with `profile: development`, missing provider and a junk query token is still accepted as an ordinary public Nebius enqueue in a disabled-worker, blocked-network local harness. No real request is dispatched by that reproduction.

**Repair:** forbid unknown request fields; require an explicit provider constrained to supported values; verify wrong `profile`, missing provider and invalid provider all return 422 before any row/reservation/queue mutation. Keep side-effecting negative tests local with blocked real transports, and limit live verification to read-only requests unless separately authorized. Schema hardening prevents this particular mistake; it does not make a valid production POST free.

The executor's reported production verification accidentally created an unapproved run. Its journal/readback amount is **$0.055226 across 16 model calls**, and the live row confirms that accounting. This is not an independently reconciled provider invoice, remaining credit balance or bank-card charge. The incident is an authorization/process violation, not evidence that download tickets granted POST privileges. The $10 formal proposal remains unapproved.

Incident evidence: [deployment record](../attest-deployment-2026-10-19c/README.md).

### 3. Whole-suite historical-corpus test is stale against the final evidence tree

`tests/test_audit_core.py:767–785` assumes every included report bundle is historical. Its directory filters skip the older `attest-audit-*` reports but include the newly created `attest-revision5-repairs-2026-10-19/evaluation-codex` protocol-3 bundles. It fails at line 780 because a valid modern bundle correctly reports `historical=false`.

**Repair:** select a genuinely frozen historical corpus explicitly, or classify fixtures by their supported protocol and verify both historical and modern behavior separately. Do not change the product checker to mislabel modern evidence as historical. Run the full suite again after final batch/report/export generation, from the exact final pinned tree.

This appears to be a fixture-selection regression, not evidence that the passing modern bundle is invalid. Nevertheless, the completion claim of 352 passing tests is not reproducible on the current final tree. The earlier saved test log reports success; this independent later run has one failure.

## Next step

Complete these three follow-ups, preserve original evidence, run all targeted negative/positive controls and the final-tree full suite, then create a new pin. Keep development on Codex; no additional paid verification is authorized by this review. Main application remains on yungou, necessary Docker components on Aliyun, and existing services must remain protected.

Formal Nemotron comparison, official billing/credit verification and the outstanding video/publication/submission/pilot work remain separate from implementation closure.
