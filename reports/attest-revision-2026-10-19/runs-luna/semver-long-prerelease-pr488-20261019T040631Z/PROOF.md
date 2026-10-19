# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: VERIFIED**  
Run `semver-long-prerelease-pr488-20261019T040631Z` · profile `development-luna-implementer` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:06:31.150081+00:00, finished 2026-10-19T04:25:36.742220+00:00.

**Accept this patch.** All 25 sealed tests pass on the candidate in a fresh sandbox, and 8 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch, the held-out tests and the drift audit all passed.

Key evidence (E1): 25 of 25 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: The existing test suite result is parsed console output, not per-test exit codes under the supervisor. The held-out tests result is parsed console output, not per-test exit codes under the supervisor.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 25 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 8 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 12 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 9 tests written after the patch by an independent model instance pass on the candidate (E3).
- The held-out tests (tests/test_heldout_pr488.py), which the implementer never saw, pass on the candidate (E4).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 17 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the held-out tests result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 8 of 25 failed on the unmodified base; 25 of 25 pass on the candidate |
| E2 | Mutation check | pass | bound | 12 of 12 one-line mutants caught, 0 survived, 0 unknown; score 1.0 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 9 of 9 pass |
| E4 | Held-out tests | pass | stdout | 450 of 450 pass (tests/test_heldout_pr488.py); parsed console output |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `d68b82a7812623a4f828de375f5cf07a18c01e9c4a54b171ebedfdf61fe74fa6`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `6cc2bc67-8cf1-4cd8-8c21-bc863cd01a23`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `5f9dc8ad94e5f64c` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-luna (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Update prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without int conversion. Preserve existing version precedence, constructor permissiveness, Unicode digit conversion and eager error behavior, parsing restrictions, operand handling, and stored attributes. Limit implementation changes to prerelease comparison in that file and keep the existing test suite passing unchanged.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.Version / semver.version.Version | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Retain the existing constructor and exports, including VersionInfo. Core parts are converted to integers. Prerelease and build are stored as None or str(argumen | ValueError: a converted core part is negative.; Existing TypeError or ValueError from core-part conversion remains unchanged.; Invalid prerelease syntax alone m |
| Version._nat_cmp | _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Preserve this classmethod's comparison contract, returning exactly -1, 0, or 1. Split each input on dots, treating None and an empty string as one empty identif | ValueError: any identifier satisfying str.isdigit() in the non-ASCII fallback fails int(identifier), even in an unmatched trailing identifier or after an earlie |
| Version.compare | compare(self, other: Comparable) -> int | Return exactly -1, 0, or 1. Preserve operand conversion for str, bytes, dict, tuple, list, and compatible Version instances. Compare major, minor, and patch bef | TypeError: unsupported operand type, retaining existing behavior.; Existing parsing or constructor exceptions propagate when converting supported operands.; Val |
| Version comparison operators | __eq__(self, other: Comparable) -> bool; __ne__(self, other: Comparable) -> bool; __lt__(self, other: Comparable) -> bool; __le__(self, other: Comparable) -> bool; __gt__(self, other: Comparable) -> bool; __ge__(self, other: Comparable) -> bool | Continue deriving results from compare(), including long numeric prereleases and sorting. Preserve the existing decorator's NotImplemented behavior for unsuppor | Exceptions from prerelease comparison propagate for accepted operands.; Existing Python operator behavior following NotImplemented remains unchanged. |
| Version.parse | parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Remain unchanged. Parse canonical ASCII SemVer prereleases, including 5000-digit numeric identifiers, preserving their text. Retain bytes decoding, subclass con | ValueError: invalid SemVer input, including numeric prereleases with leading zeros or non-ASCII digits.; TypeError: unsupported input type.; Existing bytes deco |
| Version.is_valid | is_valid(cls, version: str) -> bool | Remain unchanged: return True when parse succeeds and False when parse raises ValueError. Canonical long numeric prereleases remain valid. | Exceptions not caught by the existing ValueError handler continue to propagate. |
| semver.compare | compare(ver1: str, ver2: str) -> int | Continue delegating to Version.parse(ver1).compare(ver2), with existing deprecation warning behavior. Inherit corrected long numeric prerelease comparison. | Existing parsing and comparison exceptions propagate. |
| Version.replace | replace(self, **parts: Union[int, Optional[str]]) -> "Version" | Remain unchanged: construct a new version with replaced parts without mutating the original. Replacing only build metadata must leave comparison equality intact | TypeError: unknown replacement keyword, retaining existing behavior.; Existing constructor validation exceptions remain unchanged. |

Acceptance criteria:
AC1. 1. With v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) is 0, semver.compare(v, '0.0.0-2') is 1, and the reversed comparison is -1, without ValueError.
AC2. 2. For each prerelease pair ('9' * 4999, '1' + '0' * 4999), ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'), ('1' * 5000, 'alpha'), and ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'), parse versions with core 0.0.0 and verify low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
AC3. 3. ASCII numeric comparison uses no int conversion, including after stripping leading zeros. It must work with the interpreter's integer-string conversion limit enabled and must not change that limit or other global interpreter settings. On runtimes supporting the limit, verify the 5000-digit regressions with a limit of 4300.
AC4. 4. For version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). The original prerelease text remains unchanged.
AC5. 5. For constructor-created equal-core versions, verify these (left, right, expected) cases: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Each reverse comparison returns the negated result, and both prerelease attributes retain their supplied values.
AC6. 6. Constructor-created prereleases '0' * 5000 and '0' compare equal; '0' * 5000 + '1' and '1' compare equal. A 5000-digit ASCII numeric identifier compares numerically against the legacy Unicode numeric identifier '١٢' without converting the ASCII identifier to int.
AC7. 7. Dot splitting preserves empty components. Version._nat_cmp('', None) == 0, Version._nat_cmp('a', 'a.') == -1, and Version._nat_cmp('a..1', 'a.0.1') == 1. Empty identifiers are non-numeric. At the public version level, both '' and None represent absence of a prerelease.
AC8. 8. Version.parse('0.0.0-' + p) raises ValueError for each p in ('01', '01.2', '١٢', '１２'); Version.is_valid returns False for those same version strings.
AC9. 9. Equal-core constructor comparisons raise ValueError for ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), in both operand orders. Also verify errors for ('a.²', 'a') and ('²', None), demonstrating eager validation of unmatched identifiers and validation before release-presence precedence. No exact exception message is required.
AC10. 10. Invalid legacy digit identifiers do not affect unequal-core comparison. With prerelease='²' on both operands, independently verify differences in major, minor, and patch return the correct result in both directions; specifically Version(0, 0, 0, prerelease='²') < Version(1, 0, 0, prerelease='²') is True.
AC11. 11. All six rich comparison operators agree with compare() for long numeric prereleases, including equality across differing build metadata. Existing operand acceptance, rejection, and exception behavior remains unchanged.
AC12. 12. The existing pytest suite in tests/ passes without modifications. Implementation changes are confined to prerelease comparison in src/semver/version.py; parsing and native-backend code remain unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are jointly satisfiable by changing only Version._nat_cmp: eagerly validate legacy Unicode conversions and compare normalized numeric strings without converting ASCII identifiers to int. The supplied caller already compares core versions first and applies release-presence precedence afterward; no conflict with the supplied fixed code was found. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `94b45bfdf901eb8f8afd4fbb4b4396c3bbbe6073cc081fa9db1f19a324e59f25`, 25 test methods, sealed at 2026-10-19T04:12:25.727586+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (8 of 25 methods: ERROR 8): 8 of 25 methods failing, 17 passing; operation `01a1525c-43ad-77ee-a283-d612cb0304f2`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.SealedPrereleaseComparisonTests.test_absent_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_accepted_rich_operands_propagate_prerelease_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_arbitrary_length_leading_zero_normalization | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_compare_accepts_supported_operands | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_compare_rejects_unsupported_operand | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_core_validation | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_prerelease_compatibility_table | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_constructor_preserves_noncanonical_values | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_deprecated_compare_emits_warning | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_eager_legacy_conversion_in_both_lists | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_eager_legacy_conversion_in_unmatched_components | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_empty_dot_identifiers | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_integer_string_limit_is_unchanged | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_ascii_compares_with_unicode_number | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_public_entry_points | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_parse_bytes_optional_parts_and_subclass | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_parse_rejects_noncanonical_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_parse_type_and_decode_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_replace_build_preserves_long_prerelease_precedence | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_replace_rejects_unknown_keyword | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_rich_equality_ignores_build_metadata | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_rich_operators_match_compare | ERROR (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_rich_operators_reject_invalid_collections | ok (1 ev) | ok (1 ev) |
| test_sealed.SealedPrereleaseComparisonTests.test_unequal_cores_skip_prerelease_conversion | ok (1 ev) | ok (1 ev) |


## 4. Candidate patch
1 changed path(s); scope check passed; 6 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,21 +185,38 @@
 
     @classmethod
     def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int:
-        def cmp_prerelease_tag(a, b):
-            if isinstance(a, int) and isinstance(b, int):
-                return _cmp(a, b)
-            elif isinstance(a, int):
-                return -1
-            elif isinstance(b, int):
-                return 1
+        def normalize(parts):
+            normalized = []
+            for identifier in parts:
+                if identifier and all("0" <= char <= "9" for char in identifier):
+                    normalized.append((True, identifier.lstrip("0") or "0"))
+                elif identifier.isdigit():
+                    # Preserve the legacy int conversion (and its exceptions) for
+                    # non-ASCII digits. Do this for every identifier up front.
+                    normalized.append((True, int(identifier)))
+                else:
+                    normalized.append((False, identifier))
+            return normalized
+
+        a_parts = normalize((a or "").split("."))
+        b_parts = normalize((b or "").split("."))
+
+        def compare_numeric(value_a, value_b):
+            # Legacy Unicode identifiers are stored as ints; converting those
+            # back to decimal text is bounded by the successful int conversion.
+            text_a = str(value_a) if isinstance(value_a, int) else value_a
+            text_b = str(value_b) if isinstance(value_b, int) else value_b
+            return _cmp((len(text_a), text_a), (len(text_b), text_b))
+
+        for (numeric_a, sub_a), (numeric_b, sub_b) in zip(a_parts, b_parts):
+            if numeric_a and numeric_b:
+                cmp_result = compare_numeric(sub_a, sub_b)
+            elif numeric_a:
+                cmp_result = -1
+            elif numeric_b:
+                cmp_result = 1
             else:
-                return _cmp(a, b)
-
-        a_parts = [int(x) if x.isdigit() else x for x in (a or "").split(".")]
-        b_parts = [int(x) if x.isdigit() else x for x in (b or "").split(".")]
-
-        for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
+                cmp_result = _cmp(sub_a, sub_b)
             if cmp_result != 0:
                 return cmp_result
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (31 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (25 of 25 methods, each in its own process). Operation `01a15263-e0c7-76a9-b052-6453a3076d2b`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 1.04s (424 passed of 424); operation `01a15264-0a5f-7250-b848-29b29b5c6000`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite (evidence class `stdout`; tests/test_heldout_pr488.py): 450 passed, 1 skipped in 0.83s (450 passed of 450); operation `01a15264-23c3-77e9-a327-cf975ce2057a`. Gate: failures block VERIFIED.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 1.04s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| heldout_suite | Held-out tests | pass | stdout | E4 | 450 passed, 1 skipped in 0.83s |
| mutation | Mutation check | pass | bound | E2 | score 1.0 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (9 of 9 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 12 killed, 0 survived, 0 unknown; mutation score 1.000 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-9a06573642 | src/semver/version.py | 191 | LtE -> Lt | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-3e90-76bc-89d5-aec2845df878 |
| m02-f063e772f9 | src/semver/version.py | 191 | LtE -> Lt | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-3ee0-7112-a28b-ea8a27070e2a |
| m03-59eba2234c | src/semver/version.py | 191 | And -> Or | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-3eb3-72d0-ab75-4d3e971815f0 |
| m04-e5aeb64341 | src/semver/version.py | 192 | True -> False | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_public_entry_points, test_sealed.SealedPrereleaseCompariso | 01a15264-3ee3-73ce-8110-707a34430440 |
| m05-194113dc78 | src/semver/version.py | 192 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_public_entry_points, test_sealed.SealedPrereleaseCompariso | 01a15264-3ed6-7486-9d5c-a59a42a148eb |
| m06-f55f6da6e8 | src/semver/version.py | 196 | True -> False | killed | test_sealed.SealedPrereleaseComparisonTests.test_constructor_prerelease_compatibility_table, test_sealed.SealedPrereleas | 01a15264-3ee7-7679-8c34-714d9311591e |
| m07-70316359d1 | src/semver/version.py | 198 | False -> True | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-3f03-710d-81a6-8fb5b27e356f |
| m08-76cf2e4437 | src/semver/version.py | 201 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_public_entry_points, test_sealed.SealedPrereleaseCompariso | 01a15264-3eff-7582-8c7b-7e99f7ee3acc |
| m09-5927ba9aed | src/semver/version.py | 202 | Or -> And | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_public_entry_points, test_sealed.SealedPrereleaseCompariso | 01a15264-69e0-774c-bdb6-3645b0b20117 |
| m10-ada323be36 | src/semver/version.py | 212 | And -> Or | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-6a6f-7532-b50c-34a13a9afed5 |
| m11-2010aa9fd0 | src/semver/version.py | 215 | 1 -> 2 | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-6ebb-7115-ab16-aa63c6459696 |
| m12-ff600f945e | src/semver/version.py | 217 | 1 -> 2 | killed | test_sealed.SealedPrereleaseComparisonTests.test_long_numeric_precedence_and_sorting, test_sealed.SealedPrereleaseCompar | 01a15264-6e7b-7125-bd34-05669103f719 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `2610768e50d22053f60cfbefe49ee16106cd7f69163a3187f356252441b7ad75`): OK (9 of 9 methods, each in its own process); binding ok; operation `01a15266-ae45-7721-93d3-cf0f8173e213`. Notes: Targets long zero padding, later identifiers, Unicode digit classification and eager errors, core precedence with collection operands, and rich operator consistency.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the reported bug within _nat_cmp: ASCII numbers use identifier.lstrip("0") or "0" and length-then-lexicographic comparison, while int(identifier) preserves legacy Unicode conversion and both complete lists are normalized eagerly. No unrelated changes appear; observed outputs report 424 tests passed, 1 skipped, and successful focused checks, although the focused scripts themselves are not shown.

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
| codex_gateway:gpt-6-astra | spec | spec | low | 36984 | 2508 | 0 | - | 114.8s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 37432 | 153 | 0 | - | 49.1s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36272 | 5249 | 0 | - | 143.2s | ok |
| codex_gateway:gpt-6-luna | implement | implement-1 | medium | 28607 | 169 | 14080 | - | 87.3s | ok |
| codex_gateway:gpt-6-luna | implement | implement-2 | medium | 30181 | 1680 | 14464 | - | 79.8s | ok |
| codex_gateway:gpt-6-luna | implement | implement-3 | medium | 30917 | 294 | 0 | - | 93.8s | ok |
| codex_gateway:gpt-6-luna | implement | implement-4 | medium | 33272 | 1267 | 16128 | - | 48.3s | ok |
| codex_gateway:gpt-6-luna | implement | implement-5 | medium | 33515 | 949 | 16384 | - | 107.6s | ok |
| codex_gateway:gpt-6-luna | implement | implement-6 | medium | 16914 | 240 | 7040 | - | 56.3s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12538 | 1951 | 0 | - | 136.2s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13504 | 190 | 0 | - | 109.4s | ok |

Model calls: 11 (0 failed, 0 malformed); tokens in/out/cached 310136/14650/68096; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a15257-2ead-7275-9b0b-7df622e2b9ca | SUCCESS | 0 | 0.684s | retained | off | 0.0011641400000000001 |
| checkpoint | 01a15257-595b-74ce-8c2e-eee5e982a826 | SUCCESS | 0 | 3.548s | retained | on | 0.02357558 |
| red-1 | 01a1525c-43ad-77ee-a283-d612cb0304f2 | SUCCESS | 0 | 6.021s | disposable | off | 0.05166843000000001 |
| impl-tests-3 | 01a15260-6ba1-70aa-9c30-18c67ccacce2 | SUCCESS | 0 | 1.939s | disposable | off | 0.01104037 |
| impl-python-4 | 01a15261-4190-7758-851f-40d1752be65b | SUCCESS | 0 | 0.686s | disposable | off | 0.00244748 |
| impl-python-5 | 01a15262-f430-774c-83dc-b5e1dd5822e9 | SUCCESS | 0 | 0.767s | disposable | off | 0.00244621 |
| verify | 01a15263-e0c7-76a9-b052-6453a3076d2b | SUCCESS | 0 | 5.984s | disposable | off | 0.05212011 |
| existing | 01a15264-0a5f-7250-b848-29b29b5c6000 | SUCCESS | 0 | 3.344s | disposable | off | 0.01113764 |
| heldout | 01a15264-23c3-77e9-a327-cf975ce2057a | SUCCESS | 0 | 2.036s | disposable | off | 0.01101568 |
| mutant-m01-9a06573642 | 01a15264-3e90-76bc-89d5-aec2845df878 | SUCCESS | 0 | 5.779s | disposable | off | 0.04858320000000001 |
| mutant-m02-f063e772f9 | 01a15264-3ee0-7112-a28b-ea8a27070e2a | SUCCESS | 0 | 5.822s | disposable | off | 0.04845609 |
| mutant-m04-e5aeb64341 | 01a15264-3ee3-73ce-8110-707a34430440 | SUCCESS | 0 | 5.874s | disposable | off | 0.049214810000000005 |
| mutant-m03-59eba2234c | 01a15264-3eb3-72d0-ab75-4d3e971815f0 | SUCCESS | 0 | 5.803s | disposable | off | 0.04849156 |
| mutant-m06-f55f6da6e8 | 01a15264-3ee7-7679-8c34-714d9311591e | SUCCESS | 0 | 5.749s | disposable | off | 0.048515970000000005 |
| mutant-m05-194113dc78 | 01a15264-3ed6-7486-9d5c-a59a42a148eb | SUCCESS | 0 | 5.826s | disposable | off | 0.048642 |
| mutant-m07-70316359d1 | 01a15264-3f03-710d-81a6-8fb5b27e356f | SUCCESS | 0 | 5.67s | disposable | off | 0.048770310000000004 |
| mutant-m08-76cf2e4437 | 01a15264-3eff-7582-8c7b-7e99f7ee3acc | SUCCESS | 0 | 5.641s | disposable | off | 0.04837728000000001 |
| mutant-m09-5927ba9aed | 01a15264-69e0-774c-bdb6-3645b0b20117 | SUCCESS | 0 | 5.62s | disposable | off | 0.048233090000000006 |
| mutant-m10-ada323be36 | 01a15264-6a6f-7532-b50c-34a13a9afed5 | SUCCESS | 0 | 5.669s | disposable | off | 0.048508020000000006 |
| mutant-m11-2010aa9fd0 | 01a15264-6ebb-7115-ab16-aa63c6459696 | SUCCESS | 0 | 5.692s | disposable | off | 0.04803935000000001 |
| mutant-m12-ff600f945e | 01a15264-6e7b-7125-bd34-05669103f719 | SUCCESS | 0 | 5.691s | disposable | off | 0.0482124 |
| breaker-tests | 01a15266-ae45-7721-93d3-cf0f8173e213 | SUCCESS | 0 | 2.947s | disposable | off | 0.02255039 |

Sandbox operations: 22, total guest duration 96.792s, retained images ['3c9bac8c-7d11-4d14-b978-b09491d6fe08', '6cc2bc67-8cf1-4cd8-8c21-bc863cd01a23'].

## 11. Limitations of this bundle
- Profile 'development-luna-implementer': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
- Sealed and adversarial suites run one child process per test under a supervisor that never imports candidate code and is the first step of its branch; two verifier canaries detect blanket result forgery. A candidate can still forge its own result from inside a child after the nonce was read if it spares the canaries (the mutation gate and held-out tests are the structural detectors).
- The repository's own suite and the held-out suite run after the sealed verification in their own branches. They are bound through the same supervisor only for unittest repositories whose tests are statically discoverable; otherwise they are parsed from console output and the gate is labelled evidence_class 'stdout'.
- Model-written sealed and adversarial tests can be wrong; their failures block VERIFIED. An independent arbiter classifies each failure (implementation bug, test defect or contract dispute) and, for pure test defects, offers a corrected module. The correction counts only after mechanical validation (same test methods, only the failing ones changed, passes on the candidate, still fails on the unmodified base or is caught by a mutant); the corrected gate is then re-run and the verdict re-derived from the gates. A sealed test that failed by assertion is never overridden. The classification itself remains a model judgement.
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
