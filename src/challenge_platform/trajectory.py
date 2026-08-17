"""Temporal challenge trajectory utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrajectoryPoint:
    time_index: int
    severity: float


def validate_trajectory(values: tuple[float, ...]) -> None:
    if not values:
        raise ValueError("trajectory must contain at least one point")
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("trajectory values must be in [0, 1]")


def summarize_trajectory(values: tuple[float, ...]) -> tuple[float, float, float]:
    """Return onset, peak, and terminal severity for a normalized trajectory."""
    validate_trajectory(values)
    return values[0], max(values), values[-1]


def resample_trajectory(values: tuple[float, ...], points: int) -> tuple[TrajectoryPoint, ...]:
    """Linearly resample a normalized trajectory to a fixed number of points."""
    validate_trajectory(values)
    if points < 1:
        raise ValueError("points must be >= 1")
    if points == 1:
        return (TrajectoryPoint(0, values[0]),)
    if len(values) == 1:
        return tuple(TrajectoryPoint(i, values[0]) for i in range(points))

    result: list[TrajectoryPoint] = []
    scale = (len(values) - 1) / (points - 1)
    for index in range(points):
        position = index * scale
        left = int(position)
        right = min(left + 1, len(values) - 1)
        fraction = position - left
        severity = values[left] + (values[right] - values[left]) * fraction
        result.append(TrajectoryPoint(index, severity))
    return tuple(result)
