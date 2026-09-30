"""Defensive phenotype analytics with explicit provenance and reproducibility."""
from .audit import AuditRecord, audit_from_dict, audit_json, build_audit_record, verify_audit_record
from .benchmark import DetectionMetrics, detection_metrics, held_out_rate
from .evaluation import evaluate_benchmark
from .generator import derive_challenge, perturb_phenotype
from .models import ChallengeScenario, EvidenceLevel, PhenotypeVector, ScenarioBasis
from .novelty import NoveltyResult, nearest_reference, novelty_score
from .registry import ScenarioRegistry
from .rescue import RescueResult, score_rescue
from .trajectory import TrajectoryPoint, resample_trajectory, summarize_trajectory

__all__ = [
    "AuditRecord", "ChallengeScenario", "DetectionMetrics", "EvidenceLevel", "NoveltyResult",
    "PhenotypeVector", "RescueResult", "ScenarioBasis", "ScenarioRegistry", "TrajectoryPoint",
    "audit_from_dict", "audit_json", "build_audit_record", "derive_challenge", "detection_metrics",
    "evaluate_benchmark", "held_out_rate", "nearest_reference", "novelty_score", "perturb_phenotype",
    "resample_trajectory", "score_rescue", "summarize_trajectory", "verify_audit_record",
]
