# Revision 6: bounded core follow-up

Scope: R5-02 mandatory evidence and R5-03 grounded/constrained INFEASIBLE only. Read source, repair reports/tests and the recorded three-cell batch; run the two small offline reproductions below. No full suite, provider, network, Sandbox or production request. Product files, earlier audits and original runs are untouched. This new review folder exists because a concrete new counterexample was found.

## R5-02: closed for the reported omission

`attest/core/check.py:189–229` now requires the existing stage independently of its presence and uses the recorded execution mode; task-declared held-out evidence is also mandatory. A fresh temporary copy of the revision-6 protocol-3 durationkit bundle is the positive control: complete and fully verified. Removing both `verification.existing` and `verify_raw.existing`, then re-rendering PROOF and regenerating the unsigned manifest, now returns `ok=false`, `fully_verified=false`, `evidence_complete=false`, two errors, zero warnings. The named errors are `gates_match_stage_records` and `required_evidence`.

This closes the precise jointly-deleted-stage counterexample. It tests semantic completeness, not cryptographic authenticity of unsigned manifests. This review does not claim exhaustive closure of all possible evidence shapes.

## R5-03: partial — dynamic-type alias bypasses the constrained-witness rule

**Source:** `attest/core/pipeline.py:252–277` checks the immediate call spelling against a blacklist. The same AST check is used by the offline checker at `attest/core/check.py:165–171`. Grounding is then set from task-only IDs plus this check at `pipeline.py:1317–1323`; a grounded result can end the task INFEASIBLE at `pipeline.py:851–856`.

The repairs correctly separate TC/AC criteria and hold derived/mixed or visibly unconstrained conflicts. However:

```python
from builtins import type as make_type
import sys
Z = make_type('Z', (str,), {'__len__': (0).__int__})
x = Z('a=b')
print('CONTRADICTION TC1: this value is a custom str subclass')
sys.exit(3)
```

This program creates a dynamic `str` subclass with overridden `__len__`, precisely outside the declared constrained input domain. The bounded local toy confirms `type(x) is str == false`, `isinstance(x, str) == true`, and `len(x) == 0`. Nevertheless, `witness_constraint_problems` returns `[]` because the call is named `make_type`, not `type`.

Actual `Pipeline.contract_audit` with a controlled fake answer/execution sets `provenance=task`, `witness_constrained=true`, `demonstrated=true`, `grounded=true`. No real model or sandbox executes here. This demonstrates the mechanical guard bypass and subsequent classification; it does not assert that a production run used it, nor claim the fabricated marker proves a real contradiction. The existing INFEASIBLE branch consumes exactly that grounded flag.

**Impact:** the new rule cannot reliably claim that grounded witnesses avoid dynamic classes/out-of-domain subclass values. This is separate from the already disclosed semantic limitation that valid criterion IDs and observed output do not themselves prove logical impossibility.

**Fix:** default unknown constructs/call origins to unconstrained; use a small positive AST/call/import grammar or a restricted witness format with trusted evaluation. If aliases are supported, resolve imported/assigned callable origins, including reassignments, and reject dynamic constructors through aliases and indirect calls. Do not fix this by merely blacklisting the example alias. Keep such evidence NEEDS HUMAN unless the constraint is established.

**Acceptance:** direct `type`, imported/assigned aliases of `type`, aliases of forbidden dynamic-code functions, `types.new_class` and indirect constructor paths must be unconstrained/held. Keep a genuine literal-input trusted-reference witness as the positive control. Test pipeline classification and the offline checker, not only the helper's error strings.

## Observed product tradeoff

The recorded revision-6 batch (`reports/attest-revision5-repairs-2026-10-19/evaluation-codex/RESULTS.md:12–14`) has durationkit VERIFIED/correct and kvparse VERIFIED/correct; RLE is NEEDS HUMAN with no patch. RLE cites mixed task/derived criteria, so a safe hold replaces the earlier automatic INFEASIBLE. This is improved false-refusal handling with more human escalation, not proof that all contradiction reasoning is solved or a correctness advantage over a baseline. The all-seven-closures claim still needs the concrete R5-03 gap above addressed.

## Reproduce

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B reports/attest-revision6-review-2026-10-19/core-repro.py
```

[Script](core-repro.py) · [Exact results and current source hashes](core-repro-results.json). Temporary copied bundles are removed; only this new audit result is persisted.
