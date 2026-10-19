"""Acceptance tests for the OPS-01/02/03 repairs of the 19 Oct 2026 audit: deploy/yungou/install.sh (staged, verified,
transactional release switch with automatic restore), rollback.sh (scoped version rollback with digest readback),
decommission.sh (explicit --yes) and build_bundle.sh (authoritative required-file list, RELEASE.json manifest).

The scripts run unchanged against a throwaway fake host under the rehearsal shims of deploy/yungou/rehearsal/shims (systemctl,
nginx-modern, useradd, chown, install and the interpreter) with a fake health server started by the shimmed `systemctl restart`;
a small release tree (the real attest/ package with a synthetic version, the deploy directory under test, one-line documents)
is bundled by build_bundle.sh. The same shims drive deploy/yungou/rehearsal/rehearse.sh on a Linux host with the full public tree.
Offline, no network, nothing outside the temporary directories is touched. Skipped when bash or tar is missing; bash 3.2 (macOS)
is enough: the scripts use no associative arrays, mapfile, readarray, ${var,,} or timeout."""

import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import unittest
import urllib.request
from pathlib import Path

from attest.core.provenance import attest_revision

ROOT = Path(__file__).resolve().parent.parent
DEPLOY = ROOT / "deploy" / "yungou"
SHIMS = DEPLOY / "rehearsal" / "shims"
BASH = shutil.which("bash")
TAR = shutil.which("tar")
DOCS = ("README.md", "LICENSE", "FREEZE.md", "TESTING.md", "PILOT.md", "PILOT_FEEDBACK.md", "METHOD.md", "attest-console.md")
VERSIONS = {"a": "9.0.1-test", "b": "9.0.2-test", "c": "9.0.3-test"}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def make_tree(dest: Path, version: str) -> None:
    """A small release tree: the real attest/ package with a synthetic version, the deploy directory under test, one-line documents."""
    shutil.copytree(ROOT / "attest", dest / "attest", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dest / "attest" / "__init__.py").write_text(f'"""test tree"""\n\n__version__ = "{version}"\n', encoding="utf-8")
    shutil.copytree(DEPLOY, dest / "deploy" / "yungou", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in DOCS:
        (dest / name).write_text(f"{name} of the test tree, version {version}\n", encoding="utf-8")
    (dest / "pyproject.toml").write_text(f'[project]\nname = "attest"\nversion = "{version}"\n', encoding="utf-8")
    for sub in ("examples", "tests", "reports"):
        (dest / sub).mkdir()
        (dest / sub / "README.md").write_text(f"{sub} placeholder of the test tree\n", encoding="utf-8")


def build_bundle(tree: Path, out: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHON": sys.executable}
    return subprocess.run([BASH, str(tree / "deploy" / "yungou" / "build_bundle.sh"), str(out)], capture_output=True, text=True, env=env, timeout=300)


class Host:
    """A throwaway fake host (opt/attest, etc/systemd/system, etc/nginx/conf.d, etc/attest, var/lib/attest under one root), the
    staged deploy directory next to the scripts, and the environment pointing the scripts and the shims at it."""

    def __init__(self, base: Path, port: int):
        self.base = base
        self.root = base / "host"
        self.deploy = base / "deploy"
        self.rehearsal = base / "rehearsal"
        for sub in ("opt/attest", "etc/systemd/system", "etc/nginx/conf.d", "etc/attest", "var/lib/attest", "var/www/letsencrypt"):
            (self.root / sub).mkdir(parents=True)
        for sub in ("logs", "state", "tmp"):
            (self.rehearsal / sub).mkdir(parents=True)
        self.deploy.mkdir()
        for name in ("install.sh", "rollback.sh", "decommission.sh", "attest.service", "attest.axiqo.xyz.conf"):
            shutil.copy(DEPLOY / name, self.deploy / name)
        # synthetic secrets file: short placeholder values assembled at runtime (the public export scans for key-like assignments)
        (self.deploy / "attest.env").write_text("".join(name + "=" + "placeholder\n" for name in ("NEBIUS_API_KEY", "ATTEST_ADMIN_TOKEN")), encoding="utf-8")
        self.port = port
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("REHEARSAL_")}
        self.env.update({
            "ATTEST_ROOT": str(self.attest), "SYSTEMD_UNIT_DIR": str(self.root / "etc/systemd/system"),
            "NGINX_CONF_DIR": str(self.root / "etc/nginx/conf.d"), "ATTEST_ENV_DIR": str(self.root / "etc/attest"),
            "ATTEST_DATA_DIR": str(self.root / "var/lib/attest"), "LETSENCRYPT_LIVE": str(self.root / "etc/letsencrypt/live/attest.axiqo.xyz"),
            "LETSENCRYPT_WEBROOT": str(self.root / "var/www/letsencrypt"),
            "PYTHON_BIN": str(SHIMS / "python3.12"), "SYSTEMCTL": str(SHIMS / "systemctl"), "NGINX_BIN": str(SHIMS / "nginx-modern"),
            "USERADD": str(SHIMS / "useradd"), "CHOWN": str(SHIMS / "chown"), "INSTALL": str(SHIMS / "install"),
            "HEALTH_URL": f"http://127.0.0.1:{port}/api/health", "HEALTH_DEADLINE_SECONDS": "20", "HEALTH_POLL_SECONDS": "0.2",
            "MEMORY_MAX": "200M", "TMPDIR": str(self.rehearsal / "tmp"), "PYTHON": sys.executable,
            "REHEARSAL_DIR": str(self.rehearsal), "REHEARSAL_SHIMS": str(SHIMS), "REHEARSAL_REAL_PYTHON": sys.executable,
            "REHEARSAL_HEALTH_PORT": str(port), "REHEARSAL_APP_LINK": str(self.attest / "app"),
        })

    @property
    def attest(self) -> Path:
        return self.root / "opt" / "attest"

    @property
    def unit(self) -> Path:
        return self.root / "etc" / "systemd" / "system" / "attest.service"

    @property
    def vhost(self) -> Path:
        return self.root / "etc" / "nginx" / "conf.d" / "attest.axiqo.xyz.conf"

    def run(self, script: str, *args: str, **overrides: str) -> subprocess.CompletedProcess:
        env = {**self.env, **overrides}
        return subprocess.run([BASH, script, *args], cwd=self.deploy, env=env, capture_output=True, text=True, timeout=300)

    def _label(self, name: str):
        link = self.attest / name
        if link.is_symlink():
            return Path(os.readlink(link)).name
        return "REAL-DIRECTORY" if link.is_dir() else None

    def active(self):
        return self._label("app")

    def previous(self):
        return self._label("app.prev")

    def health(self):
        try:
            with urllib.request.urlopen(self.env["HEALTH_URL"], timeout=3) as response:
                return json.load(response)
        except Exception:  # noqa: BLE001 - unreachable means "no service"
            return None

    def service_active(self) -> bool:
        return subprocess.run([str(SHIMS / "systemctl"), "is-active", "attest.service"], env=self.env, capture_output=True).returncode == 0

    def stop(self) -> None:
        subprocess.run([str(SHIMS / "systemctl"), "stop", "attest.service"], env=self.env, capture_output=True)

    def shim_calls(self) -> str:
        path = self.rehearsal / "logs" / "shim-calls.log"
        return path.read_text(encoding="utf-8") if path.exists() else ""


@unittest.skipUnless(BASH and TAR and os.name == "posix", "bash and tar are required to run the deployment scripts")
class AuditOpsTests(unittest.TestCase):
    """Scenarios of the isolated rehearsal (reports/attest-audit-repairs-2026-10-19/ops/): numbers refer to that record."""

    @classmethod
    def setUpClass(cls):
        cls.base = Path(tempfile.mkdtemp(prefix="attest-ops-"))
        cls.trees, cls.bundles, cls.manifests = {}, {}, {}
        for key, version in VERSIONS.items():
            tree = cls.base / f"tree-{key}"
            make_tree(tree, version)
            out = cls.base / f"{key}.tar.gz"
            proc = build_bundle(tree, out)
            if proc.returncode != 0:
                raise RuntimeError(f"build_bundle.sh failed for {key}:\n{proc.stdout}\n{proc.stderr}")
            with tarfile.open(out) as archive:
                manifest = json.load(archive.extractfile("RELEASE.json"))
            cls.trees[key], cls.bundles[key], cls.manifests[key] = tree, out, manifest

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)

    def setUp(self):
        self.host = Host(Path(tempfile.mkdtemp(prefix="attest-ops-host-")), free_port())
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.host.stop()
        shutil.rmtree(self.host.base, ignore_errors=True)

    def label(self, key: str) -> str:
        return self.manifests[key]["label"]

    def install(self, key: str, expect_ok: bool = True, **overrides) -> subprocess.CompletedProcess:
        proc = self.host.run("install.sh", str(self.bundles[key]), **overrides)
        output = proc.stdout + proc.stderr
        if expect_ok:
            self.assertEqual(proc.returncode, 0, output)
            self.assertIn("install complete:", proc.stdout, output)
        else:
            self.assertNotEqual(proc.returncode, 0, output)
            self.assertIn("INSTALL FAILED", output)
            self.assertNotIn("install complete", output)
        return proc

    def assert_serving(self, version: str) -> None:
        health = self.host.health()
        self.assertIsNotNone(health, "the fake service does not answer")
        self.assertEqual(health["version"], version)
        self.assertTrue(health["worker_alive"])

    # ---- OPS-03: build_bundle.sh ----------------------------------------------------------------------------------------------
    def test_release_manifest_records_version_digest_and_every_member(self):
        for key, manifest in self.manifests.items():
            tree = self.trees[key]
            self.assertEqual(manifest["version"], VERSIONS[key])
            self.assertEqual(manifest["package_digest"]["digest"], attest_revision(tree / "attest")["digest"],
                             "the independent digest must equal attest.core.provenance.attest_revision()")
            self.assertEqual(manifest["label"], f"{VERSIONS[key]}-{manifest['package_digest']['digest'][:12]}")
            self.assertEqual(manifest["dependencies"][:3], ["fastapi==0.115.5", "uvicorn[standard]==0.32.1", "jsonschema==4.23.0"])
            self.assertIn("*.env", manifest["exclusions"])
            paths = {entry["path"] for entry in manifest["files"]}
            for name in DOCS + ("pyproject.toml", "attest/__init__.py", "deploy/yungou/install.sh", "deploy/yungou/requirements.txt"):
                self.assertIn(name, paths)
            with tarfile.open(self.bundles[key]) as archive:
                members = {m.name[2:] if m.name.startswith("./") else m.name for m in archive.getmembers() if m.isfile()}
            members.discard("RELEASE.json")
            self.assertEqual(members, paths, "archive members and RELEASE.json entries must agree")
            for entry in manifest["files"][:40]:
                data = (tree / entry["path"]).read_bytes()
                self.assertEqual(entry["size"], len(data))
                import hashlib
                self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())

    def test_build_fails_when_a_required_document_is_missing(self):
        tree = self.base / "tree-missing"
        make_tree(tree, "9.0.9-test")
        (tree / "TESTING.md").unlink()
        out = self.base / "missing.tar.gz"
        proc = build_bundle(tree, out)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("required path(s) missing", proc.stderr)
        self.assertIn("TESTING.md", proc.stderr)
        self.assertFalse(out.exists())

    def test_build_excludes_env_files_and_lists_nothing_it_did_not_archive(self):
        tree = self.base / "tree-env"
        make_tree(tree, "9.0.8-test")
        (tree / "deploy" / "secret.env").write_text("NEBIUS_API_KEY" + "=" + "never-ship\n", encoding="utf-8")
        out = self.base / "env.tar.gz"
        proc = build_bundle(tree, out)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        with tarfile.open(out) as archive:
            names = archive.getnames()
            manifest = json.load(archive.extractfile("RELEASE.json"))
        self.assertNotIn("deploy/secret.env", names)
        self.assertNotIn("deploy/secret.env", {e["path"] for e in manifest["files"]})

    # ---- OPS-02: install.sh ----------------------------------------------------------------------------------------------------
    def test_scenario_1_clean_install_switches_and_passes_strict_health(self):
        proc = self.install("a")
        self.assertEqual(self.host.active(), self.label("a"))
        self.assertIsNone(self.host.previous())
        self.assert_serving(VERSIONS["a"])
        release = self.host.attest / "releases" / self.label("a")
        self.assertTrue((release / "venv" / "bin" / "python").exists(), "per-release virtualenv")
        self.assertTrue((release / "RELEASE.json").is_file())
        installed = json.loads((release / "INSTALLED.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["package_digest"], self.manifests["a"]["package_digest"]["digest"])
        self.assertIn("ExecStart=/opt/attest/app/venv/bin/python", self.host.unit.read_text(encoding="utf-8"))
        self.assertIn("MemoryMax=200M", self.host.unit.read_text(encoding="utf-8"))
        vhost = self.host.vhost.read_text(encoding="utf-8")
        self.assertIn("proxy_pass http://127.0.0.1:4070;", vhost)
        self.assertNotIn("ssl_certificate", vhost, "http-only fallback while no certificate exists")
        self.assertIn("RELEASE.json entries verified in place", proc.stdout)
        self.assertIn(f"attest_revision() digest {self.manifests['a']['package_digest']['digest']}", proc.stdout)
        self.assertIn("nginx reloaded with the new vhost", proc.stdout)

    def test_scenario_2_second_install_keeps_the_previous_release(self):
        self.install("a")
        proc = self.install("b")
        self.assertEqual(self.host.active(), self.label("b"))
        self.assertEqual(self.host.previous(), self.label("a"))
        self.assertTrue((self.host.attest / "releases" / self.label("a") / "venv").exists())
        self.assert_serving(VERSIONS["b"])
        self.assertIn("vhost unchanged; nginx is not touched", proc.stdout)

    def test_scenario_3_dependency_failure_leaves_the_previous_release_serving(self):
        self.install("a")
        proc = self.install("b", expect_ok=False, REHEARSAL_PIP_FAIL="1")
        self.assertIn("dependency installation failed", proc.stderr)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assertFalse((self.host.attest / "releases" / self.label("b")).exists(), "the failed release directory is removed")
        self.assert_serving(VERSIONS["a"])
        self.assertIn("is healthy", proc.stdout)

    def test_scenario_4_health_failure_restores_the_previous_release(self):
        self.install("a")
        proc = self.install("b", expect_ok=False, REHEARSAL_HEALTH_BAD_VERSION=VERSIONS["b"])
        self.assertIn("the service serves another version", proc.stdout)
        self.assertIn("previous release re-selected", proc.stdout)
        self.assertIn("is healthy", proc.stdout)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assertIsNone(self.host.previous())
        self.assert_serving(VERSIONS["a"])

    def test_scenario_5_nginx_test_failure_restores_vhost_and_previous_release(self):
        self.install("a")
        before = self.host.vhost.read_bytes()
        staged = self.host.deploy / "attest.axiqo.xyz.conf"   # the change sits in the first server block, which the http-only rendering keeps
        staged.write_text(staged.read_text(encoding="utf-8").replace("listen 80;", "listen 80;\n    # a vhost change so that the nginx test runs", 1), encoding="utf-8")
        proc = self.install("b", expect_ok=False, REHEARSAL_NGINX_T_FAIL="1")
        self.assertIn("nginx -t failed", proc.stderr)
        self.assertIn("vhost restored", proc.stdout)
        self.assertEqual(self.host.vhost.read_bytes(), before)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assert_serving(VERSIONS["a"])
        self.assertNotIn("nginx reloaded with the new vhost", proc.stdout)

    def test_install_refuses_a_tampered_release_manifest(self):
        self.install("a")
        work = self.host.base / "tamper"
        with tarfile.open(self.bundles["b"]) as archive:
            archive.extractall(work, filter="data")
        with (work / "README.md").open("a", encoding="utf-8") as handle:
            handle.write("a line appended after RELEASE.json was written\n")
        tampered = self.host.base / "b-tampered.tar.gz"
        with tarfile.open(tampered, "w:gz") as archive:
            for child in sorted(work.iterdir()):
                archive.add(child, arcname=child.name)
        proc = self.host.run("install.sh", str(tampered))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("mismatch: README.md", proc.stdout)
        self.assertIn("the release is refused", proc.stderr)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assert_serving(VERSIONS["a"])

    def test_install_refuses_a_bundle_without_manifest(self):
        plain = self.host.base / "plain.tar.gz"
        with tarfile.open(plain, "w:gz") as archive:
            archive.add(self.trees["a"] / "attest", arcname="attest")
        proc = self.host.run("install.sh", str(plain))
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("has no RELEASE.json", proc.stderr)
        self.assertIsNone(self.host.active())

    def test_scenario_8_legacy_directory_layout_is_migrated_and_rolled_back(self):
        attest = self.host.attest
        shutil.copytree(self.trees["a"], attest / "app")
        (attest / "app" / "RELEASE.json").unlink(missing_ok=True)
        subprocess.run([str(SHIMS / "python3.12"), "-m", "venv", str(attest / "venv")], env=self.host.env, check=True)
        subprocess.run([str(attest / "venv" / "bin" / "python"), "-m", "pip", "install", "-r", str(self.trees["a"] / "deploy" / "yungou" / "requirements.txt")],
                       env=self.host.env, check=True)
        unit = (DEPLOY / "attest.service").read_text(encoding="utf-8").replace("__MEMORY_MAX__", "200M").replace("/opt/attest/app/venv/", "/opt/attest/venv/")
        self.host.unit.write_text(unit, encoding="utf-8")
        shutil.copy(self.host.deploy / "attest.env", self.host.root / "etc" / "attest" / "attest.env")
        subprocess.run([str(SHIMS / "systemctl"), "restart", "attest.service"], env=self.host.env, check=True)
        digest_a = self.manifests["a"]["package_digest"]["digest"]
        legacy = f"legacy-{VERSIONS['a']}-{digest_a[:12]}"
        proc = self.install("b")
        self.assertIn("old layout migrated", proc.stdout)
        self.assertEqual(self.host.active(), self.label("b"))
        self.assertEqual(self.host.previous(), legacy)
        legacy_venv = attest / "releases" / legacy / "venv"
        self.assertTrue(legacy_venv.is_symlink())
        self.assertEqual(os.readlink(legacy_venv), str(attest / "venv"))
        self.assertTrue((attest / "releases" / legacy / "INSTALLED.json").is_file())
        self.assertFalse((attest / "app").is_dir() and not (attest / "app").is_symlink())
        self.assert_serving(VERSIONS["b"])
        proc = self.host.run("rollback.sh")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.host.active(), legacy)
        self.assertIn("recorded in INSTALLED.json", proc.stdout)
        self.assertIn(f"attest_revision() digest {digest_a}", proc.stdout)
        self.assert_serving(VERSIONS["a"])

    # ---- OPS-01: rollback.sh and decommission.sh ---------------------------------------------------------------------------------------
    def test_scenario_6_rollback_restores_previous_release_and_reads_back_its_digest(self):
        self.install("a")
        self.install("b")
        calls_before = self.host.shim_calls()
        proc = self.host.run("rollback.sh")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("rollback complete", proc.stdout)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assertEqual(self.host.previous(), self.label("b"))
        self.assert_serving(VERSIONS["a"])
        digest_a = self.manifests["a"]["package_digest"]["digest"]
        self.assertIn(f"recorded in RELEASE.json: version {VERSIONS['a']}, package digest {digest_a}", proc.stdout)
        self.assertIn(f"attest_revision() digest {digest_a}", proc.stdout)
        self.assertIn("RELEASE.json entries verified in place", proc.stdout)
        self.assertIn("attest.db", proc.stdout, "the store path and the schema note are printed")
        self.assertIn("SELECT *", proc.stdout)
        new_calls = self.host.shim_calls()[len(calls_before):]
        self.assertNotIn("nginx-modern", new_calls, "the rollback never calls nginx")
        self.assertNotIn("systemctl reload", new_calls, "the rollback never reloads nginx")
        self.assertIn("systemctl restart attest.service", new_calls)
        listing = self.host.run("rollback.sh", "--list")
        self.assertEqual(listing.returncode, 0, listing.stdout + listing.stderr)
        self.assertIn(f"{self.label('a')}", listing.stdout)
        self.assertIn("(active)", listing.stdout)
        self.assertIn("(previous)", listing.stdout)

    def test_rollback_refuses_without_a_previous_release_and_changes_nothing(self):
        self.install("a")
        proc = self.host.run("rollback.sh")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no previous release", proc.stderr)
        self.assertIn("nothing was switched", proc.stdout)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assert_serving(VERSIONS["a"])

    def test_rollback_failure_after_the_switch_re_selects_the_release_that_was_serving(self):
        self.install("a")
        self.install("b")
        # the fake service misreports the version of release a: the rollback's health check fails after the switch
        proc = self.host.run("rollback.sh", REHEARSAL_HEALTH_BAD_VERSION=VERSIONS["a"])
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ROLLBACK FAILED", proc.stderr)
        self.assertIn("re-selecting the release that was active before this rollback", proc.stdout)
        self.assertEqual(self.host.active(), self.label("b"))
        self.assertEqual(self.host.previous(), self.label("a"))
        self.assert_serving(VERSIONS["b"])

    def test_scenario_7_decommission_requires_yes_and_then_removes_only_the_vhost(self):
        self.install("a")
        proc = self.host.run("decommission.sh")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("decommission.sh will:", proc.stdout)
        self.assertIn("refusing: pass --yes", proc.stdout)
        self.assertTrue(self.host.service_active())
        self.assertTrue(self.host.vhost.is_file())
        self.assertEqual(self.host.active(), self.label("a"))
        proc = self.host.run("decommission.sh", "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("decommissioned:", proc.stdout)
        self.assertFalse(self.host.service_active())
        self.assertFalse(self.host.vhost.exists())
        self.assertTrue((self.host.attest / "releases" / self.label("a")).is_dir(), "releases, store and secrets are kept")
        self.assertTrue(self.host.unit.is_file(), "the unit file stays (disabled)")

    # ---- paths the server rehearsal does not reach ---------------------------------------------------------------------------------
    def test_clean_install_health_failure_leaves_no_release_and_stops_the_service(self):
        proc = self.install("a", expect_ok=False, REHEARSAL_HEALTH_BAD_VERSION=VERSIONS["a"])
        self.assertIn("there was no release before this run", proc.stdout)
        self.assertIsNone(self.host.active())
        self.assertFalse((self.host.attest / "releases" / self.label("a")).exists(), "the failed release directory is removed")
        self.assertFalse(self.host.unit.exists(), "the new unit file is removed again")
        self.assertFalse(self.host.vhost.exists(), "the new vhost is removed again")
        self.assertFalse(self.host.service_active())

    def test_reinstalling_the_active_release_refreshes_without_switching(self):
        self.install("a")
        proc = self.install("a")
        self.assertIn("refresh mode", proc.stdout)
        self.assertEqual(self.host.active(), self.label("a"))
        self.assertIsNone(self.host.previous())
        self.assert_serving(VERSIONS["a"])

    def test_old_releases_are_pruned_but_never_the_active_or_previous_one(self):
        self.install("a")
        self.install("b")
        proc = self.install("c", KEEP_RELEASES="2")
        self.assertIn(f"pruned old release {self.label('a')}", proc.stdout)
        names = sorted(p.name for p in (self.host.attest / "releases").iterdir() if not p.name.startswith("."))
        self.assertEqual(names, sorted([self.label("b"), self.label("c")]))
        self.assertEqual(self.host.active(), self.label("c"))
        self.assertEqual(self.host.previous(), self.label("b"))
        self.assert_serving(VERSIONS["c"])


if __name__ == "__main__":
    unittest.main()
