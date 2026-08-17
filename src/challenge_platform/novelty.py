"""Novelty/OOD scoring over observable phenotype vectors."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Iterable

from .models import PhenotypeVector


@dataclass(frozen=True)
class NoveltyResult:
    score: float
    nearest_distance: float
    nearest_id: str | None
    is_novel: bool


def nearest_reference(
    candidate: PhenotypeVector,
    references: Iterable[tuple[str, PhenotypeVector]],
) -> tuple[str | None, float]:
    best_id: str | None = None
    best_distance = inf
    for reference_id, reference in references:
        distance = candidate.distance(reference)
        if distance < best_distance:
            best_id = reference_id
            best_distance = distance
    return best_id, best_distance


def novelty_score(
    candidate: PhenotypeVector,
    references: Iterable[tuple[str, PhenotypeVector]],
    *,
    threshold: float = 0.75,
) -> NoveltyResult:
    """Score how far a candidate is from the nearest known state."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative")
    nearest_id, distance = nearest_reference(candidate, references)
    if nearest_id is None:
        return NoveltyResult(score=1.0, nearest_distance=inf, nearest_id=None, is_novel=True)
    score = min(1.0, distance / threshold) if threshold else float(distance > 0)
    return NoveltyResult(
        score=score,
        nearest_distance=distance,
        nearest_id=nearest_id,
        is_novel=distance >= threshold,
    )
