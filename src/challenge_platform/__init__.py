"""Defensive cardiac challenge platform primitives."""

from .audit import AuditRecord, build_audit_record
from .benchmark import DetectionMetrics, detection_metrics, held_out_rate
from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis
from .novelty import NoveltyResult, nearest_reference, novelty_score
from .registry import ScenarioRegistry
from .rescue import RescueResult, score_rescue
from .trajectory import TrajectoryPoint, resample_trajectory, summarize_trajectory

__all__ = [
    "AuditRecord",
    "ChallengeScenario",
    "DetectionMetrics",
    "EvidenceLevel",
    "NoveltyResult",
    "PhenotypeVector",
    "RescueResult",
    "ScenarioBasis",
    "ScenarioRegistry",
    "TrajectoryPoint",
    "build_audit_record",
    "detection_metrics",
    "held_out_rate",
    "nearest_reference",
    "novelty_score",
    "resample_trajectory",
    "score_rescue",
    "summarize_trajectory",
]
