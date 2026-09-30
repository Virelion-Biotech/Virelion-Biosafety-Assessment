"""Nearest-reference distance: an uncalibrated baseline, not a probability."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from .models import PhenotypeVector, nonempty_text


@dataclass(frozen=True)
class NoveltyResult:
    score: float
    nearest_distance: float
    nearest_id: str
    is_novel: bool


def nearest_reference(candidate: PhenotypeVector,
                      references: Iterable[tuple[str, PhenotypeVector]]) -> tuple[str, float]:
    distances = []
    seen = set()
    for reference_id, reference in references:
        reference_id = nonempty_text(reference_id, "reference_id")
        if reference_id in seen:
            raise ValueError(f"duplicate reference_id: {reference_id}")
        seen.add(reference_id)
        distances.append((candidate.distance(reference), reference_id))
    if not distances:
        raise ValueError("at least one reference is required for novelty scoring")
    distance, reference_id = min(distances)  # Stable tie-break by identifier.
    return reference_id, distance


def novelty_score(candidate: PhenotypeVector,
                  references: Iterable[tuple[str, PhenotypeVector]], *,
                  threshold: float = 0.75) -> NoveltyResult:
    if type(threshold) not in (int, float) or not isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be finite and strictly positive")
    nearest_id, distance = nearest_reference(candidate, references)
    return NoveltyResult(min(1.0, distance / threshold), distance, nearest_id,
                         distance >= threshold)
