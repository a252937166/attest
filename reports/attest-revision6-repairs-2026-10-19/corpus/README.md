# Item 3: the recorded-evidence tests classify their fixtures explicitly (19 October 2026)

Finding (revision-6 review, item 3): `RecordedCorpusHistorical` in `tests/test_audit_core.py` globbed every `proof_bundle.json`
under `reports/`, skipped snapshots, the `attest-audit-*` folders and three known-defective sets, and asserted that each bundle
checks as historical. The revision-6 development batch added three protocol-3 bundles under
`reports/attest-revision5-repairs-2026-10-19/evaluation-codex/`, which the glob picked up; the checker correctly reported them as
modern (`historical` false), so the test failed. The revision-6 suite log showed 352 passing tests because the suite had been run
before that batch existed; the review's later run on the final tree found 351 passing and this one failing.

The product checker is unchanged by this repair: it labels a bundle historical exactly when the bundle declares no evidence
protocol. The test is what was wrong.

## What changed (tests only)

`tests/test_audit_core.py`:

- `HISTORICAL_CORPUS`: the frozen list of report folders recorded before the evidence protocol existed (Attest 0.5.0, 19 Oct
  2026 07:58 UTC): the first slice, the 15 Oct verification, the 16 Oct evaluation, M1, M4, the 17 Oct reliability round, the
  freeze folder, the M5 evaluation and the revision-4 batches except the stopped one.
- `MODERN_CORPUS`: every folder recorded under a protocol, with the protocol its bundles declare: the two revision-5 batches
  (protocol 2), the revision-6 batch (protocol 3) and the four revision-7 batches of this pass (protocol 4).
- `KNOWN_DEFECTIVE` and `SYNTHETIC_DEFECTIVE`: the two partial copies of the 16 Oct hardening report, the stopped revision-4
  batch, and the 19 Oct audit's deliberately defective synthetic bundles.
- `RecordedCorpusInventory`: every run directory under `reports/` (outside snapshots) belongs to exactly one class; an
  unclassified or doubly classified directory fails with its path. A new batch folder therefore fails until it is deliberately
  added to `MODERN_CORPUS`; it can never silently join the historical corpus.
- `RecordedCorpusHistorical`: every bundle of the historical corpus declares no protocol (a fixture that does is reported as
  misclassified), checks `ok`, is historical, has no protocol, is not fully verified and has no evidence-complete status; more
  than 100 bundles.
- `RecordedCorpusModern`: every bundle of the modern corpus declares exactly its folder's protocol, is not historical, and checks
  `ok`, evidence complete and fully verified; every listed folder contains bundles.

## Final-tree runs

REV7-CORPUS-RESULTS
