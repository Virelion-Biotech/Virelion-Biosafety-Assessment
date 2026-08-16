"""Report generation: plain-text summary and JSON export."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from . import data
from .models import AssessmentResult, Inputs

BANNER = "VIRELION BIOTECH \u2014 BIOSAFETY LEVEL ASSESSMENT SUMMARY"


def text_summary(inputs: Inputs, result: AssessmentResult, generated_at: datetime | None = None) -> str:
    """Render the same plain-text summary the original tool exported as .txt."""
    now = generated_at or datetime.now()
    lines: list[str] = []
    lines.append(BANNER)
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("INPUTS")
    lines.append(f"  Cell type:            {data.CELL_TYPE_STEP.label_for(inputs.cell_type)}")
    lines.append(f"  Genetic modification: {data.GENETIC_MOD_STEP.label_for(inputs.genetic_mod)}")
    lines.append(f"  Viral vector:         {data.VECTOR_STEP.label_for(inputs.vector)}")
    lines.append(f"  Scale:                {data.SCALE_STEP.label_for(inputs.scale)}")
    lines.append(f"  Intended use:         {data.USE_STEP.label_for(inputs.use)}")
    lines.append(f"  Additional risk:      {data.RISK_STEP.label_for(inputs.risk)}")
    lines.append("")
    review_suffix = " (REVIEW REQUIRED)" if result.review_required else ""
    lines.append(f"SUGGESTED CONTAINMENT: {result.bsl_label}{review_suffix}")
    lines.append("")

    def section(title: str, items: list[str]) -> None:
        lines.append(title.upper())
        for item in items:
            lines.append(f"  - {item}")
        lines.append("")

    section("Engineering controls & PPE", result.notes.controls)
    section("Waste handling", result.notes.waste)
    section("Training", result.notes.training)
    section("Documentation", result.notes.docs)

    lines.append("-" * 60)
    lines.append(
        "This is a general planning reference based on public CDC/NIH BMBL, NIH "
        "Guidelines for"
    )
    lines.append(
        "rDNA Research, and WHO Laboratory Biosafety Manual guidance. It is not a "
        "substitute for"
    )
    lines.append(
        "formal review and approval by your Institutional Biosafety Committee / "
        "Biosafety Officer."
    )
    return "\n".join(lines)


def json_summary(inputs: Inputs, result: AssessmentResult, generated_at: datetime | None = None) -> str:
    """Render a machine-readable JSON export (useful for CI / scripted checks)."""
    now = generated_at or datetime.now()
    payload = {
        "generated_at": now.isoformat(timespec="seconds"),
        "inputs": {
            "cell_type": inputs.cell_type.value,
            "genetic_mod": inputs.genetic_mod.value,
            "vector": inputs.vector.value,
            "scale": inputs.scale.value,
            "use": inputs.use.value,
            "risk": inputs.risk.value,
        },
        "inputs_labels": {
            "cell_type": data.CELL_TYPE_STEP.label_for(inputs.cell_type),
            "genetic_mod": data.GENETIC_MOD_STEP.label_for(inputs.genetic_mod),
            "vector": data.VECTOR_STEP.label_for(inputs.vector),
            "scale": data.SCALE_STEP.label_for(inputs.scale),
            "use": data.USE_STEP.label_for(inputs.use),
            "risk": data.RISK_STEP.label_for(inputs.risk),
        },
        "result": {
            "bsl_label": result.bsl_label,
            "level": result.level,
            "flag": result.flag,
            "enhanced": result.enhanced,
            "review_required": result.review_required,
            "status_band": result.status_band,
            "summary_text": result.summary_text,
            "notes": asdict(result.notes),
        },
        "sources": list(data.SOURCES),
        "disclaimer": data.DISCLAIMER,
    }
    return json.dumps(payload, indent=2)


def default_filename(now: datetime | None = None, ext: str = "txt") -> str:
    now = now or datetime.now()
    return f"virelion-bsa-summary-{now.strftime('%Y-%m-%d')}.{ext}"
