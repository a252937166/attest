# Runtime boundaries, release and deployment audit — 19 October 2026

This report records defects in the audited source and bounded local reproductions. It does not establish compromise, exposed real credentials, live service exhaustion or a real billing loss. No product source, product tests or production services were changed. The source hashes are in [boundaries-repro-results.json](boundaries-repro-results.json).

Run [boundaries-repro.py](boundaries-repro.py) from the repository root with the existing virtualenv. All six reproductions return `confirmed=true`. Files are synthetic and disposable; the regex runs in a child forcibly stopped after one second; no repository-provided program, external model or Sandbox API executes.

## Findings

### BOUND-01 — P2: model-controlled regex executes without a host deadline

**Location:** `attest/core/workspace.py:86–112`.

`Workspace.search` compiles the model's expression with Python `re` and searches every input line on the orchestrator. Its output limit does not bound search work. The bounded reproduction uses a 29-byte synthetic line and `(a+)+$`; the child exceeds one second and is killed by the auditor. A normal implementer search action can therefore occupy the sole worker indefinitely, outside the execution Sandbox. No production hang was induced.

**Fix:** default to literal search; if regex is needed, use a linear-time engine or a separate process with explicit time/bytes/line limits. Return a bounded action error and release the worker on timeout. A thread timeout does not reliably stop a Python regex holding the GIL.

**Acceptance:** the adversarial expression, long single lines and a large multi-file search all return or are cancelled within the documented limit; ordinary symbol search still succeeds. The HTTP worker remains responsive.

### BOUND-02 — P2: direct CLI repository snapshots follow outside file symlinks

**Location:** `attest/core/workspace.py:19–29`; direct snapshot use in the pipeline. `import_local` separately skips links and GitHub extraction materializes only contained regular-file links.

The reproduction creates a temporary repository containing a symlink to a temporary sentinel outside it. `snapshot_repo()` includes the outside sentinel's contents. The direct local CLI can send a file outside the user's named repository to the model/Sandbox. This is a local repository-input boundary; no public HTTP route for creating such a symlink was demonstrated.

**Fix:** explicitly reject/skip symlinks and non-regular files before opening, or deliberately materialize only contained targets with recorded provenance and bounds. Enforce containment for every read; avoid following a link swapped between checking and opening. Do not rely solely on the separate import command being safe.

**Acceptance:** outside file/directory links, broken links and link changes cannot read outside the chosen repository; safe internal-link behavior is explicit and identical between import and direct run.

### BOUND-03 — P2: archive limits are applied after decompression and whole-file reads

**Location:** `attest/core/external.py:129–148`, `171–173`.

`getmembers()` enumerates the archive before bounding member count, and `extractfile(...).read()` reads a whole member before `_check_tree` enforces file/total bytes. A small compressed repository can consume memory above the advertised import limits. The tiny reproduction sets a 16-byte limit, records `read(-1)` returning 64 bytes, then observes refusal. It does not allocate a large archive or crash a process. The final write refusal does work; it happens too late to protect import memory.

**Fix:** iterate tar members in a bounded streaming manner; check declared size, cumulative uncompressed bytes and member count before reading; cap every read to remaining allowance plus one; reject duplicate/unsafe paths and excessive link entries. Enforce the same policy for all archive input modes.

**Acceptance:** oversized declared members and excessive headers/links fail before contents are loaded. A highly compressible synthetic archive stays within a small measured memory ceiling; normal pinned python-semver import continues to work.

### BOUND-04 — P2: the guest stream limit truncates only after unbounded capture

**Location:** `attest/sandbox/tf_sandboxes.py:38–96`, especially `78–81`.

The runner uses `capture_output=True`, then clips the completed byte strings. The 1,024-byte reproduction cap still captures 8,193 bytes before displaying 1,043 characters. This establishes post-capture truncation; the reproduction uses only a tiny locally authored print command. A noisy candidate could consume the Sandbox's memory before this presentation limit applies. The VM memory limit is a separate last resort and may turn a test into an infrastructure error.

