"""Example: use biosafety_assessment as a library, e.g. inside a notebook,
a lab intake form backend, or a batch script that checks many protocols
at once.

Run with:
    python examples/example_usage.py
"""

from biosafety_assessment import CellType, GeneticMod, Inputs, Risk, Scale, Use, Vector, assess
from biosafety_assessment.export import text_summary

protocols = [
    Inputs(
        cell_type=CellType.IPSC,
        genetic_mod=GeneticMod.STABLE,
        vector=Vector.LENTIVIRUS,
        scale=Scale.SMALL,
        use=Use.RESEARCH,
        risk=Risk.NONE,
    ),
    Inputs(
        cell_type=CellType.NHP,
        genetic_mod=GeneticMod.TRANSIENT,
        vector=Vector.LENTI_HIGHTITER,
        scale=Scale.PRODUCTION,
        use=Use.PRECLINICAL,
        risk=Risk.NONE,
    ),
]

for i, protocol in enumerate(protocols, start=1):
    result = assess(protocol)
    print(f"--- Protocol {i}: {result.bsl_label} ({result.status_band}) ---")

print()
print(text_summary(protocols[-1], assess(protocols[-1])))
