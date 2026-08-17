"""Command-line entry point for deterministic challenge generation."""

from __future__ import annotations

import argparse
import json

from .generator import derive_challenge
from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="virelion-challenge",
        description="Generate phenotype-level defensive challenge variants.",
    )
    parser.add_argument("--scenario-id", default="CH-001")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--magnitude", type=float, default=0.15)
    parser.add_argument("--held-out", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    reference = ChallengeScenario(
        scenario_id="REFERENCE",
        title="Reference cardiac state",
        basis=ScenarioBasis.EXPERIMENTAL,
        evidence_level=EvidenceLevel.OBSERVED,
        phenotype=PhenotypeVector(
            {
                "inflammation": 0.15,
                "vascular_dysfunction": 0.10,
                "contractile_impairment": 0.05,
                "mitochondrial_stress": 0.10,
            }
        ),
    )
    challenge = derive_challenge(
        reference,
        scenario_id=args.scenario_id,
        seed=args.seed,
        magnitude=args.magnitude,
        held_out=args.held_out,
    )
    print(
        json.dumps(
            {
                "scenario_id": challenge.scenario_id,
                "basis": challenge.basis.value,
                "evidence_level": challenge.evidence_level.value,
                "phenotype": dict(challenge.phenotype.features),
                "uncertainty": challenge.uncertainty,
                "held_out": challenge.held_out,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
