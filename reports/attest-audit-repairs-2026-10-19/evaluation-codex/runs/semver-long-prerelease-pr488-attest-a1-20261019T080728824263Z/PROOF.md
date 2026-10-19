# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: VERIFIED**  
Run `semver-long-prerelease-pr488-attest-a1-20261019T080728824263Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T08:07:28.825785+00:00, finished 2026-10-19T08:26:36.912932+00:00.

**Accept this patch.** All 23 sealed tests pass on the candidate in a fresh sandbox, and 8 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 23 of 23 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.889, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4).

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 23 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 8 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 8 of 9 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 15 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 8 of 23 failed on the unmodified base; 23 of 23 pass on the candidate |
| E2 | Mutation check | pass | bound | 8 of 9 one-line mutants caught, 1 survived, 0 unknown; score 0.889 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `bebfebfc4bcfdac2b3d8de3361919f592abc7494e4052b76fab3fde2ac27bc70`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `b5a520b3-91eb-49d3-b6db-c7a70882a661`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.5.0 revision `722cd6dd1a217c6d` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/7` sha256 `97d3d47d1d5b4fed`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `db8e2a76834b83ac`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-audit-repairs-2026-10-19/evaluation-codex/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Fix prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without integer conversion. Preserve existing ordering, constructor permissiveness, Unicode digit conversion behavior and eager conversion errors, core-version precedence, strict parsing, build-metadata exclusion, and public interfaces. Only comparison-related implementation in src/semver/version.py may change; the existing pytest suite must pass unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version (also semver.Version and VersionInfo) | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Constructor behavior is unchanged. Core parts are converted to integers. Prerelease and build are stored as None or str(argument), without prerelease validation | ValueError: a converted core part is negative.; TypeError or ValueError: existing core-part integer conversion fails; preserve existing behavior. |
| Version._nat_cmp | _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Preserve this classmethod's interface. Split each operand on '.', treating None or '' as one empty identifier and preserving empty parts elsewhere. A nonempty i | ValueError: any non-ASCII identifier satisfying str.isdigit() fails int(identifier), even if another identifier already determines ordering. Preserve runtime in |
| Version.compare | compare(self, other: Comparable) -> int | Keep existing operand coercion: strings and bytes are parsed; dictionaries and tuples/lists construct a version; compatible Version instances are used directly. | TypeError: unsupported operand type.; Existing parsing or constructor exceptions: operand coercion fails.; ValueError: equal-core operands contain a legacy digi |
| Version comparison operators | __eq__(self, other: Comparable) -> bool; __ne__(self, other: Comparable) -> bool; __lt__(self, other: Comparable) -> bool; __le__(self, other: Comparable) -> bool; __gt__(self, other: Comparable) -> bool; __ge__(self, other: Comparable) -> bool | Continue deriving supported comparisons from Version.compare, including sorting long numeric prereleases. Preserve the existing decorator's NotImplemented behav | ValueError: propagate prerelease conversion errors from compare for supported equal-core operands.; Preserve existing Python operator behavior following NotImpl |
| Version.parse | parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Unchanged classmethod. Accept canonical versions containing arbitrarily long ASCII numeric prerelease identifiers and preserve their text. Continue rejecting le | ValueError: invalid SemVer input, including prereleases '01', '01.2', '١٢', and '１２'.; TypeError: unsupported input type.; Preserve existing decoding and core c |
| Version.is_valid | is_valid(cls, version: str) -> bool | Unchanged classmethod: return True when parse succeeds and False when parse raises ValueError. A canonical 5000-digit numeric prerelease remains valid. | Exceptions other than ValueError from parse continue to propagate. |
| semver.compare | compare(ver1: str, ver2: str) -> int | Continue delegating to Version.parse(ver1).compare(ver2), with existing deprecation warning behavior. Long numeric prereleases receive the corrected ordering. | Propagate existing parsing and comparison exceptions. |
| Version.replace | replace(self, **parts: Union[int, Optional[str]]) -> "Version" | Unchanged: construct a replacement version without mutating the original. Replacing only build metadata must not affect comparison, including for long numeric p | TypeError: unknown replacement keys.; Preserve existing constructor exceptions for invalid replacement values. |

