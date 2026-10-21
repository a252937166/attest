"""Offline tests for the console's task picker data (0.10.3): the labels derived from the task files without changing them, and the
run a visitor opens when browsing a task (the latest Attest verdict, not an infrastructure error or the baseline arm)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from attest.app.db import Store  # noqa: E402
from attest.app.worker import task_display  # noqa: E402


def example(task_dir: str) -> dict:
    return json.loads((ROOT / "examples" / task_dir / "task.json").read_text(encoding="utf-8"))


class TaskLabels(unittest.TestCase):
    def test_the_public_tasks_get_short_titles_and_their_references(self):
        semver = task_display(example("semver-is-compatible"))
        self.assertEqual((semver["title"], semver["repository"], semver["issue"], semver["note"]),
                         ("Add Version.is_compatible()", "python-semver", "issue #284", None))
        self.assertEqual(semver["upstream_commit"], "9b475f7")
        self.assertFalse(semver["sample"])
        variant = task_display(example("semver-is-compatible-v2"))
        self.assertEqual((variant["title"], variant["issue"], variant["note"]),
                         ("Add Version.is_compatible()", "issue #284", "contract resolved against upstream tests"))
        prerelease = task_display(example("semver-long-prerelease-pr488"))
        self.assertEqual((prerelease["title"], prerelease["repository"], prerelease["issue"]),
                         ("Compare long numeric prerelease identifiers without int conversion", "python-semver", "issue #487"))
        sample = task_display(example("durationkit-task"))
        self.assertEqual((sample["title"], sample["repository"], sample["issue"], sample["sample"]),
                         ("Accept unit suffixes in parse_duration", "durationkit", None, True))

    def test_a_title_that_names_another_repository_is_shown_whole(self):
        shown = task_display({"title": "Fix X to other-repo (upstream issue #9)", "upstream": {"url": "https://github.com/a/b"}})
        self.assertEqual((shown["title"], shown["issue"], shown["repository"]), ("Fix X to other-repo (upstream issue #9)", None, "b"))
        cited = task_display({"title": "Fix the thing (upstream issue #9)", "upstream": {"url": "https://github.com/a/b/"}})
        self.assertEqual((cited["title"], cited["issue"], cited["repository"]), ("Fix the thing", "issue #9", "b"))

    def test_the_task_files_are_read_not_written(self):
        before = {p: p.read_bytes() for p in (ROOT / "examples").glob("*/task.json")}
        for data in map(lambda p: json.loads(p.read_text(encoding="utf-8")), before):
            task_display(data)
        self.assertEqual(before, {p: p.read_bytes() for p in before})


class BrowseTarget(unittest.TestCase):
    def test_browsing_opens_the_latest_attest_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "s.db")
            rows = [("verified", "VERIFIED", "2026-10-21T01:00:00"), ("error", "ERROR", "2026-10-21T02:00:00"),
                    ("baseline", "BASELINE", "2026-10-21T03:00:00")]
            for run_id, verdict, at in rows:
                store.create_run(run_id=run_id, task_id="t", task_title="T", provider="nebius", profile_label="judge-demo", status="finished",
                                 verdict=verdict, created_at=at, started_at=at, finished_at=at, cost_usd=0.05, requester="import")
            store.create_run(run_id="only-error", task_id="u", task_title="U", provider="nebius", profile_label="judge-demo", status="finished",
                             verdict="ERROR", created_at="2026-10-21T04:00:00", requester="import")
            estimates = store.task_estimates()
            self.assertEqual(estimates["t"]["latest_run_id"], "baseline")
            self.assertEqual((estimates["t"]["latest_evidence_run_id"], estimates["t"]["latest_evidence_verdict"]), ("verified", "VERIFIED"))
            self.assertEqual(estimates["t"]["latest_evidence_at"], "2026-10-21T01:00:00")
            self.assertEqual(estimates["u"]["latest_run_id"], "only-error")
            self.assertIsNone(estimates["u"]["latest_evidence_run_id"])


if __name__ == "__main__":
    unittest.main()
