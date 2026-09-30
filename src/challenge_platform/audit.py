"""Immutable audit events with separate event and reproducible content hashes."""
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime, timezone

from .models import nonempty_text
from .serialization import canonical_json, freeze_json, plain_json, pretty_json


def _hash(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _content(payload: dict) -> dict:
    return {key: value for key, value in payload.items()
            if key not in {"run_id", "created_at", "content_hash", "record_hash"}}


@dataclass(frozen=True)
class AuditRecord:
    run_id: str
    scenario_id: str
    dataset_version: str
    model_version: str
    seed: int
    inputs: Mapping[str, object]
    outputs: Mapping[str, object]
    created_at: str
    content_hash: str
    record_hash: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("audit schema_version must be 1")
        for name in ("run_id", "scenario_id", "dataset_version", "model_version"):
            value = getattr(self, name)
            if nonempty_text(value, name) != value:
                raise ValueError(f"{name} cannot have surrounding whitespace")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")
        if not isinstance(self.created_at, str):
            raise ValueError("created_at must be an ISO timestamp")
        date = datetime.fromisoformat(self.created_at)
        if date.utcoffset() is None:
            raise ValueError("created_at must include a timezone")
        for name in ("inputs", "outputs"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise ValueError(f"{name} must be a JSON object")
            object.__setattr__(self, name, freeze_json(value))
        for name in ("record_hash", "content_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64 or any(
                ch not in "0123456789abcdef" for ch in value
            ):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")

    def to_dict(self) -> dict:
        return {field.name: plain_json(getattr(self, field.name)) for field in fields(self)}


def build_audit_record(
    *, run_id: str, scenario_id: str, dataset_version: str, model_version: str,
    seed: int, inputs: Mapping[str, object], outputs: Mapping[str, object],
    created_at: str | None = None,
) -> AuditRecord:
    """Hash computation content independently of event identity and wall time.

    Hashes detect changes relative to a trusted digest; they are not signatures.
    """
    payload = {
        "schema_version": 1, "run_id": run_id, "scenario_id": scenario_id,
        "dataset_version": dataset_version, "model_version": model_version,
        "seed": seed, "inputs": freeze_json(inputs), "outputs": freeze_json(outputs),
        "created_at": created_at if created_at is not None else datetime.now(timezone.utc).isoformat(),
    }
    payload["content_hash"] = _hash(_content(payload))
    return AuditRecord(**payload, record_hash=_hash(payload))


def verify_audit_record(record: AuditRecord) -> bool:
    payload = record.to_dict()
    expected = payload.pop("record_hash")
    return _hash(_content(payload)) == record.content_hash and _hash(payload) == expected


def audit_from_dict(data: object) -> AuditRecord:
    if not isinstance(data, Mapping) or set(data) != {field.name for field in fields(AuditRecord)}:
        raise ValueError("invalid audit record fields")
    record = AuditRecord(**data)
    if not verify_audit_record(record):
        raise ValueError("audit hash verification failed")
    return record


def audit_json(record: AuditRecord) -> str:
    if not verify_audit_record(record):
        raise ValueError("audit hash verification failed")
    return pretty_json(record.to_dict())
