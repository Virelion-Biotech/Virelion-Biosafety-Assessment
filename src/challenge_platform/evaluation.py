"""Held-out family evaluation with declared split and ancestry checks."""
from __future__ import annotations

from dataclasses import asdict

from .benchmark import detection_metrics, held_out_rate
from .models import ChallengeScenario
from .novelty import novelty_score
from .registry import ScenarioRegistry


def _lineage_ids(scenario: ChallengeScenario) -> set[str]:
    ids = {scenario.scenario_id}
    parent = scenario.provenance.get("parent")
    while parent is not None:
        ancestor = ChallengeScenario.from_dict(parent)
        ids.add(ancestor.scenario_id)
        parent = ancestor.provenance.get("parent")
    return ids


def evaluate_benchmark(data: object, *, threshold: float = 0.75) -> dict:
    """Score a fixed-threshold cohort; reject declared family/ancestry overlap.

    This validates supplied metadata, not undisclosed model-training history.
    Threshold selection/calibration must occur outside this held-out cohort.
    """
    if not isinstance(data, dict) or set(data) != {"schema_version", "references", "cases"}:
        raise ValueError("benchmark requires schema_version, references, and cases")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("benchmark schema_version must be 1")
    registry = ScenarioRegistry.from_dict({"schema_version": 1, "scenarios": data["references"]})
    references = registry.list()
    if not references:
        raise ValueError("benchmark requires at least one reference")
    if any(item.held_out for item in references):
        raise ValueError("reference scenarios cannot be marked held_out")
    if any(item.family_id is None for item in references):
        raise ValueError("family_id is required for every benchmark scenario")
    if not isinstance(data["cases"], list) or not data["cases"]:
        raise ValueError("benchmark requires a nonempty cases array")
    families = {item.family_id for item in references}
    reference_lineage = set().union(*(_lineage_ids(item) for item in references))
    seen = {item.scenario_id for item in references}
    labels, predictions, rows = [], [], []
    for case in data["cases"]:
        if not isinstance(case, dict) or set(case) != {"scenario", "abnormal"}:
            raise ValueError("each benchmark case requires scenario and abnormal")
        if type(case["abnormal"]) is not bool:
            raise ValueError("case abnormal label must be boolean")
        scenario = ChallengeScenario.from_dict(case["scenario"])
        if not scenario.held_out or scenario.family_id is None:
            raise ValueError("benchmark cases require held_out=true and a family_id")
        if scenario.scenario_id in seen:
            raise ValueError(f"duplicate scenario_id: {scenario.scenario_id}")
        seen.add(scenario.scenario_id)
        if scenario.family_id in families or _lineage_ids(scenario) & reference_lineage:
            raise ValueError(f"reference/held-out family or ancestry overlap: {scenario.scenario_id}")
        result = novelty_score(scenario.phenotype,
                               [(item.scenario_id, item.phenotype) for item in references],
                               threshold=threshold)
        labels.append(case["abnormal"])
        predictions.append(result.is_novel)
        rows.append({"scenario_id": scenario.scenario_id, "family_id": scenario.family_id,
                     "evidence_level": scenario.evidence_level.value,
                     "abnormal": case["abnormal"], **asdict(result)})
    positive_predictions = [prediction for label, prediction in zip(labels, predictions) if label]
    return {"schema_version": 1, "threshold": threshold,
            "metrics": asdict(detection_metrics(labels, predictions)),
            "held_out_detection_rate": held_out_rate(positive_predictions) if positive_predictions else None,
            "cases": sorted(rows, key=lambda item: item["scenario_id"]),
            "limitations": "Metadata-only split validation; no verification of undisclosed training data. "
                           "Threshold is user-supplied, not calibrated on this cohort. "
                           "Distance scores are not probabilities or biological validation."}
