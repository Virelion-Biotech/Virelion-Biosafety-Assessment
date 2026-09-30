"""Regression cases from PR #1's review and persisted-data boundaries."""
import json
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from challenge_platform import (
    ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis, ScenarioRegistry,
    audit_from_dict, audit_json, build_audit_record, derive_challenge, detection_metrics,
    evaluate_benchmark, held_out_rate, nearest_reference, novelty_score,
    perturb_phenotype, resample_trajectory, score_rescue, verify_audit_record,
)
from challenge_platform.serialization import load_json


def scenario(sid="s", family="family", features=None, held_out=False):
    return ChallengeScenario(sid, "Synthetic fixture", ScenarioBasis.COMPUTATIONAL,
        EvidenceLevel.SYNTHETIC, PhenotypeVector(features or {"a": 0.1, "b": 0.2}),
        family_id=family, held_out=held_out, uncertainty=1.0)


def audit(**updates):
    values = dict(run_id="run", scenario_id="s", dataset_version="data-1", model_version="model-1",
                  seed=7, inputs={"nested": {"values": [1, 2]}}, outputs={"score": 0.5})
    values.update(updates)
    return build_audit_record(**values)


@pytest.mark.parametrize("features", [{}, {"": 0.1}, {"a": 2}, {"a": float("nan")},
    {"a": float("inf")}, {"a": True}, {"a": "0.1"}, {"a": 0.1, " a ": 0.2}, {1: 0.2}])
def test_phenotype_rejects_invalid_or_ambiguous_measurements(features):
    with pytest.raises(ValueError):
        PhenotypeVector(features)


def test_phenotype_is_a_defensive_immutable_snapshot():
    source = {"a": 0.5}
    phenotype = PhenotypeVector(source)
    source["a"] = 9
    assert phenotype.features["a"] == 0.5
    with pytest.raises(TypeError):
        phenotype.features["a"] = 9


def test_missing_measurements_cannot_count_as_rescue_or_match():
    baseline = PhenotypeVector({"a": 0, "b": 0})
    challenged = PhenotypeVector({"a": 1, "b": 1})
    partial_treated = PhenotypeVector({"b": 0})
    with pytest.raises(ValueError, match="feature sets must match"):
        score_rescue(baseline, challenged, partial_treated)
    with pytest.raises(ValueError, match="feature sets must match"):
        baseline.distance(partial_treated)


def test_unaffected_features_do_not_inflate_recovery():
    baseline = PhenotypeVector({"a": 0, "b": 0, "c": 0})
    challenged = PhenotypeVector({"a": 1, "b": 0, "c": 0})
    result = score_rescue(baseline, challenged, challenged)
    assert result.overall == 0
    assert result.per_feature == {"a": 0, "b": None, "c": None}
    assert result.eligible_features == ("a",)


def test_new_impairment_is_visible_even_when_affected_feature_recovers():
    baseline = PhenotypeVector({"a": 0, "b": 0})
    result = score_rescue(baseline, PhenotypeVector({"a": 1, "b": 0}),
                          PhenotypeVector({"a": 0, "b": 0.5}))
    assert result.overall == 1
    assert result.new_impairment == {"b": 0.5}
    assert score_rescue(baseline, baseline, baseline).overall is None


def test_recovery_penalizes_overshoot_and_worsening():
    assert score_rescue(PhenotypeVector({"a": 0.5}), PhenotypeVector({"a": 0.75}),
                         PhenotypeVector({"a": 0})).overall == -1


def test_equal_vectors_reordered_yield_identical_seeded_variants():
    a = PhenotypeVector({"a": 0.5, "b": 0.5})
    b = PhenotypeVector({"b": 0.5, "a": 0.5})
    assert a == b
    assert perturb_phenotype(a, seed=7) == perturb_phenotype(b, seed=7)
    assert perturb_phenotype(a, seed=7, magnitude=0) == a


