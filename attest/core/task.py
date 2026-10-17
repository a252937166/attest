"""Task specification: loaded from task.json, frozen with content digests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

GUEST_PYTHON = "/usr/local/bin/python"
GUEST_REPO = "/tmp/w"
GUEST_SEALED_DIR = "/tmp/sealed"
GUEST_DEPS_DIR = "/tmp/deps"


@dataclass
class TaskSpec:
    id: str
    title: str
    statement: str
    acceptance_criteria: list[str]
    repo_dir: Path
    allowed_write_globs: list[str]
    protected_globs: list[str]
    test_command: list[str]
    base_image: str = "python:3.12-slim"
    language: str = "python"
    import_hint: str = ""
    test_runner: str = "unittest"
    install_command: list[str] | None = None
    requirements_lock: str | None = None
    python_paths: list[str] = field(default_factory=list)
    checkpoint_timeout: int = 300
    test_timeout: int = 180
    heldout_tests: dict[str, str] = field(default_factory=dict)
    upstream: dict | None = None  # {"url", "commit", "reference"} for tasks taken from an external repository
    max_file_bytes: int = 200_000  # per-file bound of the repository snapshot (hard cap 1,000,000)
    source_path: Path | None = None
    extra: dict = field(default_factory=dict)

    @property
    def checkpoint_networking(self) -> bool:
        return bool(self.install_command)

    def guest_env(self) -> dict:
        paths = [GUEST_DEPS_DIR] + [f"{GUEST_REPO}/{p.strip('/')}" for p in self.python_paths] + [GUEST_REPO]
        return {"PYTHONPATH": ":".join(paths)}

    def sealed_extra_paths(self) -> list[str]:
        return [GUEST_DEPS_DIR] + [f"{GUEST_REPO}/{p.strip('/')}" for p in self.python_paths]

    @classmethod
    def load(cls, path: Path) -> "TaskSpec":
        data = json.loads(path.read_text(encoding="utf-8"))
        repo_dir = (path.parent / data.get("repo_dir", "repo")).resolve()
        if not repo_dir.is_dir():
            raise FileNotFoundError(f"task repo directory missing: {repo_dir}")
        return cls(id=data["id"], title=data["title"], statement=data["statement"].strip(),
                   acceptance_criteria=list(data.get("acceptance_criteria", [])), repo_dir=repo_dir,
                   allowed_write_globs=list(data.get("allowed_write_globs", ["**"])),
                   protected_globs=list(data.get("protected_globs", ["tests/**"])),
                   test_command=list(data.get("test_command") or
                                     [GUEST_PYTHON, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"]),
                   base_image=data.get("base_image", "python:3.12-slim"), language=data.get("language", "python"),
                   import_hint=data.get("import_hint", ""), test_runner=data.get("test_runner", "unittest"),
                   install_command=data.get("install_command"), requirements_lock=data.get("requirements_lock"),
                   python_paths=list(data.get("python_paths", [])),
                   checkpoint_timeout=int(data.get("checkpoint_timeout", 300)), test_timeout=int(data.get("test_timeout", 180)),
                   heldout_tests=cls._load_heldout(path.parent, data.get("heldout_tests") or {}),
                   upstream=cls._load_upstream(data.get("upstream")), source_path=path,
                   max_file_bytes=min(int(data.get("max_file_bytes", 200_000)), 1_000_000),
                   extra={k: v for k, v in data.items() if k not in {
                       "id", "title", "statement", "acceptance_criteria", "repo_dir", "allowed_write_globs",
                       "protected_globs", "test_command", "base_image", "language", "import_hint", "test_runner",
                       "install_command", "requirements_lock", "python_paths", "checkpoint_timeout", "test_timeout",
                       "heldout_tests", "upstream", "max_file_bytes"}})

    @staticmethod
    def _load_upstream(data) -> dict | None:
        """Upstream repository of an externally sourced task: url, commit (the exact base revision) and a reference."""
        if not data:
            return None
        if not isinstance(data, dict) or not data.get("url"):
            raise ValueError("task.upstream must be an object with at least a url")
        return {"url": str(data["url"]), "commit": data.get("commit"), "reference": data.get("reference")}

    @staticmethod
    def _load_heldout(root: Path, mapping: dict) -> dict[str, str]:
        """heldout_tests maps a guest-relative test path to a local file whose content is injected at verification."""
        loaded = {}
        for guest_rel, local in mapping.items():
            loaded[guest_rel] = (root / local).read_text(encoding="utf-8")
        return loaded

    def frozen(self, snapshot: dict[str, bytes]) -> dict:
        files = {path: hashlib.sha256(data).hexdigest() for path, data in sorted(snapshot.items())}
        body = {"id": self.id, "title": self.title, "statement": self.statement,
                "acceptance_criteria": self.acceptance_criteria, "allowed_write_globs": self.allowed_write_globs,
                "protected_globs": self.protected_globs, "test_command": self.test_command,
                "base_image": self.base_image, "language": self.language, "import_hint": self.import_hint,
                "test_runner": self.test_runner, "install_command": self.install_command,
                "requirements_lock": self.requirements_lock, "python_paths": self.python_paths,
                "heldout_tests_sha256": {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in sorted(self.heldout_tests.items())},
                "repo_files_sha256": files}
        if self.upstream:
            body["upstream"] = self.upstream  # only present for externally sourced tasks, so other digests are unchanged
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        body["spec_sha256"] = hashlib.sha256(canonical).hexdigest()
        return body
