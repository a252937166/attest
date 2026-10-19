# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: NEEDS HUMAN**  
Run `semver-long-prerelease-pr488-attest-a1-20261017T153144999808Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T15:31:45.000676+00:00, finished 2026-10-17T15:42:43.091411+00:00.

**Hold this patch.** 1 of the 20 sealed acceptance tests fail on the candidate. The sealed tests were written before the patch from the task statement; each failure is either a missing behaviour or a test that misreads the request.

Key evidence (E1): test_core_precedence_skips_bad_prerelease_conversion: ValueError: too many values to unpack (expected 2)



What to do: Read the failing sealed test and decide whether it states the requirement correctly. If it does, the implementation is incomplete; if not, correct the task statement and run again.

Reasons: child process nonzero exit: test_core_precedence_skips_bad_prerelease_conversion exit 1
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; arbitration (advisory): generated-test failures could not be cleared by arbitration; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- 1 sealed acceptance test(s) fail on the candidate (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- A model audit found the work aligned with the request (score 0.06, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- Anything about mutation resistance: the mutation check did not run (E2).
- Anything from tests written after the patch: that stage did not run (E3).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | FAIL | bound | 9 of 20 failed on the unmodified base; 19 of 20 pass on the candidate; binding FAILED |
| E2 | Mutation check | not run | bound | not run: verification did not pass |
| E3 | Tests written after the patch | not run | bound | not run: verification did not pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0.06, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | generated-test failures could not be cleared by arbitration; human review required |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `4c1f95b0f1c13ddc44498ea7e4cb5191e1250819ffcae4d9877b065dbb344246`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `e9901f1d-2e18-4589-9072-1662d9867d12`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `36369c7b57230897` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-freeze-2026-10-17/evaluation-newtasks-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Fix prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without integer conversion, while preserving existing version precedence, constructor permissiveness, Unicode-digit integer semantics, eager conversion errors, parsing restrictions, and public APIs. Limit implementation changes to this file's prerelease comparison logic and keep the existing pytest suite unchanged and passing.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version (also semver.Version and VersionInfo) | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Preserve construction unchanged. Core parts are converted to integers. Prerelease and build are stored as None or str(argument); string prereleases retain their | ValueError: a converted core component is negative.; TypeError or ValueError: existing core integer conversion fails. Preserve existing constructor errors. |
| Version._nat_cmp | @classmethod _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Retain this existing internal comparison entry point. Split each value on dots, treating None and empty string as one empty identifier. A nonempty identifier co | ValueError: any non-ASCII-containing identifier has str.isdigit() true but int(identifier) fails, even if an earlier identifier or the list lengths would determ |
| Version.compare | compare(self, other: Comparable) -> int | Preserve existing operand coercion for Version, str, bytes, dict, tuple, and list. Return exactly -1, 0, or 1. Compare major, minor, and patch first; a core dif | TypeError: unsupported operand type, preserving existing behavior.; TypeError or ValueError: existing operand parsing or construction fails.; ValueError: equal- |
| Version comparison operators | __eq__(self, other: Comparable) -> bool; __ne__(self, other: Comparable) -> bool; __lt__(self, other: Comparable) -> bool; __le__(self, other: Comparable) -> bool; __gt__(self, other: Comparable) -> bool; __ge__(self, other: Comparable) -> bool | Continue deriving results from compare, so equality, ordering, and sorting support long ASCII numeric prereleases. Preserve the existing decorator's NotImplemen | ValueError: propagate prerelease comparison errors for successfully constructed equal-core operands.; Preserve existing parsing errors and Python operator behav |
| Version.parse | @classmethod parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Remain unchanged. Accept canonical prereleases containing arbitrarily long ASCII numeric identifiers, retaining their text. Continue strict prerelease validatio | ValueError: invalid SemVer input, including prereleases '01', '01.2', '١٢', and '１２'.; TypeError: unsupported input type. Preserve existing byte decoding and ot |
| Version.is_valid | @classmethod is_valid(cls, version: str) -> bool | Remain unchanged: return True when parse succeeds and False when parse raises ValueError. A canonical 5000-digit ASCII numeric prerelease is valid. | Errors other than ValueError retain their existing propagation behavior. |
| semver.compare | compare(ver1: str, ver2: str) -> int | Preserve the existing deprecated wrapper and warning behavior. Its delegation to Version.parse(ver1).compare(ver2) must inherit the fixed long-identifier compar | Preserve parsing and comparison exceptions from the delegated operations. |
| Version.replace | replace(self, **parts: Union[int, Optional[str]]) -> "Version" | Remain unchanged: return a new instance with requested parts replaced. Replacing only build metadata must preserve comparison equality, including for long numer | TypeError: unknown replacement keys, preserving existing behavior.; Preserve other errors from constructing the replacement instance. |

Acceptance criteria:
1. 1. With v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) == 0, semver.compare(v, '0.0.0-2') == 1, and semver.compare('0.0.0-2', v) == -1, without ValueError.
2. 2. For each prerelease pair (low, high): ('9' * 4999, '1' + '0' * 4999), ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'), ('1' * 5000, 'alpha'), and ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'), parse each with core 0.0.0 and verify low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
3. 3. For version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). Reverse comparisons have the corresponding opposite ordering.
4. 4. Using equal-core directly constructed versions, verify these (left, right, result) cases: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Reverse comparisons return the negated result, and each prerelease attribute remains exactly as supplied.
5. 5. Directly constructed prereleases '0' * 5000 and '0' compare equal; '0' * 5000 + '12' compares equal to both '12' and '١٢'; '1' * 5000 compares greater than '１２'. No ASCII numeric identifier is converted to an integer, including when compared with a legacy Unicode numeric identifier.
6. 6. Identifier boundaries and empty parts retain their meaning: Version._nat_cmp('', None) == 0, Version._nat_cmp('a', 'a.') == -1, Version._nat_cmp('a..b', 'a..c') == -1, and Version._nat_cmp('0', '') == -1. At the public version level, prerelease '0' remains lower than an absent prerelease.
7. 7. Version.parse('0.0.0-' + p) raises ValueError for each p in ('01', '01.2', '١٢', '１２'); Version.is_valid returns False for the same strings.
8. 8. Equal-core directly constructed versions raise ValueError for prerelease pairs ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), in both operand orders. Also verify eager failures beyond the shorter list's end, such as ('a', 'a.²'), and against an absent prerelease, such as ('²', None). No exact exception message is required.
9. 9. Version(0, 0, 0, prerelease='²') < Version(1, 0, 0, prerelease='²') is True without error. Independently verify that differing minor and patch components likewise decide ordering without examining these prereleases.
10. 10. Run long-ASCII regression checks on a CPython interpreter with an active decimal integer-string limit below 5000 digits, such as the default 4300. The implementation must neither disable nor alter that limit. Review the changed comparison path to verify ASCII numeric values use normalized length and string comparison rather than integer conversion.
11. 11. The existing pytest suite passes unchanged, including operand handling, subclass, parsing, optional-backend, and comparison regressions. Implementation changes are confined to prerelease comparison logic in src/semver/version.py.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d1085c068233a23d987bc9e2bb3021a401eb0183ecbd87d4a4ba66aadfc2f81a`, 20 test methods, sealed at 2026-10-17T15:35:14.168954+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 20 methods: ERROR 9): 9 of 20 methods failing, 11 passing; operation `01a14a80-b32e-77bf-bdf4-5a09067918b5`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedPrereleaseComparison.test_canonical_5000_digit_prerelease_parses_and_compares | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_compare_coerces_supported_operand_types | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_comparison_operators_derive_from_long_numeric_compare | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_constructor_remains_permissive_and_core_errors_remain | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_core_precedence_skips_bad_prerelease_conversion | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_digits_and_warns | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_direct_constructor_numeric_and_text_identifiers | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_identifier_boundaries_and_empty_parts | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_legacy_digit_conversion_errors_are_eager_in_both_orders | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_legacy_unicode_digits_keep_integer_conversion_limit | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_ascii_comparison_respects_active_integer_string_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_leading_zeros_and_mixed_unicode_numeric_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_numeric_and_identifier_precedence | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_prerelease_release_precedence_and_build_replacement | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_operators_propagate_legacy_conversion_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parse_bytes_and_optional_components_still_work | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parser_rejects_noncanonical_and_unicode_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_public_class_alias | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_replace_rejects_unknown_parts | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_unsupported_operands_preserve_compare_and_operator_behavior | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,23 +185,27 @@
 
     @classmethod
     def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int:
-        def cmp_prerelease_tag(a, b):
-            if isinstance(a, int) and isinstance(b, int):
-                return _cmp(a, b)
-            elif isinstance(a, int):
-                return -1
-            elif isinstance(b, int):
-                return 1
+        def normalize(identifier: str):
+            if identifier and all("0" <= digit <= "9" for digit in identifier):
+                return True, identifier.lstrip("0") or "0"
+            if identifier.isdigit():
+                # Preserve integer conversion and its errors for Unicode digits.
+                return True, str(int(identifier))
+            return False, identifier
+
+        # Normalize both lists before comparing so Unicode conversion errors are eager.
+        a_parts = [normalize(x) for x in (a or "").split(".")]
+        b_parts = [normalize(x) for x in (b or "").split(".")]
+
+        for (a_numeric, sub_a), (b_numeric, sub_b) in zip(a_parts, b_parts):
+            if a_numeric != b_numeric:
+                return -1 if a_numeric else 1
+            if a_numeric:
+                result = _cmp(len(sub_a), len(sub_b)) or _cmp(sub_a, sub_b)
             else:
-                return _cmp(a, b)
-
-        a_parts = [int(x) if x.isdigit() else x for x in (a or "").split(".")]
-        b_parts = [int(x) if x.isdigit() else x for x in (b or "").split(".")]
-
-        for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
-            if cmp_result != 0:
-                return cmp_result
+                result = _cmp(sub_a, sub_b)
+            if result:
+                return result
 
         return _cmp(len(a_parts), len(b_parts))
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (20 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (1 of 20 methods: ERROR 1). Operation `01a14a85-8c8e-71b9-ba0d-7f6de5bc970f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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
| no_nonzero_exit | FAIL |
| no_signal | pass |
| no_timeout | pass |
| no_missing_or_forged_result | pass |
| all_expected_pass | FAIL |
| no_startup_hooks_on_import_path | pass |
| canary_must_pass_ok | pass |
| canary_must_fail_failed | pass |

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.84s (424 passed of 424); operation `01a14a85-b2e8-74f6-8bd4-2fe573ef9858`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.84s |
| sealed_binding | Sealed tests, nonce-bound | FAIL | bound | E1 | child process nonzero exit: test_core_precedence_skips_bad_prerelease_conversion exit 1 |
| mutation | Mutation check | not run | bound | E2 | not run: verification did not pass |
| adversarial_tests | Tests written after the patch | not run | bound | E3 | not run: verification did not pass |
| drift_audit | Drift audit | pass | model | E5 | score 0.06 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: sealed_binding, mutation (not run), adversarial_tests (not run).

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutation pass not run (verification did not pass).

(none)

E3: model-written adversarial tests: not run.



### Counterexamples
- E1 `test_core_precedence_skips_bad_prerelease_conversion`: ERROR; ValueError: too many values to unpack (expected 2); arbiter: Defective test, by the arbiter; contract basis: Version.compare must decide differing major, minor, or patch components before examining prereleases, including prereleases whose legacy integer conversion would fail (acceptance criterion 9).

## 8. E5 Drift audit
Score 0.060 (aligned; threshold 0.6). The diff solves the stated comparison bug within scope: `identifier.lstrip("0") or "0"` and length/string comparisons avoid ASCII integer conversion, while `str(int(identifier))` and eager normalization of both lists preserve legacy Unicode behavior. The reported 424 passing tests and one skip are supported by tool output, but the required limit-sensitive regression verification is not demonstrated.

Scope narrowed: Verification omitted the explicit long-ASCII regression checks under a confirmed active integer-string limit below 5000 digits (criterion 10). The trail shows only the existing pytest suite; it does not show execution of the supplied acceptance cases.  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
generated-test failures could not be cleared by arbitration; human review required (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_core_precedence_skips_bad_prerelease_conversion | test_defect | The loop attempts to unpack each six-element tuple into two variables, raising ValueError before any candidate comparison runs. The intended | Version.compare must decide differing major, minor, or patch components before examining prereleases, including prereleases whose legacy int |

- `sealed` corrected re-run: candidate OK (20 of 20 methods, each in its own process); base FAILED (8 of 20 methods: ERROR 8); cleared=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 36986 | 2490 | 0 | - | 98.0s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36147 | 4247 | 0 | - | 77.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 13363 | 132 | 7168 | - | 26.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 15793 | 135 | 7168 | - | 17.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 31038 | 272 | 22528 | - | 22.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 14947 | 127 | 7168 | - | 15.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 32156 | 294 | 23040 | - | 25.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 16052 | 107 | 7168 | - | 19.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 16292 | 131 | 7168 | - | 38.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 33566 | 166 | 23680 | - | 26.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-9 | medium | 35037 | 315 | 24448 | - | 27.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-10 | medium | 17383 | 798 | 7168 | - | 27.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-11 | medium | 17536 | 132 | 7168 | - | 16.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-12 | medium | 17891 | 151 | 7168 | - | 25.5s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13865 | 247 | 0 | - | 26.0s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-sealed | medium | 16538 | 3306 | 0 | - | 77.5s | ok |

Model calls: 16 (0 failed, 0 malformed); tokens in/out/cached 364590/13050/151040; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a14a7d-b122-740c-93ed-36c7ddd3b09a | SUCCESS | 0 | 0.701s | retained | off | 0.0012095699999999999 |
| checkpoint | 01a14a7d-c768-76c2-9c88-d9b3fa7fa3f5 | SUCCESS | 0 | 3.511s | retained | on | 0.02347872 |
| red-1 | 01a14a80-b32e-77bf-bdf4-5a09067918b5 | SUCCESS | 0 | 5.086s | disposable | off | 0.042798289999999996 |
| impl-python-3 | 01a14a81-dbb0-7418-aa6e-d76d7af9a34b | SUCCESS | 0 | 0.612s | disposable | off | 0.0018703600000000002 |
| impl-python-5 | 01a14a82-8886-727e-93dd-d6382ad17cf8 | SUCCESS | 0 | 0.623s | disposable | off | 0.0019144099999999999 |
| impl-python-9 | 01a14a84-49c6-7271-a98a-9c1dc13cfa71 | SUCCESS | 0 | 1.612s | disposable | off | 0.0018595200000000001 |
| impl-tests-11 | 01a14a85-0e74-73f2-bc1e-d3a2828891dd | SUCCESS | 0 | 1.872s | disposable | off | 0.01097473 |
| verify | 01a14a85-8c8e-71b9-ba0d-7f6de5bc970f | SUCCESS | 0 | 5.062s | disposable | off | 0.04291128 |
| existing | 01a14a85-b2e8-74f6-8bd4-2fe573ef9858 | SUCCESS | 0 | 1.853s | disposable | off | 0.01095929 |
| arbitrate-sealed-candidate | 01a14a87-6265-7723-8eaa-8028eadf9a73 | SUCCESS | 0 | 6.03s | disposable | off | 0.04272095000000001 |
| arbitrate-sealed-base | 01a14a87-8973-719b-b64f-576c2e527310 | SUCCESS | 0 | 5.534s | disposable | off | 0.04292608 |

Sandbox operations: 11, total guest duration 32.496s, retained images ['7c96877c-303f-441e-9a3b-54922ec4df23', 'e9901f1d-2e18-4589-9072-1662d9867d12'].

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
