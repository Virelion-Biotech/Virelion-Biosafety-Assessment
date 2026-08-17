"""Typed models for scenario-grounded defensive challenge states.

The models describe observable host-response phenotypes and evidence provenance.
They intentionally do not represent operational construction parameters for a
biological agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


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


@dataclass(frozen=True)
class PhenotypeVector:
    """Normalized observable state representation.

    Values are constrained to [0, 1] and represent effect magnitude, not
    biological-agent properties.
    """

    features: Mapping[str, float]

    def __post_init__(self) -> None:
        clean: dict[str, float] = {}
        for name, value in self.features.items():
            if not name or not name.strip():
                raise ValueError("phenotype feature names must be non-empty")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"phenotype value for {name!r} must be in [0, 1]")
            clean[name.strip()] = float(value)
        object.__setattr__(self, "features", clean)

    def distance(self, other: "PhenotypeVector") -> float:
        """Euclidean distance over the union of available feature names."""
        keys = set(self.features) | set(other.features)
        return sum(
            (self.features.get(k, 0.0) - other.features.get(k, 0.0)) ** 2
            for k in keys
        ) ** 0.5


@dataclass(frozen=True)
class ChallengeScenario:
    """A reproducible, evidence-labelled challenge state."""

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

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0, 1]")
        if self.temporal_profile and any(
            not 0.0 <= float(value) <= 1.0 for value in self.temporal_profile
        ):
            raise ValueError("temporal_profile values must be in [0, 1]")
