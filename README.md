# virelion-biosafety-assessment

**Biosafety Level (BSL) Assessment Tool** for cardiac stem-cell and gene-therapy laboratory work — now a Python package/CLI instead of a single-page web app.

A six-step planning aid that suggests a minimum biosafety level and related engineering controls, waste handling, training, and documentation notes, based on public CDC/NIH and WHO guidance. Built for iPSC / ESC-derived cardiomyocyte / primary-cell and viral-vector workflows.

> **Not a substitute for formal review.** Final BSL determination is an institutional decision. This tool does not replace protocol registration or sign-off by an Institutional Biosafety Committee (IBC) or Biosafety Officer.

## Why a Python package instead of the web app

This started as a single `index.html` file. This repo re-implements the same assessment logic as a small, tested Python library + CLI so it can be:

- installed and run from a terminal (`virelion-bsa`) or scripted (`python -m biosafety_assessment`)
- imported as a library in a notebook, intake form backend, or batch script (`from biosafety_assessment import assess, Inputs, ...`)
- used non-interactively in CI to sanity-check protocol metadata against expected containment levels
- unit tested — the full escalation logic is covered in `tests/test_rules.py`

## Install

```bash
git clone https://github.com/Virelion-Biotech/virelion-biosafety-assessment.git
cd virelion-biosafety-assessment
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Requires Python 3.10+. No third-party runtime dependencies.

## Usage

### Interactive wizard

```bash
virelion-bsa
```

Walks through the six steps (cell type → genetic modification → viral vector → scale → intended use → additional risk factors) and prints the suggested containment placard plus controls/waste/training/documentation notes.

### Non-interactive / scripted

Pass every field as a flag to skip the wizard — useful in CI or shell scripts:

```bash
virelion-bsa \
  --cell-type ipsc \
  --genetic-mod stable \
  --vector lentivirus \
  --scale small \
  --use research \
  --risk none \
  --export summary.txt \
  --json summary.json
```

Run `virelion-bsa --help` for the full list of accepted values for each flag.

### As a library

```python
from biosafety_assessment import assess, Inputs, CellType, GeneticMod, Vector, Scale, Use, Risk

result = assess(Inputs(
    cell_type=CellType.NHP,
    genetic_mod=GeneticMod.TRANSIENT,
    vector=Vector.LENTI_HIGHTITER,
    scale=Scale.PRODUCTION,
    use=Use.PRECLINICAL,
    risk=Risk.NONE,
))

print(result.bsl_label)        # "BSL-3"
print(result.status_band)      # "BSL-3 PATH — IBC APPROVAL REQUIRED"
print(result.notes.controls)   # list of engineering-control notes
```

See `examples/example_usage.py` for a batch-checking example.

## Repo layout

```
src/biosafety_assessment/
  models.py    # enums for the 6 inputs + AssessmentResult dataclass
  data.py      # option labels/descriptions for each step (single source of truth)
  rules.py     # the assessment engine (assess()) — ported 1:1 from the original tool
  export.py    # plain-text and JSON report generation
  cli.py       # interactive wizard + argparse-driven scriptable CLI
  __main__.py  # `python -m biosafety_assessment` entry point
tests/         # pytest suite covering baseline + every escalation/combination path
examples/      # example_usage.py — library usage outside the CLI
```

## Cell types covered

| Option | Notes |
|--------|--------|
| iPSC | Induced pluripotent stem cell line |
| ESC-derived CM | Embryonic stem cell–derived cardiomyocyte |
| Primary cells | Directly isolated human/animal tissue |
| NHP primary cells | Non-human primate tissue / cells (escalates review) |
| Known BBP-positive | Material known/suspected to contain bloodborne pathogens |

## Vectors covered

- None
- AAV (adeno-associated virus)
- Lentivirus (typically 2nd/3rd-gen, SIN) → enhanced BSL-2
- Lentivirus — high-titer production → enhanced; may path to BSL-3 at production scale
- Retrovirus (gammaretroviral)
- Adenovirus (E1-deleted, replication-defective)
- RCV / unknown competence → BSL-3 path + IBC flag
- Other / unsure → IBC review flag

## Higher-risk escalators

- Oncogenic / transforming insert
- In vivo animal work
- Aerosol generation outside BSC
- High sharps / injection risk
- RG3 / high-consequence agent → BSL-3 path
- RG4 / maximum containment → BSL-4 path (regulatory + BSL-4 facility required)
- Combinations that force BSL-3 include high-titer at production scale, RCV + aerosol/in vivo, BBP-positive + integrating vector, and related pairs.

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

## Sources (public guidance)

- CDC/NIH *Biosafety in Microbiological and Biomedical Laboratories* (BMBL), 6th ed.
- NIH *Guidelines for Research Involving Recombinant or Synthetic Nucleic Acid Molecules*
- WHO *Laboratory Biosafety Manual*, 4th ed.

## License

MIT — see [LICENSE](LICENSE).
