"""Safe challenge synthesis from phenotype-level parameters."""

from __future__ import annotations

import random
from dataclasses import replace

from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis


def perturb_phenotype(
    baseline: PhenotypeVector,
    *,
    seed: int,
    magnitude: float = 0.15,
) -> PhenotypeVector:
    """Create a bounded phenotype variant reproducibly.

    The function operates only on observable phenotype values. It does not
    generate or encode biological-agent construction parameters.
    """
    if not 0.0 <= magnitude <= 1.0:
        raise ValueError("magnitude must be in [0, 1]")

    rng = random.Random(seed)
    values = {
        key: min(1.0, max(0.0, value + rng.uniform(-magnitude, magnitude)))
        for key, value in baseline.features.items()
    }
    return PhenotypeVector(values)


def derive_challenge(
    baseline: ChallengeScenario,
    *,
    scenario_id: str,
    seed: int,
    magnitude: float,
    held_out: bool = True,
) -> ChallengeScenario:
    """Derive a new challenge state while preserving provenance."""
    phenotype = perturb_phenotype(baseline.phenotype, seed=seed, magnitude=magnitude)
    return replace(
        baseline,
        scenario_id=scenario_id,
        title=f"Derived challenge from {baseline.scenario_id}",
        basis=ScenarioBasis.COMPUTATIONAL,
        evidence_level=EvidenceLevel.DERIVED,
        phenotype=phenotype,
        evidence_refs=tuple(baseline.evidence_refs) + (baseline.scenario_id,),
        uncertainty=min(1.0, baseline.uncertainty + magnitude * 0.5),
        held_out=held_out,
        notes="Phenotype-level computational variation derived from a grounded reference state.",
    )
