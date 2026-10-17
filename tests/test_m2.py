"""Milestone M2: bundle provenance, artifact manifest, offline `attest check`, exhibits E1 to E7 and the verdict rule.

Offline only: the fake provider and executor from tests/test_verification.py produce complete run directories; the real
supervisor runs locally (not as root) to show the new per-test failure text. Tampered copies of a run directory and of a
downloaded-style zip must fail the check with the right named finding.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from attest import __version__
from attest.cli import main as cli_main
from attest.core.check import CheckError, check_bundle
from attest.core.exhibits import counterexamples, decision, exhibits, parse_assertion, proves, reason_class
from attest.core.manifest import MANIFEST_FILE, build_manifest, purpose_of, verify_manifest
from attest.core.pipeline import Pipeline
from attest.core.proof import render_markdown
from attest.core.provenance import attest_revision, build_provenance, guest_digests, sampling_from
from attest.core.sealed import SUPERVISOR_SRC, SUPERVISOR_VERSION, bind_verification, guest_files_for, new_nonce, sealed_steps, static_test_ids, summarize
from attest.core.task import TaskSpec
from attest.core.verdict import derive, expected_verdict
from attest.ledger import Ledger
from tests.test_verification import HELDOUT_SRC, TASK, FakeExecutor, FakeProvider

ROOT = Path(__file__).resolve().parent.parent


def offline_run(scenario: str, out_dir: Path, heldout=None, **kwargs) -> tuple[dict, Path]:
    """Run the offline pipeline into a kept directory and return (bundle, run_dir)."""
    ledger = Ledger()
    task = TaskSpec.load(TASK)
    if heldout is not None:
        task.heldout_tests = heldout
    pipeline = Pipeline(task=task, provider=FakeProvider(ledger, scenario), executor=FakeExecutor(ledger, scenario), ledger=ledger,
                        out_dir=out_dir, max_turns=4, max_mutants=6, mutant_workers=2, tavily=None, profile_label="m2-offline",
                        run_id=f"m2-{scenario}", **kwargs)
    with contextlib.redirect_stdout(io.StringIO()):
        bundle = pipeline.run()
    return bundle, pipeline.out_dir


def zip_like_console(run_dir: Path, target: Path) -> Path:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(run_dir.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=f"{run_dir.name}/{path.relative_to(run_dir).as_posix()}")
    return target


def findings(report: dict, ok=False) -> dict:
    return {c["name"]: c["detail"] for c in report["checks"] if c["ok"] is ok and (ok or c["severity"] == "error")}


class Provenance(unittest.TestCase):
    def test_revision_is_a_stable_digest_over_the_package(self):
        first, second = attest_revision(), attest_revision()
        self.assertEqual(first["digest"], second["digest"])
        self.assertEqual(len(first["digest"]), 64)
        self.assertGreater(first["files"], 10)
        self.assertEqual(first["version"], __version__)
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "attest", Path(tmp) / "attest")
            (Path(tmp) / "attest" / "core" / "sealed.py").write_text("# changed\n", encoding="utf-8")
            self.assertNotEqual(attest_revision(Path(tmp) / "attest")["digest"], first["digest"])

    def test_guest_digests_name_the_supervisor_version(self):
        guest = guest_digests()
        self.assertEqual(guest["supervisor"]["version"], SUPERVISOR_VERSION)
        self.assertEqual(len(guest["supervisor"]["sha256"]), 64)
        self.assertEqual(len(guest["child_sha256"]), 64)
        self.assertEqual(len(guest["canary_sha256"]), 64)
        self.assertEqual(len(guest["guest_runner_sha256"]), 64)
        self.assertIn(SUPERVISOR_VERSION, SUPERVISOR_SRC)

    def test_sampling_is_recorded_for_both_providers(self):
        codex = sampling_from({"provider": "codex_gateway", "roles": {"spec": ["gpt-6-astra", "low"], "implement": ["gpt-6-sol", "medium"]}})
        self.assertIsNone(codex["temperature"])
        self.assertEqual(codex["roles"]["spec"], {"model": "gpt-6-astra", "effort": "low"})
        nebius = sampling_from({"provider": "nebius_tokenfactory", "temperature": 0.2, "max_tokens": 16000, "roles": {"spec": "nvidia/x"}})
        self.assertEqual(nebius["temperature"], 0.2)
        self.assertEqual(nebius["roles"]["spec"], {"model": "nvidia/x", "effort": None})

    def test_upstream_is_loaded_and_frozen_only_when_present(self):
        semver = TaskSpec.load(ROOT / "examples" / "semver-is-compatible-v2" / "task.json")
        self.assertEqual(semver.upstream["url"], "https://github.com/python-semver/python-semver")
        self.assertEqual(len(semver.upstream["commit"]), 40)
        frozen = semver.frozen({"src/semver/__init__.py": b"x"})
        self.assertEqual(frozen["upstream"]["commit"], semver.upstream["commit"])
        plain = TaskSpec.load(TASK)
        self.assertIsNone(plain.upstream)
        self.assertNotIn("upstream", plain.frozen({"durationkit/__init__.py": b"x"}))
        prov = build_provenance({"provider": "codex_gateway", "roles": {}}, {"max_turns": 3}, semver.upstream)
        self.assertEqual(prov["upstream"]["url"], semver.upstream["url"])
        self.assertEqual(prov["limits"], {"max_turns": 3})


class VerdictRule(unittest.TestCase):
    def test_every_gate_must_pass_and_skipped_never_counts(self):
        gates = {"existing_suite": {"ok": True}, "sealed_binding": {"ok": True}, "mutation": {"ok": True}, "adversarial_tests": {"ok": True}, "drift_audit": {"ok": True}}
        self.assertEqual(derive(gates, {"scope_ok": True, "implementer_finished": True}, True)["verdict"], "VERIFIED")
        gates["mutation"] = {"ok": False, "skipped": True}
        out = derive(gates, {"scope_ok": True, "implementer_finished": True}, True)
        self.assertEqual(out["verdict"], "NEEDS HUMAN")
        self.assertEqual(out["blocking"], ["mutation (not run)"])
        gates["mutation"] = {"ok": True}
        self.assertEqual(derive(gates, {"scope_ok": False}, True)["blocking"], ["scope policy violated"])
        self.assertEqual(derive(gates, {"implementer_finished": False}, True)["blocking"], ["implementer did not finish"])

    def test_arbitration_changes_the_verdict_only_in_apply_mode(self):
        gates = {"sealed_binding": {"ok": True}, "adversarial_tests": {"ok": False}}
        arb = {"cleared": True}
        self.assertEqual(derive(gates, {}, True, arb)["verdict"], "NEEDS HUMAN")
        out = derive(gates, {}, True, arb, apply=True)
        self.assertEqual((out["verdict"], out["cleared_by_arbitration"]), ("VERIFIED", True))
        self.assertEqual(derive(gates, {}, True, {"cleared": False}, apply=True)["verdict"], "NEEDS HUMAN")

    def test_expected_verdict_on_recorded_bundles(self):
        self.assertTrue(expected_verdict({"verdict": {"verdict": "NEEDS HUMAN"}, "gates": {}})["consistent"])
        self.assertFalse(expected_verdict({"verdict": {"verdict": "VERIFIED"}, "gates": {}})["consistent"])
        forged = {"verdict": {"verdict": "VERIFIED"}, "gates": {"sealed_binding": {"ok": False}}, "candidate": {}, "verification": {"binding": {"ok": False}}}
        out = expected_verdict(forged)
        self.assertTrue(out["applicable"])
        self.assertFalse(out["consistent"])
        self.assertIn("sealed_binding", out["blocking"])


class Exhibits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="attest-m2-exhibits-"))
        cls.bundles = {}
        for scenario, heldout in (("honest", None), ("heldout_fail", {"tests/test_heldout.py": HELDOUT_SRC}), ("forge_all_ok", None), ("sealed_defect", None)):
            cls.bundles[scenario], _ = offline_run(scenario, cls.tmp, heldout=heldout)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_exhibits_have_fixed_refs_and_honest_statuses(self):
        items = exhibits(self.bundles["honest"])
        self.assertEqual([e["ref"] for e in items], ["E1", "E2", "E3", "E4", "E5", "E6", "E7"])
        by = {e["ref"]: e for e in items}
        self.assertEqual([by[r]["status"] for r in ("E1", "E2", "E3", "E5")], ["pass"] * 4)
        self.assertEqual(by["E4"]["status"], "none")  # durationkit has no held-out suite: never shown as a pass
        self.assertFalse(by["E6"]["shown"])
        self.assertFalse(by["E7"]["shown"])
        held = {e["ref"]: e for e in exhibits(self.bundles["heldout_fail"])}
        self.assertEqual(held["E4"]["status"], "fail")
        self.assertIn("tests/test_heldout.py", held["E4"]["summary"])

    def test_decision_copy_is_authored_per_reason_class(self):
        verified = decision(self.bundles["honest"])
        self.assertEqual((verified["statement"], verified["reason_class"]), ("Accept this patch.", "verified"))
        self.assertEqual(verified["evidence"]["ref"], "E1")
        self.assertTrue(any("held-out" in w for w in verified["weak"]))
        held = decision(self.bundles["heldout_fail"])
        self.assertEqual((held["statement"], held["reason_class"]), ("Hold this patch.", "heldout_failed"))
        self.assertEqual(held["evidence"]["ref"], "E4")
        forged = decision(self.bundles["forge_all_ok"])
        self.assertEqual(forged["reason_class"], "integrity")
        self.assertIn("canary_must_fail_failed", forged["evidence"]["text"])
        defect = decision(self.bundles["sealed_defect"])
        self.assertEqual(defect["reason_class"], "sealed_failed")
        self.assertEqual(reason_class({"verdict": {"verdict": "ERROR"}}), "error")

    def test_proves_cites_exhibits_and_never_overclaims(self):
        what = proves(self.bundles["honest"])
        self.assertTrue(any("(E1)" in line and "sealed acceptance tests" in line for line in what["proves"]))
        self.assertTrue(any("(E2)" in line for line in what["proves"]))
        self.assertTrue(any("requester's intent" in line for line in what["does_not_prove"]))
        self.assertTrue(any("no held-out suite" in line for line in what["does_not_prove"]))
        held = proves(self.bundles["heldout_fail"])
        self.assertTrue(any("held-out tests fail" in line for line in held["proves"]))
        self.assertTrue(any("That the patch is wrong" in line for line in held["does_not_prove"]))

    def test_counterexamples_parse_assertions_and_keep_argument_order_honest(self):
        parsed = parse_assertion("Traceback (most recent call last):\n  File \"t.py\", line 3, in test_x\n    self.assertEqual(encode('a1'), 'a1')\nAssertionError: 'a111' != 'a1'\n- a111\n+ a1\n")
        self.assertEqual((parsed["kind"], parsed["first"], parsed["second"], parsed["parsed"]), ("AssertionError", "'a111'", "'a1'", True))
        self.assertEqual(parse_assertion("")["parsed"], False)
        typed = parse_assertion("...\nTypeError: n must be an integer\n")
        self.assertEqual((typed["kind"], typed["first"]), ("TypeError", None))
        items = counterexamples(self.bundles["heldout_fail"])
        self.assertTrue(items)
        self.assertEqual(items[0]["exhibit"], "E4")
        self.assertIsNone(items[0]["classification"])

    def test_legacy_fail_open_adversarial_record_is_not_a_pass(self):
        legacy = json.loads(json.dumps(self.bundles["honest"]))
        legacy["breaker"]["adversarial"] = {"skipped": "only 0 adversarial tests were written"}
        legacy["gates"]["adversarial_tests"] = {"ok": True, "detail": "only 0 adversarial tests were written"}
        e3 = {e["ref"]: e for e in exhibits(legacy)}["E3"]
        self.assertEqual(e3["status"], "not_run")
        self.assertIn("no longer allows", e3["summary"])
        self.assertIn("E3", render_markdown(legacy))


class ManifestAndCheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="attest-m2-check-"))
        cls.bundle, cls.run_dir = offline_run("honest", cls.tmp)
        cls.hold_bundle, cls.hold_dir = offline_run("heldout_fail", cls.tmp, heldout={"tests/test_heldout.py": HELDOUT_SRC})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _copy(self, src: Path, name: str) -> Path:
        target = self.tmp / name
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(src, target)
        return target

    def test_new_bundles_carry_provenance_manifest_and_raw_results(self):
        prov = self.bundle["provenance"]
        self.assertEqual(prov["attest_version"], __version__)
        self.assertEqual(prov["supervisor"]["version"], SUPERVISOR_VERSION)
        self.assertEqual(prov["limits"]["max_turns"], 4)
        self.assertEqual(prov["limits"]["min_adversarial_when_no_mutants"], 6)
        self.assertIsNone(prov["upstream"])
        manifest = json.loads((self.run_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
        listed = {f["path"] for f in manifest["files"]}
        for name in ("proof_bundle.json", "PROOF.md", "verify_raw.json", "ledger.json", "sealed/test_sealed.py", "candidate.patch", "breaker_tests.py"):
            self.assertIn(name, listed)
        self.assertNotIn(MANIFEST_FILE, listed)
        self.assertEqual(manifest["run_id"], self.bundle["run_id"])
        self.assertTrue(verify_manifest(self.run_dir, manifest)["ok"])
        raw = json.loads((self.run_dir / "verify_raw.json").read_text(encoding="utf-8"))
        for key in ("red", "sealed", "existing", "adversarial"):
            self.assertIn(key, raw)
        self.assertEqual(raw["sealed"]["nonce"], self.bundle["verification"]["sealed"]["nonce"])
        self.assertEqual(self.bundle["verdict"]["derivation"]["verdict"], "VERIFIED")
        self.assertEqual(purpose_of("mutants_m01-abc.py"), "Source of one mutant used in E2")
        proof = (self.run_dir / "PROOF.md").read_text(encoding="utf-8")
        for needle in ("## 0. What this bundle proves, and what it does not", "## 1. Frozen task and provenance", SUPERVISOR_VERSION, "(E1)", "## 13. Artifacts"):
            self.assertIn(needle, proof)

    def test_check_passes_on_directory_and_zip(self):
        report = check_bundle(self.run_dir)
        self.assertTrue(report["ok"], findings(report))
        self.assertTrue(report["manifest_verified"])
        self.assertEqual(report["warnings"], 0, [c for c in report["checks"] if c["ok"] is None])
        names = {c["name"] for c in report["checks"]}
        for needed in ("manifest_digests", "sealed_binding_recomputed", "adversarial_binding_recomputed", "existing_binding_recomputed",
                       "ledger_totals", "gates_match_stage_records", "verdict_derivation", "proof_md_matches"):
            self.assertIn(needed, names)
        archive = zip_like_console(self.run_dir, self.tmp / "honest.zip")
        zipped = check_bundle(archive)
        self.assertTrue(zipped["ok"], findings(zipped))
        self.assertEqual(zipped["run_id"], self.bundle["run_id"])
        hold = check_bundle(self.hold_dir)
        self.assertTrue(hold["ok"], findings(hold))
        self.assertIn("heldout_binding_recomputed", {c["name"] for c in hold["checks"]})

    def test_tampered_artifact_fails_the_manifest(self):
        copy = self._copy(self.run_dir, "tampered-proof")
        (copy / "PROOF.md").write_text((copy / "PROOF.md").read_text(encoding="utf-8") + "\nedited after the fact\n", encoding="utf-8")
        report = check_bundle(copy)
        self.assertFalse(report["ok"])
        self.assertIn("manifest_digests", findings(report))
        self.assertIn("PROOF.md", findings(report)["manifest_digests"])
        self.assertIn("proof_md_matches", findings(report))

    def test_forged_verdict_fails_the_derivation_even_with_a_regenerated_manifest(self):
        copy = self._copy(self.hold_dir, "forged-verdict")
        bundle = json.loads((copy / "proof_bundle.json").read_text(encoding="utf-8"))
        bundle["verdict"]["verdict"] = "VERIFIED"
        (copy / "proof_bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        (copy / MANIFEST_FILE).write_text(json.dumps(build_manifest(copy, bundle["run_id"])) + "\n", encoding="utf-8")  # attacker re-signs
        report = check_bundle(copy)
        self.assertFalse(report["ok"])
        bad = findings(report)
        self.assertIn("verdict_derivation", bad)
        self.assertIn("heldout_suite", bad["verdict_derivation"])
        self.assertIn("verified_has_no_reasons", bad)
        self.assertIn("proof_md_matches", bad)
        self.assertNotIn("manifest_digests", bad)

    def test_edited_sealed_tests_and_outcomes_are_caught(self):
        copy = self._copy(self.run_dir, "edited-sealed")
        sealed = copy / "sealed" / "test_sealed.py"
        sealed.write_text(sealed.read_text(encoding="utf-8").replace("3600.0", "3601.0"), encoding="utf-8")
        report = check_bundle(copy)
        bad = findings(report)
        self.assertIn("sealed_file_digest", bad)
        self.assertIn("manifest_digests", bad)
        copy2 = self._copy(self.run_dir, "edited-outcomes")
        bundle = json.loads((copy2 / "proof_bundle.json").read_text(encoding="utf-8"))
        bundle["verification"]["sealed"]["tests"][0]["outcome"] = "FAIL"
        (copy2 / "proof_bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        (copy2 / MANIFEST_FILE).write_text(json.dumps(build_manifest(copy2, bundle["run_id"])) + "\n", encoding="utf-8")
        bad2 = findings(check_bundle(copy2))
        self.assertIn("sealed_outcomes_match_raw", bad2)
        copy3 = self._copy(self.run_dir, "edited-ledger")
        bundle = json.loads((copy3 / "proof_bundle.json").read_text(encoding="utf-8"))
        bundle["ledger"]["totals"]["model_calls"] = 1
        (copy3 / "proof_bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
        (copy3 / MANIFEST_FILE).write_text(json.dumps(build_manifest(copy3, bundle["run_id"])) + "\n", encoding="utf-8")
        self.assertIn("ledger_totals", findings(check_bundle(copy3)))

    def test_old_bundle_without_manifest_is_reported_as_unchecked_not_as_tampered(self):
        old = ROOT / "reports" / "attest-m1-2026-10-16" / "runs" / "balanced-brackets-20261016T192809Z"
        report = check_bundle(old)
        self.assertTrue(report["ok"], findings(report))
        self.assertFalse(report["manifest_verified"])
        self.assertFalse(report["manifest_present"])
        self.assertIn("manifest_present", {c["name"] for c in report["checks"] if c["ok"] is None})

    def test_cli_exit_codes_and_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli_main(["check", str(self.run_dir), "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out.getvalue())["ok"])
        copy = self._copy(self.run_dir, "cli-tampered")
        (copy / "candidate.patch").write_text("tampered\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli_main(["check", str(copy)]), 1)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli_main(["check", str(self.tmp / "does-not-exist")]), 1)
        with self.assertRaises(CheckError):
            check_bundle(self.tmp)

    def test_zip_with_unsafe_paths_is_refused(self):
        bad = self.tmp / "unsafe.zip"
        with zipfile.ZipFile(bad, "w") as archive:
            archive.writestr("../escape/proof_bundle.json", "{}")
        with self.assertRaises(CheckError):
            check_bundle(bad)


class TransportRobustness(unittest.TestCase):
    """A chunked response cut short while reading is a transport failure: GET polls retry it, a POST stays uncertain."""

    def test_incomplete_read_is_a_transport_error(self):
        import http.client
        from unittest import mock

        import attest.http as http_module

        class Response:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, n):
                raise http.client.IncompleteRead(b"x" * 10)

        class Opener:
            def open(self, req, timeout=None):
                return Response()

        with mock.patch.object(http_module, "opener", lambda: Opener()):
            with self.assertRaises(http_module.TransportError) as caught:
                http_module.request_json("GET", "https://example.invalid/op", {}, timeout=5)
        self.assertIn("IncompleteRead", str(caught.exception))


class RealSupervisorFailureText(unittest.TestCase):
    """The v5 child keeps the assertion traceback so the console and PROOF.md can show the counterexample."""

    def test_failing_test_reports_the_assertion_in_failure_tail(self):
        tmp = Path(tempfile.mkdtemp(prefix="attest-m2-sup-"))
        try:
            repo = tmp / "w"
            (repo / "pkg").mkdir(parents=True)
            (repo / "pkg" / "__init__.py").write_text("def encode(s):\n    return s + '111'\n", encoding="utf-8")
            sealed = ("import unittest\nfrom pkg import encode\n\nclass T(unittest.TestCase):\n"
                      "    def test_roundtrip(self):\n        self.assertEqual(encode('a1'), 'a1')\n"
                      "    def test_type(self):\n        encode(None)\n")
            sealed_dir = tmp / "sealed"
            files = guest_files_for(str(sealed_dir), "test_sealed", sealed, repo_dir=str(repo), extra_paths=[], canary=True)
            for path, data in files.items():
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_bytes(data)
            nonce = new_nonce()
            steps = sealed_steps(sys.executable, str(repo), str(sealed_dir), nonce, [], {"PYTHONPATH": str(repo)}, timeout=120, per_test_timeout=30)
            outputs = {}
            for step in steps:
                proc = subprocess.run(step["cmd"], cwd=step["cwd"], env={**os.environ, "PYTHONPATH": str(repo)}, capture_output=True, timeout=120)
                outputs[step["name"]] = proc.stdout.decode()
            result = json.loads(outputs["sealed_result"])
            self.assertEqual(result["supervisor"], SUPERVISOR_VERSION)
            by = {t["id"].split(".")[-1]: t for t in result["tests"]}
            self.assertEqual(by["test_roundtrip"]["outcome"], "FAIL")
            self.assertIn("AssertionError: 'a1111' != 'a1'", by["test_roundtrip"]["failure_tail"])
            self.assertEqual(by["test_type"]["outcome"], "ERROR")
            self.assertIn("TypeError", by["test_type"]["failure_tail"])
            summary = summarize(result)
            self.assertIn("AssertionError", next(t for t in summary["tests"] if t["id"].endswith("test_roundtrip"))["failure_tail"])
            binding = bind_verification(result, static_test_ids(sealed), __import__("attest.core.sealed", fromlist=["sha256_text"]).sha256_text(sealed), nonce)
            self.assertFalse(binding["ok"])
            fake = {"verdict": {"verdict": "NEEDS HUMAN", "reasons": ["x"]}, "gates": {"sealed_binding": {"ok": False}},
                    "verification": {"binding": binding, "sealed": summary}}
            example = next(c for c in counterexamples(fake) if c["name"] == "test_roundtrip")
            self.assertEqual((example["assertion"]["first"], example["assertion"]["second"]), ("'a1111'", "'a1'"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
