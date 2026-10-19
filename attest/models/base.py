"""Model provider interface: structured JSON answers only, validated by the caller."""

from __future__ import annotations

import math
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


INPUT_TOKEN_KEYS = ("input_tokens", "prompt_tokens")
OUTPUT_TOKEN_KEYS = ("output_tokens", "completion_tokens")


def token_count(value: Any) -> int | None:
    """A usable token counter is a non-negative integer (a float with an integral value is accepted because some gateways send
    numbers as floats). Booleans, negatives, NaN/inf, text and nulls are not counters and yield None: a missing or malformed
    counter must never be read as zero (audit finding AC-04)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value >= 0 and value.is_integer() else None
    return None


def extract_usage(usage: dict | None) -> tuple[int | None, int | None, int | None]:
    if not isinstance(usage, dict):
        return None, None, None

    def pick(*keys):
        for key in keys:
            count = token_count(usage.get(key))
            if count is not None:
                return count
        return None

    cached = pick("cached_input_tokens", "cache_read_input_tokens")
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details")
    if cached is None and isinstance(details, dict):
        cached = token_count(details.get("cached_tokens"))
    return pick(*INPUT_TOKEN_KEYS), pick(*OUTPUT_TOKEN_KEYS), cached


def usage_problem(usage: Any, tokens_in: int | None, tokens_out: int | None) -> str | None:
    """Why a successful generation cannot be priced from its usage, or None when both counters are usable. An HTTP 200 whose
    usage is missing, empty, partial or malformed proves that an answer was generated, not that it was free: the caller keeps
    the reservation unsettled instead of settling a known zero."""
    if usage is None:
        return "the response carries no usage object"
    if not isinstance(usage, dict):
        return f"usage is not an object but {type(usage).__name__}"
    if not usage:
        return "usage is an empty object"
    missing = []
    if tokens_in is None:
        missing.append("input (" + " or ".join(INPUT_TOKEN_KEYS) + ")")
    if tokens_out is None:
        missing.append("output (" + " or ".join(OUTPUT_TOKEN_KEYS) + ")")
    if missing:
        return "usage has no usable " + " and no usable ".join(missing) + f" counter; keys present: {sorted(map(str, usage))[:8]}"
    return None
