"""Strict, deterministic JSON and immutable snapshots for persisted data."""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from types import MappingProxyType


def freeze_json(value: object) -> object:
    """Copy a JSON value recursively; reject lossy coercions and nonfinite numbers."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise ValueError("JSON object keys must be strings")
        return MappingProxyType({key: freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: plain_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain_json(item) for item in value]
    return value


def canonical_json(value: object) -> str:
    return json.dumps(plain_json(freeze_json(value)), sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def pretty_json(value: object) -> str:
    return json.dumps(plain_json(freeze_json(value)), sort_keys=True, indent=2,
                      allow_nan=False)


def load_json(text: str) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"nonfinite JSON number: {value}")

    value = json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_constant)
    return plain_json(freeze_json(value))
