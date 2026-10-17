"""Model provider interface: structured JSON answers only, validated by the caller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..ledger import ModelCall


class ModelError(RuntimeError):
    def __init__(self, message: str, uncertain: bool = False, rate_limited: bool = False):
        super().__init__(message)
        self.uncertain = uncertain  # transport outcome unknown: never replay
        self.rate_limited = rate_limited  # the provider's quota refused the request (definite, nothing executed)


@dataclass
class ModelResult:
    json: Any
    text: str | None
    call: ModelCall


class ModelProvider(Protocol):
    name: str

    def structured(self, role: str, prompt: str, schema: dict, stage: str) -> ModelResult: ...

    def describe(self) -> dict: ...


def validate_json(instance: Any, schema: dict) -> str | None:
    """Return an error string if the instance violates the schema, else None."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        if not isinstance(instance, dict):
            return "expected an object"
        missing = [k for k in schema.get("required", []) if k not in instance]
        return f"missing required keys: {missing}" if missing else None
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as error:  # type: ignore[attr-defined]
        return str(error.message)[:400]
    return None


def extract_usage(usage: dict | None) -> tuple[int | None, int | None, int | None]:
    if not isinstance(usage, dict):
        return None, None, None

    def pick(*keys):
        for key in keys:
            value = usage.get(key)
            if isinstance(value, (int, float)):
                return int(value)
        return None

    cached = pick("cached_input_tokens", "cache_read_input_tokens")
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details")
    if cached is None and isinstance(details, dict):
        value = details.get("cached_tokens")
        cached = int(value) if isinstance(value, (int, float)) else None
    return pick("input_tokens", "prompt_tokens"), pick("output_tokens", "completion_tokens"), cached
