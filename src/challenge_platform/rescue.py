"""Phenotype recovery / countermeasure scoring."""

from __future__ import annotations

from dataclasses import dataclass

from .models import PhenotypeVector


@dataclass(frozen=True)
class RescueResult:
    overall: float
    per_feature: dict[str, float]


def score_rescue(
    baseline: PhenotypeVector,
    challenged: PhenotypeVector,
    treated: PhenotypeVector,
) -> RescueResult:
    """Measure movement from challenged state toward baseline.

    Each feature is evaluated independently. A score of 0 means no movement
    toward baseline, 1 means return to baseline, and negative values indicate
    movement farther away. Values are clipped to [-1, 1] for comparability.
    """
    keys = set(baseline.features) | set(challenged.features) | set(treated.features)
    per_feature: dict[str, float] = {}
    for key in keys:
        b = baseline.features.get(key, 0.0)
        c = challenged.features.get(key, 0.0)
        t = treated.features.get(key, 0.0)
        initial_gap = abs(b - c)
        if initial_gap == 0.0:
            per_feature[key] = 1.0 if abs(t - b) == 0.0 else 0.0
            continue
        recovery = (abs(b - c) - abs(b - t)) / initial_gap
        per_feature[key] = max(-1.0, min(1.0, recovery))

    overall = sum(per_feature.values()) / len(per_feature) if per_feature else 0.0
    return RescueResult(overall=overall, per_feature=per_feature)
