"""Typed data models for the Virelion biosafety level (BSL) assessment tool.

These mirror the six form fields from the original web tool 1:1, plus the
result shape produced by the assessment engine in :mod:`rules`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CellType(str, Enum):
    IPSC = "ipsc"
    ESC_CM = "esc_cm"
    PRIMARY = "primary"
    NHP = "nhp"
    BBP_POSITIVE = "bbp_positive"


class GeneticMod(str, Enum):
    NONE = "none"
    TRANSIENT = "transient"
    STABLE = "stable"
    ONCOGENIC = "oncogenic"


class Vector(str, Enum):
    NONE = "none"
    AAV = "aav"
    LENTIVIRUS = "lentivirus"
    LENTI_HIGHTITER = "lenti_hightiter"
    RETROVIRUS = "retrovirus"
    ADENOVIRUS = "adenovirus"
    RCV = "rcv"
    OTHER = "other"


class Scale(str, Enum):
    BENCH = "bench"
    SMALL = "small"
    PRODUCTION = "production"


class Use(str, Enum):
    RESEARCH = "research"
    PRECLINICAL = "preclinical"
    THERAPEUTIC = "therapeutic"
    INVIVO = "invivo"


class Risk(str, Enum):
    NONE = "none"
    AEROSOL = "aerosol"
    SHARPS_HIGH = "sharps_high"
    RG3 = "rg3"
    RG4 = "rg4"


@dataclass(frozen=True)
class Inputs:
    """The six assessment inputs, one per wizard step."""

    cell_type: CellType
    genetic_mod: GeneticMod
    vector: Vector
    scale: Scale
    use: Use
    risk: Risk


@dataclass
class Notes:
    controls: list[str] = field(default_factory=list)
    waste: list[str] = field(default_factory=list)
    training: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "controls": list(self.controls),
            "waste": list(self.waste),
            "training": list(self.training),
            "docs": list(self.docs),
        }


@dataclass
class AssessmentResult:
    """Output of :func:`biosafety_assessment.rules.assess`."""

    level: int
    flag: bool
    enhanced: bool
    notes: Notes

    @property
    def plus(self) -> bool:
        """True when BSL-2 (or below) work carries BSL-2+ / flagged conditions."""
        return self.level < 3 and (self.flag or self.enhanced)

    @property
    def bsl_label(self) -> str:
        return f"BSL-{self.level}{'+' if self.plus else ''}"

    @property
    def review_required(self) -> bool:
        return self.flag or self.level >= 3

    @property
    def status_band(self) -> str:
        """Short uppercase status band, matching the original placard."""
        if self.level >= 4:
            return "BSL-4 PATH \u2014 MAXIMUM CONTAINMENT / REGULATORY APPROVAL"
        if self.level >= 3:
            return "BSL-3 PATH \u2014 IBC APPROVAL REQUIRED"
        if self.flag:
            return "REVIEW REQUIRED \u2014 SEE FLAGGED ITEMS"
        if self.enhanced:
            return "ENHANCED BSL-2 PRACTICES APPLY"
        return f"STANDARD BSL-{self.level} PRACTICES APPLY"

    @property
    def status_severity(self) -> str:
        """One of 'red', 'amber', 'green' -- for CLI colorization."""
        if self.level >= 3 or self.flag:
            return "red"
        if self.enhanced:
            return "amber"
        return "green"

    @property
    def summary_text(self) -> str:
        if self.level >= 4:
            return (
                "Maximum containment suggested. Federal registration, BSL-4 facility "
                "access, and full institutional + regulatory approval are required "
                "before any work."
            )
        if self.level >= 3:
            return (
                "Suggested higher containment. IBC must confirm facility, practices, "
                "and approval before any work begins."
            )
        if self.flag:
            return (
                "Suggested minimum containment with flagged items requiring IBC "
                "review before work begins."
            )
        if self.enhanced:
            return (
                "Suggested BSL-2 with enhanced practices (BSL-2+) for the selected "
                "vector or procedure."
            )
        return "Suggested minimum containment level for the selected parameters."
