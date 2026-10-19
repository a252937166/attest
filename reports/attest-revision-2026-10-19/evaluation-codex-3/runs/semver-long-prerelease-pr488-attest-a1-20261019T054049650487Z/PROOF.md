# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: VERIFIED**  
Run `semver-long-prerelease-pr488-attest-a1-20261019T054049650487Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T05:40:49.650911+00:00, finished 2026-10-19T05:52:53.012985+00:00.

**Accept this patch.** All 21 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 21 of 21 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 21 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 12 sealed test(s) which already passed on the base say anything about the change (E1).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 9 of 21 failed on the unmodified base; 21 of 21 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `bebfebfc4bcfdac2b3d8de3361919f592abc7494e4052b76fab3fde2ac27bc70`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `84252770-298a-4871-b7bd-92d67c2f2a70`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `b27a1c070a852ae2` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-3/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Fix prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without integer conversion. Preserve existing numeric precedence, string ordering, identifier-list ordering, constructor permissiveness, Unicode digit conversion and eager conversion errors, core-version precedence, release precedence, and build-metadata independence. Keep public interfaces, parsing, stored attributes, and all unrelated behavior unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version (also semver.Version and VersionInfo) | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Constructor behavior remains unchanged. Core components are converted with int(). Prerelease and build are stored as None or str(argument). In particular, strin | ValueError: a converted core component is negative.; TypeError or ValueError: existing core-component integer conversion fails; preserve existing behavior. |
| Version._nat_cmp | @classmethod def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Return exactly -1, 0 or 1. Split each input on dots, treating None and the empty string as a single empty identifier and preserving other empty identifiers. A n | ValueError: any non-ASCII-containing identifier satisfies str.isdigit() but int(identifier) fails, even in an unmatched suffix or after an earlier pair that wou |
| Version.compare | def compare(self, other: Comparable) -> int | Preserve existing operand coercion for Version instances, strings, bytes, dictionaries, tuples and lists. Return exactly -1, 0 or 1. After operand coercion, com | TypeError: unsupported operand type, preserving existing handling.; ValueError or TypeError: existing operand parsing or construction fails.; ValueError: equal  |
| Version comparison operators | __eq__(self, other: Comparable) -> bool; __ne__(self, other: Comparable) -> bool; __lt__(self, other: Comparable) -> bool; __le__(self, other: Comparable) -> bool; __gt__(self, other: Comparable) -> bool; __ge__(self, other: Comparable) -> bool | Continue deriving results from compare(). Long numeric prereleases work through equality, ordering and sorted(). Preserve the existing decorator's NotImplemente | Propagate comparison-time ValueError for invalid legacy digit identifiers when cores are equal.; Preserve existing parsing errors and Python operator behavior f |
| Version.parse | @classmethod def parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Remain unchanged. Accept canonical ASCII numeric prereleases of 5000 digits and preserve their text. Reject noncanonical numeric prereleases and non-ASCII prere | ValueError: invalid SemVer syntax, including prereleases '01', '01.2', '١٢' and '１２'.; TypeError: unsupported version input type.; Preserve existing decoding an |
| Version.is_valid | @classmethod def is_valid(cls, version: str) -> bool | Remain unchanged: return True when parse succeeds and False when parse raises ValueError. A canonical 5000-digit ASCII numeric prerelease is valid. | Exceptions other than ValueError from parse retain their existing propagation behavior. |
| semver.compare | def compare(ver1: str, ver2: str) -> int | Continue delegating to Version.parse(ver1).compare(ver2), retaining its deprecation warning and exposing the corrected ordering. | Propagate existing parsing and comparison exceptions. |

Acceptance criteria:
AC1. 1. Let v = '0.0.0-' + '1' * 5000. Version.is_valid(v) is True, Version.parse(v).compare(v) is 0, semver.compare(v, '0.0.0-2') is 1, and semver.compare('0.0.0-2', v) is -1, without ValueError.
AC2. 2. For parsed prereleases, each following pair is strictly increasing: ('9' * 4999, '1' + '0' * 4999); ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'); ('1' * 5000, 'alpha'); ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'). For every pair, low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
AC3. 3. For version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). Comparison leaves prerelease text unchanged.
AC4. 4. For equal-core constructor operands, the following (left, right, result) cases hold: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), ('٠٠١', '1', 0). Reverse comparisons negate the result, and both prerelease attributes retain the supplied values.
AC5. 5. Constructor prereleases '0' * 5000 and '0' compare equal; '0' * 5000 + '12' compares equal to both '12' and '١٢'; '1' * 5000 compares greater than '١٢'. None of these comparisons converts the ASCII identifier to int or raises a digit-limit error.
AC6. 6. Version.parse('0.0.0-' + p) raises ValueError for each p in ('01', '01.2', '١٢', '１２'); Version.is_valid returns False for those strings.
AC7. 7. Equal-core constructor comparisons raise ValueError for each pair ('²', '2'), ('a.²', 'b.0'), ('a.0', 'b.²'), ('a', 'a.²'), and ('²', None), and for their reversals. Comparing a version whose prerelease is '²' with itself also raises ValueError; equality or identity shortcuts must not suppress validation.
AC8. 8. Core precedence bypasses prerelease validation for already-constructed operands: Version(0, 0, 0, prerelease='²') < Version(1, 0, 0, prerelease='²') is True. Equivalent tests where minor alone or patch alone differs also succeed, with compare returning -1 forward and 1 in reverse.
AC9. 9. Empty identifiers remain non-numeric strings. Direct helper results include Version._nat_cmp('', None) == 0, Version._nat_cmp('a.', 'a') == 1, Version._nat_cmp('a..1', 'a..2') == -1, and Version._nat_cmp('0', '') == -1. At the public version level, a numeric prerelease still precedes a release because release precedence overrides the helper's empty-string ordering.
AC10. 10. ASCII numeric comparison uses normalized decimal length followed by lexicographic order for all lengths, without int() conversion or changing interpreter integer-string conversion limits. On CPython with the conversion limit enabled at 4300 digits, the 5000-digit cases pass and the limit remains unchanged.
AC11. 11. Existing supported operand coercions, comparison operators, deprecation warnings, parsing behavior, attribute storage and build-metadata independence remain unchanged. The existing pytest suite, including tests/ and configured doctests, passes without modifying its files.
AC12. 12. The implementation diff is confined to prerelease comparison and necessary internal support in src/semver/version.py. No parsing logic, optional native backend integration or unrelated behavior is changed.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only prerelease comparison in src/semver/version.py: eagerly normalize ASCII numeric identifiers as strings and retain legacy int() validation for Unicode digit identifiers. The existing compare() already applies core precedence before prerelease validation and release precedence afterward; no conflict with the supplied fixed code was found. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `27e6a91a94b667af648c6b7a4ea22c11e265de1cf0dab3f34aa6c10d6132ffce`, 21 test methods, sealed at 2026-10-19T05:45:32.365909+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 21 methods: ERROR 9): 9 of 21 methods failing, 12 passing; operation `01a152b1-8c09-7062-999f-055fa1256ea9`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestSealedPrereleaseComparison.test_all_comparison_operators_use_long_numeric_precedence | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_ascii_comparison_preserves_integer_conversion_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_compare_accepts_existing_operand_forms | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_constructor_identifier_ordering_and_spelling | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_constructor_storage_and_core_conversion_remain_permissive | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_core_precedence_bypasses_prerelease_validation | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_identifiers_and_warns | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_helper_preserves_empty_identifiers_and_list_length | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_identity_and_equality_do_not_skip_digit_validation | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_legacy_digit_errors_are_eager_in_both_directions | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_legacy_unicode_conversion_keeps_enabled_digit_limit_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_ascii_number_exceeds_short_unicode_number | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_leading_zeros_equal_ascii_and_unicode_values | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_is_valid_and_compares_with_itself | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_prerelease_ignores_build_and_precedes_release | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_long_zero_identifiers_normalize_without_changing_storage | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parse_bytes_subclass_and_optional_core_parts | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_parser_rejects_noncanonical_and_unicode_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_release_precedence_overrides_empty_helper_ordering | ok (1 ev) | ok (1 ev) |
| test_sealed.TestSealedPrereleaseComparison.test_unsupported_operands_and_invalid_collections | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

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
+        def normalize(identifier):
+            if not identifier.isdigit():
+                return False, identifier
+            if identifier.isascii():
+                return True, identifier.lstrip("0") or "0"
+            return True, str(int(identifier))
+
+        # Convert every digit identifier before comparing, including suffixes that
+        # would otherwise be skipped by an earlier ordering difference.
+        a_parts = [normalize(x) for x in (a or "").split(".")]
+        b_parts = [normalize(x) for x in (b or "").split(".")]
+
+        for (a_numeric, sub_a), (b_numeric, sub_b) in zip(a_parts, b_parts):
+            if a_numeric and b_numeric:
+                cmp_result = _cmp(len(sub_a), len(sub_b)) or _cmp(sub_a, sub_b)
+            elif a_numeric != b_numeric:
+                cmp_result = -1 if a_numeric else 1
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

Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a152b6-3e11-765d-8c1c-059904ff1af5`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.82s (424 passed of 424); operation `01a152b6-623b-74ba-92f7-4fb73fb4f599`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.82s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-8288489984 | src/semver/version.py | 189 | remove `not` | killed | test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_identifiers_and_warns, test_sealed.TestSe | 01a152b6-7ccd-76aa-96bc-61e7c73cf335 |
| m02-02bb80d96e | src/semver/version.py | 190 | False -> True | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting, test_sealed.TestSealedPrere | 01a152b6-7d42-7502-b175-ff3a99cfdc0c |
| m03-55cff228c8 | src/semver/version.py | 192 | True -> False | killed | test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_identifiers_and_warns, test_sealed.TestSe | 01a152b6-7c98-722c-a602-7c4765566e21 |
| m04-c0629ee05e | src/semver/version.py | 192 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_identifiers_and_warns, test_sealed.TestSe | 01a152b6-7d45-744b-9ddb-0e2e9b3598fc |
| m05-96a4a08394 | src/semver/version.py | 193 | True -> False | killed | test_sealed.TestSealedPrereleaseComparison.test_constructor_identifier_ordering_and_spelling, test_sealed.TestSealedPrer | 01a152b6-7cea-77db-8ad6-5909a3105234 |
| m06-30068866a5 | src/semver/version.py | 197 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_is_valid_and_compares_with_itself, test_sealed.Te | 01a152b6-7cd1-733e-9c04-e3b6bdf5f73d |
| m07-d641d5a726 | src/semver/version.py | 198 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_is_valid_and_compares_with_itself, test_sealed.Te | 01a152b6-7cc1-7279-b463-6562ed98173d |
| m08-0caf6b9f13 | src/semver/version.py | 201 | And -> Or | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting, test_sealed.TestSealedPrere | 01a152b6-7ce3-76ea-a11c-633c3cdeeb1a |
| m09-0cfee599a7 | src/semver/version.py | 202 | Or -> And | killed | test_sealed.TestSealedPrereleaseComparison.test_deprecated_compare_orders_long_identifiers_and_warns, test_sealed.TestSe | 01a152b6-a350-7601-96ca-eb384deeb084 |
| m10-66243e3b21 | src/semver/version.py | 203 | NotEq -> Eq | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting, test_sealed.TestSealedPrere | 01a152b6-a3ef-707c-98f4-eb0139d8e769 |
| m11-90f47e45d2 | src/semver/version.py | 204 | 1 -> 2 | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting, test_sealed.TestSealedPrere | 01a152b6-a663-75c3-916d-5848bd4e5c47 |
| m12-5c18743ba0 | src/semver/version.py | 204 | 1 -> 2 | killed | test_sealed.TestSealedPrereleaseComparison.test_long_parsed_identifier_ordering_and_sorting, test_sealed.TestSealedPrere | 01a152b6-a647-7076-bcfd-ac74a927fafe |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `fddc373879067d5693f6e3757f93b2e0844ab6aa2b45966de7b8135e0c5c07cb`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a152b7-c57c-775d-8ccd-61e99d590d83`. Notes: Targets long decimal boundaries, Unicode normalization, eager conversion errors, identifier lists, operand coercion, and text preservation.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the stated task: `identifier.lstrip("0") or "0"` normalizes ASCII numbers without int(), length then string comparison preserves numeric ordering, and eager list comprehensions retain Unicode conversion errors through `str(int(identifier))`. Changes are confined to `_nat_cmp`; observed output supports the reported 424 passing tests, one skipped test, and successful targeted checks at the 4300-digit limit, although the targeted script itself is not shown.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 36986 | 2445 | 0 | - | 104.4s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 37385 | 140 | 0 | - | 35.4s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36250 | 4390 | 7168 | - | 115.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 14390 | 123 | 7168 | - | 39.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 29504 | 142 | 14336 | - | 50.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 30756 | 937 | 22144 | - | 54.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 15777 | 124 | 7168 | - | 42.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 33617 | 834 | 23680 | - | 45.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 16882 | 221 | 7168 | - | 56.3s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12419 | 2475 | 0 | - | 64.2s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13360 | 210 | 0 | - | 36.4s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 277326/12041/88832; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a152ad-6812-7246-8182-9a33ed398736 | SUCCESS | 0 | 0.698s | retained | off | 0.00118668 |
| checkpoint | 01a152ad-7d44-71ff-bb6a-e492b9f0b1e3 | SUCCESS | 0 | 3.467s | retained | on | 0.023246000000000003 |
| red-1 | 01a152b1-8c09-7062-999f-055fa1256ea9 | SUCCESS | 0 | 5.395s | disposable | off | 0.044363730000000004 |
| impl-tests-4 | 01a152b4-8710-72f2-802b-ac06dd6b7827 | SUCCESS | 0 | 1.916s | disposable | off | 0.011140339999999999 |
| impl-python-5 | 01a152b5-51b9-704c-91b8-8cfa62873c96 | SUCCESS | 0 | 0.672s | disposable | off | 0.0024061500000000006 |
| verify | 01a152b6-3e11-765d-8c1c-059904ff1af5 | SUCCESS | 0 | 5.243s | disposable | off | 0.04442581 |
| existing | 01a152b6-623b-74ba-92f7-4fb73fb4f599 | SUCCESS | 0 | 1.837s | disposable | off | 0.01077209 |
| mutant-m01-8288489984 | 01a152b6-7ccd-76aa-96bc-61e7c73cf335 | SUCCESS | 0 | 5.007s | disposable | off | 0.04132563000000001 |
| mutant-m02-02bb80d96e | 01a152b6-7d42-7502-b175-ff3a99cfdc0c | SUCCESS | 0 | 4.988s | disposable | off | 0.041102980000000004 |
| mutant-m04-c0629ee05e | 01a152b6-7d45-744b-9ddb-0e2e9b3598fc | SUCCESS | 0 | 4.935s | disposable | off | 0.04104783 |
| mutant-m03-55cff228c8 | 01a152b6-7c98-722c-a602-7c4765566e21 | SUCCESS | 0 | 4.795s | disposable | off | 0.04057161 |
| mutant-m05-96a4a08394 | 01a152b6-7cea-77db-8ad6-5909a3105234 | SUCCESS | 0 | 4.927s | disposable | off | 0.04113970000000001 |
| mutant-m06-30068866a5 | 01a152b6-7cd1-733e-9c04-e3b6bdf5f73d | SUCCESS | 0 | 4.987s | disposable | off | 0.04102596000000001 |
| mutant-m07-d641d5a726 | 01a152b6-7cc1-7279-b463-6562ed98173d | SUCCESS | 0 | 4.926s | disposable | off | 0.0411056 |
| mutant-m08-0caf6b9f13 | 01a152b6-7ce3-76ea-a11c-633c3cdeeb1a | SUCCESS | 0 | 4.988s | disposable | off | 0.04094326 |
| mutant-m09-0cfee599a7 | 01a152b6-a350-7601-96ca-eb384deeb084 | SUCCESS | 0 | 4.917s | disposable | off | 0.040999560000000004 |
| mutant-m10-66243e3b21 | 01a152b6-a3ef-707c-98f4-eb0139d8e769 | SUCCESS | 0 | 4.951s | disposable | off | 0.0411671 |
| mutant-m11-90f47e45d2 | 01a152b6-a663-75c3-916d-5848bd4e5c47 | SUCCESS | 0 | 4.9s | disposable | off | 0.0411978 |
| mutant-m12-5c18743ba0 | 01a152b6-a647-7076-bcfd-ac74a927fafe | SUCCESS | 0 | 4.966s | disposable | off | 0.041939300000000006 |
| breaker-tests | 01a152b7-c57c-775d-8ccd-61e99d590d83 | SUCCESS | 0 | 2.886s | disposable | off | 0.022330310000000003 |

Sandbox operations: 20, total guest duration 81.401s, retained images ['48bf88bf-9415-492d-8aef-559060e9991a', '84252770-298a-4871-b7bd-92d67c2f2a70'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception raised in the code under test is never overridden (only a test-internal crash or a timeout may be corrected). The classification itself remains a model judgement.
- INFEASIBLE is recorded only when a witness program written by the contract auditor demonstrated the contradiction by running on the unmodified repository (exit code and output recorded); the witness's logic is the model's, its execution is not.
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
| contract_audit.json | Contract audit: claimed conflicts and the result of executing their witness programs |
| sealed/test_sealed.py | Sealed acceptance tests (E1), written before the patch |
| candidate.patch | Unified diff of the candidate patch |
| verify.json | Fresh-branch verification: sealed, existing and held-out suites with binding |
| verify_raw.json | Raw supervisor results used to recompute the binding offline |
| breaker.json | Breaker pass: mutants (E2) and tests written after the patch (E3) |
| breaker_tests.py | Tests written after the patch (E3) |
| drift.json | Drift audit (E5) |
| arbitration.json | Arbitration of generated-test failures (E6) |
| ledger.json | Model calls and sandbox operations with usage and cost |
| ledger.jsonl | Append-only ledger journal: reservations before each request, call records as they complete |