Acceptance criteria:
AC1. 1. With v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) == 0, semver.compare(v, '0.0.0-2') == 1, and semver.compare('0.0.0-2', v) == -1, without ValueError.
AC2. 2. Parse each pair of prereleases under core 0.0.0: ('9' * 4999, '1' + '0' * 4999), ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'), ('1' * 5000, 'alpha'), and ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'). For every pair, low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
AC3. 3. For version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). Build metadata never participates in ordering.
AC4. 4. For constructor-created equal-core versions, the following (left, right, result) cases hold: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Reverse comparisons return the negated result, and both prerelease attributes retain their original values.
AC5. 5. ASCII numeric normalization works beyond integer-conversion limits even for constructor-only inputs: '0' * 5000 equals '0'; '0' * 5000 + '12' equals '12' and '١٢'; '1' * 5000 exceeds '１２'. Verify both directions and unchanged stored attributes.
AC6. 6. Direct _nat_cmp comparisons preserve empty identifiers: _nat_cmp('', None) == 0, _nat_cmp('a.', 'a') == 1, _nat_cmp('a..1', 'a..01') == 0, and _nat_cmp('', '0') == 1. Public comparison separately treats an empty prerelease as a release.
AC7. 7. Version.parse('0.0.0-' + p) raises ValueError and Version.is_valid('0.0.0-' + p) is False for p in ('01', '01.2', '١٢', '１２').
AC8. 8. Equal-core constructor comparisons raise ValueError for ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), in both directions. They also raise for ('a', 'a.²'), ('²', None), and ('²', '²'), proving that no earlier ordering decision, release precedence, or equality shortcut suppresses conversion errors.
AC9. 9. Version(0, 0, 0, prerelease='²') < Version(1, 0, 0, prerelease='²') is True. Differences in minor or patch likewise decide ordering before examining prereleases; reverse compare calls return 1 without ValueError.
AC10. 10. Run long-identifier regression checks on CPython with its integer-string conversion limit enabled at 4300 digits where supported. The implementation must not raise or disable that limit, convert ASCII numeric identifiers to integers, or impose an identifier-length cap. Verify the conversion restriction by source inspection as well as behavioral tests.
AC11. 11. The existing pytest suite passes unchanged, including configured doctests and existing operand-type, parsing, subclass, and optional-backend coverage.
AC12. 12. The implementation diff is confined to comparison-related changes in src/semver/version.py; public signatures, parsing, constructor storage, and unrelated behavior remain unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The contract is satisfiable by changing only _nat_cmp: eagerly convert legacy Unicode digit identifiers, normalize ASCII numeric identifiers as strings, then compare numeric values by normalized length and text. The existing compare flow already preserves core precedence, eager prerelease errors, release precedence, and build exclusion; no conflict with the supplied fixed code was found. Rule: a conflict is demonstrated only when it names existing acceptance criteria and its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' that names at least one of them and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run; the witness's reasoning is the model's and its execution is recorded, which is not a formal proof of impossibility

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `1a6842c8ea0387437cd06538ba53da505efd23505e5dc53fbc33074d7fa9313e`, 23 test methods, sealed at 2026-10-19T08:14:11.098394+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (8 of 23 methods: ERROR 8): 8 of 23 methods failing, 15 passing; operation `01a15339-9645-7581-a2c0-17b2485d32a6`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.SealedPrereleaseComparisonTests.test_all_comparison_operators_propagate_unicode_conversion_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_all_six_operators_derive_from_long_numeric_comparison | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_build_metadata_does_not_change_long_prerelease_precedence | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_compare_coerces_supported_operand_forms | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_compare_propagates_operand_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_identifiers_keep_legacy_order_and_text | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_long_ascii_normalization_and_unicode_comparison | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_storage_and_core_conversion_remain_permissive | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_core_precedence_skips_invalid_prerelease_conversion | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_cpython_digit_limit_remains_enabled_for_long_ascii_comparisons | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_is_valid_propagates_non_value_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_prerelease_is_valid_and_self_equal | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_prerelease_pairs_compare_and_sort | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_unicode_digits_keep_legacy_integer_conversion_limit | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_module_compare_orders_long_numeric_identifiers_both_ways | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_nat_cmp_preserves_empty_identifiers | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_operators_preserve_notimplemented_for_invalid_operands | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_parse_preserves_bytes_optional_components_and_subclasses | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_public_comparison_treats_empty_prerelease_as_release | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_replace_rejects_unknown_parts | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_strict_parse_rejects_noncanonical_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_unicode_conversion_errors_survive_earlier_identifier_difference | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_unicode_conversion_errors_survive_length_release_and_equality | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 7 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,21 +185,22 @@
 
     @classmethod
     def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int:
