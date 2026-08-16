"""Biosafety level (BSL) suggestion engine.

This is a direct, line-for-line port of the ``assess()`` function from the
original single-page tool, so behavior (including note text and escalation
order) matches the earlier web version exactly. See ``tests/test_rules.py``
for scenario coverage.

This module only ever *raises* or holds the containment level and *adds*
advisory notes -- it never lowers a level or removes a flag once set.
"""

from __future__ import annotations

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


def assess(inputs: Inputs) -> AssessmentResult:
    notes = Notes()
    level = 2  # default: human/animal-cell-derived material under BSL-2 / BBP precautions
    flag = False
    enhanced = False  # BSL-2+ style practices without necessarily raising the numeric level

    # --- Baseline -----------------------------------------------------
    notes.controls.append("Class II biosafety cabinet for all open manipulations.")
    notes.controls.append(
        "Lab coat, gloves, eye protection; treat all human-derived material as "
        "potentially infectious."
    )
    notes.waste.append(
        "Decontaminate liquid/solid culture waste (e.g., autoclave or EPA-registered "
        "disinfectant) before disposal."
    )
    notes.waste.append(
        "Sharps and contaminated disposables into designated biohazard sharps/waste "
        "containers."
    )
    notes.training.append(
        "Institutional bloodborne pathogens / human-derived material handling training."
    )
    notes.training.append("Biosafety cabinet use and general BSL-2 practices training.")
    notes.docs.append(
        "IBC protocol registration covering the cell line(s) and any vectors, prior to "
        "starting work."
    )
    notes.docs.append(
        "Standard operating procedures for culture, passage, and waste decontamination "
        "on file."
    )

    # --- Cell type escalators ------------------------------------------
    if inputs.cell_type == CellType.PRIMARY:
        notes.controls.append(
            "Confirm donor/source screening status; apply universal precautions "
            "regardless of screening result."
        )
    if inputs.cell_type == CellType.NHP:
        enhanced = True
        flag = True
        notes.controls.append(
            "NHP-derived material: apply enhanced PPE and strict sharps controls; "
            "consider herpes B virus exposure protocol where applicable."
        )
        notes.training.append(
            "Species-specific NHP pathogen awareness training (e.g., B virus) per "
            "institutional policy."
        )
        notes.docs.append(
            "FLAG: NHP primary cells require explicit IBC review and may trigger "
            "additional occupational health requirements."
        )
    if inputs.cell_type == CellType.BBP_POSITIVE:
        enhanced = True
        flag = True
        notes.controls.append(
            "Known/suspected bloodborne pathogen\u2013positive material: enhanced PPE, "
            "double-gloving as policy requires, minimize aerosol and sharps."
        )
        notes.training.append(
            "Documented bloodborne pathogen training specific to the agent(s) of concern."
        )
        notes.docs.append(
            "FLAG: IBC and occupational health must be notified; exposure response plan "
            "specific to the agent must be on file."
        )

    # --- Genetic modification -------------------------------------------
    if inputs.genetic_mod == GeneticMod.TRANSIENT:
        notes.docs.append(
            "Note transfection reagent/construct identity in the protocol (map, "
            "selectable markers)."
        )
    if inputs.genetic_mod == GeneticMod.STABLE:
        notes.docs.append(
            "Document integration method and any selectable markers used for the "
            "stable line."
        )
        notes.training.append(
            "Training on handling genome-modified lines per IBC protocol conditions."
        )
    if inputs.genetic_mod == GeneticMod.ONCOGENIC:
        enhanced = True
        flag = True
        notes.controls.append(
            "Oncogenic / transforming insert: treat cultures and waste with heightened "
            "care; avoid sharps where possible."
        )
        notes.docs.append(
            "FLAG: constructs encoding known oncogenes or transforming products require "
            "explicit IBC risk assessment under the NIH Guidelines."
        )
        notes.training.append(
            "Brief personnel on oncogene-specific handling and spill response."
        )

    # --- Vector logic -----------------------------------------------------
    if inputs.vector == Vector.NONE:
        pass
    elif inputs.vector == Vector.AAV:
        notes.controls.append(
            "AAV manipulations performed in BSC; standard BSL-2 practices generally "
            "apply for replication-defective, helper-dependent constructs."
        )
        notes.docs.append(
            "Record AAV serotype and whether the construct meets institutional "
            "exempt/non-exempt criteria under the NIH Guidelines."
        )
        notes.training.append(
            "Vector-specific handling training for AAV (packaging system, helper "
            "plasmids if used)."
        )
    elif inputs.vector == Vector.ADENOVIRUS:
        notes.controls.append(
            "BSC use for all open steps; standard BSL-2 practices for E1-deleted, "
            "replication-defective adenoviral vectors."
        )
        notes.docs.append(
            "Confirm and document replication-competence testing status of the "
            "adenoviral prep."
        )
        notes.training.append("Vector-specific handling training for adenoviral vectors.")
    elif inputs.vector == Vector.LENTIVIRUS:
        enhanced = True
        notes.controls.append(
            'Enhanced BSL-2 ("BSL-2+") practices for lentiviral vector work: BSC use, '
            "aerosol-minimizing technique, sealed centrifuge rotors/buckets."
        )
        notes.waste.append(
            "Inactivate lentiviral-vector-contaminated waste with an effective "
            "disinfectant (e.g., appropriate bleach contact time) before disposal."
        )
        notes.docs.append(
            "Document vector generation (2nd/3rd gen), self-inactivating (SIN) design, "
            "and packaging plasmid set in the IBC protocol."
        )
        notes.training.append(
            "Vector-specific training on lentiviral handling, spill response, and "
            "needlestick/sharps exposure protocol."
        )
    elif inputs.vector == Vector.LENTI_HIGHTITER:
        enhanced = True
        flag = True
        notes.controls.append(
            "High-titer lentiviral production: enhanced BSL-2+ practices; sealed "
            "rotors, no open centrifugation, minimize volume outside BSC."
        )
        notes.controls.append(
            "Consider dedicated production space or campaign-based decontamination "
            "between runs."
        )
        notes.waste.append(
            "Inactivate all high-titer waste with validated contact time before "
            "disposal or autoclaving."
        )
        notes.docs.append(
            "FLAG: high-titer lentiviral production often requires IBC review of "
            "titer, scale, and packaging system before start."
        )
        notes.training.append(
            "Production-specific training on high-titer harvest, concentration, and "
            "spill response."
        )
        # Production-scale high-titer can push some institutions toward BSL-3 consideration
        if inputs.scale == Scale.PRODUCTION:
            level = max(level, 3)
            notes.docs.append(
                "FLAG: high-titer lentiviral production at bioreactor scale \u2014 many "
                "institutions require BSL-3 or a formal BSL-2+ suite assessment. "
                "Confirm with IBC before work."
            )
    elif inputs.vector == Vector.RETROVIRUS:
        enhanced = True
        flag = True
        notes.controls.append(
            "Enhanced BSL-2 practices for gammaretroviral vectors; sealed rotors for "
            "centrifugation, BSC for all open steps."
        )
        notes.waste.append(
            "Inactivate retroviral-vector-contaminated waste before disposal; confirm "
            "disinfectant efficacy against enveloped viruses."
        )
        notes.docs.append(
            "Document env pseudotype and replication-competent retrovirus (RCR) "
            "testing plan in the protocol."
        )
        notes.training.append(
            "Vector-specific training on retroviral handling and RCR testing procedures."
        )
        notes.controls.append(
            "FLAG: confirm replication-incompetence and packaging cell line status "
            "with IBC \u2014 amphotropic/ecotropic env choice affects host range risk."
        )
    elif inputs.vector == Vector.RCV:
        enhanced = True
        flag = True
        level = max(level, 3)
        notes.controls.append(
            "Replication-competent or untested vector: treat as higher-risk; full "
            "containment for all open steps; no open centrifugation."
        )
        notes.waste.append(
            "Inactivate all waste with a validated method; do not discard until "
            "competence status is resolved."
        )
        notes.docs.append(
            "FLAG: RCV or unknown competence requires immediate IBC notification and "
            "a dedicated risk assessment \u2014 work should not proceed under standard "
            "BSL-2 assumptions."
        )
        notes.training.append(
            "Specialized training on RCV response, spill, and exposure protocols "
            "before any manipulation."
        )
    elif inputs.vector == Vector.OTHER:
        flag = True
        notes.docs.append(
            "FLAG: vector not in standard categories \u2014 requires a dedicated IBC "
            "vector risk assessment before work begins."
        )

    # --- Scale --------------------------------------------------------
    if inputs.scale == Scale.SMALL:
        notes.controls.append(
            "Use sealed centrifuge safety cups for spins above bench-scale volumes."
        )
    if inputs.scale == Scale.PRODUCTION:
        notes.controls.append(
            "Prefer closed/functionally-closed bioreactor systems to reduce aerosol "
            "generation at scale."
        )
        notes.controls.append(
            "Dedicated equipment or validated decontamination between campaigns; "
            "consider a dedicated suite if throughput is sustained."
        )
        notes.training.append(
            "Scale-specific training on bioreactor operation, harvest, and "
            "closed-system sampling."
        )
        notes.docs.append(
            "Standard operating procedures specific to production-scale culture and "
            "harvest, reviewed by EHS."
        )

    # --- Intended use ---------------------------------------------------
    if inputs.use == Use.PRECLINICAL:
        notes.docs.append(
            "Cross-reference biosafety protocol with the study's GLP documentation "
            "package."
        )
    if inputs.use == Use.THERAPEUTIC:
        notes.docs.append(
            "Align biosafety documentation with GMP quality system records (batch "
            "records, deviation logs) \u2014 biosafety and quality review run in "
            "parallel, not as substitutes for each other."
        )
        notes.training.append(
            "Personnel qualification records maintained jointly with Quality for "
            "GMP-track work."
        )
    if inputs.use == Use.INVIVO:
        enhanced = True
        flag = True
        notes.controls.append(
            "In vivo work: animal housing and procedure rooms must meet institutional "
            "animal biosafety requirements; PPE for injection/surgical delivery."
        )
        notes.docs.append(
            "FLAG: coordinate IBC and IACUC review for vector/cell delivery into "
            "animals; shedding and carcass disposal plans required."
        )
        notes.training.append(
            "Animal biosafety and procedure-specific training (injection, surgery, "
            "necropsy as applicable)."
        )

    # --- Additional risk factors -----------------------------------------
    if inputs.risk == Risk.AEROSOL:
        enhanced = True
        flag = True
        notes.controls.append(
            "Aerosol-generating steps outside a BSC: relocate to BSC or use sealed "
            "systems; respiratory protection only if institutionally approved and "
            "fit-tested."
        )
        notes.docs.append(
            "FLAG: aerosol generation outside primary containment requires IBC/EHS "
            "review of procedure and controls."
        )
        # Aerosol + integrating high-risk vectors escalate further below
    if inputs.risk == Risk.SHARPS_HIGH:
        enhanced = True
        notes.controls.append(
            "High sharps/injection risk: engineered sharps, one-handed techniques, "
            "immediate disposal; consider safety needles."
        )
        notes.training.append(
            "Sharps safety and exposure response drill specific to this workflow."
        )
    if inputs.risk == Risk.RG3:
        level = max(level, 3)
        flag = True
        notes.controls.append(
            "Risk Group 3 / high-consequence agent: BSL-3 practices and facility "
            "requirements apply unless IBC formally assigns a lower level with "
            "documented justification."
        )
        notes.waste.append(
            "All waste handled under BSL-3 waste protocols; no removal from "
            "containment without validated inactivation."
        )
        notes.docs.append(
            "FLAG: RG3 or equivalent work requires full IBC approval, facility "
            "verification, and medical surveillance as mandated."
        )
        notes.training.append(
            "BSL-3 facility training and agent-specific SOP sign-off before access."
        )
    if inputs.risk == Risk.RG4:
        level = max(level, 4)
        flag = True
        notes.controls.append(
            "Risk Group 4 / maximum containment: BSL-4 facility, positive-pressure "
            "suits or equivalent, and fully contained laboratory systems are required."
        )
        notes.waste.append(
            "All materials remain under maximum containment until validated "
            "inactivation under BSL-4 procedures."
        )
        notes.docs.append(
            "FLAG: RG4 / select-agent maximum-containment work is outside standard "
            "cardiac stem-cell programs \u2014 requires federal registration, dedicated "
            "BSL-4 facility access, and full institutional + regulatory approval. Do "
            "not proceed without that chain of approval."
        )
        notes.training.append(
            "BSL-4 facility training, medical surveillance, and agent-specific "
            "clearance before any access."
        )

    # --- Combinations that further escalate ------------------------------
    if inputs.vector == Vector.LENTI_HIGHTITER and inputs.risk == Risk.AEROSOL:
        level = max(level, 3)
        flag = True
        notes.docs.append(
            "FLAG: high-titer lentivirus combined with aerosol outside BSC is "
            "treated as BSL-3\u2013equivalent until IBC assigns otherwise."
        )
    if inputs.vector == Vector.LENTI_HIGHTITER and inputs.scale == Scale.PRODUCTION:
        level = max(level, 3)
        flag = True
    if inputs.vector == Vector.RCV and (
        inputs.scale == Scale.PRODUCTION
        or inputs.risk == Risk.AEROSOL
        or inputs.use == Use.INVIVO
    ):
        level = max(level, 3)
        flag = True
        notes.docs.append(
            "FLAG: replication-competent vector at scale, with aerosols, or in vivo "
            "\u2014 maintain BSL-3 assumptions until IBC formally assigns otherwise."
        )
    if inputs.cell_type == CellType.BBP_POSITIVE and inputs.vector in (
        Vector.LENTIVIRUS,
        Vector.LENTI_HIGHTITER,
        Vector.RETROVIRUS,
        Vector.RCV,
    ):
        level = max(level, 3)
        flag = True
        notes.docs.append(
            "FLAG: BBP-positive material plus integrating or replication-competent "
            "vector \u2014 BSL-3 path until IBC and occupational health complete dual "
            "risk assessment."
        )
    if inputs.cell_type == CellType.NHP and (
        inputs.vector == Vector.LENTI_HIGHTITER
        or inputs.vector == Vector.RCV
        or inputs.risk == Risk.RG3
    ):
        level = max(level, 3)
        flag = True
        notes.docs.append(
            "FLAG: NHP material combined with high-titer/RCV vector or RG3 work "
            "\u2014 escalate containment and occupational health review."
        )
    if inputs.genetic_mod == GeneticMod.ONCOGENIC and (
        inputs.vector == Vector.LENTI_HIGHTITER
        or inputs.vector == Vector.RCV
        or inputs.scale == Scale.PRODUCTION
    ):
        level = max(level, 3)
        flag = True
        notes.docs.append(
            "FLAG: oncogenic/transforming insert with high-titer, RCV, or production "
            "scale \u2014 IBC must confirm containment before work."
        )
    if inputs.use == Use.INVIVO and (inputs.vector == Vector.RCV or inputs.risk == Risk.RG3):
        level = max(level, 3)
        flag = True

    return AssessmentResult(level=level, flag=flag, enhanced=enhanced, notes=notes)
