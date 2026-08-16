from biosafety_assessment import (
    CellType,
    GeneticMod,
    Inputs,
    Risk,
    Scale,
    Use,
    Vector,
    assess,
)


def make_inputs(**overrides) -> Inputs:
    defaults = dict(
        cell_type=CellType.IPSC,
        genetic_mod=GeneticMod.NONE,
        vector=Vector.NONE,
        scale=Scale.BENCH,
        use=Use.RESEARCH,
        risk=Risk.NONE,
    )
    defaults.update(overrides)
    return Inputs(**defaults)


def test_baseline_is_standard_bsl2():
    result = assess(make_inputs())
    assert result.level == 2
    assert result.flag is False
    assert result.enhanced is False
    assert result.bsl_label == "BSL-2"
    assert result.review_required is False
    assert "Class II biosafety cabinet for all open manipulations." in result.notes.controls


def test_lentivirus_is_enhanced_but_not_flagged():
    result = assess(make_inputs(vector=Vector.LENTIVIRUS))
    assert result.level == 2
    assert result.enhanced is True
    assert result.flag is False
    assert result.bsl_label == "BSL-2+"


def test_high_titer_lentivirus_bench_scale_is_flagged_not_bsl3():
    result = assess(make_inputs(vector=Vector.LENTI_HIGHTITER, scale=Scale.BENCH))
    assert result.level == 2
    assert result.flag is True
    assert result.enhanced is True
    assert result.bsl_label == "BSL-2+"


def test_high_titer_lentivirus_at_production_scale_escalates_to_bsl3():
    result = assess(make_inputs(vector=Vector.LENTI_HIGHTITER, scale=Scale.PRODUCTION))
    assert result.level == 3
    assert result.flag is True
    assert result.review_required is True


def test_rcv_forces_bsl3():
    result = assess(make_inputs(vector=Vector.RCV))
    assert result.level == 3
    assert result.flag is True
    assert result.enhanced is True


def test_rg3_forces_bsl3():
    result = assess(make_inputs(risk=Risk.RG3))
    assert result.level == 3
    assert result.flag is True


def test_rg4_forces_bsl4():
    result = assess(make_inputs(risk=Risk.RG4))
    assert result.level == 4
    assert result.flag is True
    assert result.bsl_label == "BSL-4"
    assert "BSL-4 PATH" in result.status_band


def test_high_titer_lentivirus_plus_aerosol_escalates_to_bsl3():
    result = assess(make_inputs(vector=Vector.LENTI_HIGHTITER, risk=Risk.AEROSOL))
    assert result.level == 3
    assert result.flag is True


def test_bbp_positive_plus_lentivirus_escalates_to_bsl3():
    result = assess(make_inputs(cell_type=CellType.BBP_POSITIVE, vector=Vector.LENTIVIRUS))
    assert result.level == 3
    assert result.flag is True


def test_bbp_positive_plus_aav_does_not_escalate_to_bsl3():
    # AAV is not in the integrating/replication-competent vector list for this combo rule.
    result = assess(make_inputs(cell_type=CellType.BBP_POSITIVE, vector=Vector.AAV))
    assert result.level == 2
    assert result.flag is True  # still flagged from BBP-positive alone
    assert result.enhanced is True


def test_nhp_plus_high_titer_escalates_to_bsl3():
    result = assess(make_inputs(cell_type=CellType.NHP, vector=Vector.LENTI_HIGHTITER))
    assert result.level == 3
    assert result.flag is True


def test_oncogenic_plus_production_scale_escalates_to_bsl3():
    result = assess(
        make_inputs(genetic_mod=GeneticMod.ONCOGENIC, vector=Vector.AAV, scale=Scale.PRODUCTION)
    )
    assert result.level == 3
    assert result.flag is True


def test_invivo_plus_rcv_is_bsl3():
    result = assess(make_inputs(use=Use.INVIVO, vector=Vector.RCV))
    assert result.level == 3
    assert result.flag is True


def test_other_vector_flags_without_raising_level():
    result = assess(make_inputs(vector=Vector.OTHER))
    assert result.level == 2
    assert result.flag is True


def test_plus_suffix_only_applies_below_bsl3():
    below = assess(make_inputs(vector=Vector.LENTIVIRUS))
    assert below.plus is True
    at_or_above = assess(make_inputs(risk=Risk.RG3))
    assert at_or_above.plus is False


def test_status_band_progression():
    assert assess(make_inputs()).status_band.startswith("STANDARD")
    assert assess(make_inputs(vector=Vector.LENTIVIRUS)).status_band == (
        "ENHANCED BSL-2 PRACTICES APPLY"
    )
    assert assess(make_inputs(vector=Vector.OTHER)).status_band == (
        "REVIEW REQUIRED \u2014 SEE FLAGGED ITEMS"
    )
    assert "BSL-3 PATH" in assess(make_inputs(risk=Risk.RG3)).status_band
    assert "BSL-4 PATH" in assess(make_inputs(risk=Risk.RG4)).status_band
