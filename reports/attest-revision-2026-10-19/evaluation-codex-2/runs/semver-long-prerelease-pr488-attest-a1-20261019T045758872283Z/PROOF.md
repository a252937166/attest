# Attest Proof Bundle: Compare long numeric prerelease identifiers without int conversion (python-semver issue #487)

**Verdict: VERIFIED**  
Run `semver-long-prerelease-pr488-attest-a1-20261019T045758872283Z` · profile `eval-attest-a1` · provider `codex_gateway` · executor `tf_sandboxes`  
Started 2026-10-19T04:57:58.873826+00:00, finished 2026-10-19T05:09:25.380274+00:00.

**Accept this patch.** All 25 sealed tests pass on the candidate in a fresh sandbox, and 9 of them failed on the unmodified base. The existing test suite, the mutation check, the tests written after the patch and the drift audit all passed.

Key evidence (E1): 24 of 25 sealed tests pass, each in its own process; the nonce and the sealed-file digest matched.

Weak spots: 1 one-line change(s) to the patch were not caught by the sealed tests (score 0.857, threshold 0.5). They mark lines the acceptance tests do not constrain (E2). The existing test suite result is parsed console output, not per-test exit codes under the supervisor. No held-out suite exists for this task, so nothing outside the model-written tests exercised the patch (E4). 1 of the sealed tests failed as written and were corrected by the arbiter; the correction kept every test method, changed only the failing ones, passes on the candidate and discriminates (every corrected sealed test fails on the unmodified base (red check preserved)), and the gate was re-run on it (E6). Whether the original test was wrong is the arbiter's judgement; both versions are in the bundle.

What to do: Merge the patch, or download the Proof Bundle and re-run the sealed suite yourself.

Reasons: all gates passed
Warnings: existing suite evidence is parsed console output (test runner 'pytest' is parsed from console output; only unittest suites run bound); the sealed, mutation and adversarial gates are bound; arbitration (validated corrections re-run their gates): all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (every corrected sealed test fails on the unmodified base (red check preserved)); the affected gate(s) are re-run on the corrected modules

## 0. What this bundle proves, and what it does not
Generated from the recorded gates; each statement cites the exhibit that carries it.

Proves:
- The candidate passes all 25 sealed acceptance tests in a fresh sandbox, each in its own process, bound by nonce, file digest and canaries (E1).
- 9 of those tests failed on the unmodified checkpoint, so they test the change and not the baseline (E1).
- The repository's own suite passes on the candidate (gates table, evidence class stdout).
- 6 of 7 one-line mutants of the changed lines were caught by the sealed tests (E2).
- 8 tests written after the patch by an independent model instance pass on the candidate (E3).
- A model audit found the work aligned with the request (score 0, aligned (threshold 0.6); E5). This is a judgement, not evidence.

Does not prove:
- That the 16 sealed test(s) which already passed on the base say anything about the change (E1).
- That the sealed tests constrain the lines marked by the 1 surviving mutant(s) (E2).
- Anything beyond the model-written tests and the repository's own suite: no held-out suite was configured for this task (E4).
- That the sealed tests capture the requester's intent: they were written by a model from the task statement, so a VERIFIED patch is correct against those tests, not against unstated requirements (E1).
- That the patch is correct for inputs none of the suites exercise.
- That the drift audit is evidence: it is a model judgement and never the basis of VERIFIED on its own (E5).
- That the existing test suite result is bound: it is parsed console output of the repository's test command, not per-test exit codes (gates table).
- That the arbiter's classification of the corrected test(s) is right: the correction was validated by execution and the gate re-run, but which side was wrong is a model judgement; the original tests and results are preserved (E6).

| Exhibit | Evidence | Status | Class | Summary |
| --- | --- | --- | --- | --- |
| E1 | Sealed tests, written before the patch | pass | bound | 1 of 25 failed on the candidate as sealed; 1 test(s) corrected by the arbiter and validated (every corrected sealed test fails on the unmodified base (red check preserved)); the corrected module passes (OK (25 of 25 methods, each in its own process)) |
| E2 | Mutation check | pass | bound | 6 of 7 one-line mutants caught, 1 survived, 0 unknown; score 0.857 (threshold 0.5) |
| E3 | Tests written after the patch | pass | bound | 8 of 8 pass |
| E4 | Held-out tests | none | - | none configured for this task |
| E5 | Drift audit | pass | model | score 0, aligned (threshold 0.6) |
| E6 | Arbitration of generated-test failures | advisory | model | all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (every corrected sealed test fails on the unmodified base (red check preserved)); the affected gate(s) are re-run on the corrected modules |

