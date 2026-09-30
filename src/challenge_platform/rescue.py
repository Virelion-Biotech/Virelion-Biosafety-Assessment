"""Recovery over affected features, with collateral change reported separately."""
from __future__ import annotations

from dataclasses import dataclass
from math import fsum

from .models import PhenotypeVector


@dataclass(frozen=True)
class RescueResult:
    overall: float | None
    per_feature: dict[str, float | None]
    eligible_features: tuple[str, ...]
    new_impairment: dict[str, float]


def score_rescue(baseline: PhenotypeVector, challenged: PhenotypeVector,
                 treated: PhenotypeVector) -> RescueResult:
    """Score fractional gap closure only where challenge changed baseline.

    Missing measurements are rejected. Unaffected features have null recovery;
    departures from their baseline are reported as new_impairment. An overall
    null means no challenged features are eligible, not successful recovery.
    """
    baseline.require_same_features(challenged)
    baseline.require_same_features(treated)
    per_feature = {}
    new_impairment = {}
    eligible = []
    for key in sorted(baseline.features):
        b, c, t = (state.features[key] for state in (baseline, challenged, treated))
        gap = abs(b - c)
        if gap == 0:
            per_feature[key] = None
            if t != b:
                new_impairment[key] = abs(t - b)
            continue
        eligible.append(key)
        per_feature[key] = max(-1.0, min(1.0, (gap - abs(b - t)) / gap))
    overall = fsum(per_feature[k] for k in eligible) / len(eligible) if eligible else None
    return RescueResult(overall, per_feature, tuple(eligible), new_impairment)
