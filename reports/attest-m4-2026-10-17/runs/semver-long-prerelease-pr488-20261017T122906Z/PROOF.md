# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: NEEDS HUMAN**  
Run `semver-long-prerelease-pr488-20261017T122906Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T12:29:06.875741+00:00, finished 2026-10-17T13:25:17.531346+00:00.

**Hold this patch.** Tests written after the patch fail on the candidate and were not arbitrated, so each failure is still an open question: a bug in the patch, a defective test or a contract gap.

Key evidence (E3): test_empty_components_and_length_after_equal_prefix: -1 != 1 (the test's first argument against its second)



What to do: Read each failing test and classify it yourself; the bundle keeps the test source and the captured output. Fix the patch or the task statement accordingly, then run again.

Reasons: adversarial suite binding failed: child process nonzero exit: test_empty_components_and_length_after_equal_prefix exit 1; model-written adversarial tests failed: 1 of 10 (test_breaker.BreakerTests.test_empty_components_and_length_after_equal_prefix); each failure is a bug or a contract disagreement to resolve
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; arbitration (advisory): generated-test failures could not be cleared by arbitration; human review required

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 20 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 6 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 11 of 11 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 1 test(s) written after the patch fail on the candidate (E3).
- The held-out tests (tests/test_heldout_pr488.py), which the implementer never saw, pass on the candidate (E4).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 14 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the held-out tests result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the arbiter's classifications are correct: arbitration is a model judgement, kept advisory, and the original tests and results are preserved (E6).
- That the patch is wrong: a failing generated test may itself be defective or may ask a question the contract leaves open (E3, E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 6 of 20 failed on the unmodified base; 20 of 20 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 11 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | FAIL | bound | 9 of 10 pass; 1 failing: test_empty_components_and_length_after_equal_prefix; binding FAILED |
| E4 | Held-out tests | pass | stdout | 450 of 450 pass (tests/test_heldout_pr488.py); parsed console output |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | generated-test failures could not be cleared by arbitration; human review required |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `f7465e98247d560502e8d61f9ba8b559918cd52cab04e4ee9f9af8b48a19d0cd`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `c2ff6ca5-1414-40eb-bd4e-633e7c43bf0b`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `01668a24b9d03791` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Change prerelease comparison in src/semver/version.py so ASCII numeric identifiers of any length compare by normalized decimal strings without integer conversion. Preserve all existing precedence rules, constructor permissiveness and stored values, Unicode-digit integer semantics and eager conversion errors, core-version short-circuiting, strict parsing, build-metadata handling, and public interfaces. Only comparison-related implementation in this file may change.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version (also semver.Version and VersionInfo) | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Constructor behavior remains unchanged: core components are converted to integers; prerelease and build are stored as None or str(value). String prereleases ret | ValueError: a converted core component is negative.; TypeError or ValueError: existing core-component integer conversion fails. |
| Version._nat_cmp | @classmethod def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Preserve this internal comparison entry point. Split each operand on dots, treating None and '' as one empty identifier and preserving empty parts. A nonempty i | ValueError: any non-ASCII-containing identifier satisfies str.isdigit() but int(identifier) fails, including an identifier after an already decisive position or |
| Version.compare | def compare(self, other: Comparable) -> int | Keep existing coercion of str/bytes through parse, dict through keyword construction, and tuple/list through positional construction. Compare major, minor, and  | TypeError: other has an unsupported type, preserving existing accepted types and subclass behavior.; TypeError or ValueError: existing operand parsing or constr |
| Version comparison operators | def __eq__(self, other: Comparable) -> bool; def __ne__(self, other: Comparable) -> bool; def __lt__(self, other: Comparable) -> bool; def __le__(self, other: Comparable) -> bool; def __gt__(self, other: Comparable) -> bool; def __ge__(self, other: Comparable) -> bool | Continue deriving results from compare, so equality, ordering, and sorting inherit the corrected numeric comparison. Preserve the existing decorator's NotImplem | ValueError: supported operands reach equal-core prerelease comparison and encounter a failing legacy Unicode conversion.; Existing parsing errors and Python ope |
| Version.parse | @classmethod def parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Remain unchanged. Accept canonical arbitrarily long ASCII numeric prerelease identifiers and preserve their spelling. Continue strict SemVer prerelease validati | ValueError: invalid SemVer syntax, including prereleases '01', '01.2', '١٢', and '１２'.; TypeError: unsupported input type.; Existing decoding and core integer-c |
| Version.is_valid | @classmethod def is_valid(cls, version: str) -> bool | Remain unchanged: return True when parse succeeds and False when parse raises ValueError. Long canonical ASCII numeric prereleases remain valid. | Exceptions other than ValueError from parse continue to propagate. |
| semver.compare | def compare(ver1: str, ver2: str) -> int | Keep the existing deprecated wrapper and warning behavior. Return Version.parse(ver1).compare(ver2), inheriting the fix without changes to _deprecated.py. | Propagate existing parsing and comparison exceptions. |

Acceptance criteria:
1. 1. For v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) == 0, semver.compare(v, '0.0.0-2') == 1, and semver.compare('0.0.0-2', v) == -1, without ValueError.
2. 2. For parsed prereleases, each following (low, high) pair yields low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high]: ('9' * 4999, '1' + '0' * 4999); ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'); ('1' * 5000, 'alpha'); ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'). Use core 0.0.0 throughout.
3. 3. With version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). Neither comparison changes stored prerelease or build values.
4. 4. For same-core constructor instances, (left prerelease, right prerelease, expected compare result) is: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Reverse comparisons negate each result. Both prerelease attributes remain exactly as supplied.
5. 5. Long leading-zero constructor identifiers also work: '0' * 5000 equals '0'; '0' * 5000 + '1' equals '1'; '0' * 5000 + '12' equals '١٢'; and '1' * 5000 is greater than '１２'. No ASCII identifier is converted to int, including for comparison with a Unicode numeric identifier.
6. 6. Version.parse('0.0.0-' + p) raises ValueError for each p in ('01', '01.2', '١٢', '１２'); constructor acceptance of these strings remains unchanged.
7. 7. Equal-core constructor comparisons raise ValueError for ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), in both directions. The failure is also eager for an unmatched suffix, such as ('a', 'a.²'), and against an absent prerelease, such as ('²', None). No exact exception message is required.
8. 8. Prerelease conversion is skipped when cores differ: instances carrying '²' compare successfully in both directions for core pairs (0,0,0)/(1,0,0), (0,0,0)/(0,1,0), and (0,0,0)/(0,0,1), returning -1 in the listed direction. The corresponding less-than expressions are True.
9. 9. Empty identifiers retain string semantics: Version._nat_cmp('', None) == 0, Version._nat_cmp('a', 'a.') == -1, and Version._nat_cmp('a.0', 'a.') == -1. At the public version level, both '' and None are equivalent absent prereleases and rank above nonempty prereleases.
10. 10. ASCII numeric comparison uses normalized decimal length followed by lexicographic order, never integer conversion, for short and long identifiers alike. The implementation does not change interpreter integer-string conversion limits or depend on disabling them. Verify the 5000-digit regressions with CPython's 4300-digit limit enabled where supported.
11. 11. Existing accepted comparison operand forms, unsupported-operand behavior, parsing, optional native parser behavior, and deprecation warnings remain unchanged. All six rich comparison operators remain consistent with compare.
12. 12. The existing pytest suite in tests/ passes without modifications. The implementation diff is confined to comparison-related code in src/semver/version.py.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `93918dd02cc3f35c6bf34732a4ba8ea7b94b885e245d424b8e0a4fcc619d2e03`, 20 test methods, sealed at 2026-10-17T13:16:22.807113+00:00 by `gpt-6-sol`; attempts: 3.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (6 of 20 methods: ERROR 6): 6 of 20 methods failing, 14 passing; operation `01a14a01-8e1f-708d-8a88-7b4571974ed8`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedPrereleaseComparison.test_absent_prereleases_are_equivalent_and_follow_nonempty_ones | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_all_rich_operators_follow_long_numeric_compare | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_build_metadata_does_not_affect_long_prerelease_precedence_or_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_compare_accepts_existing_operand_forms | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_compare_propagates_supported_operand_parse_and_construction_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_constructor_identifiers_keep_legacy_ordering_and_spelling | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_constructor_keeps_core_conversion_and_permissive_metadata | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_different_core_components_short_circuit_bad_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_empty_identifiers_keep_string_and_list_length_semantics | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_legacy_unicode_integer_limit_and_ascii_comparison_with_limit_enabled | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_leading_zero_identifiers_compare_with_ascii_and_unicode | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifiers_order_in_both_directions_and_sort | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_numeric_tags_precede_text_and_normalized_decimal_order_is_exact | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parse_keeps_bytes_decoding_and_optional_minor_patch_rules | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parse_rejects_invalid_prereleases_accepted_by_constructor | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_rich_operators_propagate_equal_core_unicode_conversion_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_subclass_parse_and_versioninfo_alias_remain_available | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_unicode_conversion_errors_are_eager_across_both_full_lists | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_unsupported_operands_and_invalid_collections_keep_operator_fallback | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 10 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,22 +185,26 @@
 
     @classmethod
     def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int:
-        def cmp_prerelease_tag(a, b):
-            if isinstance(a, int) and isinstance(b, int):
-                return _cmp(a, b)
-            elif isinstance(a, int):
-                return -1
-            elif isinstance(b, int):
-                return 1
+        def normalize(identifier: str) -> Tuple[bool, str]:
+            if identifier and identifier.isdigit():
+                if identifier.isascii():
+                    return True, identifier.lstrip("0") or "0"
+                return True, str(int(identifier))
+            return False, identifier
+
+        # Convert both complete lists before comparing so invalid Unicode digit
+        # identifiers raise even after an earlier position determines precedence.
+        a_parts = [normalize(x) for x in (a or "").split(".")]
+        b_parts = [normalize(x) for x in (b or "").split(".")]
+
+        for (a_numeric, sub_a), (b_numeric, sub_b) in zip(a_parts, b_parts):
+            if a_numeric != b_numeric:
+                return -1 if a_numeric else 1
+            if a_numeric:
+                cmp_result = _cmp(len(sub_a), len(sub_b)) or _cmp(sub_a, sub_b)
             else:
-                return _cmp(a, b)
-
-        a_parts = [int(x) if x.isdigit() else x for x in (a or "").split(".")]
-        b_parts = [int(x) if x.isdigit() else x for x in (b or "").split(".")]
-
-        for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
-            if cmp_result != 0:
+                cmp_result = _cmp(sub_a, sub_b)
+            if cmp_result:
                 return cmp_result
 
         return _cmp(len(a_parts), len(b_parts))
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (19 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (20 of 20 methods, each in its own process). Operation `01a14a07-3143-7680-a26a-4be93fd92445`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.83s (424 passed of 424); operation `01a14a07-68ed-70d6-828a-e88a4c016d2c`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite (evidence class `stdout`; tests/test_heldout_pr488.py): 450 passed, 1 skipped in 0.88s (450 passed of 450); operation `01a14a07-83c4-7777-a1b6-219504f8313f`. Gate: failures block VERIFIED.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.83s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| heldout_suite | Held-out tests | pass | stdout | E4 | 450 passed, 1 skipped in 0.88s |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 11 mutants |
| adversarial_tests | Tests written after the patch | FAIL | bound | E3 | FAILED (1 of 10 methods: FAIL 1) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived NEEDS HUMAN; blocking: adversarial_tests.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 11 generated, 11 evaluated: 11 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-b51e2c5b2a | src/semver/version.py | 189 | And -> Or | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifiers_order_in_both_directions_and_sort, test_sealed.T | 01a14a07-a83e-72cb-b1c3-c19540d8e596 |
| m02-1157dbb718 | src/semver/version.py | 191 | True -> False | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-a17e-70bc-be38-38720142cfef |
| m03-a25d63edad | src/semver/version.py | 191 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-a1bd-75eb-9e46-82f8dcb698e7 |
| m04-2bf44037df | src/semver/version.py | 192 | True -> False | killed | test_sealed.TestSealedPrereleaseComparison.test_constructor_identifiers_keep_legacy_ordering_and_spelling, test_sealed.T | 01a14a07-a10b-70f8-b164-be8fb5a028ea |
| m05-a8bb642650 | src/semver/version.py | 193 | False -> True | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifiers_order_in_both_directions_and_sort, test_sealed.T | 01a14a07-a168-777e-be2f-b6e5a8f4f90e |
| m06-35e869d479 | src/semver/version.py | 197 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-a157-71f8-a7c0-f57b34848d0d |
| m07-ca331d568c | src/semver/version.py | 198 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-a142-76ab-bbbb-3d093653ee1d |
| m08-5af987bea7 | src/semver/version.py | 201 | NotEq -> Eq | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-a15e-719c-aa49-efd548ca0a7f |
| m09-4b03dd6098 | src/semver/version.py | 202 | 1 -> 2 | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifiers_order_in_both_directions_and_sort, test_sealed.T | 01a14a07-bcc2-7532-8100-1bd8294391dc |
| m10-8db852c51b | src/semver/version.py | 202 | 1 -> 2 | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifiers_order_in_both_directions_and_sort, test_sealed.T | 01a14a07-c543-7284-a759-10f2095a4faa |
| m11-fe732ef7a8 | src/semver/version.py | 204 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_canonical_identifier_parses_and_deprecated_compare_warns, test_seal | 01a14a07-c872-738f-9a1a-0d3dff5c355c |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `7ffb125d9d285f84119197371911b4d00d3da10640ec073311656b542cba915d`): FAILED (1 of 10 methods: FAIL 1); binding FAILED; operation `01a14a08-d673-741c-88df-106446b2e20a`. Notes: Targets reduced integer limits, Unicode decimal variants, eager error validation, empty components, coercion, and strict parsing boundaries.

| Failing adversarial test | Outcome |
| --- | --- |
| test_empty_components_and_length_after_equal_prefix | FAIL |

### Counterexamples
- E3 `test_empty_components_and_length_after_equal_prefix`: FAIL; AssertionError: -1 != 1; first `-1` vs second `1` (the test's argument order decides which is the actual value)

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated comparison bug within _nat_cmp: `identifier.lstrip("0") or "0"` and length-then-lexicographic comparison avoid ASCII integer conversion, while `str(int(identifier))` and complete-list normalization preserve Unicode numeric behavior and eager errors. No unrelated code changes appear, and the observed test output supports the reported 424 passed and 1 skipped, although the trail does not show dedicated 5000-digit regression checks with the conversion limit enabled.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
generated-test failures could not be cleared by arbitration; human review required (mode: advisory). Classifications: {'implementation_bug': 0, 'test_defect': 0, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; arbitration is advisory unless apply mode is on, and never flips an implementation bug or contract dispute

(none)

- `adversarial` corrected re-run: candidate n/a; base n/a; cleared=False; error: arbiter call failed: HTTP 502 from https://development-gateway.invalid/run: {"type":"error","error":{"message":"Invalid schema for response_format 'codex_output_schema': 'schema.properties.classifications.items.required' is required to include every key in properties. Missing 'defect_kind'.","type":"invalid_request_error","param":"text.format.schema","code":"invalid_json_sc

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 36964 | 2423 | 0 | - | 83.7s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | - | - | - | - | 275.2s | error |
| codex_gateway:gpt-6-sol | seal | seal-2 | medium | - | - | - | - | 381.2s | error |
| codex_gateway:gpt-6-sol | seal | seal-3 | medium | 36076 | 5325 | 7040 | - | 77.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 13299 | 92 | 7168 | - | 44.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 15726 | 105 | 7168 | - | 61.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 15184 | 125 | 7168 | - | 30.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 15636 | 109 | 7168 | - | 35.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 15919 | 129 | 7168 | - | 25.7s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 15785 | 223 | 7168 | - | 30.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 32818 | 194 | 23296 | - | 38.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 33885 | 955 | 23808 | - | 37.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-9 | medium | 34735 | 226 | 7168 | - | 24.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-10 | medium | 17789 | 218 | 7168 | - | 18.7s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12345 | 2621 | 7040 | - | 59.3s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13617 | 205 | 0 | - | 31.5s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial | medium | - | - | - | - | 14.1s | error |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-adversarial-repair | medium | - | - | - | - | 15.2s | error |

Model calls: 18 (4 failed, 0 malformed, 0 rejected by the provider's hourly limit and retried after waiting 1980 s in total); tokens in/out/cached 309778/12950/118528; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a149d6-90dd-727f-be85-8cbb60aa70e6 | SUCCESS | 0 | 0.696s | retained | off | 0.0011738500000000002 |
| checkpoint | 01a149d6-ae5a-7230-8091-d247a9310d34 | SUCCESS | 0 | 3.502s | retained | on | 0.02344449 |
| red-3 | 01a14a01-8e1f-708d-8a88-7b4571974ed8 | SUCCESS | 0 | 4.978s | disposable | off | 0.04290149 |
| impl-python-6 | 01a14a05-2a89-758c-9bef-d0bb1dc11c78 | SUCCESS | 0 | 0.589s | disposable | off | 0.0018368800000000002 |
| impl-tests-9 | 01a14a06-cc37-7332-8b60-b01d0cedebaa | SUCCESS | 0 | 1.901s | disposable | off | 0.01092748 |
| verify | 01a14a07-3143-7680-a26a-4be93fd92445 | SUCCESS | 0 | 5.005s | disposable | off | 0.043210450000000004 |
| existing | 01a14a07-68ed-70d6-828a-e88a4c016d2c | SUCCESS | 0 | 1.857s | disposable | off | 0.01093251 |
| heldout | 01a14a07-83c4-7777-a1b6-219504f8313f | SUCCESS | 0 | 1.922s | disposable | off | 0.01128438 |
| mutant-m03-a25d63edad | 01a14a07-a1bd-75eb-9e46-82f8dcb698e7 | SUCCESS | 0 | 4.624s | disposable | off | 0.039113060000000005 |
| mutant-m02-1157dbb718 | 01a14a07-a17e-70bc-be38-38720142cfef | SUCCESS | 0 | 4.697s | disposable | off | 0.03960496 |
| mutant-m04-2bf44037df | 01a14a07-a10b-70f8-b164-be8fb5a028ea | SUCCESS | 0 | 4.645s | disposable | off | 0.03933372 |
| mutant-m06-35e869d479 | 01a14a07-a157-71f8-a7c0-f57b34848d0d | SUCCESS | 0 | 4.661s | disposable | off | 0.03929345 |
| mutant-m05-a8bb642650 | 01a14a07-a168-777e-be2f-b6e5a8f4f90e | SUCCESS | 0 | 4.657s | disposable | off | 0.03896187 |
| mutant-m01-b51e2c5b2a | 01a14a07-a83e-72cb-b1c3-c19540d8e596 | SUCCESS | 0 | 4.684s | disposable | off | 0.03920158 |
| mutant-m07-ca331d568c | 01a14a07-a142-76ab-bbbb-3d093653ee1d | SUCCESS | 0 | 4.643s | disposable | off | 0.03934859 |
| mutant-m08-5af987bea7 | 01a14a07-a15e-719c-aa49-efd548ca0a7f | SUCCESS | 0 | 4.646s | disposable | off | 0.039096990000000005 |
| mutant-m09-4b03dd6098 | 01a14a07-bcc2-7532-8100-1bd8294391dc | SUCCESS | 0 | 4.601s | disposable | off | 0.039283750000000006 |
| mutant-m10-8db852c51b | 01a14a07-c543-7284-a759-10f2095a4faa | SUCCESS | 0 | 4.604s | disposable | off | 0.03937112 |
| mutant-m11-fe732ef7a8 | 01a14a07-c872-738f-9a1a-0d3dff5c355c | SUCCESS | 0 | 4.655s | disposable | off | 0.03910666 |
| breaker-tests | 01a14a08-d673-741c-88df-106446b2e20a | SUCCESS | 0 | 2.981s | disposable | off | 0.024125709999999998 |

Sandbox operations: 20, total guest duration 74.548s, retained images ['8b2d0e0e-ef71-45f0-a857-0d021b0e6962', 'c2ff6ca5-1414-40eb-bd4e-633e7c43bf0b'].

## 11. Limitations of this bundle
- Profile 'development': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
