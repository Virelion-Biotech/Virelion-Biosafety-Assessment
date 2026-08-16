"""Virelion Biotech biosafety level (BSL) assessment tool.

Public API::

    from biosafety_assessment import Inputs, CellType, GeneticMod, Vector, Scale, Use, Risk, assess

    result = assess(Inputs(
        cell_type=CellType.IPSC,
        genetic_mod=GeneticMod.STABLE,
        vector=Vector.LENTIVIRUS,
        scale=Scale.SMALL,
        use=Use.RESEARCH,
        risk=Risk.NONE,
    ))
    print(result.bsl_label, result.status_band)

Not a substitute for formal review. Final BSL determination is an
institutional decision made by your Institutional Biosafety Committee (IBC)
and Biosafety Officer.
"""

from .models import (
    AssessmentResult,
    CellType,
    GeneticMod,
    Inputs,
    Notes,
    Risk,
    Scale,
    Use,
    Vector,
)
from .rules import assess

__version__ = "1.0.0"

__all__ = [
    "AssessmentResult",
    "CellType",
    "GeneticMod",
    "Inputs",
    "Notes",
    "Risk",
    "Scale",
    "Use",
    "Vector",
    "assess",
    "__version__",
]