## 1. Frozen task and provenance
Task `semver-long-prerelease-pr488`, spec digest `bebfebfc4bcfdac2b3d8de3361919f592abc7494e4052b76fab3fde2ac27bc70`; base image `python:3.12-slim` (uuid `4fa16c8f-62a9-35a4-a4ea-07b7e8cd44ae`), checkpoint `842f9995-bc95-44fc-b7c1-a47eee02eb70`; test runner `pytest`; install: `/usr/local/bin/python -m pip install --no-cache-dir --disable-pip-version-check --target /tmp/deps pytest==8.3.3 pluggy==1.5.0 iniconfig==2.0.0 packaging==24.1` (checkpoint networking on).

Attest 0.4.0 revision `87aa03b95d6e6e33` (35 package sources; no git repository). Guest programs: supervisor `attest-sealed-supervisor/6` sha256 `93e8c9edacca93fc`, per-test child `e4e7b0b294a2004c`, canary module `9cdc57c1348fae5c`, sandbox runner `80999537285bacaf`.
Runtime: Python 3.12.0 on macOS-27.0.1-arm64-arm-64bit; package executed from `/work/attest/reports/attest-revision-2026-10-19/evaluation-codex-2/snapshot/attest`.
Pacing (development gateway): None of an assumed None requests per hour per key, at most 2 in flight, bounded wait 3900.0 s; HTTP 429 (definite rejection) retried after a bounded wait; transport-uncertain failures never retried.

Sampling (codex_gateway): temperature controlled by the gateway, max_tokens controlled by the gateway; spec: gpt-6-astra (low); seal: gpt-6-sol (medium); implement: gpt-6-sol (medium); break: gpt-6-sol (medium); audit: gpt-6-astra (low); arbitrate: gpt-6-astra (medium); summary: gpt-6-luna (low).

Limits: max_turns 12, max_mutants 12, mutation_threshold 0.5, drift_threshold 0.6, mutant_workers 8, max_seal_attempts 3, min_sealed_tests 5, min_mutants_for_score 4, min_adversarial_when_no_mutants 6, per_test_timeout_s 60, test_timeout_s 180, checkpoint_timeout_s 300, arbitrate True, arbitration_apply True, max_corrected_tests 3, max_mutants_for_discrimination 3, max_breaker_attempts 3, max_witnesses 3, witness_timeout_s 60.

Upstream: https://github.com/python-semver/python-semver at commit `887d057e66b7fdfe0adf5a206ac810766b5af938`; upstream issue #487, fixed by pull request #488 (merge commit 1d515915d50b31f23fd1fb0f572ef608453e80e3); the held-out tests are the pull request's own additions to tests/test_compare.py.

