# Attest Proof Bundle: Add Version.is_compatible() to python-semver (upstream issue #284), contract resolved against upstream tests

**Verdict: VERIFIED**  
Run `semver-is-compatible-pr368-v2-attest-a1-20261017T131508429133Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T13:15:08.432109+00:00, finished 2026-10-17T13:24:27.260628+00:00.

**Accept this patch.** All 23 sealed tests pass on the candidate in a fresh sandbox, and 20 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 23 of 23 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; 1 mutant(s) were unknown and excluded from the score

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 20 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 11 of 11 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 3 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 20 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 11 one-line mutants caught, 0 survived, 1 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-is-compatible-pr368-v2`, spec digest `2acbd8a4dda7f574825346d14f262789583c45b4ca81ec57676b3d4189a624d4`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `d38cea8c-ff1e-429e-9146-a0bcb976870e`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `b7fdd9eb0b71d237` (34 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `ad6ba42b83a3bbd1`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-reliability-2026-10-17/evaluation-paced-codex/snapshot/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 14, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `9b475f71ef9176b57f15bac8cde75df15469c75b`; parent of PR #368 (upstream issue #284); the held-out tests are the pull request's own tests from merge commit 467ea0c7c198d60e0d88e32ee4d926b4e20eb74a.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Maintainers want a concise, readable way to ask 'is version y compatible with the version x that my code was written against?' (upstream issue #284). Add an instance method Version.is_compatible(other) -> bool to the Version class in src/semver/version.py. Semantics: the call `old.is_compatible(new)` returns True when `new` can be used in place of `old`. Two versions are compatible when their majors are equal, the minor of `new` is greater than or equal to the minor of `old`, and their prerelease parts are equal (both absent counts as equal). The patch part is ignored. Versions with major 0 are special: a major-0 version is compatible only with a version that is identical in major, minor, patch and prerelease. If `other` is not a Version (instances of Version subclasses are fine) raise TypeError with the message 'Expected a Version type but got <type of other>' (for example "Expected a Version type but got <class 'str'>"); the message must start with 'Expected a Version type ' followed by the words 'but got' and the type. Document the method with a docstring that includes at least two doctest examples. Do not change any other public behaviour, do not touch tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Add Version.is_compatible(other) in src/semver/version.py to determine whether the supplied replacement version can be used in place of the receiver. Accept Version instances and subclasses, apply directional minor compatibility for nonzero majors and exact major/minor/patch/prerelease matching for major zero, ignore build metadata throughout, and reject all other argument types with the specified TypeError. Document the method with at least two working doctest examples while preserving existing public behavior and leaving all other files unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version.is_compatible | def is_compatible(self, other: "Version") -> bool | Public instance method, also available through semver.Version and the existing VersionInfo alias. The required other argument accepts positional or keyword invo | TypeError: for any other that is not an instance of Version or a subclass, raise with exactly the message f"Expected a Version type but got {type(other)}". Vali |

Acceptance criteria:
1. 1. The method is callable using imports from both semver and semver.version, and through the existing VersionInfo alias; positional other and keyword other= invocations give identical results.
2. 2. Version(1, 2, 3).is_compatible(Version(1, 2, 3)), Version(1, 2, 3).is_compatible(Version(1, 2, 4)), and Version(1, 2, 4).is_compatible(Version(1, 2, 3)) each return True.
3. 3. Version(1, 2, 9).is_compatible(Version(1, 3, 0)) returns True; reversing these operands returns False. Version(1, 1, 0).is_compatible(Version(1, 0, 0)) returns False.
4. 4. Different majors return False in both directions, including 1 versus 2 and 0 versus 1, regardless of minor, patch, or matching prerelease.
5. 5. Version(1, 2, 3, 'rc.0').is_compatible(Version(1, 2, 4, 'rc.0')) returns True. Equal prereleases also permit a higher replacement minor for matching nonzero majors.
6. 6. Different prereleases return False even when the replacement minor increases. Specifically, 'rc.1' versus 'rc.0', None versus 'rc1', and 'rc1' versus None are incompatible. Matching is case-sensitive; None and an empty string are distinct.
7. 7. Version(0, 1, 0).is_compatible(Version(0, 1, 0)) returns True. Changing only patch, minor, or prerelease returns False in either direction. Identical major-zero versions with an equal nonempty prerelease return True.
8. 8. Build metadata never affects compatibility: versions with otherwise matching required fields remain compatible when builds differ or only one build is absent, for both zero and nonzero majors. Build equality cannot make otherwise incompatible versions compatible.
9. 9. For receivers with major zero and nonzero, inputs 'wrongtype', {'a': 2}, [], '1.2.3', b'1.2.3', (1, 2, 3), None, 1, and an unrelated object each raise TypeError with message exactly equal to 'Expected a Version type but got ' followed by str(type(input)).
10. 10. With an ordinary subclass CustomVersion(Version), base-to-subclass, subclass-to-base, and subclass-to-subclass calls accept the argument and apply the same rules, including for major zero. In particular, CustomVersion(1, 0, 0).is_compatible(Version(1, 0, 0)) returns True.
11. 11. Successful calls return the singleton True or False, and all calls leave both version operands' fields unchanged.
12. 12. The method has a nonempty docstring containing at least two executable compatibility examples with expected outputs; those examples pass when evaluated with their documented imports or the repository's supplied doctest namespace.
13. 13. Only src/semver/version.py is modified. The existing tests/ pytest suite passes without edits, and existing construction, parsing, comparisons, aliases, immutability, formatting, bumping, matching, deprecated functions, and CLI behavior remain unchanged.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `e751c30e616dd336a14425141a8be07698a24e067e0fdaeda07e3c7a73ba8bf5`, 23 test methods, sealed at 2026-10-17T13:18:07.086001+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (20 of 23 methods: ERROR 20): 20 of 23 methods failing, 3 passing; operation `01a14a03-2221-70cb-83f4-6d50edfda2d1`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestCompatibility.test_base_and_subclass_arguments_are_accepted | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_build_metadata_is_ignored_for_both_major_rules | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_calls_do_not_mutate_either_operand | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_different_majors_are_incompatible_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_different_prereleases_are_incompatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_docstring_describes_rules_and_contains_two_result_examples | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_equal_build_cannot_override_incompatible_fields | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_equal_prerelease_allows_patch_and_minor_changes | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_every_successful_result_is_a_bool_singleton | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_existing_comparison_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_existing_parse_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_existing_readonly_property_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_invalid_argument_is_rejected_before_field_access | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_invalid_argument_types_for_major_zero | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_invalid_argument_types_for_nonzero_major | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_major_zero_identical_required_fields_are_compatible | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_major_zero_requires_exact_patch_minor_and_prerelease | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_none_and_empty_prerelease_are_distinct | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_nonzero_major_ignores_patch_in_both_directions | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_nonzero_major_minor_rule_is_directional | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_positional_and_keyword_other | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_public_imports_and_aliases | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_subclass_arguments_follow_major_zero_rule | ERROR (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -200,6 +200,41 @@
     def build(self, value):
         raise AttributeError("attribute 'build' is readonly")
 
+    def is_compatible(self, other: "Version") -> bool:
+        """Return whether ``other`` can replace this version.
+
+        For a nonzero major version, the majors and prereleases must match,
+        and the replacement's minor version must be at least this version's
+        minor version. For major zero, major, minor, patch, and prerelease
+        must all match. Build metadata is ignored in both cases.
+
+        :param other: the replacement Version
+        :return: True if the replacement is compatible, otherwise False
+        :raises TypeError: if ``other`` is not a Version instance
+
+        >>> semver.Version(1, 2, 9).is_compatible(semver.Version(1, 3, 0))
+        True
+        >>> semver.Version(1, 3, 0).is_compatible(semver.Version(1, 2, 9))
+        False
+        >>> semver.Version(0, 1, 0, build="a").is_compatible(semver.Version(0, 1, 0, build="b"))
+        True
+        """
+        if not isinstance(other, Version):
+            raise TypeError(f"Expected a Version type but got {type(other)}")
+
+        if self.major == 0:
+            return (
+                self.major == other.major
+                and self.minor == other.minor
+                and self.patch == other.patch
+                and self.prerelease == other.prerelease
+            )
+        return (
+            self.major == other.major
+            and other.minor >= self.minor
+            and self.prerelease == other.prerelease
+        )
+
     def to_tuple(self) -> VersionTuple:
         """
         Convert the Version object to a tuple.
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (35 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a14a06-0816-753a-9ab9-69f87a41d45b`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| nonce_matches | pass |
| no_discovery_error | pass |
| expected_test_ids_present | pass |
| no_unexpected_test_ids | pass |
| no_nonzero_exit | pass |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | pass |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `stdout`): 312 passed in 0.54s (312 passed of 312); operation `01a14a06-32df-73eb-b99d-487ab71f25fc`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 312 passed in 0.54s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 11 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 11 evaluated: 11 killed, 0 survived, 1 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-6f2e41cb85 | src/semver/version.py | 222 | remove `not` | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_positional_and_keyword | 01a14a06-4dae-715d-86dd-23a2f84d5f7e |
| m02-8f1a2a4d9c | src/semver/version.py | 223 | raise -> pass | killed | test_sealed.TestCompatibility.test_invalid_argument_types_for_nonzero_major, test_sealed.TestCompatibility.test_invalid_ | 01a14a06-4da1-74c8-89c6-7181c053eb78 |
| m03-be60e54db7 | src/semver/version.py | 225 | 0 -> 1 | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_nonzero_major_ignores_ | 01a14a06-4d81-77a9-bf79-08f27e931697 |
| m04-13d6e9bfad | src/semver/version.py | 225 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_nonzero_major_ignores_ | 01a14a06-4df4-704b-91f2-94db6f2380ef |
| m05-daa51c2554 | src/semver/version.py | 227 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_different_majors_are_incompatible_both_directions, test_sealed.TestCompatibility.test | 01a14a06-4d83-700d-8a76-0fb2d6a3eb0a |
| m06-ea8d8a0446 | src/semver/version.py | 228 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_major_zero_identical_required_fields_are_compatible, test_sealed.TestCompatibility.te | 01a14a06-4cdc-71da-bf32-2c7588612138 |
| m07-b5d8fee51d | src/semver/version.py | 229 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_major_zero_identical_required_fields_are_compatible, test_sealed.TestCompatibility.te | 01a14a06-4db8-720b-a27e-1b7622e3bf32 |
| m08-64e9d487f1 | src/semver/version.py | 230 | Eq -> NotEq | unknown |  | None |
| m09-091a822907 | src/semver/version.py | 227 | And -> Or | killed | test_sealed.TestCompatibility.test_different_majors_are_incompatible_both_directions, test_sealed.TestCompatibility.test | 01a14a06-74c1-7022-8098-84077588dcd0 |
| m10-9163b55128 | src/semver/version.py | 233 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_nonzero_major_ignores_ | 01a14a06-7bcb-73c6-8ecb-3ad59968baeb |
| m11-c952749814 | src/semver/version.py | 234 | GtE -> Gt | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_nonzero_major_ignores_ | 01a14a06-7c75-706a-a882-1756e8c523fb |
| m12-57b6cb98ee | src/semver/version.py | 235 | Eq -> NotEq | killed | test_sealed.TestCompatibility.test_public_imports_and_aliases, test_sealed.TestCompatibility.test_nonzero_major_ignores_ | 01a14a06-7c4f-7187-b910-fc6f4e528b61 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `02b9334dc76a7c1b812ad36fa2a6c13ce6a86af8d81724677444b357f9d255fd`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a14a08-22a6-7475-945a-2577900af68c`. Notes: Targets numeric boundaries, exact prerelease matching, subclass receivers, additional invalid types, and build interactions.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task: `isinstance(other, Version)` accepts subclasses and enforces the exact TypeError, while `other.minor >= self.minor` and explicit major-zero field equality implement the required rules without comparing builds. Only src/semver/version.py changes, three doctest examples document compatibility, and observed successful verification supports the claims that doctests, targeted edge cases, and all 312 existing tests pass.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 28681 | 1269 | 0 | - | 94.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 28199 | 3918 | 7040 | - | 58.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 10941 | 166 | 7168 | - | 17.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 25434 | 678 | 12416 | - | 36.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 11937 | 98 | 7168 | - | 25.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 12756 | 420 | 7168 | - | 24.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 12863 | 391 | 7168 | - | 27.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 13226 | 163 | 7168 | - | 19.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 11157 | 2183 | 7040 | - | 59.9s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 11880 | 144 | 0 | - | 44.3s | ok |

Model calls: 10 (0 failed, 0 malformed, 0 rejected by the provider's hourly limit and retried after waiting 13 s in total); tokens in/out/cached 167074/9430/62336; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint | 01a14a00-9ce0-7528-88b0-e0def8a607a1 | SUCCESS | 0 | 3.276s | retained | on | 0.022295920000000004 |
| red-1 | 01a14a03-2221-70cb-83f4-6d50edfda2d1 | SUCCESS | 0 | 6.235s | disposable | off | 0.05472349000000001 |
| impl-tests-3 | 01a14a04-8656-75b6-9e72-0c30e7c5248f | SUCCESS | 0 | 1.641s | disposable | off | 0.00949546 |
| impl-python-4 | 01a14a04-fa0e-7008-a8c0-bc0fcdcd81f9 | SUCCESS | 0 | 0.776s | disposable | off | 0.00304614 |
| impl-python-5 | 01a14a05-76b3-7610-a86a-6785b8547ec2 | SUCCESS | 0 | 0.774s | disposable | off | 0.00310226 |
| verify | 01a14a06-0816-753a-9ab9-69f87a41d45b | SUCCESS | 0 | 6.146s | disposable | off | 0.0543517 |
| existing | 01a14a06-32df-73eb-b99d-487ab71f25fc | SUCCESS | 0 | 1.582s | disposable | off | 0.00930517 |
| mutant-m01-6f2e41cb85 | 01a14a06-4dae-715d-86dd-23a2f84d5f7e | SUCCESS | 0 | 5.947s | disposable | off | 0.05072298 |
| mutant-m02-8f1a2a4d9c | 01a14a06-4da1-74c8-89c6-7181c053eb78 | SUCCESS | 0 | 6.024s | disposable | off | 0.051104710000000005 |
| mutant-m03-be60e54db7 | 01a14a06-4d81-77a9-bf79-08f27e931697 | SUCCESS | 0 | 5.936s | disposable | off | 0.05088279 |
| mutant-m04-13d6e9bfad | 01a14a06-4df4-704b-91f2-94db6f2380ef | SUCCESS | 0 | 5.924s | disposable | off | 0.05029267 |
| mutant-m05-daa51c2554 | 01a14a06-4d83-700d-8a76-0fb2d6a3eb0a | SUCCESS | 0 | 5.932s | disposable | off | 0.050841159999999996 |
| mutant-m06-ea8d8a0446 | 01a14a06-4cdc-71da-bf32-2c7588612138 | SUCCESS | 0 | 5.745s | disposable | off | 0.05033743 |
| mutant-m07-b5d8fee51d | 01a14a06-4db8-720b-a27e-1b7622e3bf32 | SUCCESS | 0 | 5.928s | disposable | off | 0.05072734 |
| mutant-m08-64e9d487f1 | None | UNCERTAIN | None | - | disposable | off | None |
| mutant-m09-091a822907 | 01a14a06-74c1-7022-8098-84077588dcd0 | SUCCESS | 0 | 5.757s | disposable | off | 0.05038952 |
| mutant-m10-9163b55128 | 01a14a06-7bcb-73c6-8ecb-3ad59968baeb | SUCCESS | 0 | 5.768s | disposable | off | 0.05029129 |
| mutant-m11-c952749814 | 01a14a06-7c75-706a-a882-1756e8c523fb | SUCCESS | 0 | 5.792s | disposable | off | 0.050163690000000004 |
| mutant-m12-57b6cb98ee | 01a14a06-7c4f-7187-b910-fc6f4e528b61 | SUCCESS | 0 | 5.917s | disposable | off | 0.05065417 |
| breaker-tests | 01a14a08-22a6-7475-945a-2577900af68c | SUCCESS | 0 | 2.929s | disposable | off | 0.022311820000000003 |

Sandbox operations: 20, total guest duration 88.029s, retained images ['d38cea8c-ff1e-429e-9146-a0bcb976870e'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter then classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, corrects and re-verifies them (must pass on the candidate and still fail on the base). Arbitration is advisory by default and never clears an implementation bug or a contract dispute; it changes the verdict only in explicit apply mode.
- Grounding runs only when the specification names external references; sources are cited, not verified for correctness.
- Sandbox CPU/RAM quota controls were not found in the current public REST API; per operation only max_layer_bytes, a timeout and the networking flag are set.
- Sandbox raw 'cost' diagnostics are not USD; Codex gateway usage is ChatGPT allowance, not a Nebius charge; Nebius USD is computed from the public price table, not an invoice.
- Each run retains one checkpoint image on the service; no image-delete control was found in the current public REST API.
- manifest.json lists the sha256 of every artifact and `python -m attest check <run dir or zip>` recomputes digests, the sealed and adversarial bindings from verify_raw.json and the gate-to-verdict rule offline; it cannot re-execute the sandbox runs themselves.

## 13. Artifacts
Every file of the run directory is listed in `manifest.json` with its sha256 and size (written last, so it covers this file and proof_bundle.json). `python -m attest check <run dir or zip>` recomputes the digests, the sealed and adversarial bindings from `verify_raw.json`, the ledger totals and the gate-to-verdict rule, and re-renders this document.

| Artifact | Purpose |
| --- | --- |
| proof_bundle.json | The Proof Bundle: every stage record, gate and the verdict |
| PROOF.md | Human-readable rendering of the Proof Bundle |
| manifest.json | sha256 and size of every artifact (this file) |
| task.frozen.json | Frozen task: statement, policy and repository digests |
| spec.json | Specification and contract written before any code |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
