"""Publication tooling, 21 Oct 2026 (the owner's decisions for the published history): the export removes the account name that a
development session's scratch directory spells inside its own name, and the history replay can give every commit one publication
identity while keeping its dates, time zones, messages and trees. Offline; the replay tests need git."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPORT = load("attest_export_rules_identity_test", ROOT / "scripts" / "export_public.py")
NAME = "jdoe"  # a made-up account name: the real one never appears in the repository


class ScratchPathRedaction(unittest.TestCase):
    def scan_hits(self, text: str) -> list[str]:
        return [p.pattern for p in EXPORT.SCAN_PATTERNS if p.search(text)]

    def test_the_project_scratch_path_becomes_a_neutral_path(self):
        for prefix in ("/private/tmp", "/tmp"):
            path = f"{prefix}/claude-501/-Users-{NAME}-Documents-project-interesting-devpost-nebiusAi/0f1e/scratchpad/r10/attest"
            self.assertTrue(self.scan_hits(path), "the scan must flag the account name before the redaction")
            clean, count = EXPORT.redact_text(f'"package_dir": "{path}"')
            self.assertEqual(clean, '"package_dir": "/tmp/attest-session/0f1e/scratchpad/r10/attest"')
            self.assertEqual(count, 1)
            self.assertNotIn(NAME, clean)
            self.assertEqual(self.scan_hits(clean), [])

    def test_another_scratch_path_keeps_its_shape_without_the_name(self):
        clean, _ = EXPORT.redact_text(f"/tmp/claude-502/-Users-{NAME}-Projects-other/x.log")
        self.assertEqual(clean, "/tmp/claude-502/-Users-author-Projects-other/x.log")
        self.assertEqual(self.scan_hits(clean), [])

    def test_the_rules_are_named_by_label(self):
        labels = [label for label, _, _ in EXPORT.STATIC_REDACTIONS]
        self.assertIn("the author's session scratch path", labels)
        self.assertTrue(all(" " in label and "\\" not in label for label in labels))


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class ReplayIdentity(unittest.TestCase):
    OLD = "Old Name <old@example.com>"
    NEW = "Publication Name <12345+publisher@users.noreply.github.com>"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="attest-identity-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.replay = load("attest_publication_identity_test", ROOT / "scripts" / "build_publication_history.py")
        hosts = mock.patch.object(self.replay.EXPORT, "PRIVATE_HOSTS", ["gateway.example.invalid"])
        hosts.start()
        self.addCleanup(hosts.stop)
        self.review = self.tmp / "review"
        self.review.mkdir()
        self.git(self.review, "init", "-q", "-b", "main")
        for n, (stamp, zone) in enumerate((("1760900000", "+0800"), ("1760990000", "+0000")), 1):
            (self.review / f"file{n}.txt").write_text(f"commit {n}\n", encoding="utf-8")
            self.git(self.review, "add", "-A")
            env = {"GIT_AUTHOR_NAME": "Old Name", "GIT_AUTHOR_EMAIL": "old@example.com", "GIT_AUTHOR_DATE": f"{stamp} {zone}",
                   "GIT_COMMITTER_NAME": "Old Name", "GIT_COMMITTER_EMAIL": "old@example.com", "GIT_COMMITTER_DATE": f"{stamp} {zone}"}
            self.git(self.review, "commit", "-q", "-m", f"Commit {n}\n\nBody {n}.", env=env)

    def git(self, repo: Path, *args: str, env: dict | None = None) -> str:
        full = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", **(env or {})}
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=full).stdout

    def headers(self, repo: Path) -> list[dict]:
        out = []
        for sha in self.git(repo, "rev-list", "--reverse", "main").split():
            raw = self.git(repo, "cat-file", "commit", sha)
            head, _, message = raw.partition("\n\n")
            fields = dict(line.split(" ", 1) for line in head.splitlines() if line.startswith(("author ", "committer ", "tree ")))
            out.append({**fields, "message": message})
        return out

    def test_every_commit_gets_the_identity_and_keeps_its_dates_messages_and_trees(self):
        out = self.tmp / "publication"
        with mock.patch("sys.stdout"):
            result = self.replay.build(self.review, out, "main", self.NEW)
        before, after = self.headers(self.review), self.headers(out)
        self.assertEqual(len(after), 2)
        for old, new in zip(before, after):
            for role in ("author", "committer"):
                self.assertTrue(old[role].startswith(self.OLD + " "))
                self.assertEqual(new[role], self.NEW + old[role][len(self.OLD):])  # same seconds and zone
            self.assertEqual(new["message"], old["message"])
            self.assertEqual(new["tree"], old["tree"])
        self.assertEqual(result["identity"], self.NEW)
        report = self.replay.verify(self.review, out, result, [])
        self.assertEqual(report["identity"]["mismatches"], [])
        self.assertTrue(report["ok"], report)
        again = self.tmp / "publication-again"
        self.replay.build(self.review, again, "main", self.NEW)
        self.assertEqual(self.git(again, "rev-parse", "main"), self.git(out, "rev-parse", "main"))  # deterministic

    def test_without_an_identity_every_commit_keeps_its_own(self):
        out = self.tmp / "publication"
        result = self.replay.build(self.review, out, "main")
        self.assertEqual([h["author"] for h in self.headers(out)], [h["author"] for h in self.headers(self.review)])
        self.assertEqual(self.git(out, "rev-parse", "main"), self.git(self.review, "rev-parse", "main"))  # nothing to rewrite here
        report = self.replay.verify(self.review, out, result, [])
        self.assertEqual(report["identity"]["mismatches"], [])
        self.assertTrue(report["ok"], report)

    def test_a_publication_commit_with_another_identity_fails_the_verification(self):
        out = self.tmp / "publication"
        result = self.replay.build(self.review, out, "main", self.NEW)
        self.git(out, "commit", "-q", "--amend", "--no-edit", "--reset-author",
                 env={"GIT_AUTHOR_NAME": "Someone", "GIT_AUTHOR_EMAIL": "someone@example.com",
                      "GIT_COMMITTER_NAME": "Someone", "GIT_COMMITTER_EMAIL": "someone@example.com"})
        result["map"][-1]["publication"] = self.git(out, "rev-parse", "main").strip()
        report = self.replay.verify(self.review, out, result, [])
        self.assertTrue(report["identity"]["mismatches"])
        self.assertFalse(report["ok"])

    def test_a_malformed_identity_is_refused(self):
        for bad in ("no email", "Name <not-an-email>", "Name <a@b>\nInjected: 1"):
            with self.assertRaises(SystemExit):
                self.replay.build(self.review, self.tmp / "never", "main", bad)


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class ProvenanceReferences(unittest.TestCase):
    """A run first published unredacted and later as a redacted copy: the copy's REDACTION.json and derived manifest name the original
    manifest, which the replay rewrites in the older commit. Those provenance fields are not dangling references; another file naming
    the same digest still is."""

    def test_only_non_provenance_references_dangle(self):
        import hashlib, json as _json
        replay = load("attest_publication_provenance_test", ROOT / "scripts" / "build_publication_history.py")
        hosts = mock.patch.object(replay.EXPORT, "PRIVATE_HOSTS", ["gateway.example.invalid"])
        hosts.start()
        self.addCleanup(hosts.stop)
        tmp = Path(tempfile.mkdtemp(prefix="attest-provenance-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        review = tmp / "review"
        (review / "run").mkdir(parents=True)
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@example.com",
               "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@example.com", "GIT_AUTHOR_DATE": "1760900000 +0000", "GIT_COMMITTER_DATE": "1760900000 +0000"}
        git = lambda *a: subprocess.run(["git", "-C", str(review), *a], check=True, capture_output=True, env=env)  # noqa: E731
        sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
        dump = lambda o: (_json.dumps(o, indent=2, ensure_ascii=False) + "\n").encode()  # noqa: E731
        git("init", "-q", "-b", "main")
        bundle1 = b'{"package_dir": "/private/tmp/claude-501/-Users-' + NAME.encode() + b'-Documents-project-interesting-devpost-nebiusAi/s/attest"}\n'
        manifest1 = dump({"files": [{"path": "proof_bundle.json", "sha256": sha(bundle1), "bytes": len(bundle1)}], "total_bytes": len(bundle1)})
        (review / "run" / "proof_bundle.json").write_bytes(bundle1)
        (review / "run" / "manifest.json").write_bytes(manifest1)
        git("add", "-A"); git("commit", "-q", "-m", "unredacted")
        bundle2 = b'{"package_dir": "/tmp/attest-session/s/attest"}\n'
        redaction = dump({"source_manifest_sha256": sha(manifest1), "files": [{"path": "proof_bundle.json", "original_sha256": sha(bundle1), "redacted_sha256": sha(bundle2)}]})
        manifest2 = dump({"files": [{"path": "REDACTION.json", "sha256": sha(redaction), "bytes": len(redaction)}, {"path": "proof_bundle.json", "sha256": sha(bundle2), "bytes": len(bundle2)}],
                          "total_bytes": len(redaction) + len(bundle2), "derived_from": {"original_manifest_sha256": sha(manifest1)}})
        (review / "run" / "proof_bundle.json").write_bytes(bundle2)
        (review / "run" / "REDACTION.json").write_bytes(redaction)
        (review / "run" / "manifest.json").write_bytes(manifest2)
        (review / "notes.txt").write_bytes(b"the first manifest was " + sha(manifest1).encode() + b"\n")
        git("add", "-A"); git("commit", "-q", "-m", "redacted copy")
        result = replay.build(review, tmp / "publication", "main", "Publisher <publisher@example.com>")
        self.assertEqual([r["paths"] for r in result["dangling_digest_references"]], [["notes.txt"]])
        self.assertEqual(sorted(r["paths"][0] for r in result["provenance_references_to_private_originals"]), ["run/REDACTION.json", "run/manifest.json"])
        self.assertEqual(replay.provenance_digests(b"not json"), None)


if __name__ == "__main__":
    unittest.main()