@pytest.mark.parametrize("level", [EvidenceLevel.SYNTHETIC, EvidenceLevel.EXPLORATORY])
def test_derivation_does_not_upgrade_ungrounded_evidence(level):
    parent = replace(scenario(), evidence_level=level)
    derived = derive_challenge(parent, scenario_id="child", seed=2, magnitude=0.2)
    assert derived.evidence_level is level
    assert derived.held_out is False
    assert derived.family_id == parent.family_id
    assert ChallengeScenario.from_dict(derived.provenance["parent"]) == parent
    assert derived.provenance["seed"] == 2
    assert derived.provenance["magnitude"] == 0.2
    assert ChallengeScenario.from_dict(derived.to_dict()) == derived
    with pytest.raises(TypeError):
        derived.provenance["parent"]["phenotype"]["a"] = 5


def test_observed_evidence_requires_references_and_consistent_basis():
    with pytest.raises(ValueError, match="evidence_refs"):
        replace(scenario(), basis=ScenarioBasis.EXPERIMENTAL, evidence_level=EvidenceLevel.OBSERVED)
    observed = replace(scenario(), basis=ScenarioBasis.EXPERIMENTAL,
                       evidence_level=EvidenceLevel.OBSERVED, evidence_refs=("doi:fixture",))
    derived = derive_challenge(observed, scenario_id="child", seed=2, magnitude=0.1)
    assert derived.evidence_level is EvidenceLevel.DERIVED
    assert derived.evidence_refs == observed.evidence_refs
    with pytest.raises(ValueError, match="cannot claim"):
        replace(observed, basis=ScenarioBasis.COMPUTATIONAL)


def test_temporal_and_evidence_lists_are_snapshots():
    refs, times = ["source"], [0.1, 0.3]
    state = replace(scenario(), evidence_refs=refs, temporal_profile=times)
    refs.append("later")
    times[0] = 5
    assert state.evidence_refs == ("source",)
    assert state.temporal_profile == (0.1, 0.3)


def test_default_audit_clock_changes_only_event_hash():
    with patch("challenge_platform.audit.datetime") as clock:
        clock.now.return_value = datetime(2026, 1, 1, tzinfo=timezone.utc)
        a = audit()
        clock.now.return_value = datetime(2026, 1, 2, tzinfo=timezone.utc)
        b = audit(run_id="second-run")
    assert a.content_hash == b.content_hash
    assert a.record_hash != b.record_hash
    assert verify_audit_record(a) and verify_audit_record(b)


def test_audit_hashes_match_for_identical_events_and_ignore_mapping_order():
    a = audit(inputs={"a": 1, "b": 2}, created_at="2026-01-01T00:00:00+00:00")
    b = audit(inputs={"b": 2, "a": 1}, created_at=a.created_at)
    assert a.record_hash == b.record_hash
    assert a.content_hash != audit(seed=8).content_hash


def test_audit_snapshot_survives_source_mutation_and_roundtrip():
    source = {"nested": {"values": [1, 2]}}
    record = audit(inputs=source)
    before = audit_json(record)
    source["nested"]["values"].append(3)
    assert audit_json(record) == before
    with pytest.raises(TypeError):
        record.inputs["nested"]["values"][0] = 10
    assert audit_from_dict(json.loads(before)) == record


@pytest.mark.parametrize("value", [complex(1, 2), {1, 2}, object(), float("nan"), float("inf"), {1: "x"}])
def test_audit_rejects_lossy_or_nonfinite_values(value):
    with pytest.raises(ValueError):
        audit(inputs={"x": value})


@pytest.mark.parametrize("field,value", [("seed", 3), ("run_id", "changed"),
    ("created_at", "2026-01-02T00:00:00+00:00"), ("outputs", {"score": 1})])
def test_tampered_audit_is_rejected(field, value):
    data = audit().to_dict()
    data[field] = value
    with pytest.raises(ValueError, match="hash verification"):
        audit_from_dict(data)


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'])
def test_persisted_json_is_strict(text):
    with pytest.raises(ValueError):
        load_json(text)


