"""Reproducibility and provenance records for platform runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping


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
    record_hash: str


def build_audit_record(
    *,
    run_id: str,
    scenario_id: str,
    dataset_version: str,
    model_version: str,
    seed: int,
    inputs: Mapping[str, object],
    outputs: Mapping[str, object],
) -> AuditRecord:
    """Create a canonical, hash-linked run record."""
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "dataset_version": dataset_version,
        "model_version": model_version,
        "seed": seed,
        "inputs": inputs,
        "outputs": outputs,
        "created_at": created_at,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return AuditRecord(record_hash=record_hash, **payload)


def audit_json(record: AuditRecord) -> str:
    """Serialize an audit record deterministically for storage."""
    return json.dumps(asdict(record), sort_keys=True, indent=2, default=str)