**Fix:** drain both streams concurrently into bounded buffers, with an explicit truncate-or-kill policy and total output limit. Bound cleanup, kill/reap the workload process group on timeout/output exhaustion and retain a truthful failure record. See CORE-04 for the related per-test descendant pipe issue.

**Acceptance:** an isolated bounded noisy-child test stays within the configured memory/output budget, reports truncation accurately, and leaves no descendants. Normal large supervisor results must remain readable without deadlocking pipes.

### REL-01 — P1 before public release: export copies files its privacy scanner never inspects

**Location:** `scripts/export_public.py:40–49`, `77–103`, `173–185`.

Files beneath allowlisted directories are copied even when their suffix is not in `TEXT_SUFFIXES`. `.env` is not excluded; `.env` and `.zip` are not scanned. A synthetic `deploy/.env` and a ZIP containing a fake audit-only key both survive copying while `scan()` reports no hits. **No actual secret in the current public export was demonstrated.** This is a publication control failure, not evidence of a leak. The deployment tar has its own stronger `.env`/ZIP filename exclusions, which do not protect Git publication of `dist/public`.

**Fix:** use a strict allowlist for release files and explicit exclusions for credential/environment files at every depth; scan text independently of filename extensions. Reject unreviewed archives by default or recursively inspect them with bounded decompression. Run a final fail-closed scan on the exact staged publication tree. Keep original evidence private and use traceable derived manifests when redaction changes artifacts.

**Acceptance:** audit-only fake credentials in `.env`, extensionless text, alternate text extensions and nested ZIP members all block export or are excluded. Review the full Git history and exact tree before publishing; a clean working tree alone is not a secret scan.

### REL-02 — P2: an export destination can overlap and erase its own sources

**Location:** `scripts/export_public.py:194–204`.

`--force --out .` resolves to the project root and deletes every child except `.git`. The reproduction invokes the actual export main function with a patched, disposable temporary ROOT; its synthetic source sentinel is deleted and exit status is zero. No actual project file was targeted. Absolute paths and ancestor destinations are also not constrained by the code.

**Fix:** reject destination equality/overlap with the source root, its ancestors and protected paths before any deletion. Prefer a dedicated output root, stage into a sibling temporary directory, validate, then atomically replace only a recognized previous export.

**Acceptance:** root, ancestor and nested-source overlap are refused before deletion; normal `dist/public` export retains intentional Git history and replaces only prior export contents.

### OPS-01 — P1 recovery/runbook error: the documented rollback command removes service

**Location:** `deploy/yungou/rollback.sh:2–7`; contradictory instructions in `reports/attest-deployment-2026-10-19/README.md:57–62`.

The report says this script swaps `app`/`app.prev` and restarts the previous version. The actual script disables/stops Attest and removes its nginx vhost. The previous tree exists according to the deployment record, but this command does not restore it. The script was **not executed** during this audit.

**Fix:** provide a separate version-rollback command that verifies the selected old code/dependencies, atomically selects it, restarts only Attest, and checks health/version. Keep service removal in a clearly named decommission script. Correct every runbook reference to the actual behavior. Account for DB schema compatibility before restoring a store.

**Acceptance:** rehearse the rollback in an isolated equivalent environment; prove the expected old revision becomes healthy, the store is preserved, and unrelated service configurations/states remain unchanged. Do not rehearse by disabling the shared live vhost.

### OPS-02 — P2: installation switches the application before validating the release

**Location:** `deploy/yungou/install.sh:18–24`, `29–43`.

The installer replaces the active directory before dependency installation, service validation or nginx validation. It updates one shared venv, has no failure rollback, and `curl -s` neither fails on HTTP error nor asserts health JSON/version. The final `nginx -t && reload` is followed by a successful echo, so a failed nginx test can still finish with `install complete`. Source inspection confirms these paths; no server installer was run.

**Fix:** prepare a versioned app and dependencies, validate imports/configuration and the release manifest before switching; use strict health assertions with expected digest/version; roll back only Attest on failure. Validate nginx before replacing its configuration, and propagate validation/reload failures to a nonzero exit. Keep shared nginx changes scoped and reversible.