@pytest.mark.parametrize("threshold", [0, -1, float("nan"), float("inf"), True])
def test_novelty_rejects_undefined_thresholds(threshold):
    vector = PhenotypeVector({"a": 0})
    with pytest.raises(ValueError):
        novelty_score(vector, [("ref", vector)], threshold=threshold)


def test_empty_references_are_not_reported_as_evidence_of_novelty():
    with pytest.raises(ValueError, match="at least one reference"):
        novelty_score(PhenotypeVector({"a": 0}), [])


def test_nearest_ties_are_order_independent_and_ids_unique():
    vector = PhenotypeVector({"a": 0})
    assert nearest_reference(vector, [("z", vector), ("a", vector)]) == ("a", 0)
    with pytest.raises(ValueError, match="duplicate"):
        nearest_reference(vector, [("a", vector), ("a", vector)])
    result = novelty_score(vector, [("a", vector)])
    assert result.score == 0 and not result.is_novel


def test_undefined_metrics_are_null_with_counts_available():
    result = detection_metrics([False, False], [False, False])
    assert result.sensitivity is None and result.precision is None
    assert result.specificity == 1 and result.true_negatives == 2
    assert held_out_rate([True, False, True]) == 2 / 3
    with pytest.raises(ValueError):
        held_out_rate([1, 0])
    with pytest.raises(ValueError):
        detection_metrics([True], ["false"])


def benchmark_data():
    ref = scenario("ref", "reference", {"a": 0, "b": 0})
    normal = scenario("normal", "normal-family", {"a": 0.1, "b": 0.1}, True)
    abnormal = scenario("abnormal", "abnormal-family", {"a": 1, "b": 1}, True)
    return {"schema_version": 1, "references": [ref.to_dict()], "cases": [
        {"scenario": normal.to_dict(), "abnormal": False},
        {"scenario": abnormal.to_dict(), "abnormal": True}]}


def test_benchmark_reports_counts_and_held_out_detection():
    result = evaluate_benchmark(benchmark_data())
    assert result["metrics"]["accuracy"] == 1
    assert result["metrics"]["true_positives"] == 1
    assert result["metrics"]["true_negatives"] == 1
    assert result["held_out_detection_rate"] == 1


@pytest.mark.parametrize("change", ["family", "ancestry", "reference_split", "case_split", "duplicate"])
def test_benchmark_rejects_declared_leakage_and_bad_splits(change):
    data = benchmark_data()
    if change == "family":
        data["cases"][0]["scenario"]["family_id"] = "reference"
    elif change == "ancestry":
        derived = derive_challenge(ChallengeScenario.from_dict(data["references"][0]),
            scenario_id="child", seed=1, magnitude=0.2, held_out=True)
        # Even changing a declared family cannot hide the retained parent.
        data["cases"][0]["scenario"] = replace(derived, family_id="renamed").to_dict()
    elif change == "reference_split":
        data["references"][0]["held_out"] = True
    elif change == "case_split":
        data["cases"][0]["scenario"]["held_out"] = False
    else:
        data["cases"].append(data["cases"][0])
    with pytest.raises(ValueError):
        evaluate_benchmark(data)


def test_registry_roundtrip_and_combined_filters():
    registry = ScenarioRegistry()
    registry.add(scenario("z"))
    registry.add(scenario("a", held_out=True))
    restored = ScenarioRegistry.from_dict(registry.to_dict())
    assert [item.scenario_id for item in restored.list()] == ["a", "z"]
    assert [item.scenario_id for item in restored.list(basis=ScenarioBasis.COMPUTATIONAL,
            evidence_level=EvidenceLevel.SYNTHETIC, held_out=True)] == ["a"]
    with pytest.raises(ValueError, match="already exists"):
        restored.add(scenario("a"))


@pytest.mark.parametrize("points", [0, -1, 1.5, True])
def test_trajectory_point_count_requires_positive_integer(points):
    with pytest.raises(ValueError):
        resample_trajectory((0.1, 0.5), points)


def test_trajectory_edges_preserve_values():
    assert [point.severity for point in resample_trajectory((0.4,), 3)] == [0.4] * 3
    assert resample_trajectory((0, 1), 1)[0].severity == 0
