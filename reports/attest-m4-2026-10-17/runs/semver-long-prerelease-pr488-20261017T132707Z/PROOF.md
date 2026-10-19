# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: VERIFIED**  
Run `semver-long-prerelease-pr488-20261017T132707Z` · profile `development` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-17T13:27:07.259413+00:00, finished 2026-10-17T13:37:09.414183+00:00.

**Accept this patch.** All 21 sealed tests pass on the candidate in a fresh sandbox, and 7 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch, the held-out tests and the drift audit all passed.

Key evidence (E1): 21 of 21 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.917, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). The existing test suite result is parsed console output, not per-test exit codes under the supervisor. The held-out tests result is parsed console output, not per-test exit codes under the supervisor.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 21 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 7 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 11 of 12 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 10 tests written after the patch by an independent model instance pass on the candidate (E3).
- The held-out tests (tests/test_heldout_pr488.py), which the implementer never saw, pass on the candidate (E4).
- A model audit found the work aligned with the request (score 0.08, narrowed (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 14 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the held-out tests result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 7 of 21 failed on the unmodified base; 21 of 21 pass on the candidate |
| E2 | Mutation check | pass | bound | 11 of 12 one-line mutants caught, 1 survived, 0 unknown; score 0.917 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 10 of 10 pass |
| E4 | Held-out tests | pass | stdout | 450 of 450 pass (tests/test_heldout_pr488.py); parsed console output |
| E5 | Drift audit | pass | model | score 0.08, narrowed (threshold 0.6) |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `f7465e98247d560502e8d61f9ba8b559918cd52cab04e4ee9f9af8b48a19d0cd`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `0970646b-9a1d-4301-b858-d6fa6549cdf3`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.3.0 revision `8de93bfb0f148f3b` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/attest`.
Pacing (development gateway): 54 of an assumed 60 requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply False.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Fix prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without integer conversion, preserving numeric precedence, string ordering, identifier-list ordering, and all existing public behavior. Retain permissive constructor inputs, legacy integer-value comparison and eager conversion errors for non-ASCII digit identifiers, core-version comparison before prerelease examination, strict parsing, ignored build metadata, and release precedence. Only comparison-related implementation in src/semver/version.py may change.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| semver.version.Version / semver.Version | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Keep constructor behavior unchanged: convert core parts with int(); retain None for absent prerelease/build and otherwise apply str(). String prereleases, inclu | ValueError: a converted core component is negative.; TypeError or ValueError: existing core-component int() conversion fails; preserve existing behavior.; No co |
| Version._nat_cmp | @classmethod _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | Preserve this existing internal comparison entry point. Split each operand on dots, treating None and '' as one empty identifier and retaining empty parts. A no | ValueError: any non-ASCII identifier satisfying str.isdigit() cannot be converted by int(), including '²'; propagate eagerly regardless of earlier identifier di |
| Version.compare | compare(self, other: Comparable) -> int | Preserve accepted operands and coercion: strings/bytes are parsed, dictionaries and tuples/lists construct versions, and existing compatible Version instances a | TypeError: unsupported comparison operand type, preserving existing behavior.; Existing parsing or construction exceptions: operand coercion fails.; ValueError: |
| Version comparison operators | __eq__(self, other: Comparable) -> bool; __ne__(self, other: Comparable) -> bool; __lt__(self, other: Comparable) -> bool; __le__(self, other: Comparable) -> bool; __gt__(self, other: Comparable) -> bool; __ge__(self, other: Comparable) -> bool | Continue deriving results from compare(), including long numeric identifiers and sorting. Preserve the existing decorator's NotImplemented behavior for unsuppor | ValueError: propagate prerelease conversion failures from compare() for otherwise accepted operands.; Preserve existing Python operator fallback and error behav |
| semver.compare | compare(ver1: str, ver2: str) -> int | Continue delegating to Version.parse(ver1).compare(ver2), returning exactly -1, 0, or 1 with the corrected long-identifier behavior. Preserve the existing depre | Preserve parsing and comparison exceptions for invalid inputs.; No integer-conversion-limit ValueError for valid ASCII numeric prereleases. |
| Version.parse | @classmethod parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Remain unchanged. Accept canonical ASCII prereleases of arbitrary identifier length, preserve their text, retain bytes handling and optional minor/patch behavio | ValueError: invalid SemVer input, specifically prereleases '01', '01.2', '١٢', and '１２'.; TypeError: unsupported input type.; Preserve all other existing decodi |
| Version.is_valid | @classmethod is_valid(cls, version: str) -> bool | Remain unchanged: return True when parse succeeds and False when parse raises ValueError. A valid 5000-digit ASCII numeric prerelease returns True. | Preserve propagation of exceptions other than ValueError from parse(). |
| Version.replace | replace(self, **parts: Union[int, Optional[str]]) -> "Version" | Remain unchanged: return a new version with requested parts replaced. Replacing only build metadata does not change comparison equality, including for long nume | TypeError: unknown replacement keys.; Preserve existing constructor errors for replacement values. |

Acceptance criteria:
1. 1. With v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) == 0, semver.compare(v, '0.0.0-2') == 1, and semver.compare('0.0.0-2', v) == -1, without ValueError.
2. 2. Parse each pair of prereleases using the '0.0.0-' prefix: ('9' * 4999, '1' + '0' * 4999), ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'), ('1' * 5000, 'alpha'), and ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'). Each pair must satisfy low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
3. 3. With version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0).
4. 4. For equal-core constructor versions, the following (left, right, expected) cases hold: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Reverse comparison returns the negated result, and both stored prerelease attributes equal their original inputs before and after comparison.
5. 5. Constructor prereleases '0' * 5000 and '0' compare equally; '0' * 5000 + '12' and '12' compare equally; '0' * 5000 + '12' and '١٢' compare equally. A 5000-digit nonzero ASCII numeric identifier compares above '١٢'. These comparisons must not convert the ASCII identifier to an integer.
6. 6. Identifier boundaries and empty parts are preserved: Version._nat_cmp('', None) == 0, Version._nat_cmp('a', 'a.') == -1, Version._nat_cmp('a..b', 'a.b') == -1, and Version._nat_cmp('0', '') == -1. Public comparison still places prerelease '0' below an absent prerelease.
7. 7. Version.parse('0.0.0-' + p) raises ValueError for every p in ('01', '01.2', '١٢', '１２'); Version.is_valid returns False for those same version strings.
8. 8. Equal-core constructor comparisons raise ValueError for ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), and for their reversals. Also require the error for ('a', 'a.²'), ('²', '²'), and ('²', None), demonstrating eager validation beyond a matching prefix, identical inputs, and release absence.
9. 9. Already-constructed versions with prerelease '²' compare by core without raising when any decisive core component differs: (0, 0, 0) is below (1, 0, 0), (0, 1, 0), and (0, 0, 1). Forward compare returns -1, reverse returns 1, and the corresponding less-than expressions are True.
10. 10. Run the long-identifier regression checks with an active 4300-digit integer conversion limit on Python runtimes supporting that limit. The implementation must neither alter the interpreter limit nor require disabling it. Source review must confirm ASCII numeric comparison uses zero normalization, length, and lexicographic ordering rather than integer conversion or another numeric-conversion workaround.
11. 11. All existing tests in tests/ pass unchanged; the repository's configured pytest suite continues to pass. Existing operand coercion, comparison errors, aliases, parsing, constructor behavior, and unrelated version operations remain unchanged.
12. 12. The implementation diff is confined to comparison-related changes in src/semver/version.py; no tests, documentation, parsing logic, native-backend integration, or packaging files are modified.

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `d7e8529b78c544583ca83998c119605dd3bc6349aaaf487393438185cda70ef6`, 21 test methods, sealed at 2026-10-17T13:30:04.934382+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (7 of 21 methods: ERROR 7): 7 of 21 methods failing, 14 passing; operation `01a14a0e-1b7f-7365-8bf1-0d24f44e908e`.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_all_comparison_operators_derive_from_long_identifier_order | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_ascii_zero_normalization_with_legacy_numeric_identifiers | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_compare_preserves_operand_coercion_and_ignores_build | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_compare_rejects_unsupported_operands | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_comparison_operator_propagates_legacy_conversion_error | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_constructor_and_parser_keep_existing_input_behavior | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_constructor_prereleases_keep_legacy_comparison_and_original_text | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_core_components_decide_before_prerelease_conversion | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_deprecated_compare_orders_long_ascii_identifier | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_invalid_collection_operators_return_not_implemented | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_legacy_conversion_errors_are_eager_across_decisive_identifiers | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_legacy_conversion_errors_survive_matching_prefix_and_release_absence | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_long_ascii_comparison_works_with_active_integer_conversion_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_long_ascii_identifier_parses_and_compares_equal | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_long_numeric_and_identifier_list_ordering | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_natural_comparison_preserves_empty_identifiers_and_boundaries | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_non_ascii_integer_conversion_limit_remains_effective | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_release_precedence_and_empty_prerelease_equivalence | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_replace_preserves_long_prerelease_and_rejects_unknown_key | ERROR (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_strict_parser_rejects_noncanonical_prereleases | ok (1 ev) | ok (1 ev) |
| test_sealed.PrereleaseComparisonAcceptanceTests.test_version_info_alias_is_preserved | ok (1 ev) | ok (1 ev) |

## 4. Candidate patch
1 changed path(s); scope check passed; 12 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,21 +185,28 @@
 
     @classmethod
     def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int:
-        def cmp_prerelease_tag(a, b):
-            if isinstance(a, int) and isinstance(b, int):
-                return _cmp(a, b)
-            elif isinstance(a, int):
-                return -1
-            elif isinstance(b, int):
-                return 1
+        def classify(identifier):
+            if identifier and all("0" <= char <= "9" for char in identifier):
+                return (0, identifier.lstrip("0") or "0")
+            if identifier.isdigit():
+                # Preserve int() conversion and its errors for non-ASCII digits.
+                return (0, str(int(identifier)))
+            return (1, identifier)
+
+        # Classify every identifier before deciding precedence, so legacy
+        # numeric conversion errors are raised even past a decisive prefix.
+        a_parts = [classify(x) for x in (a or "").split(".")]
+        b_parts = [classify(x) for x in (b or "").split(".")]
+
+        for sub_a, sub_b in zip(a_parts, b_parts):
+            if sub_a[0] != sub_b[0]:
+                cmp_result = _cmp(sub_a[0], sub_b[0])
+            elif sub_a[0] == 0:
+                cmp_result = _cmp(len(sub_a[1]), len(sub_b[1])) or _cmp(
+                    sub_a[1], sub_b[1]
+                )
             else:
-                return _cmp(a, b)
-
-        a_parts = [int(x) if x.isdigit() else x for x in (a or "").split(".")]
-        b_parts = [int(x) if x.isdigit() else x for x in (b or "").split(".")]
-
-        for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
+                cmp_result = _cmp(sub_a[1], sub_b[1])
             if cmp_result != 0:
                 return cmp_result
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (21 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: OK (21 of 21 methods, each in its own process). Operation `01a14a12-841b-777e-8c1d-cd0859ffaaf0`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.84s (424 passed of 424); operation `01a14a12-a9ec-7295-8854-e537fca624c3`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite (evidence class `stdout`; tests/test_heldout_pr488.py): 450 passed, 1 skipped in 0.86s (450 passed of 450); operation `01a14a12-cb8b-70bc-8967-743f59838080`. Gate: failures block VERIFIED.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.84s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | all checks pass |
| heldout_suite | Held-out tests | pass | stdout | E4 | 450 passed, 1 skipped in 0.86s |
| mutation | Mutation check | pass | bound | E2 | score 0.917 on 12 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (10 of 10 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.08 (narrowed) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. Arbitration changes the verdict only in apply mode and only when every failing generated test was corrected and re-verified. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 12 generated, 12 evaluated: 11 killed, 1 survived, 0 unknown; mutation score 0.917 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-82b4493d2d | src/semver/version.py | 189 | LtE -> Lt | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_numeric_and_identifier_list_ordering, test_sealed.PrereleaseCo | 01a14a12-e89a-743f-a7fc-b8574d2b68ed |
| m02-e434cc579d | src/semver/version.py | 189 | And -> Or | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_numeric_and_identifier_list_ordering, test_sealed.PrereleaseCo | 01a14a12-e908-77be-9930-eb9236372a9d |
| m03-4d9a0d7522 | src/semver/version.py | 190 | Or -> And | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_deprecated_compare_orders_long_ascii_identifier, test_sealed.Prerel | 01a14a12-e8ec-75b4-8169-6435b62b4551 |
| m04-220164927a | src/semver/version.py | 194 | 1 -> 2 | survived |  | 01a14a12-e8f2-7118-aca4-8d356caf6409 |
| m05-5d59887f89 | src/semver/version.py | 199 | Or -> And | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_ascii_identifier_parses_and_compares_equal, test_sealed.Prerel | 01a14a12-e903-7292-8139-a5acb71ac8ca |
| m06-17726262fd | src/semver/version.py | 202 | 0 -> 1 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_deprecated_compare_orders_long_ascii_identifier, test_sealed.Prerel | 01a14a12-e8b6-7130-90df-1d4927bee2d9 |
| m07-b732065e75 | src/semver/version.py | 203 | 0 -> 1 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_numeric_and_identifier_list_ordering, test_sealed.PrereleaseCo | 01a14a12-e904-752e-9b51-4e3c637aae01 |
| m08-1bc1ef1cf7 | src/semver/version.py | 204 | 0 -> 1 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_deprecated_compare_orders_long_ascii_identifier, test_sealed.Prerel | 01a14a12-e914-7601-9c74-98d7d8d29acc |
| m09-d6c8d84df1 | src/semver/version.py | 204 | Eq -> NotEq | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_deprecated_compare_orders_long_ascii_identifier, test_sealed.Prerel | 01a14a13-0550-73c5-8e02-44a1e1f0fac0 |
| m10-26335ac838 | src/semver/version.py | 205 | 1 -> 2 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_ascii_identifier_parses_and_compares_equal, test_sealed.Prerel | 01a14a13-0642-72bb-a8b3-286ff591e9d6 |
| m11-1294d2f3ff | src/semver/version.py | 206 | 1 -> 2 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_ascii_identifier_parses_and_compares_equal, test_sealed.Prerel | 01a14a13-0749-7721-8ea4-9f0bf82c0f03 |
| m12-bb857fb63c | src/semver/version.py | 209 | 1 -> 2 | killed | test_sealed.PrereleaseComparisonAcceptanceTests.test_long_numeric_and_identifier_list_ordering, test_sealed.PrereleaseCo | 01a14a13-07c1-764b-9fbe-8912f77b9422 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `0b28d2ee4c458cd8adee6c4f21860794a3bc923740129a4d1ce3798d71669ac5`): OK (10 of 10 methods, each in its own process); binding ok; operation `01a14a14-335a-75c7-88d1-9f9b9d7aed69`. Notes: Targets long leading zeros, equal-length decimal ordering, mixed Unicode digits, eager conversion errors, operand coercion, and operator fallback.

(none)

### Counterexamples
None: no sealed, adversarial or held-out test failed on the candidate.

## 8. E5 Drift audit
Score 0.080 (narrowed; threshold 0.6). The diff appears to solve the task within scope: `identifier.lstrip("0") or "0"` and length-then-string comparison avoid ASCII integer conversion, while eager classification of both operands preserves legacy `int(identifier)` failures. Only `_nat_cmp` changes and the reported existing-suite result is supported, but the explicitly required regression verification is not demonstrated.

Scope narrowed: Verification omitted the required long-identifier regression checks under an active 4300-digit conversion limit. The trail records only the existing suite (424 passed, 1 skipped), with no observed execution of the specified long-identifier and legacy Unicode edge cases.  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
Not run (the verdict was not a generated-test NEEDS HUMAN, or arbitration was disabled).





## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 36964 | 2630 | 0 | - | 85.3s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36300 | 4131 | 0 | - | 59.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 13546 | 110 | 7168 | - | 20.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 16292 | 111 | 7168 | - | 18.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 15688 | 88 | 7168 | - | 20.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 33097 | 150 | 16384 | - | 23.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 16499 | 122 | 0 | - | 21.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 16416 | 110 | 7168 | - | 20.0s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 34256 | 131 | 24064 | - | 23.5s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 17006 | 106 | 7168 | - | 20.3s | ok |
| codex_gateway:gpt-6-sol | implement | implement-9 | medium | 54281 | 282 | 42880 | - | 25.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-10 | medium | 36577 | 1372 | 24960 | - | 35.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-11 | medium | 17644 | 144 | 7168 | - | 22.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-12 | medium | 18081 | 143 | 7168 | - | 18.1s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12591 | 2504 | 0 | - | 66.8s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 14032 | 249 | 0 | - | 27.8s | ok |

Model calls: 16 (0 failed, 0 malformed); tokens in/out/cached 389270/12383/158464; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a14a0b-971b-7727-afec-05d5ec860fc6 | SUCCESS | 0 | 0.581s | retained | off | 0.00116547 |
| checkpoint | 01a14a0b-ad8f-7167-9ac4-726da094e428 | SUCCESS | 0 | 3.591s | retained | on | 0.023784649999999997 |
| red-1 | 01a14a0e-1b7f-7365-8bf1-0d24f44e908e | SUCCESS | 0 | 5.173s | disposable | off | 0.044565070000000005 |
| impl-tests-11 | 01a14a12-15bf-77f4-8961-e3f0c1ff383d | SUCCESS | 0 | 2.145s | disposable | off | 0.011029830000000001 |
| verify | 01a14a12-841b-777e-8c1d-cd0859ffaaf0 | SUCCESS | 0 | 5.248s | disposable | off | 0.045283989999999996 |
| existing | 01a14a12-a9ec-7295-8854-e537fca624c3 | SUCCESS | 0 | 1.957s | disposable | off | 0.01092063 |
| heldout | 01a14a12-cb8b-70bc-8967-743f59838080 | SUCCESS | 0 | 2.007s | disposable | off | 0.01113572 |
| mutant-m01-82b4493d2d | 01a14a12-e89a-743f-a7fc-b8574d2b68ed | SUCCESS | 0 | 4.882s | disposable | off | 0.04087197 |
| mutant-m02-e434cc579d | 01a14a12-e908-77be-9930-eb9236372a9d | SUCCESS | 0 | 4.951s | disposable | off | 0.04102658000000001 |
| mutant-m04-220164927a | 01a14a12-e8f2-7118-aca4-8d356caf6409 | SUCCESS | 0 | 4.882s | disposable | off | 0.04072081 |
| mutant-m05-5d59887f89 | 01a14a12-e903-7292-8139-a5acb71ac8ca | SUCCESS | 0 | 4.953s | disposable | off | 0.04118776 |
| mutant-m03-4d9a0d7522 | 01a14a12-e8ec-75b4-8169-6435b62b4551 | SUCCESS | 0 | 4.951s | disposable | off | 0.04085285 |
| mutant-m06-17726262fd | 01a14a12-e8b6-7130-90df-1d4927bee2d9 | SUCCESS | 0 | 4.883s | disposable | off | 0.04107979 |
| mutant-m07-b732065e75 | 01a14a12-e904-752e-9b51-4e3c637aae01 | SUCCESS | 0 | 4.885s | disposable | off | 0.04110963 |
| mutant-m08-1bc1ef1cf7 | 01a14a12-e914-7601-9c74-98d7d8d29acc | SUCCESS | 0 | 4.98s | disposable | off | 0.0413702 |
| mutant-m09-d6c8d84df1 | 01a14a13-0550-73c5-8e02-44a1e1f0fac0 | SUCCESS | 0 | 4.96s | disposable | off | 0.04108528 |
| mutant-m10-26335ac838 | 01a14a13-0642-72bb-a8b3-286ff591e9d6 | SUCCESS | 0 | 4.805s | disposable | off | 0.04067782 |
| mutant-m11-1294d2f3ff | 01a14a13-0749-7721-8ea4-9f0bf82c0f03 | SUCCESS | 0 | 4.932s | disposable | off | 0.04101516000000001 |
| mutant-m12-bb857fb63c | 01a14a13-07c1-764b-9fbe-8912f77b9422 | SUCCESS | 0 | 4.949s | disposable | off | 0.041257459999999996 |
| breaker-tests | 01a14a14-335a-75c7-88d1-9f9b9d7aed69 | SUCCESS | 0 | 3.105s | disposable | off | 0.02433497 |

Sandbox operations: 20, total guest duration 82.82s, retained images ['09b251e5-6ad6-4772-b855-b29d18d96241', '0970646b-9a1d-4301-b858-d6fa6549cdf3'].

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