-        def cmp_prerelease_tag(a, b):
-            if isinstance(a, int) and isinstance(b, int):
-                return _cmp(a, b)
-            elif isinstance(a, int):
-                return -1
-            elif isinstance(b, int):
-                return 1
-            else:
-                return _cmp(a, b)
-
-        a_parts = [int(x) if x.isdigit() else x for x in (a or "").split(".")]
-        b_parts = [int(x) if x.isdigit() else x for x in (b or "").split(".")]
+        def comparison_key(identifier: str):
+            if identifier and all("0" <= digit <= "9" for digit in identifier):
+                normalized = identifier.lstrip("0") or "0"
+                return (0, len(normalized), normalized)
+            if identifier.isdigit():
+                # Keep the legacy conversion (and its errors) for Unicode digits.
+                normalized = str(int(identifier))
+                return (0, len(normalized), normalized)
+            return (1, identifier)
+
+        # Build both lists before comparing so every Unicode conversion is eager.
+        a_parts = [comparison_key(x) for x in (a or "").split(".")]
+        b_parts = [comparison_key(x) for x in (b or "").split(".")]
 
         for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
+            cmp_result = _cmp(sub_a, sub_b)
             if cmp_result != 0:
                 return cmp_result
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (14 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (23 of 23 methods, each in its own process). Operation `01a15340-154c-7650-a874-7f4a1627f85f`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

| Binding check | Result |
| --- | --- |
| result_file_present | pass |
| sealed_file_unchanged_before | pass |
| sealed_file_unchanged_after | pass |
| static_ids_match_red | pass |
| supervisor_completed | pass |
| verifier_isolation_active | pass |
| supervisor_cleanup_complete | pass |
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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.90s (424 passed of 424); operation `01a15340-63cd-738d-a080-4c819f1439d7`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.90s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| mutation | Mutation check | pass | bound | E2 | score 0.889 on 9 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant with authentic, structurally sound results) and the gate was re-run; the arbiter's classification alone never changes a gate, and a sealed test that failed by assertion or exception is never overridden. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 9 generated, 9 evaluated: 8 killed, 1 survived, 0 unknown; mutation score 0.889 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-e324ae55ea | src/semver/version.py | 189 | LtE -> Lt | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_prerelease_pairs_compare_and_sort, test_sealed.SealedPrereleaseCom | 01a15340-8b0a-703d-876b-83e879a2e0b1 |
| m02-bf0a088492 | src/semver/version.py | 189 | LtE -> Lt | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_prerelease_pairs_compare_and_sort, test_sealed.SealedPrereleaseCom | 01a15340-8af1-7135-96fd-5da94f95c180 |
| m03-fc0117626c | src/semver/version.py | 189 | And -> Or | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_prerelease_pairs_compare_and_sort, test_sealed.SealedPrereleaseCom | 01a15340-8b5f-7010-9e9b-d2f64fb28dc9 |
| m04-65b7c0c1a0 | src/semver/version.py | 190 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_module_compare_orders_long_numeric_identifiers_both_ways, test_sealed.S | 01a15340-8b21-72af-9d89-092bb041aca7 |
| m05-c7de678a09 | src/semver/version.py | 191 | 0 -> 1 | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_prerelease_pairs_compare_and_sort, test_sealed.SealedPrereleaseCom | 01a15340-8ab5-7435-b25d-5a154240b5db |
| m06-1762c54af1 | src/semver/version.py | 195 | 0 -> 1 | killed | test_sealed.SealedPrereleaseComparisonTests.test_constructor_identifiers_keep_legacy_order_and_text, test_sealed.SealedP | 01a15340-8b2d-7339-89fa-7787d78b29aa |
| m07-1947590542 | src/semver/version.py | 196 | 1 -> 2 | survived |  | 01a15340-8be6-718b-a0b9-97405311d13f |
| m08-3f734119e3 | src/semver/version.py | 199 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_prerelease_is_valid_and_self_equal, test_sealed.SealedPrer | 01a15340-8b65-7254-a551-80a266e7ce89 |
| m09-0db42e427b | src/semver/version.py | 200 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_prerelease_is_valid_and_self_equal, test_sealed.SealedPrer | 01a15340-c267-7478-b3d9-dbc82249e904 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `44775350aaee2425d426982d985ded9d25ff407487feb0e3f83478e3a77965b4`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a15343-9e4b-7454-ba20-f6768b127319`. Notes: Targets normalization across long dotted identifiers, eager Unicode errors, empty parts, coercion, strict parsing, and round trips.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the reported bug: `identifier.lstrip("0") or "0"` and `(0, len(normalized), normalized)` compare ASCII numeric identifiers without integer conversion, while `str(int(identifier))` preserves legacy Unicode conversion and eager list construction preserves its errors. Changes are confined to `_nat_cmp` in src/semver/version.py; observed output supports the reported 424 passing tests, one skip, and targeted checks with the 4300-digit limit enabled.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 36984 | 2545 | 7680 | - | 120.9s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 37482 | 164 | 7552 | - | 34.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36333 | 5405 | 0 | - | 149.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 14510 | 130 | 0 | - | 24.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 29782 | 154 | 14336 | - | 37.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 15294 | 1015 | 7168 | - | 125.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 15876 | 317 | 7168 | - | 78.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 16030 | 135 | 0 | - | 30.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 16933 | 794 | 0 | - | 41.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 17314 | 272 | 7168 | - | 46.0s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12478 | 2412 | 0 | - | 176.7s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13486 | 200 | 0 | - | 91.2s | ok |

Model calls: 12 (0 failed, 0 malformed); tokens in/out/cached 262502/13543/51072; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a15333-da84-74fc-ba3f-d4902be7ff10 | SUCCESS | 0 | 0.686s | retained | off | 0.00117896 |
| checkpoint | 01a15334-6c0a-75ea-8a0e-64b3db4f78c7 | SUCCESS | 0 | 3.509s | retained | on | 0.02319866 |
| red-1 | 01a15339-9645-7581-a2c0-17b2485d32a6 | SUCCESS | 0 | 5.691s | disposable | off | 0.04812315 |
| impl-tests-5 | 01a1533e-5df8-7526-9a70-a16cce8e2f8b | SUCCESS | 0 | 1.906s | disposable | off | 0.01095237 |
| impl-python-6 | 01a1533f-1ba2-77a1-a3c1-ffe69171f6ae | SUCCESS | 0 | 0.715s | disposable | off | 0.0024408 |
| verify | 01a15340-154c-7650-a874-7f4a1627f85f | SUCCESS | 0 | 5.663s | disposable | off | 0.048207070000000005 |
| existing | 01a15340-63cd-738d-a080-4c819f1439d7 | SUCCESS | 0 | 2.143s | disposable | off | 0.01118635 |
| mutant-m01-e324ae55ea | 01a15340-8b0a-703d-876b-83e879a2e0b1 | SUCCESS | 0 | 5.406s | disposable | off | 0.04496872000000001 |
| mutant-m03-fc0117626c | 01a15340-8b5f-7010-9e9b-d2f64fb28dc9 | SUCCESS | 0 | 5.398s | disposable | off | 0.04469548 |
| mutant-m02-bf0a088492 | 01a15340-8af1-7135-96fd-5da94f95c180 | SUCCESS | 0 | 5.396s | disposable | off | 0.044753860000000006 |
| mutant-m04-65b7c0c1a0 | 01a15340-8b21-72af-9d89-092bb041aca7 | SUCCESS | 0 | 5.389s | disposable | off | 0.044644390000000006 |
| mutant-m05-c7de678a09 | 01a15340-8ab5-7435-b25d-5a154240b5db | SUCCESS | 0 | 5.912s | disposable | off | 0.04490129 |
| mutant-m07-1947590542 | 01a15340-8be6-718b-a0b9-97405311d13f | SUCCESS | 0 | 5.397s | disposable | off | 0.045065 |
| mutant-m06-1762c54af1 | 01a15340-8b2d-7339-89fa-7787d78b29aa | SUCCESS | 0 | 5.524s | disposable | off | 0.045608590000000004 |
| mutant-m08-3f734119e3 | 01a15340-8b65-7254-a551-80a266e7ce89 | SUCCESS | 0 | 5.404s | disposable | off | 0.04511004000000001 |
| mutant-m09-0db42e427b | 01a15340-c267-7478-b3d9-dbc82249e904 | SUCCESS | 0 | 5.514s | disposable | off | 0.04481652 |
| breaker-tests | 01a15343-9e4b-7454-ba20-f6768b127319 | SUCCESS | 0 | 3.191s | disposable | off | 0.02413968 |

Sandbox operations: 17, total guest duration 72.844s, retained images ['c01cc9d5-ff5b-4d31-8053-c6bc952e5b71', 'b5a520b3-91eb-49d3-b6db-c7a70882a661'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing tests' bodies changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant, with every result structurally sound and bound to its nonce); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion or by an exception, whatever its origin, is never overridden (only a test the supervisor killed at its timeout may be corrected). The classification itself remains a model judgement.
- A mutant counts as killed only when a sealed test failed with an authentic child result under a structurally sound supervisor run; lost, forged, incomplete, non-isolated, crashed or timed-out runs are unknown and excluded from the mutation score, and `attest check` recomputes the classification from the raw results.
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
