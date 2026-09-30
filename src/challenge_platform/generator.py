"""Deterministic bounded variation of observable phenotypes only."""
from __future__ import annotations

import random
from dataclasses import replace

from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis, unit_value


def perturb_phenotype(baseline: PhenotypeVector, *, seed: int,
                      magnitude: float = 0.15) -> PhenotypeVector:
    magnitude = unit_value(magnitude, "magnitude")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    return PhenotypeVector({
        key: min(1.0, max(0.0, baseline.features[key] + rng.uniform(-magnitude, magnitude)))
        for key in sorted(baseline.features)
    })


def derive_challenge(baseline: ChallengeScenario, *, scenario_id: str,
                     seed: int, magnitude: float, held_out: bool = False) -> ChallengeScenario:
    """Record the full parent snapshot; derivation does not validate its evidence.

    Family identity is inherited so perturbations cannot masquerade as a new
    family in a held-out-family benchmark. held_out is a declared split label.
    """
    if isinstance(scenario_id, str) and scenario_id.strip() == baseline.scenario_id:
        raise ValueError("derived scenario_id must differ from the parent")
    phenotype = perturb_phenotype(baseline.phenotype, seed=seed, magnitude=magnitude)
    level = baseline.evidence_level if baseline.evidence_level in (
        EvidenceLevel.SYNTHETIC, EvidenceLevel.EXPLORATORY
    ) else EvidenceLevel.DERIVED
    return replace(
        baseline, scenario_id=scenario_id, title=f"Derived challenge from {baseline.scenario_id}",
        basis=ScenarioBasis.COMPUTATIONAL, evidence_level=level, phenotype=phenotype,
        evidence_refs=baseline.evidence_refs,
        family_id=baseline.family_id or baseline.scenario_id,
        uncertainty=min(1.0, baseline.uncertainty + magnitude * 0.5),
        held_out=held_out,
        provenance={"operation": "bounded_perturbation_v1", "seed": seed,
                    "magnitude": float(magnitude), "parent": baseline.to_dict()},
        notes="Computational phenotype variation; parent evidence is not independently verified. "
              "Uncertainty is an uncalibrated heuristic, not a probability or confidence interval. "
              "Any temporal profile is inherited unchanged, not simulated.",
    )
