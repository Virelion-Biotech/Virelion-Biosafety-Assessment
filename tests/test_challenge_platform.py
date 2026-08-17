from challenge_platform import (
    ChallengeScenario,
    EvidenceLevel,
    PhenotypeVector,
    ScenarioBasis,
    build_audit_record,
    novelty_score,
    score_rescue,
)
from challenge_platform.generator import derive_challenge


def make_reference() -> ChallengeScenario:
    return ChallengeScenario(
        scenario_id="REF-001",
        title="Reference cardiac stress state",
        basis=ScenarioBasis.EXPERIMENTAL,
        evidence_level=EvidenceLevel.OBSERVED,
        evidence_refs=("study:example",),
        phenotype=PhenotypeVector(
            {
                "inflammation": 0.70,
                "contractility": 0.55,
                "mitochondrial_stress": 0.35,
            }
        ),
    )


def test_phenotype_values_are_bounded() -> None:
    try:
        PhenotypeVector({"inflammation": 1.01})
    except ValueError:
        return
    raise AssertionError("out-of-range phenotype values must be rejected")


def test_challenge_derivation_is_reproducible() -> None:
    reference = make_reference()
    a = derive_challenge(reference, scenario_id="CH-001", seed=7, magnitude=0.1)
    b = derive_challenge(reference, scenario_id="CH-001", seed=7, magnitude=0.1)
    assert a.phenotype.features == b.phenotype.features
    assert a.held_out is True
    assert a.basis is ScenarioBasis.COMPUTATIONAL


def test_novelty_detects_far_state() -> None:
    reference = make_reference().phenotype
    candidate = PhenotypeVector(
        {"inflammation": 0.0, "contractility": 1.0, "mitochondrial_stress": 1.0}
    )
    result = novelty_score(candidate, [("REF-001", reference)], threshold=0.5)
    assert result.is_novel is True
    assert result.nearest_id == "REF-001"


def test_rescue_is_positive_when_treated_moves_toward_baseline() -> None:
    baseline = PhenotypeVector({"inflammation": 0.1, "contractility": 0.9})
    challenged = PhenotypeVector({"inflammation": 0.9, "contractility": 0.2})
    treated = PhenotypeVector({"inflammation": 0.3, "contractility": 0.75})
    result = score_rescue(baseline, challenged, treated)
    assert result.overall > 0.5
    assert all(value > 0 for value in result.per_feature.values())


def test_audit_record_has_stable_hash_for_record_contents() -> None:
    record = build_audit_record(
        run_id="RUN-001",
        scenario_id="CH-001",
        dataset_version="v0.1",
        model_version="baseline",
        seed=7,
        inputs={"threshold": 0.5},
        outputs={"novel": True},
    )
    assert len(record.record_hash) == 64
    assert record.scenario_id == "CH-001"
    assert record.created_at.endswith("+00:00")
