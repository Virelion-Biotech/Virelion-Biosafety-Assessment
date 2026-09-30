"""Binary benchmark metrics with counts and explicit undefined denominators."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionMetrics:
    sensitivity: float | None
    specificity: float | None
    precision: float | None
    accuracy: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int


def _booleans(values: list[bool], name: str) -> None:
    if not values or any(type(value) is not bool for value in values):
        raise ValueError(f"{name} must contain nonempty boolean observations")


def detection_metrics(y_true: list[bool], y_pred: list[bool]) -> DetectionMetrics:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    _booleans(y_true, "y_true")
    _booleans(y_pred, "y_pred")
    tp = sum(a and b for a, b in zip(y_true, y_pred))
    tn = sum(not a and not b for a, b in zip(y_true, y_pred))
    fp = sum(not a and b for a, b in zip(y_true, y_pred))
    fn = sum(a and not b for a, b in zip(y_true, y_pred))
    return DetectionMetrics(tp / (tp + fn) if tp + fn else None,
                            tn / (tn + fp) if tn + fp else None,
                            tp / (tp + fp) if tp + fp else None,
                            (tp + tn) / len(y_true), tp, tn, fp, fn)


def held_out_rate(held_out_predictions: list[bool]) -> float:
    """Fraction detected in an already selected held-out abnormal cohort.

    This does not validate train/test separation or compare known performance.
    """
    _booleans(held_out_predictions, "held_out_predictions")
    return sum(held_out_predictions) / len(held_out_predictions)
