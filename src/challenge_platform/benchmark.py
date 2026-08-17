"""Lightweight benchmark metrics for defensive challenge experiments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionMetrics:
    sensitivity: float
    specificity: float
    precision: float
    accuracy: float


def detection_metrics(y_true: list[bool], y_pred: list[bool]) -> DetectionMetrics:
    """Calculate binary detection metrics with explicit empty-class handling."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    if not y_true:
        raise ValueError("at least one observation is required")

    tp = sum(a and b for a, b in zip(y_true, y_pred))
    tn = sum((not a) and (not b) for a, b in zip(y_true, y_pred))
    fp = sum((not a) and b for a, b in zip(y_true, y_pred))
    fn = sum(a and (not b) for a, b in zip(y_true, y_pred))

    sensitivity = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    accuracy = (tp + tn) / len(y_true)
    return DetectionMetrics(sensitivity, specificity, precision, accuracy)


def held_out_rate(known_predictions: list[bool], held_out_predictions: list[bool]) -> float:
    """Fraction of held-out challenges detected as abnormal.

    This is intentionally a simple baseline metric; richer calibration and OOD
    metrics belong in the evaluation layer once model scores are available.
    """
    if not held_out_predictions:
        raise ValueError("held_out_predictions cannot be empty")
    return sum(held_out_predictions) / len(held_out_predictions)
