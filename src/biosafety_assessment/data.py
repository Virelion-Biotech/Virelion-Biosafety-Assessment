"""Option catalogue (label + description) for each of the six assessment steps.

This is the single source of truth used to render the CLI wizard menus and to
look up human-readable labels for reports/exports. Kept in original form/order
from the source web tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .models import CellType, GeneticMod, Risk, Scale, Use, Vector

T = TypeVar("T")


@dataclass(frozen=True)
class Option(Generic[T]):
    value: T
    label: str
    desc: str


@dataclass(frozen=True)
class Step(Generic[T]):
    number: str
    key: str
    title: str
    hint: str
    options: tuple[Option[T], ...]

    def label_for(self, value: T) -> str:
        for opt in self.options:
            if opt.value == value:
                return opt.label
        return str(value)


CELL_TYPE_STEP: Step[CellType] = Step(
    number="01",
    key="cell_type",
    title="Cell type",
    hint="What is the base material being cultured?",
    options=(
        Option(CellType.IPSC, "iPSC", "Induced pluripotent stem cell line"),
        Option(CellType.ESC_CM, "ESC-derived CM", "Embryonic stem cell\u2013derived cardiomyocyte"),
        Option(CellType.PRIMARY, "Primary cells", "Directly isolated human/animal tissue"),
        Option(CellType.NHP, "NHP primary cells", "Non-human primate tissue / cells"),
        Option(CellType.BBP_POSITIVE, "Known BBP-positive", "Material known/suspected to contain bloodborne pathogens"),
    ),
)

GENETIC_MOD_STEP: Step[GeneticMod] = Step(
    number="02",
    key="genetic_mod",
    title="Genetic modification",
    hint="How is the genome or expression state altered, if at all?",
    options=(
        Option(GeneticMod.NONE, "None", "Unmodified line"),
        Option(GeneticMod.TRANSIENT, "Transient", "Plasmid, mRNA, or RNP transfection"),
        Option(GeneticMod.STABLE, "Stable integration", "Genome-integrated construct or reporter"),
        Option(GeneticMod.ONCOGENIC, "Oncogenic / transforming insert", "Known oncogene, toxin, or transforming gene product"),
    ),
)

VECTOR_STEP: Step[Vector] = Step(
    number="03",
    key="vector",
    title="Viral vector(s) used",
    hint="Select the delivery system, if any",
    options=(
        Option(Vector.NONE, "None", "No viral delivery system"),
        Option(Vector.AAV, "AAV", "Adeno-associated virus"),
        Option(Vector.LENTIVIRUS, "Lentivirus", "Typically 2nd/3rd-gen, SIN"),
        Option(Vector.LENTI_HIGHTITER, "Lentivirus \u2014 high-titer production", "Large-scale or concentrated high-titer prep"),
        Option(Vector.RETROVIRUS, "Retrovirus", "Gammaretroviral vector"),
        Option(Vector.ADENOVIRUS, "Adenovirus", "E1-deleted, replication-defective"),
        Option(Vector.RCV, "RCV / unknown competence", "Replication-competent or untested for competence"),
        Option(Vector.OTHER, "Other / unsure", "Requires IBC vector-specific review"),
    ),
)

SCALE_STEP: Step[Scale] = Step(
    number="04",
    key="scale",
    title="Scale",
    hint="Working volume for the largest single step",
    options=(
        Option(Scale.BENCH, "Bench", "< 10 mL"),
        Option(Scale.SMALL, "Small scale", "10\u2013100 mL"),
        Option(Scale.PRODUCTION, "Production / bioreactor", "> 100 mL or closed bioreactor"),
    ),
)

USE_STEP: Step[Use] = Step(
    number="05",
    key="use",
    title="Intended use",
    hint="Downstream purpose of this work",
    options=(
        Option(Use.RESEARCH, "Basic research", "In-house, non-GLP"),
        Option(Use.PRECLINICAL, "Preclinical", "GLP-adjacent studies"),
        Option(Use.THERAPEUTIC, "Therapeutic manufacturing", "GMP-track, clinical intent"),
        Option(Use.INVIVO, "In vivo animal work", "Vector or cell delivery into live animals"),
    ),
)

RISK_STEP: Step[Risk] = Step(
    number="06",
    key="risk",
    title="Additional risk factors",
    hint="Select the highest applicable factor, or none",
    options=(
        Option(Risk.NONE, "None", "No additional escalators"),
        Option(Risk.AEROSOL, "Aerosol outside BSC", "Aerosol-generating steps not fully contained in a BSC"),
        Option(Risk.SHARPS_HIGH, "High sharps / injection risk", "Frequent needles, catheters, or surgical delivery"),
        Option(Risk.RG3, "RG3 / high-consequence agent", "Risk Group 3 organism or equivalent work"),
        Option(Risk.RG4, "RG4 / maximum containment", "Risk Group 4 or select-agent maximum-containment work"),
    ),
)

STEPS: tuple[Step, ...] = (
    CELL_TYPE_STEP,
    GENETIC_MOD_STEP,
    VECTOR_STEP,
    SCALE_STEP,
    USE_STEP,
    RISK_STEP,
)

SOURCES: tuple[str, ...] = (
    "CDC/NIH Biosafety in Microbiological and Biomedical Laboratories (BMBL), 6th ed.",
    "NIH Guidelines for Research Involving Recombinant or Synthetic Nucleic Acid Molecules",
    "WHO Laboratory Biosafety Manual, 4th ed.",
)

DISCLAIMER = (
    "This tool generates a general planning reference drawn from publicly available "
    "CDC/NIH (BMBL, 6th ed.; NIH Guidelines for Research Involving Recombinant or "
    "Synthetic Nucleic Acid Molecules) and WHO (Laboratory Biosafety Manual, 4th ed.) "
    "guidance. It does not replace formal review, protocol registration, or sign-off "
    "by your Institutional Biosafety Committee (IBC) and Biosafety Officer. Final BSL "
    "determination is an institutional decision."
)
