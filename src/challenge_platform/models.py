"""Validated host-response phenotypes and declared evidence provenance.

Metadata records source claims; it does not independently validate experiments.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from .serialization import freeze_json, plain_json


class EvidenceLevel(str, Enum):
    OBSERVED = "observed"
    PROXY = "proxy"
    DERIVED = "derived"
    SYNTHETIC = "synthetic"
    EXPLORATORY = "exploratory"


class ScenarioBasis(str, Enum):
    EXPERIMENTAL = "experimental"
    LITERATURE = "literature"
    PROXY = "proxy"
    COMPUTATIONAL = "computational"
    MIXED = "mixed"


def nonempty_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def unit_value(value: object, name: str) -> float:
    if type(value) not in (int, float) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return float(value)


@dataclass(frozen=True)
class PhenotypeVector:
    """Nonempty normalized measurements with immutable feature values."""

    features: Mapping[str, float]

    def __post_init__(self) -> None:
        if not isinstance(self.features, Mapping) or not self.features:
            raise ValueError("phenotype features must be a nonempty mapping")
        clean = {}
        for name, value in self.features.items():
            key = nonempty_text(name, "phenotype feature name")
            if key in clean:
                raise ValueError(f"duplicate normalized phenotype feature: {key}")
            clean[key] = unit_value(value, f"phenotype value for {key!r}")
        object.__setattr__(self, "features", MappingProxyType(dict(sorted(clean.items()))))

    def require_same_features(self, other: "PhenotypeVector") -> None:
        if self.features.keys() != other.features.keys():
            missing = sorted(self.features.keys() - other.features.keys())
            extra = sorted(other.features.keys() - self.features.keys())
            raise ValueError(f"phenotype feature sets must match; missing={missing}, extra={extra}")

    def distance(self, other: "PhenotypeVector") -> float:
        """Euclidean distance over identical feature sets; missing is not zero."""
        self.require_same_features(other)
        return math.sqrt(math.fsum((self.features[k] - other.features[k]) ** 2
                                   for k in sorted(self.features)))


@dataclass(frozen=True)
class ChallengeScenario:
    """An evidence-labelled state, not an assertion of empirical validation."""

    scenario_id: str
    title: str
    basis: ScenarioBasis
    evidence_level: EvidenceLevel
    phenotype: PhenotypeVector
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    temporal_profile: tuple[float, ...] = field(default_factory=tuple)
    uncertainty: float = 0.0
    held_out: bool = False
    notes: str = ""
    family_id: str | None = None
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("scenario_id", "title"):
            object.__setattr__(self, name, nonempty_text(getattr(self, name), name))
        try:
            object.__setattr__(self, "basis", ScenarioBasis(self.basis))
            object.__setattr__(self, "evidence_level", EvidenceLevel(self.evidence_level))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid scenario basis or evidence level") from exc
        if not isinstance(self.phenotype, PhenotypeVector):
            raise ValueError("phenotype must be a PhenotypeVector")
        if type(self.held_out) is not bool:
            raise ValueError("held_out must be a boolean")
        if not isinstance(self.notes, str):
            raise ValueError("notes must be a string")
        if not isinstance(self.evidence_refs, (tuple, list)):
            raise ValueError("evidence_refs must be an array of strings")
        refs = tuple(nonempty_text(ref, "evidence reference") for ref in self.evidence_refs)
        object.__setattr__(self, "evidence_refs", refs)
        if self.evidence_level in (EvidenceLevel.OBSERVED, EvidenceLevel.PROXY) and not refs:
            raise ValueError("observed/proxy scenarios require evidence_refs")
        if self.basis is ScenarioBasis.COMPUTATIONAL and self.evidence_level in (
            EvidenceLevel.OBSERVED, EvidenceLevel.PROXY
        ):
            raise ValueError("computational scenarios cannot claim observed/proxy evidence")
        object.__setattr__(self, "uncertainty", unit_value(self.uncertainty, "uncertainty"))
        if not isinstance(self.temporal_profile, (tuple, list)):
            raise ValueError("temporal_profile must be an array")
        object.__setattr__(self, "temporal_profile", tuple(
            unit_value(value, "temporal_profile value") for value in self.temporal_profile))
        if self.family_id is not None:
            object.__setattr__(self, "family_id", nonempty_text(self.family_id, "family_id"))
        if not isinstance(self.provenance, Mapping):
            raise ValueError("provenance must be a JSON object")
        object.__setattr__(self, "provenance", freeze_json(self.provenance))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1, "scenario_id": self.scenario_id, "title": self.title,
            "basis": self.basis.value, "evidence_level": self.evidence_level.value,
            "phenotype": dict(self.phenotype.features), "evidence_refs": list(self.evidence_refs),
            "temporal_profile": list(self.temporal_profile), "uncertainty": self.uncertainty,
            "held_out": self.held_out, "notes": self.notes, "family_id": self.family_id,
            "provenance": plain_json(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: object) -> "ChallengeScenario":
        if not isinstance(data, Mapping):
            raise ValueError("scenario must be a JSON object")
        values = dict(data)
        version = values.pop("schema_version", None)
        if type(version) is not int or version != 1:
            raise ValueError("scenario schema_version must be 1")
        try:
            values["phenotype"] = PhenotypeVector(values["phenotype"])
            return cls(**values)
        except (KeyError, TypeError) as exc:
            raise ValueError(f"invalid scenario fields: {exc}") from exc