**Acceptance:** injected dependency, health, config-test and reload failures never report success, restore the previous working Attest release, and leave all unrelated services/configuration intact. Retain the pinned dependency inventory for each release rather than updating the old release's environment in place.

### OPS-03 — P2 reproducibility gap: deployment archive omits two promised documents

**Location:** `deploy/yungou/build_bundle.sh:14–18`; promise in `reports/attest-deployment-2026-10-19/README.md:5–6`.

An actual bounded build from the current public tree creates an archive with 3,494 members but no root `FREEZE.md` or `TESTING.md`. See [release-bundle-check.json](release-bundle-check.json). The script's explicit list omits them. This demonstrates the current builder's omission; no SSH inspection of the live filesystem was performed in this audit.

**Fix:** share an authoritative release-file list, include both files, and fail archive creation if required documents/pin are absent. Generate and validate a release manifest; record the uploaded artifact's hash and read back installed critical files after deployment.

**Acceptance:** inspect the newly built archive, extract it into a clean temporary directory and follow its frozen/testing instructions without needing files outside it. Server readback must match the intended release.

### DOC-01 — P2: public copy and frozen execution limits disagree with the revised claims

**Location:** `attest/app/static/index.html:217`, `333`; `FREEZE.md:102`, `110–111`; `submission/DEVPOST.md:73–75`.

The live page's table correctly relabels NO CHANGE as unfinished, but its following paragraph still calls the two external-task outcomes “correct refusals”. It also says “no model opinion enters” the verdict while its model-generated contract audit, drift score and eligible arbitration influence gate records. A deterministic final reduction is a narrower and supportable claim. The proposed paid work says 22 calls/run, but its literal frozen evaluation command still uses 20. The draft repository link names the older M5 pin while describing revision 4, without a separate current-release URL/commit.

**Fix:** render evaluation statements from one corrected data source; label historical and current revisions distinctly. Say that deterministic code derives the verdict from recorded gates, several of which depend on model-generated evidence. Choose one approved call cap and use it in the schedule, command, proposal and enforcement. Keep the M5 pin as historical provenance and add the current code/pin/records commits explicitly.

**Acceptance:** page, README, Devpost draft, FREEZE and registered evaluation agree on labels, limits and revision scope; the exact approved command registers the intended provider/caps without execution. Do not erase historical measurements or present a development-gateway result as a Nemotron result.

## Readiness items, not newly reproduced code defects

- The live public browser opened the home page and a historical VERIFIED case file successfully; no browser warnings/errors were captured for that case. Browsing remained free and no run was enqueued. This is a desktop smoke check, not a new full light/dark/mobile/accessibility regression.
- The live read-only snapshot returned HTTP 200, version 0.4.0, an alive worker, no queued/current run, 39 Nebius rows and zero active reservations. Assets matched local files. Disk had 1,327 MB free (9.61%); this is limited headroom, not a demonstrated low-disk outage. Failed-run artifact retention is covered in the API report.
- The strict existing video decode exits 183 with invalid H.264 NAL units; see [video-decode-results.json](video-decode-results.json). Rebuild from valid source captures, use the final UI, then require a clean full audio/video decode and a visual review. No video was modified.
- The voice provenance note explicitly leaves publication terms unconfirmed. Resolve provenance or replace the voice before publication; this audit makes no legal conclusion about the provider's terms.
- `dist/public` is a clean local Git repository at records commit `85a5212` with no remote configured. This does not establish whether an owner has published a separate remote elsewhere. The Devpost file explicitly remains a draft and its video link is a local, unuploaded file.
- Revision 4 still has no formal Nemotron comparison. The latest development batch and offline checks establish workflow progress, not an advantage in correctness or cost. Preserve M5 and disclose its measured limits. Finish the repairs and a new freeze before requesting a bounded paid evaluation.
- `PILOT_FEEDBACK.md` remains a blank form; no real external developer result was verified. Seek one consented external trial if making user-impact claims, without treating an internal rehearsal as adoption.
- The account's official balance/expiry/usage and exact provider charges were not read. Local usage/reservations are not a credit statement or a bank debit. No additional paid authorization is inferred from this audit request.