python-semver (src/semver, BSD-3) is a semantic-versioning library whose central class is semver.version.Version (also exported as semver.Version). Bug report (upstream issue #487): Version.is_valid("0.0.0-" + "1" * 5000) is True, but Version.parse("0.0.0-" + "1" * 5000).compare(...) raises ValueError, because Version._nat_cmp in src/semver/version.py converts every all-digit prerelease identifier with int() and CPython refuses int conversion of strings longer than 4300 digits. Fix the prerelease comparison in src/semver/version.py so that it never converts a long ASCII numeric identifier to an int, while keeping the existing ordering rules exactly. Required semantics of the prerelease comparison: identifiers are the dot-separated parts of the prerelease string (an empty or None prerelease has one empty identifier); an identifier consisting only of ASCII digits is numeric and compares by its decimal value, computed without int(): strip leading zeros (an all-zero identifier becomes "0"), compare by length first and then lexicographically; a numeric identifier is lower than any non-numeric identifier; two non-numeric identifiers compare as plain strings; when every identifier of the shorter list is equal, the longer list is higher. Preserve the constructor's legacy behaviour: Version(0, 0, 0, prerelease=...) accepts identifiers with leading zeros and identifiers written with non-ASCII decimal digits (str.isdigit() is true), and such non-ASCII digit identifiers keep comparing by their int() value, so "١٢" compares equal to "12" and "１２" is lower than "13"; an identifier for which str.isdigit() is true but int() fails (for example "²") must still make compare() raise ValueError, eagerly, even when an earlier identifier would already decide the order, but only when the core versions are equal: a difference in major, minor or patch is decided before the prerelease is examined, so Version(0, 0, 0, prerelease="²") < Version(1, 0, 0, prerelease="²") is True. Keep everything else unchanged: Version.parse keeps rejecting non-canonical prereleases such as "01", "01.2", "١٢" and "１２" with ValueError; build metadata is ignored in comparisons; a version with a prerelease is lower than the same core version without one; the prerelease attribute is stored as given. Do not change parsing, the optional native parser, tests, docs or packaging files, and keep the whole existing pytest suite passing.

## 2. Specification and contract
Feasible: True. Update prerelease comparison in src/semver/version.py so ASCII numeric identifiers of arbitrary length compare by normalized decimal strings without integer conversion. Preserve existing version precedence, constructor permissiveness, Unicode digit conversion behavior and eager conversion errors, parsing restrictions, stored attributes, public interfaces, and the unchanged test suite.

| Name | Signature | Behavior | Errors |
| --- | --- | --- | --- |
| Version | Version(major: SupportsInt, minor: SupportsInt = 0, patch: SupportsInt = 0, prerelease: Optional[Union[String, int]] = None, build: Optional[Union[String, int]] = None) | Available as semver.Version and semver.version.Version; VersionInfo remains its alias. Constructor behavior is unchanged: core components are converted to integ | ValueError: a converted core component is negative.; TypeError or ValueError: existing core integer conversion fails. |
| Version._nat_cmp | @classmethod def _nat_cmp(cls, a: Optional[str], b: Optional[str]) -> int | This existing internal comparison boundary returns exactly -1, 0, or 1. Split each input on dots, treating None and an empty string as one empty identifier and  | ValueError: int(identifier) fails for any digit-only non-ASCII identifier anywhere in either input, including an unpaired suffix or an identifier following an a |
| Version.compare | def compare(self, other: Comparable) -> int | Preserve supported operands: Version instances compatible with the existing class check, strings, bytes, dictionaries, tuples, and lists. Preserve operand parsi | TypeError: unsupported operand type, under existing rules.; TypeError or ValueError: existing operand parsing or construction fails.; ValueError: equal-core pre |
| Version comparison operators | def __eq__(self, other: Comparable) -> bool; def __ne__(self, other: Comparable) -> bool; def __lt__(self, other: Comparable) -> bool; def __le__(self, other: Comparable) -> bool; def __gt__(self, other: Comparable) -> bool; def __ge__(self, other: Comparable) -> bool | Continue deriving supported-operand results from compare(), including sorting and build-insensitive equality. Preserve the existing decorator's NotImplemented b | ValueError: propagated from prerelease comparison for otherwise supported operands.; Preserve existing Python operator behavior after NotImplemented, including  |
| Version.parse | @classmethod def parse(cls: Type[T], version: String, optional_minor_and_patch: bool = False) -> T | Unchanged. Parse canonical SemVer strings or UTF-8 bytes, preserving subclass construction and optional minor/patch behavior. Long canonical ASCII numeric prere | ValueError: invalid SemVer input, including prereleases '01', '01.2', '١٢', and '１２'.; TypeError: unsupported input type.; UnicodeDecodeError: invalid UTF-8 byt |
| Version.is_valid | @classmethod def is_valid(cls, version: str) -> bool | Unchanged. Return True when parse succeeds and False when parse raises ValueError, including True for the specified 5000-digit canonical prerelease. | Exceptions not caught by the existing ValueError handler continue to propagate. |
| semver.compare | def compare(ver1: str, ver2: str) -> int | Keep the existing deprecated wrapper, warning behavior, and delegation to Version.parse(ver1).compare(ver2). Long ASCII numeric prereleases receive the correcte | Propagate existing parsing and comparison errors. |
| Version.replace | def replace(self, **parts: Union[int, Optional[str]]) -> "Version" | Unchanged. Return a new version with specified parts replaced. Replacing only build metadata must preserve comparison equality, including for long numeric prere | TypeError: unknown replacement keys, as before.; Preserve existing constructor errors for replacement values. |

Acceptance criteria:
AC1. 1. For v = '0.0.0-' + '1' * 5000, Version.is_valid(v) is True, Version.parse(v).compare(v) is 0, semver.compare(v, '0.0.0-2') is 1, and the reverse comparison is -1, without ValueError.
AC2. 2. For parsed equal-core versions, each pair is strictly ascending: ('9' * 4999, '1' + '0' * 4999), ('1' + '0' * 4998 + '1', '1' + '0' * 4998 + '2'), ('1' * 5000, 'alpha'), and ('alpha.' + '1' * 5000, 'alpha.' + '1' * 5000 + '.1'). For every pair, low.compare(high) == -1, high.compare(low) == 1, and sorted([high, low]) == [low, high].
AC3. 3. For version = Version.parse('0.0.0-' + '1' * 5000), version == version.replace(build='other') and version < Version(0, 0, 0). Comparison leaves all stored attributes unchanged.
AC4. 4. Using Version(0, 0, 0, prerelease=p), the following (left, right, result) cases hold: ('0001', '1', 0), ('000', '0', 0), ('02', '10', -1), ('01.2', '1.2', 0), ('2a', '10a', 1), ('01a', '1a', -1), ('-1', '0', 1), ('', None, 0), ('١٢', '12', 0), ('１２', '13', -1), ('1٢', '12', 0), and ('٠٠١', '1', 0). Reverse comparisons negate the result, and both prerelease attributes retain exactly their supplied strings or None.
AC5. 5. Constructor prereleases with long leading-zero ASCII identifiers use normalized values: '0' * 5000 equals '0', '0' * 5000 + '1' equals '1', and '0' * 5000 + '2' is lower than '10'. A 5000-digit nonzero ASCII identifier also compares numerically above the Unicode identifier '١٢', without converting the ASCII identifier to int.
AC6. 6. Identifier splitting preserves empty parts. Direct _nat_cmp('', None) == 0, _nat_cmp('a', 'a.') == -1, _nat_cmp('a..b', 'a..c') == -1, and _nat_cmp('', '0') == 1. At the version level, empty and None prereleases are equivalent releases and both rank above any nonempty valid prerelease.
AC7. 7. Version.parse('0.0.0-' + p) raises ValueError for each p in ('01', '01.2', '١٢', '１２'); Version.is_valid returns False for those same version strings. Parsing rules and native-parser integration remain unchanged.
AC8. 8. Equal-core constructor comparisons raise ValueError for ('²', '2'), ('a.²', 'b.0'), and ('a.0', 'b.²'), and for their reversals. Eagerness also applies to unpaired suffixes, such as ('a', 'a.²'), and release comparisons, such as ('²', None). No specific new exception message is required.
AC9. 9. Core precedence bypasses prerelease examination: Version(0, 0, 0, prerelease='²') < Version(1, 0, 0, prerelease='²') is True. Equivalent cases differing first in minor or patch also return the core ordering without ValueError; reverse comparisons negate it.
AC10. 10. ASCII numeric comparison uses no int conversion, including after removing leading zeros, and does not raise, disable, or otherwise modify the interpreter's integer-string conversion limit. On CPython with that facility, run the 5000-digit cases with the limit enabled at 4300 and confirm the setting is unchanged afterward.
AC11. 11. All existing tests in tests/ pass unchanged, including operand coercion, invalid-operand behavior, subclass behavior, parsing, and optional-backend tests.
AC12. 12. The implementation diff is confined to src/semver/version.py and the prerelease comparison fix; existing public signatures and unrelated behavior are unchanged.

## 2b. Contract audit (executed witnesses)
Outcome: consistent. Auditor `gpt-6-astra`; consistent=True. The requirements are jointly satisfiable by changing only _nat_cmp in src/semver/version.py: eagerly normalize numeric identifiers, retaining int() conversion and errors for Unicode digit identifiers, then compare normalized decimal strings. The existing compare() already provides core-first ordering and release precedence; no conflict with the supplied fixed code was identified. Rule: a conflict is demonstrated only when its witness program, run on the unmodified repository in a disposable sandbox branch, prints a line starting with 'CONTRADICTION' and exits with code 3; any other outcome records the conflict as claimed only, which never ends a run

(none)

## 3. E1 Sealed tests (written before implementation by an independent model instance)
`sealed/test_sealed.py` sha256 `edabc51c926a834de237a17b67a822be7f345b1cd341b3f8d1f739350114b0ff`, 25 test methods, sealed at 2026-10-19T05:02:28.988650+00:00 by `gpt-6-sol`; attempts: 1.

Red check on the unmodified checkpoint (one child process per test under the supervisor): FAILED (9 of 25 methods: ERROR 9): 9 of 25 methods failing, 16 passing; operation `01a1528a-203a-76d4-8a08-6d10972033bb`.
Coverage map (the sealer's own claim): every acceptance criterion is claimed by at least one existing test method.

| Sealed test method | Base (red) | Candidate |
| --- | --- | --- |
| test_sealed.TestCompatibility.test_all_comparison_operators_follow_compare | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_compare_accepts_supported_operand_forms | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_constructor_core_conversion_and_negative_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_invalid_compare_and_operator_operands | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_parse_bytes_optional_parts_and_input_errors | ok (1 ev) | ok (1 ev) |
| test_sealed.TestCompatibility.test_public_aliases_and_subclass_parse | ERROR (1 ev) | ERROR (1 ev) |
| test_sealed.TestCompatibility.test_replace_preserves_original_and_rejects_unknown_part | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_constructor_prerelease_comparison_matrix | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_constructor_preserves_unvalidated_prerelease_and_build | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_core_precedence_bypasses_bad_prerelease | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_empty_and_none_prereleases_have_release_precedence | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_nat_cmp_retains_empty_identifiers | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_operator_propagates_unicode_conversion_error | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_parser_rejects_leading_zeros_and_unicode_digits | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_unicode_conversion_is_eager_after_decisive_pair_or_in_suffix | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_unicode_conversion_is_eager_against_release | ok (1 ev) | ok (1 ev) |
| test_sealed.TestIdentifierSemantics.test_unicode_integer_limit_failure_remains_eager | ok (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_ascii_comparison_preserves_integer_string_limit | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_comparison_preserves_all_stored_parts | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_deprecated_compare_orders_long_prerelease_and_warns | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_long_ascii_number_compares_above_unicode_number | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_long_canonical_prerelease_parses_and_compares_equal | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_long_identifier_precedence_and_sorting | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_long_leading_zeros_normalize_without_changing_storage | ERROR (1 ev) | ok (1 ev) |
| test_sealed.TestLongAsciiPrereleases.test_long_prerelease_ignores_build_and_precedes_release | ERROR (1 ev) | ok (1 ev) |
Corrected sealed module (E6): `arbitration/sealed_corrected.py` sha256 `5d0a5ac569de78f7897dfc61d3fee8a95339489419b651e9e8675b43e54c201a`; corrected tests test_public_aliases_and_subclass_parse; on the candidate OK (25 of 25 methods, each in its own process); validated: every corrected sealed test fails on the unmodified base (red check preserved); operation `01a1528e-fa51-75c6-ae94-e39347bd77ec`. The sealed gate was re-run on it.

## 4. Candidate patch
1 changed path(s); scope check passed; 8 implementer turn(s).

```diff
--- a/src/semver/version.py
+++ b/src/semver/version.py
@@ -185,21 +185,20 @@
 
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
+        def normalize(identifier):
+            if identifier.isascii() and identifier.isdigit():
+                digits = identifier.lstrip("0") or "0"
+                return (0, len(digits), digits)
+            if identifier.isdigit():
+                digits = str(int(identifier))
+                return (0, len(digits), digits)
+            return (1, identifier)
+
+        a_parts = [normalize(x) for x in (a or "").split(".")]
+        b_parts = [normalize(x) for x in (b or "").split(".")]
 
         for sub_a, sub_b in zip(a_parts, b_parts):
-            cmp_result = cmp_prerelease_tag(sub_a, sub_b)
+            cmp_result = _cmp(sub_a, sub_b)
             if cmp_result != 0:
                 return cmp_result
```

Static tamper scan of the added lines: no suspicious constructs on the added lines (12 added lines checked against 19 patterns; a warning, never a gate).


## 5. Fresh-branch verification (E1 binding; E4 held-out)
Order: verify: sealed supervisor is the only step of its branch (nothing imports candidate code before it); existing: the repository's own suite runs afterwards in its own disposable branch; heldout: held-out modules run afterwards in their own disposable branch.

Sealed suite: FAILED (1 of 25 methods: ERROR 1). Operation `01a1528d-27db-76a2-8413-29b83e1ac1e3`, networking disabled, disposable branch from the checkpoint; the supervisor is the first step and runs two verifier canaries after the suite (canary ok: True).

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

Existing suite (evidence class `stdout`): 424 passed, 1 skipped in 0.84s (424 passed of 424); operation `01a1528d-55f7-70cf-9bc6-66d2fa6baf63`; parsed from console output (test runner 'pytest' is parsed from console output; only unittest suites run bound).

E4 held-out suite: none configured.

## 6. Gates and verdict rule
Evidence classes: `bound` = per-test exit codes under the supervisor, nonce and digests checked; `stdout` = parsed console output of the repository's test command; `model` = a model judgement. Skipped gates never count as passed.

| Gate | Meaning | Result | Evidence | Exhibit | Detail |
| --- | --- | --- | --- | --- | --- |
| existing_suite | Existing test suite | pass | stdout | - | 424 passed, 1 skipped in 0.84s |
| sealed_binding | Sealed tests, nonce-bound | pass | bound | E1 | OK (25 of 25 methods, each in its own process) on the corrected sealed module (1 test(s) corrected, validated: every corrected sealed test fails on the unmodified base (red check preserved)); the original failure is kept in E1 |
| mutation | Mutation check | pass | bound | E2 | score 0.857 on 7 mutants |
| adversarial_tests | Tests written after the patch | pass | bound | E3 | OK (8 of 8 methods, each in its own process) |
| drift_audit | Drift audit | pass | model | E5 | score 0.0 (aligned) |

Verdict rule: VERIFIED only when every recorded gate passes (a skipped gate never counts as a pass), the implementer finished and the scope policy held; otherwise NEEDS HUMAN. A gate passes on a corrected generated-test module only when the correction was validated by execution (same test methods, only the failing ones changed, passes on the candidate, still discriminates on the base or a mutant) and the gate was re-run; the arbiter's classification alone never changes a gate. Derived VERIFIED; blocking: nothing.

## 7. Breaker pass (E2 mutation check; E3 tests written after the patch)
E2: mutants of changed lines, each in its own branch: 7 generated, 7 evaluated: 6 killed, 1 survived, 0 unknown; mutation score 0.857 (threshold 0.5).

| Mutant | File | Line | Mutation | Status | Killed by | Operation |
| --- | --- | --- | --- | --- | --- | --- |
| m01-3595e235d3 | src/semver/version.py | 189 | And -> Or | killed | test_sealed.TestLongAsciiPrereleases.test_long_identifier_precedence_and_sorting, test_sealed.TestIdentifierSemantics.te | 01a1528f-4576-76a3-8ffd-8536b42a9942 |
| m02-b7f855b9f7 | src/semver/version.py | 190 | Or -> And | killed | test_sealed.TestLongAsciiPrereleases.test_deprecated_compare_orders_long_prerelease_and_warns, test_sealed.TestLongAscii | 01a1528f-4271-71c6-8155-3f1b7998ed33 |
| m03-7670945007 | src/semver/version.py | 191 | 0 -> 1 | killed | test_sealed.TestLongAsciiPrereleases.test_long_identifier_precedence_and_sorting, test_sealed.TestLongAsciiPrereleases.t | 01a1528f-44bc-7767-95ed-aca40a11f4cf |
| m04-774331b9b5 | src/semver/version.py | 194 | 0 -> 1 | killed | test_sealed.TestLongAsciiPrereleases.test_long_ascii_number_compares_above_unicode_number, test_sealed.TestIdentifierSem | 01a1528f-426c-7665-b13a-f35bc04bc7fb |
| m05-d8742a529a | src/semver/version.py | 195 | 1 -> 2 | survived |  | 01a1528f-456b-720d-b0b5-1db0aeb725a0 |
| m06-8b05c1c0e7 | src/semver/version.py | 197 | Or -> And | killed | test_sealed.TestLongAsciiPrereleases.test_long_canonical_prerelease_parses_and_compares_equal, test_sealed.TestLongAscii | 01a1528f-45a8-70c7-b0e3-914be2b387cb |
| m07-09e5acb6bc | src/semver/version.py | 198 | Or -> And | killed | test_sealed.TestLongAsciiPrereleases.test_long_canonical_prerelease_parses_and_compares_equal, test_sealed.TestLongAscii | 01a1528f-44ce-728d-9126-ddd57ea39ca0 |

E3: model-written adversarial tests (`breaker_tests.py`, by `gpt-6-sol`, sha256 `8b8405c77c1db940a2ab2689d1605ee6120a9b2387c1cf996bcd5c4f471d15af`): OK (8 of 8 methods, each in its own process); binding ok; operation `01a15290-8484-7652-96f9-1dcfa57a7682`. Notes: Targets integer limit boundaries, mixed digit normalization, empty identifiers, eager Unicode errors, operand coercion, ordering, and compound parser restrictions.

(none)

Adversarial authoring: 1 attempt(s).

### Counterexamples
- E1 `test_public_aliases_and_subclass_parse`: ERROR; TypeError: Expected str, bytes, dict, tuple, list, or Derived instance, but got <class 'semver.version.Version'>; arbiter: Defective test, by the arbiter; contract basis: Version.compare preserves Version operands compatible with the existing class check and existing TypeError behavior. Version.parse preserves subclass construction; it does not broaden comparison operand compatibility.

## 8. E5 Drift audit
Score 0.000 (aligned; threshold 0.6). The diff solves the task within src/semver/version.py: `identifier.lstrip("0") or "0"` and `(0, len(digits), digits)` implement arbitrary-length ASCII numeric ordering, while `str(int(identifier))` preserves legacy Unicode conversion and eager list comprehensions preserve conversion errors. No unrelated behavior changes are evident; observed output supports the reported 424 passed, 1 skipped and successful targeted checks, although the targeted script itself is not shown.

Scope narrowed: none  
Scope widened: none  
Unsupported claims: none

## 8b. E6 Arbitration of generated-test failures
all 1 failing generated test(s) classified as test defects; the corrected tests pass on the candidate and discriminate (every corrected sealed test fails on the unmodified base (red check preserved)); the affected gate(s) are re-run on the corrected modules (mode: validated corrections re-run their gates). Classifications: {'implementation_bug': 0, 'test_defect': 1, 'contract_dispute': 0}. original tests, results and reasons are preserved unchanged; the arbiter's classification alone never changes a gate Rule: a correction counts only when it keeps every test method, changes only the failing ones, passes on the candidate and still discriminates (fails on the unmodified base, or is caught by a mutant of the patch); a sealed test that failed by assertion is never overridden; a validated correction re-runs its gate and the verdict is derived from the gates Gates re-run on validated corrections: sealed_binding (tests test_public_aliases_and_subclass_parse; every corrected sealed test fails on the unmodified base (red check preserved)).

| Failing test | Classification | Rationale | Contract basis |
| --- | --- | --- | --- |
| test_public_aliases_and_subclass_parse | test_defect | The test assumes a subclass instance must accept a base Version instance as its comparison operand. The preserved class check requires a Der | Version.compare preserves Version operands compatible with the existing class check and existing TypeError behavior. Version.parse preserves |

- `sealed` corrected re-run: candidate OK (25 of 25 methods, each in its own process); base FAILED (9 of 25 methods: ERROR 9); validated=True

## 9. Grounding
No grounding calls (specification named no external references).



## 10. Ledger
| Model | Role | Stage | Effort | In | Out | Cached | USD | Elapsed | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| codex_gateway:gpt-6-astra | spec | spec | low | 36986 | 2529 | 7680 | - | 100.9s | ok |
| codex_gateway:gpt-6-astra | audit | contract-audit | low | 37457 | 187 | 7552 | - | 30.0s | ok |
| codex_gateway:gpt-6-sol | seal | seal-1 | medium | 36326 | 5457 | 0 | - | 84.9s | ok |
| codex_gateway:gpt-6-sol | implement | implement-1 | medium | 14453 | 125 | 7168 | - | 17.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-2 | medium | 45427 | 420 | 29440 | - | 27.6s | ok |
| codex_gateway:gpt-6-sol | implement | implement-3 | medium | 31119 | 816 | 22272 | - | 33.2s | ok |
| codex_gateway:gpt-6-sol | implement | implement-4 | medium | 15704 | 119 | 7168 | - | 15.8s | ok |
| codex_gateway:gpt-6-sol | implement | implement-5 | medium | 16008 | 197 | 7168 | - | 18.4s | ok |
| codex_gateway:gpt-6-sol | implement | implement-6 | medium | 16146 | 117 | 0 | - | 16.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-7 | medium | 34267 | 1058 | 24064 | - | 30.1s | ok |
| codex_gateway:gpt-6-sol | implement | implement-8 | medium | 17638 | 231 | 7168 | - | 18.0s | ok |
| codex_gateway:gpt-6-astra | audit | drift-audit | low | 13437 | 192 | 0 | - | 23.0s | ok |
| codex_gateway:gpt-6-astra | arbitrate | arbitrate-sealed | medium | 16883 | 3975 | 0 | - | 76.9s | ok |
| codex_gateway:gpt-6-sol | break | break-tests-1 | medium | 12422 | 2620 | 7040 | - | 71.9s | ok |

Model calls: 14 (0 failed, 0 malformed); tokens in/out/cached 344273/18043/126720; USD: n/a (Codex gateway allowance, not billed in USD).

| Sandbox op | Operation | Status | Exit | Duration | Image | Net | raw cost diag (not USD) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-files-1 | 01a15286-3f59-77b8-a344-d9b8ffdf83c5 | SUCCESS | 0 | 0.687s | retained | off | 0.0011611500000000001 |
| checkpoint | 01a15286-7b80-764b-8cbc-f365e9b34cb1 | SUCCESS | 0 | 4.222s | retained | on | 0.02342869 |
| red-1 | 01a1528a-203a-76d4-8a08-6d10972033bb | SUCCESS | 0 | 6.097s | disposable | off | 0.05249956000000001 |
| impl-tests-6 | 01a1528c-3b54-7056-be74-5dc2a20f5665 | SUCCESS | 0 | 1.828s | disposable | off | 0.01074981 |
| impl-python-7 | 01a1528c-ce03-7339-8711-19844460f217 | SUCCESS | 0 | 0.703s | disposable | off | 0.0024533500000000004 |
| verify | 01a1528d-27db-76a2-8413-29b83e1ac1e3 | SUCCESS | 0 | 5.96s | disposable | off | 0.05156183 |
| existing | 01a1528d-55f7-70cf-9bc6-66d2fa6baf63 | SUCCESS | 0 | 1.844s | disposable | off | 0.010847810000000001 |
| arbitrate-sealed-candidate | 01a1528e-fa51-75c6-ae94-e39347bd77ec | SUCCESS | 0 | 6.083s | disposable | off | 0.051995030000000005 |
| arbitrate-sealed-base | 01a1528f-1e2f-715e-a469-df1664a35616 | SUCCESS | 0 | 6.119s | disposable | off | 0.0520885 |
| mutant-m02-b7f855b9f7 | 01a1528f-4271-71c6-8155-3f1b7998ed33 | SUCCESS | 0 | 5.776s | disposable | off | 0.04892056000000001 |
| mutant-m03-7670945007 | 01a1528f-44bc-7767-95ed-aca40a11f4cf | SUCCESS | 0 | 5.712s | disposable | off | 0.0482218 |
| mutant-m04-774331b9b5 | 01a1528f-426c-7665-b13a-f35bc04bc7fb | SUCCESS | 0 | 5.603s | disposable | off | 0.047758930000000005 |
| mutant-m06-8b05c1c0e7 | 01a1528f-45a8-70c7-b0e3-914be2b387cb | SUCCESS | 0 | 5.585s | disposable | off | 0.04821588000000001 |
| mutant-m05-d8742a529a | 01a1528f-456b-720d-b0b5-1db0aeb725a0 | SUCCESS | 0 | 5.733s | disposable | off | 0.04841573 |
| mutant-m01-3595e235d3 | 01a1528f-4576-76a3-8ffd-8536b42a9942 | SUCCESS | 0 | 5.754s | disposable | off | 0.04843890000000001 |
| mutant-m07-09e5acb6bc | 01a1528f-44ce-728d-9126-ddd57ea39ca0 | SUCCESS | 0 | 5.777s | disposable | off | 0.04876744 |
| breaker-tests | 01a15290-8484-7652-96f9-1dcfa57a7682 | SUCCESS | 0 | 2.676s | disposable | off | 0.020413090000000002 |

Sandbox operations: 17, total guest duration 76.159s, retained images ['ed6df82d-a4d3-447a-b0d6-9801a73b5345', '842f9995-bc95-44fc-b7c1-a47eee02eb70'].

## 11. Limitations of this bundle
- Profile 'eval-attest-a1': inference provider codex_gateway; submission runs must use NVIDIA Nemotron on Nebius Token Factory and are labeled separately.
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
