"""In-memory scenario registry with provenance-aware filtering."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import ChallengeScenario, EvidenceLevel, ScenarioBasis


@dataclass
class ScenarioRegistry:
    """Small deterministic registry suitable for a local file-backed layer later."""

    _items: dict[str, ChallengeScenario] = field(default_factory=dict)

    def add(self, scenario: ChallengeScenario) -> None:
        if scenario.scenario_id in self._items:
            raise ValueError(f"scenario already exists: {scenario.scenario_id}")
        self._items[scenario.scenario_id] = scenario

    def upsert(self, scenario: ChallengeScenario) -> None:
        self._items[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> ChallengeScenario:
        try:
            return self._items[scenario_id]
        except KeyError as exc:
            raise KeyError(f"unknown scenario: {scenario_id}") from exc

    def list(
        self,
        *,
        basis: ScenarioBasis | None = None,
        evidence_level: EvidenceLevel | None = None,
        held_out: bool | None = None,
    ) -> tuple[ChallengeScenario, ...]:
        values = self._items.values()
        if basis is not None:
            values = (s for s in values if s.basis is basis)
        if evidence_level is not None:
            values = (s for s in values if s.evidence_level is evidence_level)
        if held_out is not None:
            values = (s for s in values if s.held_out is held_out)
        return tuple(sorted(values, key=lambda item: item.scenario_id))

    def __len__(self) -> int:
        return len(self._items)

    def to_dict(self) -> dict:
        return {"schema_version": 1, "scenarios": [item.to_dict() for item in self.list()]}

    @classmethod
    def from_dict(cls, data: object) -> "ScenarioRegistry":
        if not isinstance(data, dict) or set(data) != {"schema_version", "scenarios"}:
            raise ValueError("registry requires schema_version and scenarios")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("registry schema_version must be 1")
        if not isinstance(data["scenarios"], list):
            raise ValueError("registry scenarios must be an array")
        registry = cls()
        for item in data["scenarios"]:
            registry.add(ChallengeScenario.from_dict(item))
        return registry
