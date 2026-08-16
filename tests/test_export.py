import json
from datetime import datetime

from biosafety_assessment import CellType, GeneticMod, Inputs, Risk, Scale, Use, Vector, assess
from biosafety_assessment.export import default_filename, json_summary, text_summary


def sample_inputs() -> Inputs:
    return Inputs(
        cell_type=CellType.IPSC,
        genetic_mod=GeneticMod.STABLE,
        vector=Vector.LENTIVIRUS,
        scale=Scale.SMALL,
        use=Use.RESEARCH,
        risk=Risk.NONE,
    )


def test_text_summary_contains_key_fields():
    inputs = sample_inputs()
    result = assess(inputs)
    text = text_summary(inputs, result, generated_at=datetime(2026, 1, 1, 9, 0, 0))
    assert "VIRELION BIOTECH" in text
    assert "SUGGESTED CONTAINMENT: BSL-2+" in text
    assert "Cell type:            iPSC" in text
    assert "ENGINEERING CONTROLS & PPE" in text
    assert "Generated: 2026-01-01 09:00:00" in text


def test_json_summary_round_trips():
    inputs = sample_inputs()
    result = assess(inputs)
    payload = json.loads(json_summary(inputs, result, generated_at=datetime(2026, 1, 1)))
    assert payload["inputs"]["vector"] == "lentivirus"
    assert payload["result"]["level"] == 2
    assert payload["result"]["bsl_label"] == "BSL-2+"
    assert "controls" in payload["result"]["notes"]


def test_default_filename_format():
    name = default_filename(datetime(2026, 3, 4), ext="json")
    assert name == "virelion-bsa-summary-2026-03-04.json"
