"""Executor interface: one checkpoint, many disposable branches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class StepResult:
    name: str
    cmd: list[str]
    exit_code: int | None
    timed_out: bool
    duration_s: float | None
    stdout: str
    stderr: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.error


@dataclass
class RunResult:
    stage: str
    operation_uuid: str | None
    status: str | None
    exit_code: int | None
    timed_out: bool | None
    signal: int | None
    duration_s: float | None
    image_uuid: str
    result_image_uuid: str | None
    steps: list[StepResult] = field(default_factory=list)
    runner_error: str | None = None
    stdout_truncated: bool = False
    raw_stdout_excerpt: str = ""
    raw_stderr_excerpt: str = ""
    chain: list[str] = field(default_factory=list)  # earlier retained operations a chunked checkpoint was built from

    @property
    def ok(self) -> bool:
        return self.status == "SUCCESS" and self.exit_code == 0 and not self.runner_error

    def step(self, name: str) -> StepResult | None:
        for step in self.steps:
            if step.name == name:
                return step
        return None


class Executor(Protocol):
    name: str

    def resolve_image(self, tag: str) -> str: ...

    def create_checkpoint(self, image: str, files: dict[str, bytes], steps: list[dict], stage: str,
                          timeout: int = 120) -> RunResult: ...

    def run_branch(self, image: str, files: dict[str, bytes], steps: list[dict], stage: str,
                   deletes: list[str] | None = None, timeout: int = 120) -> RunResult: ...

    def describe(self) -> dict: ...
