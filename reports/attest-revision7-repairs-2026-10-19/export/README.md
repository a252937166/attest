# Public export: a privacy defect found and repaired, and the provenance of every exported bundle (revision 8, 19 October 2026)

## The defect

The export redacts the development gateway's host name from every public copy and fails when its final scan still finds it.
Both steps matched the host as plain text. The exporter's own redaction patterns, however, spelled the host as a regular
expression (with a backslash before each dot), and two kinds of files carried those patterns into the public tree:

- the public copy of `scripts/export_public.py` itself (the patterns are in its source), and
- every `REDACTION.json` (125 in the revision-7 export), whose `rules` field listed the patterns, JSON-escaped.

Neither spelling matched the plain-text redaction or the scan, so every export since the review repository was created (its first
commit, 17 Oct 2026) carried the host: all 46 commits of the review repository contain it, 126 files in its last revision-7
commit. The review repository has never been pushed and has no remote.

## The repair

- The private host comes from the exporter's private configuration (the gateway URL in `ATTEST_CODEX_BASE_URL` or the private
  notes file, plus `ATTEST_EXPORT_PRIVATE_HOSTS`), never from the script, so the public copy of the script names no private host.
- The host is matched with any number of backslashes before each dot, so its plain, regex-escaped and JSON-escaped spellings are
  all redacted and all fail the final scan; a scan hit is reported by label, without printing the host.
- `REDACTION.json` records rule labels ("private development-gateway host (from the exporter's private configuration)", "the
  author's home directory", ...), never patterns. Each rewritten file is still traced by its original and redacted digests.
- Tests: `tests/test_external.py`, `RedactedExport` (the test sets the private host itself, so it does not depend on the machine it
  runs on): the redaction record cannot spell the host, and both escaped spellings planted in a file are scan hits that do not
  print the host.

## What remains for the owner

The fix applies to every export from revision 8 on: the revision-8 commit of the review repository holds no copy of the host
(verified below). The earlier commits still do. Before the repository is published, its history must not be published as it is:
either publish a fresh repository from the final tree (the pins in `FREEZE.md` stay verifiable through their package, harness and
examples digests, which do not depend on commit ids) or rewrite the history (which changes the commit ids `FREEZE.md` cites).
This is a publication decision and was not taken in this pass.

## Provenance of every exported bundle

`scripts/check_export_provenance.py` runs `attest check` on every bundle of the export, compares every exported file with its
source in the private tree (byte for byte, or through `REDACTION.json`'s original and redacted digests, with the derived manifest
marked as such), and compares each batch bundle's package digest and provider profile with its batch's registration
(`schedule.json`) and its row (`evaluation.json`).

| Export | Bundles | `attest check` | Fully verified (protocol 2 / 3 / 4) | Historical | Identical to the source, or traced by `REDACTION.json` | Batch bundles: package digest equals the registered one | Provider profile equals the registered one | Problems |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| revision 7 (`provenance-revision7-export.json`) | 175 | 175 OK | 18 (7 / 3 / 8) | 157 | 175 (125 redacted copies) | 89 of 110; the other 21: 11 bundles predate the recorded digest, 10 sit in an early batch whose schedule registered none | 11 (the 99 others predate profile registration) | none |
| revision 8 (`provenance-revision8-export.json`) | 181 | 181 OK | 24 (7 / 3 / 14) | 157 | 181 (131 redacted copies) | 95 of 116; the same 21 | 17 | none |
| 0.8.1, the final export of this pass (`provenance-0.8.1-export.json`) | 181 | 181 OK | 24 (7 / 3 / 14) | 157 | 181 (131 redacted copies) | 95 of 116; the same 21 | 17 | none |

In the revision-8 export no file contains the development gateway's host in any spelling (searched with the pattern that allows
backslashes before each dot), and the export's own scan and git-ignore checks report nothing.
